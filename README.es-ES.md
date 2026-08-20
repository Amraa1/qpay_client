# qpay-client

![Tests](https://github.com/Amraa1/qpay_client/actions/workflows/test.yml/badge.svg)
![codecov](https://codecov.io/github/Amraa1/qpay_client/graph/badge.svg?token=TIZAF2HOWT)
![PyPI - Version](https://img.shields.io/pypi/v/qpay-client)
![Python](https://img.shields.io/pypi/pyversions/qpay-client.svg)
![PyPI - License](https://img.shields.io/pypi/l/qpay-client)
![PyPI - Downloads](https://img.shields.io/pypi/dw/qpay-client)
![Documentation Status](https://readthedocs.org/projects/qpay-client/badge/?version=latest)

`qpay-client` es un cliente de Python listo para producción para la API de pagos QPay v2, el principal proveedor de pagos de Mongolia.
Desarrollado y utilizado en sistemas de producción, soporta clientes asíncronos y síncronos, esquemas validados con Pydantic v2, gestión automática de tokens, lógica de reintentos con retroceso exponencial y envoltorios tipados para todos los endpoints comunes.

Documentación: [qpay-client.readthedocs.io](https://qpay-client.readthedocs.io/en/latest/)

Portal de desarrolladores de QPay: [developer.qpay.mn](https://developer.qpay.mn)

## Características

- Soporte tanto para `AsyncQPayClient` como para `QPayClient` (síncrono)
- Autenticación y renovación de tokens gestionados automáticamente
- Validación de solicitudes/respuestas mediante esquemas de Pydantic v2
- Lógica de reintento para errores de red y fallos transitorios del servidor
- Sondeo (`polling`) configurable para `payment_check` con retroceso exponencial
- Soporte para gestores de contexto `with` y `async with`
- Excepciones estructuradas `QPayError` con códigos y descripciones de error

## Instalación

Usando `pip`:

```bash
pip install qpay-client
```

Usando `uv`:

```bash
uv add qpay-client
```

Usando `poetry`:

```bash
poetry add qpay-client
```

## Inicio rápido

### Cliente asíncrono

```python
from decimal import Decimal

from qpay_client.v2 import AsyncQPayClient, QPaySettings
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest

settings = QPaySettings.sandbox()

async def main():
    async with AsyncQPayClient(settings=settings) as client:
        invoice = await client.invoice_create(
            InvoiceCreateSimpleRequest(
                sender_invoice_no="ORDER-1001",
                invoice_receiver_code="terminal",
                invoice_description="Test invoice",
                amount=Decimal("1500"),
                callback_url="https://example.com/qpay/callback?payment_id=ORDER-1001",
            )
        )

        print(invoice.invoice_id)
        print(invoice.qPay_shortUrl)
```

### Cliente síncrono

```python
from decimal import Decimal

from qpay_client.v2 import QPayClient, QPaySettings
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest

settings = QPaySettings.sandbox()

with QPayClient(settings=settings) as client:
    invoice = client.invoice_create(
        InvoiceCreateSimpleRequest(
            sender_invoice_no="ORDER-1002",
            invoice_receiver_code="terminal",
            invoice_description="Sync test invoice",
            amount=Decimal("2500"),
            callback_url="https://example.com/qpay/callback?payment_id=ORDER-1002",
        )
    )

    print(invoice.invoice_id)
```

## Configuración

### Sandbox

```python
from qpay_client.v2 import QPaySettings

settings = QPaySettings.sandbox()
```

### Producción

```python
from qpay_client.v2 import QPaySettings

settings = QPaySettings.production(
    username="your-merchant-username",
    password="your-merchant-password",
    invoice_code="YOUR_INVOICE_CODE",
)
```

### Configuración de reintentos y retrasos

```python
settings = QPaySettings.sandbox(
    client_retries=2,
    client_delay=0.25,
    client_jitter=0.1,
    payment_check_retries=8,
    payment_check_delay=0.5,
    payment_check_jitter=0.2,
)
```

## Verificación de un pago

```python
from qpay_client.v2.enums import ObjectType
from qpay_client.v2.schemas import Offset, PaymentCheckRequest

check_request = PaymentCheckRequest(
    object_type=ObjectType.invoice,
    object_id="YOUR_INVOICE_ID",
    offset=Offset(page_number=1, page_limit=100),
)

result = await client.payment_check(check_request)

if result.count > 0:
    print("Payment found")
```

## Flujo de devolución (callback) con FastAPI

`examples/quickstart.py` contiene un ejemplo asíncrono funcional con un endpoint de devolución de QPay.

El patrón general es:

1. Crear una factura
2. Almacenar el `invoice_id` en tu base de datos
3. En la devolución de QPay, llamar a `payment_check` para verificar el pago
4. Devolver `"SUCCESS"` con código HTTP 200

Para ejecutar el ejemplo:

```bash
fastapi dev examples/quickstart.py
```

Es obligatorio devolver HTTP 200 con el cuerpo `"SUCCESS"` desde tu endpoint de devolución, según lo requiere QPay.

## Rutas de importación

Importa clientes y configuraciones desde `qpay_client.v2`:

```python
from qpay_client.v2 import AsyncQPayClient, QPayClient, QPaySettings, QPayError
```

Importa esquemas y enumeraciones desde sus módulos respectivos:

```python
from qpay_client.v2.enums import ObjectType
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest, Offset, PaymentCheckRequest
```

## Endpoints soportados

### Autenticación

- `token`
- `refresh`

### Factura (Invoice)

- `invoice_get`
- `invoice_create`
- `invoice_cancel`

### Pago (Payment)

- `payment_get`
- `payment_list`
- `payment_check`
- `payment_cancel`
- `payment_refund`

### Ebarimt

- `ebarimt_get`
- `ebarimt_create`

### Suscripción (Subscription)

- `subscription_get`
- `subscription_cancel`

## Notas

- Nunca llames a `QPaySettings()` directamente; utiliza los métodos fábrica `sandbox()` o `production()`.
- Todos los métodos de endpoints públicos verifican y renuevan la autenticación automáticamente; no es necesario gestionar los tokens manualmente.
- `payment_check` realiza sondeos con retroceso exponencial; ajusta la configuración de reintentos/retrasos según tu caso de uso.
- No guardes credenciales de producción en control de versiones.

## Licencia

Licencia MIT
