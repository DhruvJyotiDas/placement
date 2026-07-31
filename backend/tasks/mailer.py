"""Tiny SMTP helper built on the standard library.

Points at MailHog (localhost:1025) in development — every mail the app sends
is then readable in the MailHog web UI at http://localhost:8025.

Sending is deliberately fail-soft: if no SMTP server is listening, the mail is
logged to the console instead of raising, so a demo never dies on a dead port.
"""

# ── Imports ──────────────────────────────────────────────────────────
import smtplib                          # Python ka built-in SMTP client — mail bhejne ke liye
from email.message import EmailMessage  # HTML + attachment wala email banane ke liye ye class use karte hai

from flask import current_app           # current_app se hum config (SMTP host/port etc.) uthayenge


# ── Main function: ek email bhejna ──────────────────────────────────
def send_email(to, subject, html_body, attachments=None):
    """Send one HTML email, optionally with file attachments.

    attachments: list of (filename, bytes_content, mime_subtype) tuples,
    e.g. [('export.csv', b'...', 'csv')].
    """
    # Flask app ka config dictionary nikal liya — isme SMTP_HOST, SMTP_PORT, MAIL_SENDER waghera hai
    cfg = current_app.config

    # ── Step 1: Email message object banao ──────────────────────────
    message = EmailMessage()                 # ek khaali email message object
    message['From'] = cfg['MAIL_SENDER']     # sender ka address (config se aa raha hai)
    message['To'] = to                       # jisko mail bhejni hai uska address
    message['Subject'] = subject             # mail ka subject line

    # Plain-text fallback — agar kisi ka mail client HTML support nahi karta to ye dikhega
    message.set_content('This message requires an HTML-capable mail client.')
    # Asli content HTML format me add kar rahe hai (alternative version ke roop me)
    message.add_alternative(html_body, subtype='html')

    # ── Step 2: Attachments add karo (agar diye gaye ho) ────────────
    # attachments ek list hai jisme (filename, file-ka-content-bytes-me, mime-type) hota hai
    for filename, content, subtype in (attachments or []):
        message.add_attachment(
            content, maintype='text', subtype=subtype, filename=filename,
        )

    # ── Step 3: Actual mail bhejne ki koshish karo ──────────────────
    try:
        # SMTP server (MailHog ya asli server) se connection banao, 10 second ka timeout
        with smtplib.SMTP(cfg['SMTP_HOST'], cfg['SMTP_PORT'], timeout=10) as smtp:
            # MailHog ko login ki zaroorat nahi, lekin agar SMTP_USER set hai to login karo
            if cfg['SMTP_USER']:
                smtp.login(cfg['SMTP_USER'], cfg['SMTP_PASSWORD'])
            smtp.send_message(message)   # yahi line actually mail bhejti hai
        print(f'[MAIL] Sent "{subject}" -> {to}')   # success ka log console me
        return True                                  # mail successfully bhej di

    # ── Step 4: Agar SMTP server available hi nahi hai to crash mat karo ──
    except (OSError, smtplib.SMTPException) as exc:
        # Fail-soft: error aane par pura app crash nahi hoga, bas console pe print kar denge
        print(f'[MAIL] SMTP unavailable ({exc}). Falling back to console.')
        print(f'[MAIL] To: {to}\n[MAIL] Subject: {subject}\n{html_body}\n')
        return False   # mail nahi bhej payi, lekin app chalta rahega
