"""Channel senders. A channel is 'configured' only when its credentials exist in .env.

Email    : SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM   (Gmail: smtp.gmail.com / 587 / app password)
SMS      : TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_SMS_FROM
WhatsApp : TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM   (e.g. +14155238886)
"""
import base64
import json
import os
import smtplib
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage

CHANNELS = {
    "whatsapp": {"label": "WhatsApp", "needs": "phone"},
    "sms": {"label": "SMS", "needs": "phone"},
    "email": {"label": "Email (Gmail / SMTP)", "needs": "email"},
}


REQUIRED_KEYS = {
    "email": ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"],
    "sms": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_SMS_FROM"],
    "whatsapp": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM"],
}


def missing_keys(channel):
    """Names (never values) of the .env settings still empty for this channel."""
    return [k for k in REQUIRED_KEYS.get(channel, []) if not _env(k)]


def _env(name):
    return os.getenv(name, "").strip()


def is_configured(channel):
    if channel == "email":
        return all(_env(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))
    if channel == "sms":
        return all(_env(k) for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_SMS_FROM"))
    if channel == "whatsapp":
        return all(_env(k) for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM"))
    return False


def _twilio(to, body, from_, prefix=""):
    sid, token = _env("TWILIO_ACCOUNT_SID"), _env("TWILIO_AUTH_TOKEN")
    data = urllib.parse.urlencode({"To": prefix + to, "From": prefix + from_, "Body": body}).encode()
    req = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", data=data)
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode())
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            info = json.loads(resp.read().decode())
            return True, f"accepted by provider ({info.get('status', 'queued')})"
    except urllib.error.HTTPError as exc:
        try:
            msg = json.loads(exc.read().decode()).get("message", "")
        except Exception:
            msg = ""
        return False, f"provider error {exc.code}: {msg}"[:300]
    except Exception as exc:
        return False, f"network error: {exc}"[:300]


def _smtp(to, subject, body):
    host, port = _env("SMTP_HOST"), int(_env("SMTP_PORT") or 587)
    user, pwd = _env("SMTP_USER"), _env("SMTP_PASSWORD")
    msg = EmailMessage()
    msg["From"] = _env("SMTP_FROM") or user
    msg["To"] = to
    msg["Subject"] = subject or "Message from Moseta"
    msg.set_content(body)
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=20)
        else:
            server = smtplib.SMTP(host, port, timeout=20)
            server.starttls()
        with server:
            server.login(user, pwd)
            server.send_message(msg)
        return True, "email accepted by mail server"
    except Exception as exc:
        return False, f"email error: {exc}"[:300]


def send(channel, recipient, message, subject=""):
    """Returns (ok, detail). `recipient` is a phone (+E.164) or an email address."""
    if channel == "email":
        return _smtp(recipient, subject, message)
    if channel == "sms":
        return _twilio(recipient, message, _env("TWILIO_SMS_FROM"))
    if channel == "whatsapp":
        return _twilio(recipient, message, _env("TWILIO_WHATSAPP_FROM"), prefix="whatsapp:")
    return False, "unknown channel"
