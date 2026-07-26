"""Tiny SMTP helper built on the standard library.

Points at MailHog (localhost:1025) in development — every mail the app sends
is then readable in the MailHog web UI at http://localhost:8025.

Sending is deliberately fail-soft: if no SMTP server is listening, the mail is
logged to the console instead of raising, so a demo never dies on a dead port.
"""
import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(to, subject, html_body, attachments=None):
    """Send one HTML email, optionally with file attachments.

    attachments: list of (filename, bytes_content, mime_subtype) tuples,
    e.g. [('export.csv', b'...', 'csv')].
    """
    cfg = current_app.config

    message = EmailMessage()
    message['From'] = cfg['MAIL_SENDER']
    message['To'] = to
    message['Subject'] = subject
    message.set_content('This message requires an HTML-capable mail client.')
    message.add_alternative(html_body, subtype='html')

    for filename, content, subtype in (attachments or []):
        message.add_attachment(
            content, maintype='text', subtype=subtype, filename=filename,
        )

    try:
        with smtplib.SMTP(cfg['SMTP_HOST'], cfg['SMTP_PORT'], timeout=10) as smtp:
            if cfg['SMTP_USER']:
                smtp.login(cfg['SMTP_USER'], cfg['SMTP_PASSWORD'])
            smtp.send_message(message)
        print(f'[MAIL] Sent "{subject}" -> {to}')
        return True

    except (OSError, smtplib.SMTPException) as exc:
        print(f'[MAIL] SMTP unavailable ({exc}). Falling back to console.')
        print(f'[MAIL] To: {to}\n[MAIL] Subject: {subject}\n{html_body}\n')
        return False
