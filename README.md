# Visa Appointment Checker Bot

This Python script automates the process of checking for available appointments on the Visametric website (Uzbekistan region). If an appointment becomes available, it notifies the user via email and/or Telegram.

## 🚀 Features

- Uses `undetected_chromedriver` to bypass bot detection
- Solves CAPTCHA using OCR (via OCR.space API)
- Checks appointment availability on [Visametric](https://uz-appointment.visametric.com/en)
- Sends alerts via:
  - 📧 Email
  - 📬 Telegram
- Runs in an infinite loop, checking every 30 minutes

## 🧰 Requirements

- Python 3.7+
- Chrome browser
- ChromeDriver (automatically handled by `undetected_chromedriver`)

### Python Packages

Install dependencies:

```bash
pip install -r requirements.txt
