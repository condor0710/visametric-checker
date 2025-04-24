import time
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import winsound
from telegram.error import TelegramError
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Bot
import asyncio

# Your OCR.Space API key
OCR_SPACE_API_KEY = ''  # <-- your real API key

# Email and Telegram configurations
SEND_EMAIL = True
SEND_TELEGRAM = True

# Email settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_password"
RECIPIENT_EMAIL = "recipient_email@example.com"

# Telegram bot details
bot_token = ''
chat_id = ''  # This can be your user ID or a group chat ID


def create_driver():
    """Create a new undetected Chrome driver."""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-plugins-discovery")
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")  # Uncomment to make Chrome invisible

    options.add_argument(
        "user_agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    )

    driver = uc.Chrome(options=options, use_subprocess=True)
    return driver


def ocr_space_file(filename, overlay=False, api_key=OCR_SPACE_API_KEY, language='eng'):
    """ OCR.space API request with local file. """
    payload = {
        'isOverlayRequired': overlay,
        'apikey': api_key,
        'language': language,
    }
    with open(filename, 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image',
                          files={filename: f},
                          data=payload)
    return r.content.decode()


def solve_captcha(driver):
    """Solves the captcha by capturing and reading the image."""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[1]/div/div/div/div[2]/div[9]/img'))
        )

        captcha_element = driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div/div[2]/div[9]/img')
        captcha_element.screenshot('captcha.png')
        print("Captcha image saved as captcha.png")

        # Send to OCR.space API
        ocr_result_raw = ocr_space_file(filename='captcha.png')
        print("Full OCR Response:", ocr_result_raw)

        ocr_result = json.loads(ocr_result_raw)
        parsed_text = ocr_result['ParsedResults'][0]['ParsedText']
        parsed_text_clean = ''.join(filter(str.isdigit, parsed_text))  # Only digits

        print(f"Captcha detected: {parsed_text_clean}")
        return parsed_text_clean

    except Exception as e:
        print(f"Error while solving captcha: {e}")
        return None


def send_email(subject, body):
    """Send an email notification."""
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
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


async def send_telegram_message(message):
    """Send a message to a specific Telegram chat using async."""
    bot = Bot(token=bot_token)
    try:
        await bot.send_message(chat_id=chat_id, text=message)
        print("Telegram message sent successfully!")
    except TelegramError as e:
        print(f"Error sending Telegram message: {e}")


def check_appointment(driver):
    """Check for available appointments."""
    driver.get('https://uz-appointment.visametric.com/en')

    time.sleep(3)

    captcha_solution = solve_captcha(driver)
    if not captcha_solution:
        print("Captcha solution failed.")
        return False

    try:
        captcha_input = driver.find_element(By.ID, 'mailConfirmCodeControl')
        captcha_input.clear()
        captcha_input.send_keys(captcha_solution)

        submit_btn = driver.find_element(By.ID, 'confirmationbtn')
        submit_btn.click()

        time.sleep(3)

    except Exception as e:
        print(f"Captcha entry error: {e}")
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

        Select(wait.until(EC.element_to_be_clickable((By.ID, 'totalPerson')))).select_by_index(2)
        time.sleep(1)

        next_btn = wait.until(EC.element_to_be_clickable((By.ID, 'btnAppCountNext')))
        next_btn.click()
        print("Clicked on Next button.")

        time.sleep(3)

        try:
            error_box = driver.find_element(By.CLASS_NAME, 'alert-danger')
            if "no available date" in error_box.text.lower():
                print(f"[{time.strftime('%H:%M:%S')}] No available date.")
                return False
        except Exception:
            print(f"[{time.strftime('%H:%M:%S')}] APPOINTMENT AVAILABLE!")
            return True

    except Exception as e:
        print(f"Error while filling form: {e}")
        return False


async def main_loop():
    """Main loop to check for appointments every 30 minutes."""
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
                # If you want to exit after finding, uncomment next line
                # break
            else:
                print(f"[{time.strftime('%H:%M:%S')}] No appointment found. Waiting for 30 minutes...")
                await send_telegram_message(f"[{time.strftime('%H:%M:%S')}] No appointment found. Waiting for 30 minutes...")

        except Exception as e:
            print(f"Error during checking: {e}")

        finally:
            if driver:
                try:
                    driver.quit()
                    print("Browser closed successfully.")
                except Exception as e:
                    print(f"Error closing browser: {e}")

        await asyncio.sleep(1800)  # 30 minutes


if __name__ == "__main__":
    asyncio.run(main_loop())
