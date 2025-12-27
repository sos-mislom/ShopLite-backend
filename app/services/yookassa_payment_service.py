import uuid
import base64
import httpx

async def create_payment(shop_id: str, secret_key: str, payment_data: dict):
    authorization_header_value = f'Basic {base64.b64encode(f"{shop_id}:{secret_key}".encode()).decode()}'
    idempotence_key = str(uuid.uuid4())

    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://api.yookassa.ru/v3/payments',
            json=payment_data,
            headers={
                'Authorization': authorization_header_value,
                'Idempotence-Key': idempotence_key
            }
        )
        if response.status_code == 200:
            payment_response = response.json()
            print("Payment created successfully:", payment_response) # TODO нормальное логгирование
            return payment_response['id']
        else:
            raise Exception(f"Error creating payment: {response.text}")

# TODO ДЛЯ ТЕСТА, ПОТОМ УБРАТЬ
if __name__ == "__main__":
    import asyncio

    total_price = 100.00
    order_id = 1

    shop_id = ''
    api_key = ''
    payment_data = {
        "amount": {
            "value": f"{round(total_price, 2)}",
            "currency": "RUB"
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": "https://example.com/thank-you-page"
        },
        "description": f"Заказ №{order_id}",
        "metadata": {
            "order_id": order_id
        }
    }
    asyncio.run(create_payment(shop_id, api_key, payment_data))