# import required modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

import time
from typing import List, Dict, Any  # <-- Added this line
import logging

from email_validator import validate_email, EmailNotValidError
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailTool:
    def __init__(self, email_adress: str, password: str, api_passwd: str):

        opt = Options()
        opt.add_argument('--disable-blink-features=AutomationControlled')
        opt.add_argument('--start-maximized')
        opt.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.geolocation": 0,
            "profile.default_content_setting_values.notifications": 1
            })
        self.driver = webdriver.Chrome(options=opt)
        self.email = email_adress or None
        self.passwd = password or None
        self.apipasswd = api_passwd or None


    def gmail_login(self):
        try:
            # Login Page
            self.driver.get(
            'https://accounts.google.com/ServiceLogin?hl=en&passive=true&continue=https://www.google.com/&ec=GAZAAQ')

            # input Gmail
            self.driver.find_element(By.ID, "identifierId").send_keys(self.email)
            self.driver.find_element(By.ID, "identifierNext").click()
            self.driver.implicitly_wait(10)

            # input Password
            self.driver.find_element(By.XPATH,'//*[@id="password"]/div[1]/div/div[1]/input').send_keys(self.passwd)
            self.driver.implicitly_wait(10)
            self.driver.find_element(By.ID, "passwordNext").click()
            self.driver.implicitly_wait(10)

            # go to google home page
            self.driver.get('https://google.com/')
            self.driver.implicitly_wait(100)

            # WebDriverWait(driver, 30).until(
            #     lambda d: ("myaccount.google.com" in d.current_url)
            #             or ("mail.google.com" in d.current_url)
            #     )
            return True

        except Exception as e:
            self.driver.save_screenshot("gmail_login_error.png")
            raise Exception(f"Failed to login to Gmail account: {str(e)}")

    def verify_email(self, verification_link: str) -> bool:
        """
        Verify an email by visiting the verification link.

        Args:
            verification_link (str): URL of the verification link

        Returns:
            bool: True if verification successful
        """
        try:
            self.driver.get(verification_link)
            WebDriverWait(self.driver, 30).until(
                lambda d: ("verified" in d.current_url.lower()) or ("success" in d.current_url.lower())
            )
            return True
        except Exception as e:
            self.driver.save_screenshot("email_verification_error.png")
            raise Exception(f"Failed to verify email: {str(e)}")


    def read_mail(self,limit: int = 10,unread_only: bool = False) -> List[Dict[str, Any]]:
        try:

            if not self.email or not self.apipasswd:
                raise ValueError("No email account is currently logged in")

            # Connect to Gmail IMAP server
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email,self.apipasswd)
            mail.select("inbox")

            # Search for emails
            search_criteria = "(UNSEEN)" if unread_only else "ALL"
            status, messages = mail.search(None, search_criteria)
            if status != "OK":
                raise Exception("Failed to search emails")

            email_ids = messages[0].split()[:limit]
            emails: List[Dict[str, Any]] = []

            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                email_info: Dict[str, Any] = {
                    "subject": msg["subject"],
                    "from": msg["from"],
                    "date": msg["date"],
                    "body": self._extract_email_body(msg)
                    }
                emails.append(email_info)

            mail.close()
            mail.logout()
            return emails
        except Exception as e:
            raise Exception(f"Failed to read emails: {str(e)}")


    def _extract_email_body(self, msg: email.message.Message) -> str:
        """Extract the body text from an email message."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    return part.get_payload(decode=True).decode(errors="ignore")
        else:
            return msg.get_payload(decode=True).decode(errors="ignore")
        return ""

    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """
        Send an email from the current Gmail account.

        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body content
            is_html (bool): Whether the body is HTML content

        Returns:
            bool: True if email sent successfully
        """
        if not self.email or not self.passwd:
            raise ValueError("No email account is currently logged in")

        try:
            # Validate recipient email
            try:
                validate_email(to_email)
            except EmailNotValidError as e:
                raise ValueError(f"Invalid recipient email: {str(e)}")

            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = to_email
            msg["Subject"] = subject

            # Attach body
            if is_html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # Send email via SMTP
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(self.email, self.apipasswd)
                smtp.send_message(msg)

            return True

        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")

    def turnOffMicCam():
        # turn off Microphone
        time.sleep(2)
        driver.find_element(By.XPATH,
        '//*[@id="yDmH0d"]/c-wiz/div/div/div[8]/div[3]/div/div/div[2]/div/div[1]/div[1]/div[1]/div/div[4]/div[1]/div/div/div').click()
        driver.implicitly_wait(3000)

        # turn off camera
        time.sleep(1)
        driver.find_element(By.XPATH,
            '//*[@id="yDmH0d"]/c-wiz/div/div/div[8]/div[3]/div/div/div[2]/div/div[1]/div[1]/div[1]/div/div[4]/div[2]/div/div').click()
        driver.implicitly_wait(3000)


    def joinNow():
        # Join meet
        print(1)
        time.sleep(5)
        driver.implicitly_wait(2000)
        driver.find_element(By.CSS_SELECTOR,
         'div.uArJ5e.UQuaGc.Y5sE8d.uyXBBb.xKiqt').click()
        print(1)


    def AskToJoin():
        # Ask to Join meet
        time.sleep(5)
        driver.implicitly_wait(2000)
        driver.find_element(By.CSS_SELECTOR,
            'div.uArJ5e.UQuaGc.Y5sE8d.uyXBBb.xKiqt').click()
         # Ask to join and join now buttons have same xpaths