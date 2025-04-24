import time
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Bot
from telegram.error import TelegramError
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

# Config variables from .env
OCR_SPACE_API_KEY = os.getenv('OCR_SPACE_API_KEY')
SEND_EMAIL = os.getenv('SEND_EMAIL', 'True') == 'True'
SEND_TELEGRAM = os.getenv('SEND_TELEGRAM', 'True') == 'True'
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
bot_token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')


def create_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    options.add_argument(
        "user_agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")
    return uc.Chrome(options=options, use_subprocess=True)


def ocr_space_file(filename, overlay=False, api_key=OCR_SPACE_API_KEY, language='eng'):
    payload = {'isOverlayRequired': overlay, 'apikey': api_key, 'language': language}
    with open(filename, 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image', files={filename: f}, data=payload)
    return r.content.decode()


def solve_captcha(driver):
    for attempt in range(3):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[1]/div/div/div/div[2]/div[9]/img')))
            captcha_element = driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div/div[2]/div[9]/img')
            captcha_element.screenshot('captcha.png')
            logging.info("Captcha image saved as captcha.png")
            ocr_result_raw = ocr_space_file('captcha.png')
            parsed_text = json.loads(ocr_result_raw)['ParsedResults'][0]['ParsedText']
            digits_only = ''.join(filter(str.isdigit, parsed_text))
            logging.info(f"Captcha detected: {digits_only}")
            return digits_only
        except Exception as e:
            logging.warning(f"Captcha solving attempt {attempt+1} failed: {e}")
    return None


def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error("Error sending email", exc_info=True)


async def send_telegram_message(message):
    bot = Bot(token=bot_token)
    try:
        await bot.send_message(chat_id=chat_id, text=message)
        logging.info("Telegram message sent successfully!")
    except TelegramError as e:
        logging.error("Error sending Telegram message", exc_info=True)


def check_appointment(driver):
    driver.get('https://uz-appointment.visametric.com/en')
    time.sleep(3)
    captcha_solution = solve_captcha(driver)
    if not captcha_solution:
        return False
    try:
        driver.find_element(By.ID, 'mailConfirmCodeControl').send_keys(captcha_solution)
        driver.find_element(By.ID, 'confirmationbtn').click()
        time.sleep(3)
    except Exception as e:
        logging.error("Captcha input error", exc_info=True)
        return False

    try:
        wait = WebDriverWait(driver, 15)
        Select(wait.until(EC.element_to_be_clickable((By.ID, 'country')))).select_by_visible_text('Schengen Visa')
        time.sleep(1)
        Select(wait.until(EC.element_to_be_clickable((By.ID, 'visitingcountry')))).select_by_index(1)
        time.sleep(1)
        Select(wait.until(EC.element_to_be_clickable((By.ID, 'city')))).select_by_visible_text('Tashkent')
        time.sleep(1)
        Select(wait.until(EC.element_to_be_clickable((By.ID, 'office')))).select_by_visible_text('Tashkent')
        time.sleep(1)
        Select(wait.until(EC.element_to_be_clickable((By.ID, 'officetype')))).select_by_index(1)
        time.sleep(1)
        Select(wait.until(EC.element_to_be_clickable((By.ID, 'totalPerson')))).select_by_index(1)
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.ID, 'btnAppCountNext'))).click()
        time.sleep(3)
        try:
            if "no available date" in driver.find_element(By.CLASS_NAME, 'alert-danger').text.lower():
                logging.info("No available date.")
                return False
        except:
            logging.info("APPOINTMENT AVAILABLE!")
            return True
    except Exception as e:
        logging.error("Form filling error", exc_info=True)
        return False


async def main_loop():
    while True:
        driver = None
        try:
            driver = create_driver()
            found = check_appointment(driver)
            if found:
                if SEND_EMAIL:
                    send_email("Appointment Available", "An appointment is now available!")
                if SEND_TELEGRAM:
                    await send_telegram_message("An appointment is now available!")
            else:
                await send_telegram_message("No appointment found. Retrying in 30 minutes.")
        except Exception as e:
            logging.error("Error during check", exc_info=True)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logging.error("Error closing browser", exc_info=True)
        await asyncio.sleep(1800)


if __name__ == "__main__":
    asyncio.run(main_loop())
