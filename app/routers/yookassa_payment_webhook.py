import ipaddress
import json
from fastapi import APIRouter, Request, Response

router = APIRouter(prefix="/webhook", tags=["Webhook"])

# Допустимые сети Юкассы (https://yookassa.ru/developers/using-api/webhooks#ip)
ALLOWED_NETWORKS = [
    ipaddress.ip_network('185.71.76.0/27'),
    ipaddress.ip_network('185.71.77.0/27'),
    ipaddress.ip_network('77.75.153.0/25'),
    ipaddress.ip_address('77.75.156.11'),
    ipaddress.ip_address('77.75.156.35'),
    ipaddress.ip_network('77.75.154.128/25'),
    ipaddress.ip_network('2a02:5180::/32')
]

@router.post("/yookassa/payment-status")
async def yookassa_payment_handler(request: Request):
    remote_ip = request.client.host
    if not _is_ip_allowed(remote_ip):
        return Response(status_code=401, content="Unauthorized IP address")

    raw_body = await request.body()
    data = json.loads(raw_body.decode('utf-8'))

    payment_id = data["object"].get("id")
    order_id = data["object"]["metadata"].get("order_id")

    # TODO достаем из БД заказ по order_id, получаем из него истинный payment_id
    order_payment_id = payment_id # ЗАГЛУШКА

    if order_payment_id != payment_id:
        return Response(status_code=400, content="Notification outdated")
        # TODO тут можно дополнительно ходить на Юкассу и проверять совпадают ли присланные данные (например статусы оплаты)

    event_type = data.get('event', '')
    object_data = data.get('object', {})
    _handle_event(event_type, object_data)

    return Response(status_code=200, content="OK")

def _is_ip_allowed(ip_str):
    for network in ALLOWED_NETWORKS:
        if isinstance(network, ipaddress.IPv4Network) or isinstance(network, ipaddress.IPv6Network):
            if ipaddress.ip_address(ip_str) in network:
                return True
        elif isinstance(network, ipaddress.IPv4Address) or isinstance(network, ipaddress.IPv6Address):
            if ipaddress.ip_address(ip_str) == network:
                return True
    return False

def _handle_event(event_type: str, object_data: dict):
    if event_type == 'payment.succeeded':
        _process_successful_payment(object_data)
    elif event_type == 'payment.canceled':
        _process_canceled_payment(object_data)
    else:
        pass

def _process_successful_payment(payment_data: dict):
    order_id = payment_data.get('metadata', {}).get('order_id')
    amount = payment_data.get('amount', {}).get('value')
    print(f"Платеж успешен! Order #{order_id}, сумма: {amount} руб.")

    # TODO дальнейшая логика успешной оплаты

def _process_canceled_payment(payment_data: dict):
    order_id = payment_data.get('metadata', {}).get('order_id')
    reason = payment_data.get('cancellation_details', {}).get('reason')
    print(f"Платеж отменён! Order #{order_id}. Причина: {reason}")

    # TODO дальнейшая логика отмененной оплаты