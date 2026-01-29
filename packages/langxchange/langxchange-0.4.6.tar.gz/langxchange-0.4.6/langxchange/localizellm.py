# langxchange/localizellm.py
"""
LocalizeLLM - Advanced Local Language Model Management and Fine-tuning
Enhanced with local model downloading, management, and fine-tuning capabilities
Author: Langxchange
Version: v0.2.2
Date: 2025-07-12
"""

import os
import json
import logging
import shutil
import hashlib
import tempfile
import gc
import torch
import torch.nn as nn
from pathlib import Path
from typing import List, Dict, Union, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from tqdm import tqdm

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline,
    GenerationConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from torch.utils.data import Dataset, DataLoader
from sentence_transformers import SentenceTransformer
from huggingface_hub import snapshot_download, login


@dataclass
class LocalLLMConfig:
    """Configuration class for LocalizeLLM settings."""
    chat_model: str = "meta-llama/Llama-2-7b-chat-hf"
    embed_model: str = "all-MiniLM-L6-v2"
    hf_token: Optional[str] = None
    device: Optional[str] = None
    max_memory_per_gpu: Optional[str] = "8GB"
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    local_models_dir: str = "./local_models"
    cache_dir: Optional[str] = None
    trust_remote_code: bool = False
    learning_rate: float = 5e-5
    batch_size: int = 4
    max_epochs: int = 3
    warmup_steps: int = 100
    max_length: int = 512
    gradient_accumulation_steps: int = 1
    fp16: bool = True
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: List[str] = None


@dataclass
class ModelInfo:
    """Information about a local model."""
    name: str
    path: str
    size_gb: float
    download_date: str
    model_type: str
    config_hash: str
    fine_tuned: bool = False
    fine_tune_info: Optional[Dict] = None


class CustomDataset(Dataset):
    """Custom dataset class for fine-tuning."""
    def __init__(self, texts: List[str], tokenizer, max_length: int = 512):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': encoding['input_ids'].flatten()
        }


