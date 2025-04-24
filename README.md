# 🛂 Visametric Appointment Checker Bot

This is a Python automation script that checks for visa appointment availability on [Visametric's Uzbekistan portal](https://uz-appointment.visametric.com/en) and notifies you via **Telegram** and/or **Email** when a slot opens up.

It's designed to run automatically in the background, solving CAPTCHAs using OCR and simulating user interactions with the website.

---

## ✨ Features

- 🕵️‍♂️ Stealth browsing with undetected ChromeDriver
- 🧠 CAPTCHA solver using OCR.space API
- ⏱️ Automated checks every 30 minutes
- 🔔 Real-time alerts via:
  - 📬 Email
  - 📱 Telegram Bot
- 📸 CAPTCHA image saved for solving

---

## 🔧 Requirements

- Python 3.7+
- Chrome installed
- API key from [OCR.space](https://ocr.space/OCRAPI)

Install required Python libraries:

```bash
pip install -r requirements.txt
```

`requirements.txt` should contain:
```
undetected-chromedriver
requests
selenium
python-telegram-bot==13.15
```

---

## ⚙️ Configuration

Update these variables in the script before running:

```python
OCR_SPACE_API_KEY = 'your_ocr_api_key'

SEND_EMAIL = True
SEND_TELEGRAM = True

SENDER_EMAIL = 'your_email@gmail.com'
SENDER_PASSWORD = 'your_email_password_or_app_password'
RECIPIENT_EMAIL = 'recipient@example.com'

bot_token = 'your_telegram_bot_token'
chat_id = 'your_telegram_chat_id'
```

> 💡 For Gmail, create an [App Password](https://myaccount.google.com/apppasswords) instead of using your main password.

---

## 🚀 Usage

Run the script:

```bash
python your_script.py
```

- The bot will open a Chrome window, solve the CAPTCHA, and try to proceed with form submission.
- If an appointment is found, it sends a notification.
- If not, it logs the attempt and waits 30 minutes before trying again.

---

## 🤖 Telegram Setup

1. Talk to [@BotFather](https://t.me/BotFather) to create a bot and get a token.
2. Start a chat with your bot so it can message you.
3. Use [@userinfobot](https://t.me/userinfobot) to get your chat ID.

---

## 📧 Email Notes

- If using Gmail, enable 2FA and use an App Password.
- You may need to allow "less secure apps" if not using App Passwords (not recommended).

---

## 🔍 How It Works (Under the Hood)

1. Launches a Chrome browser using `undetected-chromedriver`.
2. Captures CAPTCHA image and sends it to OCR.space.
3. Inputs CAPTCHA solution into form.
4. Fills out appointment form fields (e.g. visa type, city, office).
5. Submits the form.
6. Checks if a "No date available" message is present.
7. Sends notification if appointment is available.
8. Loops every 30 minutes.

---

## 🛡️ Disclaimer

This script interacts with a third-party website and may break if the site's layout or CAPTCHA system changes. Use at your own risk and respect all terms of service.

---

## 📝 License

MIT License – free to use, modify, and share.

---

## 🙌 Credits

- CAPTCHA solved via [OCR.space API](https://ocr.space/)
- Automation powered by [Selenium](https://www.selenium.dev/) and [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
- Telegram integration via [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
