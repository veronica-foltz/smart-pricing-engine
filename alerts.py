import os, smtplib, requests
from email.message import EmailMessage

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")  # create an incoming webhook
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
ALERT_TO   = os.getenv("ALERT_TO")  # "you@example.com"

def send_slack(text: str):
  if not SLACK_WEBHOOK: return
  try: requests.post(SLACK_WEBHOOK, json={"text": text}, timeout=5)
  except Exception: pass

def send_email(subject: str, body: str):
  if not (SMTP_HOST and SMTP_USER and SMTP_PASS and ALERT_TO): return
  msg = EmailMessage()
  msg["From"] = SMTP_USER; msg["To"] = ALERT_TO; msg["Subject"] = subject
  msg.set_content(body)
  with smtplib.SMTP_SSL(SMTP_HOST, 465) as s:
      s.login(SMTP_USER, SMTP_PASS); s.send_message(msg)