class LocalizeLLM:
    """
    Advanced Local Language Model Manager with fine-tuning capabilities.
    """

    def __init__(self, config: Optional[LocalLLMConfig] = None, **kwargs):
        self._setup_logging()
        self.config = config or LocalLLMConfig()
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        if self.config.target_modules is None:
            self.config.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]
        self._apply_env_defaults()
        self._setup_local_storage()
        self._validate_config()
        self.device = self._detect_device()
        self.tokenizer = None
        self.model = None
        self.generator = None
        self.embedder = None
        self.model_info = None
        self.trainer = None
        self.training_args = None
        self.logger.info(f"LocalizeLLM initialized on device: {self.device}")

    def _setup_logging(self) -> None:
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            os.makedirs("logs", exist_ok=True)
            fh = logging.FileHandler(f"logs/local_llm_{datetime.now():%Y%m%d}.log")
            fh.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            ))
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)
            self.logger.setLevel(logging.INFO)

    def _apply_env_defaults(self) -> None:
        if not self.config.chat_model:
            self.config.chat_model = os.getenv("LLAMA_CHAT_MODEL", self.config.chat_model)
        if not self.config.embed_model:
            self.config.embed_model = os.getenv("LLAMA_EMBED_MODEL", self.config.embed_model)
        if not self.config.hf_token:
            self.config.hf_token = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")
        if not self.config.cache_dir:
            self.config.cache_dir = os.getenv("HF_CACHE_DIR", f"{self.config.local_models_dir}/cache")

    def _setup_local_storage(self) -> None:
        self.local_models_path = Path(self.config.local_models_dir)
        self.local_models_path.mkdir(parents=True, exist_ok=True)
        for sub in ["models", "fine_tuned", "datasets", "checkpoints", "cache", "snapshots"]:
            (self.local_models_path / sub).mkdir(exist_ok=True)
        self.registry_file = self.local_models_path / "model_registry.json"
        self._load_model_registry()

    def _load_model_registry(self) -> None:
        if self.registry_file.exists():
            with open(self.registry_file) as f:
                data = json.load(f)
                self.model_registry = {k: ModelInfo(**v) for k, v in data.items()}
        else:
            self.model_registry = {}

    def _save_json_atomic(self, path: str, data: Any) -> None:
        dir_ = os.path.dirname(path)
        with tempfile.NamedTemporaryFile('w', dir=dir_, delete=False) as tf:
            json.dump(data, tf, indent=2)
            tmp = tf.name
        shutil.move(tmp, path)

    def _save_model_registry(self) -> None:
        data = {k: asdict(v) for k, v in self.model_registry.items()}
        self._save_json_atomic(str(self.registry_file), data)

    def _validate_config(self) -> None:
        if self.config.load_in_8bit and self.config.load_in_4bit:
            raise ValueError("Cannot use both 8-bit and 4-bit quantization.")
        if self.config.learning_rate <= 0:
            raise ValueError("Learning rate must be positive.")

    def _detect_device(self) -> str:
        if self.config.device:
            return self.config.device
        if torch.cuda.is_available():
            self.logger.info("CUDA available")
            return f"cuda:{torch.cuda.current_device()}"
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            self.logger.info("MPS available")
            return "mps"
        self.logger.info("Using CPU")
        return "cpu"

    def _calculate_file_hash(self, file_path: str) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()

    def _get_directory_size(self, path: Path) -> float:
        total = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return total / (1024 ** 3)

    def list_available_models(self) -> Dict[str, ModelInfo]:
        return self.model_registry.copy()

    def download_model(
        self,
        model_name: str,
        force_download: bool = False,
        progress_callback: Optional[callable] = None
    ) -> str:
        local_path = self.local_models_path / "models" / model_name.replace("/", "_")
        if local_path.exists() and not force_download and model_name in self.model_registry:
            self.logger.info(f"{model_name} exists locally.")
            return str(local_path)
        try:
            self.logger.info(f"Downloading {model_name}")
            if self.config.hf_token:
                login(token=self.config.hf_token, add_to_git_credential=False)
            snapshot_download(
                repo_id=model_name,
                local_dir=str(local_path),
                token=self.config.hf_token,
                cache_dir=self.config.cache_dir,
                resume_download=True
            )
            size = self._get_directory_size(local_path)
            cfg_hash = self._calculate_file_hash(str(local_path / "config.json"))
            info = ModelInfo(
                name=model_name,
                path=str(local_path),
                size_gb=size,
                download_date=datetime.now().isoformat(),
                model_type="base",
                config_hash=cfg_hash
            )
            self.model_registry[model_name] = info
            self._save_model_registry()
            self.logger.info(f"{model_name} downloaded ({size:.2f}GB)")
            return str(local_path)
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise RuntimeError(e)

    def load_local_model(self, model_identifier: str) -> None:
        try:
            if model_identifier in self.model_registry:
                model_path = self.model_registry[model_identifier].path
                model_name = model_identifier
            elif os.path.exists(model_identifier):
                model_path = model_identifier
                model_name = os.path.basename(model_identifier)
            else:
                model_path = self.download_model(model_identifier)
                model_name = model_identifier

            self.logger.info(f"Loading from {model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                local_files_only=True,
                trust_remote_code=self.config.trust_remote_code
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            load_kwargs = {
                "trust_remote_code": self.config.trust_remote_code,
                "torch_dtype": torch.float16 if self.config.fp16 else torch.float32
            }
            if self.device.startswith("cuda"):
                if self.config.load_in_8bit:
                    load_kwargs["load_in_8bit"] = True
                elif self.config.load_in_4bit:
                    load_kwargs["load_in_4bit"] = True
                else:
                    load_kwargs["device_map"] = "auto"
                    if self.config.max_memory_per_gpu:
                        load_kwargs["max_memory"] = {
                            i: self.config.max_memory_per_gpu
                            for i in range(torch.cuda.device_count())
                        }

            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                **load_kwargs,
                local_files_only=True
            )
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device.startswith("cuda") else -1
            )

            embed_path = model_path.replace("chat", "embed") if "chat" in model_path else None
            if embed_path and os.path.exists(embed_path):
                self.embedder = SentenceTransformer(embed_path, device=self.device)
            else:
                self.embedder = SentenceTransformer(
                    self.config.embed_model,
                    device=self.device,
                    cache_folder=self.config.cache_dir
                )

            self.model_info = self.model_registry.get(model_name)
            self.logger.info(f"{model_name} loaded successfully")
        except Exception as e:
            self.logger.error(f"Load failed: {e}")
            raise RuntimeError(e)

    def prepare_fine_tuning_data(
        self, texts: List[str], validation_split: float = 0.1
    ) -> Tuple[CustomDataset, CustomDataset]:
        if not self.tokenizer:
            raise RuntimeError("Load a model first.")
        import random
        random.shuffle(texts)
        idx = int(len(texts) * (1 - validation_split))
        train, val = texts[:idx], texts[idx:]
        self.logger.info(f"Prepared {len(train)} train, {len(val)} val samples")
        return (
            CustomDataset(train, self.tokenizer, self.config.max_length),
            CustomDataset(val, self.tokenizer, self.config.max_length)
        )

    def setup_lora_fine_tuning(self) -> None:
        try:
            from peft import LoraConfig, get_peft_model, TaskType
            cfg = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                inference_mode=False,
                r=self.config.lora_rank,
                lora_alpha=self.config.lora_alpha,
                lora_dropout=self.config.lora_dropout,
                target_modules=self.config.target_modules
            )
            self.model = get_peft_model(self.model, cfg)
            self.model.print_trainable_parameters()
            self.logger.info("LoRA setup done")
        except ImportError:
            self.logger.warning("PEFT not installed; full fine-tuning will be used.")

    def fine_tune_model(
        self,
        train_dataset: CustomDataset,
        val_dataset: Optional[CustomDataset] = None,
        output_dir: Optional[str] = None,
        experiment_name: Optional[str] = None,
        use_lora: bool = True
    ) -> str:
        if not self.model or not self.tokenizer:
            raise RuntimeError("Load a model first.")
        if not experiment_name:
            experiment_name = f"fine_tune_{datetime.now():%Y%m%d_%H%M%S}"
        out = output_dir or str(self.local_models_path / "fine_tuned" / experiment_name)
        os.makedirs(out, exist_ok=True)

        if use_lora:
            self.setup_lora_fine_tuning()

            self.training_args = TrainingArguments(
                output_dir=out,
                num_train_epochs=self.config.max_epochs,
                per_device_train_batch_size=self.config.batch_size,
                per_device_eval_batch_size=self.config.batch_size,
                gradient_accumulation_steps=self.config.gradient_accumulation_steps,
                warmup_steps=self.config.warmup_steps,
                learning_rate=self.config.learning_rate,
                fp16=self.config.fp16,

                # evaluate_during_training=True,   # deprecated but may exist in your version
                # evaluation_strategy="steps",    # <-- allows eval every `eval_steps`
                save_strategy="steps",     
                logging_steps=10,
                save_steps=500,
                eval_steps=500,

                save_total_limit=3,
                # load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                report_to=None,
                dataloader_pin_memory=False,
            )       

    #     self.training_args = TrainingArguments(
    #         output_dir=out,
    #         num_train_epochs=self.config.max_epochs,
    #         per_device_train_batch_size=self.config.batch_size,
    #         per_device_eval_batch_size=self.config.batch_size,
    #         gradient_accumulation_steps=self.config.gradient_accumulation_steps,
    #         warmup_steps=self.config.warmup_steps,
    #         learning_rate=self.config.learning_rate,
    #         fp16=self.config.fp16,

    # # ** Ensure eval happens so load_best_model_at_end works **
    #         evaluation_strategy="steps",
    #         save_strategy="steps",
    #         logging_steps=10,
    #         save_steps=500,
    #         eval_steps=500,

    #         save_total_limit=3,
    #         load_best_model_at_end=True,
    #         metric_for_best_model="eval_loss",
    #         report_to=None,
    #         dataloader_pin_memory=False,
    #     )

        # self.training_args = TrainingArguments(
        #     output_dir=out,
        #     num_train_epochs=self.config.max_epochs,
        #     per_device_train_batch_size=self.config.batch_size,
        #     per_device_eval_batch_size=self.config.batch_size,
        #     gradient_accumulation_steps=self.config.gradient_accumulation_steps,
        #     warmup_steps=self.config.warmup_steps,
        #     learning_rate=self.config.learning_rate,
        #     fp16=self.config.fp16,
        #     logging_steps=10,
        #     save_steps=500,
        #     eval_steps=500,
        #     save_total_limit=3,
        #     load_best_model_at_end=True,
        #     metric_for_best_model="eval_loss",
        #     report_to=None,
        #     dataloader_pin_memory=False
        # )
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
            pad_to_multiple_of=8 if self.config.fp16 else None
        )
        self.trainer = Trainer(
            model=self.model,
            args=self.training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer
        )
        self.logger.info(f"Starting fine-tuning: {experiment_name}")
        result = self.trainer.train()
        self.trainer.save_model()
        self.tokenizer.save_pretrained(out)

        info = {
            "experiment_name": experiment_name,
            "base_model": self.model_info.name if self.model_info else "",
            "training_loss": result.training_loss,
            "total_steps": result.global_step,
            "use_lora": use_lora,
            "config": asdict(self.config),
            "completion_date": datetime.now().isoformat()
        }
        self._save_json_atomic(f"{out}/training_info.json", info)

        fine_info = ModelInfo(
            name=experiment_name,
            path=out,
            size_gb=self._get_directory_size(Path(out)),
            download_date=datetime.now().isoformat(),
            model_type="fine_tuned",
            config_hash=hashlib.sha256(json.dumps(info).encode()).hexdigest(),
            fine_tuned=True,
            fine_tune_info=info
        )
        self.model_registry[experiment_name] = fine_info
        self._save_model_registry()

        self.logger.info(f"Fine-tune complete: {out}")
        return out

    def optimize_parameters(
        self,
        parameter_ranges: Dict[str, List],
        validation_dataset: CustomDataset,
        metric: str = "perplexity"
    ) -> Dict[str, Any]:
        from itertools import product
        if not self.model:
            raise RuntimeError("Load a model first.")

        names = list(parameter_ranges.keys())
        combos = list(product(*parameter_ranges.values()))
        best_score = float('inf') if metric in ['perplexity', 'loss'] else float('-inf')
        best_params = {}
        results = []

        loader = DataLoader(validation_dataset, batch_size=8)

        self.logger.info(f"Optimizing {len(combos)} combinations")
        for combo in combos:
            params = dict(zip(names, combo))
            try:
                gen_cfg = GenerationConfig(**params)
                total_loss, total = 0.0, 0
                self.model.eval()
                with torch.no_grad():
                    for batch in loader:
                        ids = batch['input_ids'].to(self.device)
                        mask = batch['attention_mask'].to(self.device)
                        lbl = batch['labels'].to(self.device)
                        out = self.model(input_ids=ids, attention_mask=mask, labels=lbl)
                        total_loss += out.loss.item() * ids.size(0)
                        total += ids.size(0)
                avg = total_loss / total
                perp = torch.exp(torch.tensor(avg)).item()
                score = perp if metric == 'perplexity' else avg
                results.append({'parameters': params, 'loss': avg, 'perplexity': perp, 'score': score})
                if ((metric in ['perplexity', 'loss'] and score < best_score) or
                    (metric not in ['perplexity', 'loss'] and score > best_score)):
                    best_score, best_params = score, params.copy()
            except Exception as e:
                self.logger.warning(f"Param combo failed {params}: {e}")
        results.sort(key=lambda x: x['score'], reverse=(metric not in ['perplexity', 'loss']))
        return {
            'best_parameters': best_params,
            'best_score': best_score,
            'metric': metric,
            'top_results': results[:10],
            'tested': len(results)
        }
    


    # def generate_text(self, prompt, max_new_tokens=None, temperature=0.7, top_p=0.9, repetition_penalty=1.1, **kwargs):
    #     if not self.generator:
    #         raise RuntimeError("Load a model first.")
    #     # sanitize sampling params
    #     temperature = max(0.5, min(temperature, 1.0))
    #     top_p       = max(0.8, min(top_p, 1.0))
    #     repetition_penalty = min(max(repetition_penalty, 1.0), 1.2)

    #     kw = {
    #         "do_sample": True,
    #         "temperature": temperature,
    #         "top_p": top_p,
    #         "repetition_penalty": repetition_penalty,
    #         "return_full_text": False,
    #         "pad_token_id": self.tokenizer.pad_token_id,
    #         **kwargs
    #     }
    #     # use only max_new_tokens
    #     kw["max_new_tokens"] = max_new_tokens or 256

    #     # patch forward to clamp bad logits
    #     import torch
    #     orig_forward = self.model.forward
    #     def safe_forward(**fwd_kwargs):
    #         out = orig_forward(**fwd_kwargs)
    #         out.logits = torch.nan_to_num(out.logits, nan=0.0, posinf=1e4, neginf=-1e4)
    #         return out
    #     self.model.forward = safe_forward

    #     try:
    #         res = self.generator(prompt, **kw)
    #         return res[0].get("generated_text", "").strip()
    #     finally:
    #         # restore
    #         self.model.forward = orig_forward

    def generate_text(
        self,
        prompt: str,
        max_length: int = 256,
        max_new_tokens: Optional[int] = None,
        temperature: float = 0.7,
        do_sample: bool = True,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        **kwargs
    ) -> Optional[str]:
        if not self.generator:
            raise RuntimeError("Load a model first.")
        if not prompt.strip():
            raise ValueError("Prompt must be non-empty.")
        try:
            kw = {
                "do_sample": do_sample,
                "temperature": temperature if do_sample else None,
                "top_p": top_p if do_sample else None,
                "top_k": top_k if do_sample else None,
                "repetition_penalty": repetition_penalty,
                "return_full_text": False,
                "pad_token_id": self.tokenizer.pad_token_id,
                **kwargs
            }
            if max_new_tokens is not None:
                kw["max_new_tokens"] = max_new_tokens
            else:
                kw["max_length"] = max_length
            kw = {k: v for k, v in kw.items() if v is not None}
            res = self.generator(prompt, **kw)
            return res[0].get("generated_text", "").strip()
        except Exception as e:
            self.logger.error(f"Text gen failed: {e}")
            return None

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        **kwargs
    ) -> Optional[str]:
        if not messages or not isinstance(messages, list):
            raise ValueError("Messages must be non-empty list.")
        try:
            if hasattr(self.tokenizer, 'apply_chat_template'):
                if system_prompt:
                    messages = [{"role": "system", "content": system_prompt}] + messages
                prompt = self.tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            else:
                prompt = self._format_chat_manually(messages, system_prompt)
            return self.generate_text(
                prompt=prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                **kwargs
            )
        except AttributeError:
            prompt = self._format_chat_manually(messages, system_prompt)
            return self.generate_text(
                prompt=prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                **kwargs
            )
        except Exception as e:
            self.logger.error(f"Chat failed: {e}")
            return None

    def _format_chat_manually(self, messages, system_prompt=None) -> str:
        parts = []
        if system_prompt:
            parts.append(f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>")
        for msg in messages:
            role = msg["role"]
            content = msg["content"].strip()
            if not content:
                continue
            if role == "user":
                parts.append(f"<s>[INST] {content} [/INST]")
            else:
                parts.append(f" {content} </s>")
        if not parts[-1].endswith("[/INST]"):
            parts.append("")
        return "".join(parts)

    def get_embedding(self, text: Union[str, List[str]]) -> Optional[Union[List[float], List[List[float]]]]:
        if not self.embedder:
            raise RuntimeError("Embedding model not loaded.")
        if isinstance(text, str) and not text.strip():
            raise ValueError("Text cannot be empty.")
        if isinstance(text, list) and (not text or not all(isinstance(t, str) and t.strip() for t in text)):
            raise ValueError("All texts must be non-empty strings.")
        try:
            embs = self.embedder.encode(text, convert_to_tensor=False)
            if isinstance(text, str):
                return embs.tolist() if hasattr(embs, "tolist") else list(embs)
            return [e.tolist() if hasattr(e, "tolist") else list(e) for e in embs]
        except Exception as e:
            self.logger.error(f"Embedding gen failed: {e}")
            return None

    def count_tokens(self, text: Union[str, List[str]]) -> Union[int, List[int]]:
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded.")
        if isinstance(text, str):
            return 0 if not text.strip() else len(self.tokenizer.encode(text, add_special_tokens=True))
        return [0 if not t.strip() else len(self.tokenizer.encode(t, add_special_tokens=True)) for t in text]

    def save_model_snapshot(self, name: str, description: str = "") -> str:
        if not self.model:
            raise RuntimeError("No model loaded.")
        snap = self.local_models_path / "snapshots" / name
        snap.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(str(snap))
        self.tokenizer.save_pretrained(str(snap))
        meta = {
            "name": name,
            "description": description,
            "base_model": self.model_info.name if self.model_info else "",
            "save_date": datetime.now().isoformat(),
            "config": asdict(self.config)
        }
        self._save_json_atomic(str(snap / "metadata.json"), meta)
        self.logger.info(f"Snapshot saved: {snap}")
        return str(snap)

    def load_model_snapshot(self, name: str) -> None:
        snap = self.local_models_path / "snapshots" / name
        if not snap.exists():
            raise FileNotFoundError(f"No snapshot '{name}'.")
        self.load_local_model(str(snap))
        self.logger.info(f"Snapshot loaded: {name}")

    def get_model_info(self) -> Dict[str, Any]:
        info = {
            "chat_model": self.config.chat_model,
            "embed_model": self.config.embed_model,
            "device": self.device,
            "local_models_dir": str(self.local_models_path),
            "total_local_models": len(self.model_registry),
        }
        if self.tokenizer:
            info.update({
                "vocab_size": self.tokenizer.vocab_size,
                "pad_token": self.tokenizer.pad_token,
                "eos_token": self.tokenizer.eos_token,
            })
        if self.model:
            info.update({
                "model_parameters": sum(p.numel() for p in self.model.parameters()),
                "trainable_parameters": sum(p.numel() for p in self.model.parameters() if p.requires_grad),
                "model_dtype": str(next(self.model.parameters()).dtype),
                "model_device": str(next(self.model.parameters()).device),
            })
        if self.model_info:
            info["current_model_info"] = asdict(self.model_info)
        return info

    def export_model(self, output_path: str, format: str = "pytorch") -> str:
        if not self.model:
            raise RuntimeError("No model loaded.")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if format.lower() == "pytorch":
            torch.save(
                {
                    'model_state_dict': self.model.state_dict(),
                    'config': asdict(self.config),
                    'tokenizer_config': self.tokenizer.save_vocabulary(os.path.dirname(output_path))
                },
                output_path
            )
        elif format.lower() == "onnx":
            import torch.onnx
            seq_len = self.config.max_length
            dummy = torch.randint(0, self.tokenizer.vocab_size, (1, seq_len)).to(self.device)
            torch.onnx.export(
                self.model, dummy, output_path,
                export_params=True,
                opset_version=11,
                do_constant_folding=True,
                input_names=['input_ids'],
                output_names=['logits'],
                dynamic_axes={
                    'input_ids': {0: 'batch_size', 1: 'sequence'},
                    'logits': {0: 'batch_size', 1: 'sequence'}
                }
            )
        else:
            raise ValueError(f"Unsupported format: {format}")
        self.logger.info(f"Exported model to {output_path}")
        return output_path

    def clear_cache(self) -> None:
        if self.device.startswith("cuda"):
            torch.cuda.empty_cache()
            gc.collect()
            self.logger.info("GPU cache cleared")

    def cleanup(self) -> None:
        try:
            for attr in ['model', 'generator', 'embedder', 'tokenizer', 'trainer']:
                if hasattr(self, attr) and getattr(self, attr):
                    delattr(self, attr)
            self.clear_cache()
            self.logger.info("Resources cleaned up")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

    def create_learning_report(
        self,
        dataset: Union[List[str], CustomDataset],
        output_path: str = "llm_report.md"
    ) -> None:
        """
        Generate a Markdown report covering:
        - Dataset overview
        - Model configuration
        - Fine-tuning metrics (if any)
        - Historical memory & GPU/CPU usage
        - Recommendations for next steps
        """
        # 1. Dataset overview
        if isinstance(dataset, CustomDataset):
            n_samples = len(dataset)
            lengths = [
                len(self.tokenizer.encode(txt, add_special_tokens=False))
                for txt in dataset.texts[:min(n_samples, 100)]
            ]
            avg_len = sum(lengths) / len(lengths) if lengths else 0
            ds = (
                "## Dataset Overview\n\n"
                f"- **Type**: CustomDataset\n"
                f"- **Samples**: {n_samples}\n"
                f"- **Avg tokens/sample (first {len(lengths)})**: {avg_len:.1f}\n\n"
            )
        else:
            n = len(dataset)
            lengths = [
                len(self.tokenizer.encode(txt, add_special_tokens=False))
                for txt in dataset[:100]
            ]
            avg_len = sum(lengths) / len(lengths) if lengths else 0
            ds = (
                "## Dataset Overview\n\n"
                f"- **Type**: List[str]\n"
                f"- **Samples**: {n}\n"
                f"- **Avg tokens/sample (first {len(lengths)})**: {avg_len:.1f}\n\n"
            )

        # 2. Model configuration
        cfg_lines = "\n".join(f"- **{k}**: `{v}`" for k, v in asdict(self.config).items())
        cfg = f"## Model Configuration\n\n{cfg_lines}\n\n"

        # 3. Fine-tuning metrics
        if self.model_info and self.model_info.fine_tuned and self.model_info.fine_tune_info:
            fi = self.model_info.fine_tune_info
            rows = "\n".join(f"| {k} | {v} |" for k, v in {
                "training_loss": fi.get("training_loss"),
                "total_steps": fi.get("total_steps"),
                "use_lora": fi.get("use_lora")
            }.items())
            ft = (
                "## Fine-Tuning Metrics\n\n"
                "| Metric | Value |\n"
                "|--------|-------|\n"
                f"{rows}\n\n"
            )
        else:
            ft = "## Fine-Tuning Metrics\n\n_No fine-tuning has been run yet._\n\n"

        # 4. History & resources
        history = sorted(
            self.model_registry.values(),
            key=lambda m: m.download_date,
            reverse=True
        )[:3]
        hist_lines = ""
        for mi in history:
            tag = "🏷️ Fine-tuned" if mi.fine_tuned else "🔄 Downloaded"
            hist_lines += f"- {tag} `{mi.name}` on {mi.download_date} ({mi.size_gb:.2f} GB)\n"
        device_info = f"- **Device**: {self.device}\n"
        if self.device.startswith("cuda"):
            mem = torch.cuda.get_device_properties(0).total_memory / 1e9
            device_info += f"- **GPU total memory**: {mem:.1f} GB\n"
        hist = (
            "## History & Resources\n\n"
            f"{device_info}\n"
            "Recent models:\n"
            f"{hist_lines}\n"
        )

        # 5. Recommendations
        recs = []
        if self.model_info and self.model_info.fine_tuned:
            recs.append("✅ If loss remains high, adjust learning rate or increase epochs.")
        else:
            recs.append("▶️ Consider running `fine_tune_model(...)` to adapt the model.")
        recs.append("🔍 Try `optimize_parameters(...)` to tune generation quality.")
        rec = "## Recommendations\n\n" + "\n".join(f"- {r}" for r in recs) + "\n"

        # 6. Write report
        report = (
            f"# LocalizeLLM Report\n\n"
            f"_Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n"
            f"{ds}"
            f"{cfg}"
            f"{ft}"
            f"{hist}"
            f"{rec}"
        )
        with open(output_path, "w") as f:
            f.write(report)
        self.logger.info(f"Learning report written to {output_path}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.cleanup()

    def __del__(self):
        try:
            self.cleanup()
        except:
            pass


def create_local_llm(
    model_size: str = "7b",
    quantization: Optional[str] = None,
    local_dir: str = "./local_models",
    **kwargs
) -> LocalizeLLM:
    model_map = {
        "7b": "meta-llama/Llama-2-7b-chat-hf",
        "13b": "meta-llama/Llama-2-13b-chat-hf",
        "70b": "meta-llama/Llama-2-70b-chat-hf",
    }
    cfg = LocalLLMConfig(
        chat_model=model_map.get(model_size, model_map["7b"]),
        local_models_dir=local_dir,
        load_in_8bit=(quantization == "8bit"),
        load_in_4bit=(quantization == "4bit"),
        **kwargs
    )
    return LocalizeLLM(cfg)