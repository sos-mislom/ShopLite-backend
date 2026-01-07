import smtplib
from email.mime.text import MIMEText
from app.config import settings


def _send_text_email(email: str, subject: str, body: str) -> bool:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        print(f"Email sent to {email}")
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


async def send_reset_email(email: str, token: str):
    reset_link = f"http://195.133.66.226:9000/reset?token={token}"

    body = f"Для восстановления пароля перейдите по ссылке:\n{reset_link}"
    _send_text_email(email, "Восстановление пароля", body)

async def send_order_tracking_email(
    email: str,
    order_id: int,
    tracking_number: str,
    order_status: str,
    payment_status: str,
    amount: str,
    currency: str,
    payment_provider: str,
    payment_id: str,
    paid_at: str | None = None,
    tracking_url: str | None = None,
) -> bool:
    subject = f"Заказ #{order_id}: трек-номер {tracking_number}"
    lines = [
        "Спасибо за оплату! Мы получили ваш платеж.",
        f"Номер заказа: #{order_id}",
        f"Трек-номер: {tracking_number}",
        f"Статус заказа: {order_status}",
        f"Статус оплаты: {payment_status}",
        "",
        "Чек по транзакции:",
        f"- Провайдер: {payment_provider}",
        f"- ID платежа: {payment_id}",
        f"- Сумма: {amount} {currency}",
    ]
    if paid_at:
        lines.append(f"- Дата оплаты: {paid_at}")
    if tracking_url:
        lines.extend(["", f"Ссылка для отслеживания: {tracking_url}"])
    return _send_text_email(email, subject, "\n".join(lines))
