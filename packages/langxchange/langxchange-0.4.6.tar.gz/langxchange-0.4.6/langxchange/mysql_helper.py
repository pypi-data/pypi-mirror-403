import os
import logging
from typing import Optional, Union, Dict, Any, List
from contextlib import contextmanager
import pandas as pd
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import warnings


class MySQLHelper:
    """
    Enhanced MySQL Helper class with improved error handling, security, and functionality.
    
    Features:
    - Connection pooling and management
    - SQL injection protection
    - Transaction support
    - Comprehensive logging
    - Type hints and documentation
    - Context manager support
    - Batch operations
    - Connection health monitoring
    """
    
    def __init__(self, 
                 env_file: Optional[str] = None,
                 pool_size: int = 5,
                 max_overflow: int = 10,
                 pool_timeout: int = 30,
                 pool_recycle: int = 3600,
                 echo: bool = False,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize MySQL Helper with enhanced configuration.
        
        Args:
            env_file: Path to .env file (optional)
            pool_size: Number of connections to maintain in pool
            max_overflow: Maximum number of connections to create beyond pool_size
            pool_timeout: Seconds to wait for connection from pool
            pool_recycle: Seconds after which to recreate connection
            echo: Whether to log all SQL statements
            logger: Custom logger instance
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
            
        # Set up logging
        self.logger = logger or self._setup_logger()
        
        # Database configuration
        self.config = self._load_config()
        self._validate_config()
        
        # Connection parameters
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
        
        # Initialize engine
        self.engine = self._create_engine()
        self.metadata = MetaData()
        
        # Connection health
        self._is_connected = False
        self._test_connection()
        
        self.logger.info("MySQLHelper initialized successfully")
    def _setup_logger(self) -> logging.Logger:
        """Set up default logger for the class."""
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    def _load_config(self) -> Dict[str, str]:
        """Load database configuration from environment variables."""
        return {
            'host': os.getenv("MYSQL_HOST"),
            'database': os.getenv("MYSQL_DB"),
            'user': os.getenv("MYSQL_USER"),
            'password': os.getenv("MYSQL_PASSWORD"),
            'port': os.getenv("MYSQL_PORT", "3306"),
            'charset': os.getenv("MYSQL_CHARSET", "utf8mb4")
        }
    def _validate_config(self) -> None:
        """Validate required configuration parameters."""
        required_fields = ['host', 'database', 'user', 'password']
        missing_fields = [field for field in required_fields if not self.config[field]]
        
        if missing_fields:
            raise EnvironmentError(
                f"Missing required MySQL environment variables: {', '.join(missing_fields)}"
            )
    def _create_engine(self) -> sqlalchemy.engine.Engine:
        """Create SQLAlchemy engine with connection pooling."""
        connection_url = (
            f"mysql+pymysql://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
            f"?charset={self.config['charset']}"
        )
        
        try:
            engine = create_engine(
                connection_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                echo=self.echo,
                pool_pre_ping=True,  # Validate connections before use
                connect_args={
                    "connect_timeout": 10,
                    "read_timeout": 30,
                    "write_timeout": 30
                }
            )
            return engine
        except Exception as e:
            self.logger.error(f"Failed to create database engine: {e}")
            raise
    def _test_connection(self) -> None:
        """Test database connection and set connection status."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._is_connected = True
            self.logger.info("Database connection test successful")
        except Exception as e:
            self._is_connected = False
            self.logger.error(f"Database connection test failed: {e}")
            raise OperationalError("Failed to connect to database", None, None)
    @property
    def is_connected(self) -> bool:
        """Check if database connection is healthy."""
        return self._is_connected
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with automatic cleanup."""
        conn = None
        try:
            conn = self.engine.connect()
            yield conn
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    @contextmanager
    def transaction(self):
        """Context manager for database transactions with automatic rollback on error."""
        with self.get_connection() as conn:
            trans = conn.begin()
            try:
                yield conn
                trans.commit()
                self.logger.debug("Transaction committed successfully")
            except Exception as e:
                trans.rollback()
                self.logger.error(f"Transaction rolled back due to error: {e}")
                raise
    def insert_dataframe(self, 
                        table_name: str, 
                        dataframe: pd.DataFrame, 
                        if_exists: str = "append",
                        chunksize: Optional[int] = None,
                        method: Optional[str] = None) -> str:
        """
        Insert DataFrame into MySQL table with enhanced options.
        
        Args:
            table_name: Target table name
            dataframe: DataFrame to insert
            if_exists: How to behave if table exists ('fail', 'replace', 'append')
            chunksize: Number of rows to insert per batch
            method: Insert method ('multi' for faster inserts)
            
        Returns:
            Success message with row count
            
        Raises:
            RuntimeError: If insertion fails
        """
        if dataframe.empty:
            self.logger.warning(f"Empty DataFrame provided for table '{table_name}'")
            return f"[⚠️ WARNING] Empty DataFrame - no records inserted into `{table_name}`"
        try:
            # Validate table name to prevent SQL injection
            self._validate_table_name(table_name)
            
            # Set default chunksize based on DataFrame size
            if chunksize is None:
                chunksize = min(1000, max(100, len(dataframe) // 10))
            
            # Set default method for better performance
            if method is None and len(dataframe) > 100:
                method = 'multi'
            with self.get_connection() as conn:
                dataframe.to_sql(
                    table_name, 
                    con=conn, 
                    if_exists=if_exists, 
                    index=False,
                    chunksize=chunksize,
                    method=method
                )
            
            message = f"[✅ SUCCESS] Inserted {len(dataframe)} records into `{table_name}`"
            self.logger.info(message)
            return message
            
        except SQLAlchemyError as e:
            error_msg = f"[❌ ERROR] Database error inserting into `{table_name}`: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"[❌ ERROR] Unexpected error inserting into `{table_name}`: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    def query(self, 
              sql_query: str, 
              params: Optional[Dict[str, Any]] = None,
              chunksize: Optional[int] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.
        
        Args:
            sql_query: SQL query string
            params: Query parameters to prevent SQL injection
            chunksize: Number of rows to read per chunk
            
        Returns:
            Query results as DataFrame
            
        Raises:
            RuntimeError: If query fails
        """
        try:
            with self.get_connection() as conn:
                if params:
                    # Use parameterized query for security
                    query = text(sql_query)
                    result = pd.read_sql(query, conn, params=params, chunksize=chunksize)
                else:
                    result = pd.read_sql(text(sql_query), conn, chunksize=chunksize)
                
                if chunksize:
                    # If chunksize is specified, return iterator
                    return result
                
                self.logger.info(f"Query executed successfully, returned {len(result)} rows")
                return result
                
        except SQLAlchemyError as e:
            error_msg = f"[❌ ERROR] Database query failed: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"[❌ ERROR] Unexpected query error: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    def execute(self, 
                sql_command: str, 
                params: Optional[Dict[str, Any]] = None,
                autocommit: bool = True) -> str:
        """
        Execute SQL command (INSERT, UPDATE, DELETE, etc.).
        
        Args:
            sql_command: SQL command string
            params: Command parameters to prevent SQL injection
            autocommit: Whether to automatically commit the transaction
            
        Returns:
            Success message
            
        Raises:
            RuntimeError: If command fails
        """
        try:
            if autocommit:
                with self.get_connection() as conn:
                    if params:
                        result = conn.execute(text(sql_command), params)
                    else:
                        result = conn.execute(text(sql_command))
                    conn.commit()
            else:
                # Use transaction context for manual commit control
                with self.transaction() as conn:
                    if params:
                        result = conn.execute(text(sql_command), params)
                    else:
                        result = conn.execute(text(sql_command))
            
            affected_rows = getattr(result, 'rowcount', 0)
            message = f"[✅ SUCCESS] Command executed successfully. Affected rows: {affected_rows}"
            self.logger.info(message)
            return message
            
        except SQLAlchemyError as e:
            error_msg = f"[❌ ERROR] Database command failed: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"[❌ ERROR] Unexpected command error: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    def batch_execute(self, 
                     sql_command: str, 
                     params_list: List[Dict[str, Any]]) -> str:
        """
        Execute SQL command in batch with multiple parameter sets.
        
        Args:
            sql_command: SQL command string
            params_list: List of parameter dictionaries
            
        Returns:
            Success message with batch count
            
        Raises:
            RuntimeError: If batch execution fails
        """
        if not params_list:
            return "[⚠️ WARNING] Empty parameters list - no commands executed"
        try:
            with self.transaction() as conn:
                result = conn.execute(text(sql_command), params_list)
                affected_rows = getattr(result, 'rowcount', 0)
            
            message = f"[✅ SUCCESS] Batch executed {len(params_list)} commands. Total affected rows: {affected_rows}"
            self.logger.info(message)
            return message
            
        except SQLAlchemyError as e:
            error_msg = f"[❌ ERROR] Batch execution failed: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"[❌ ERROR] Unexpected batch execution error: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists in database.
        
        Args:
            table_name: Name of table to check
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            self._validate_table_name(table_name)
            with self.get_connection() as conn:
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = :database AND table_name = :table_name"
                ), {
                    'database': self.config['database'],
                    'table_name': table_name
                })
                return result.scalar() > 0
        except Exception as e:
            self.logger.error(f"Error checking table existence: {e}")
            return False
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """
        Get detailed information about table structure.
        
        Args:
            table_name: Name of table to analyze
            
        Returns:
            DataFrame with table structure information
        """
        self._validate_table_name(table_name)
        query = """
        SELECT 
            COLUMN_NAME as column_name,
            DATA_TYPE as data_type,
            IS_NULLABLE as is_nullable,
            COLUMN_DEFAULT as default_value,
            COLUMN_KEY as key_type,
            EXTRA as extra
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = :database AND TABLE_NAME = :table_name
        ORDER BY ORDINAL_POSITION
        """
        return self.query(query, {
            'database': self.config['database'],
            'table_name': table_name
        })
    def _validate_table_name(self, table_name: str) -> None:
        """
        Validate table name to prevent SQL injection.
        
        Args:
            table_name: Table name to validate
            
        Raises:
            ValueError: If table name is invalid
        """
        if not table_name or not isinstance(table_name, str):
            raise ValueError("Table name must be a non-empty string")
        
        # Basic validation - alphanumeric, underscore, and period only
        import re
        if not re.match(r'^[a-zA-Z0-9_\.]+$', table_name):
            raise ValueError(f"Invalid table name: {table_name}")
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of database connection.
        
        Returns:
            Dictionary with health check results
        """
        health = {
            'status': 'unknown',
            'timestamp': pd.Timestamp.now(),
            'connection_pool': {},
            'database_info': {},
            'errors': []
        }
        
        try:
            # Test basic connection
            with self.get_connection() as conn:
                # Get database version
                version_result = conn.execute(text("SELECT VERSION()"))
                health['database_info']['version'] = version_result.scalar()
                
                # Get current database
                db_result = conn.execute(text("SELECT DATABASE()"))
                health['database_info']['current_database'] = db_result.scalar()
                
                # Connection pool info
                pool = self.engine.pool
                health['connection_pool'] = {
                    'size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'invalid': pool.invalid()
                }
                
            health['status'] = 'healthy'
            self._is_connected = True
            
        except Exception as e:
            health['status'] = 'unhealthy'
            health['errors'].append(str(e))
            self._is_connected = False
            self.logger.error(f"Health check failed: {e}")
            
        return health
    def close(self) -> str:
        """
        Close database engine and cleanup resources.
        
        Returns:
            Success message
        """
        try:
            if hasattr(self, 'engine') and self.engine:
                self.engine.dispose()
                self._is_connected = False
                message = "[✅ SUCCESS] MySQL connection closed and resources cleaned up."
                self.logger.info(message)
                return message
            else:
                return "[ℹ️ INFO] No active connection to close."
                
        except Exception as e:
            error_msg = f"[❌ ERROR] Failed to close MySQL connection: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    def __enter__(self):
        """Context manager entry."""
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.close()
    def __repr__(self) -> str:
        """String representation of the MySQLHelper instance."""
        return (f"MySQLHelper(host='{self.config['host']}', "
                f"database='{self.config['database']}', "
                f"connected={self.is_connected})")