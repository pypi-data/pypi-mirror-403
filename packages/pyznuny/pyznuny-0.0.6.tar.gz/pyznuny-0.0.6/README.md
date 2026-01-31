# pyznuny

A Python client for interacting with the Znuny ticketing system API.

## Features

- Simple, typed client built on httpx
- Ticket create, update, and get routes
- Easy custom endpoint configuration

## Installation

```console
pip install pyznuny
```

Or with uv:

```console
uv add pyznuny
```

## Quick start

Create a client and authenticate using environment variables.

```python
from pyznuny import TicketClient
from dotenv import load_dotenv
import os

load_dotenv()

client = TicketClient(
    base_url=os.getenv("HOST"),
    username=os.getenv("USER_LOGIN"),
    password=os.getenv("PASSWORD"),
)
```

Example `.env`:

```ini
HOST=https://your-znuny-instance.com
USER_LOGIN=your-username
PASSWORD=your-password
```

## Usage examples

### Create a ticket

```python
from pyznuny.ticket.models import (
    TicketCreateArticle,
    TicketCreatePayload,
    TicketCreateTicket,
)

payload = TicketCreatePayload(
    Ticket=TicketCreateTicket(
        Title="Ticket Title",
        Queue="Ticket queue",
        State="Ticket state",
        Priority="Ticket priority",
        CustomerUser="customer@example.com",
    ),
    Article=TicketCreateArticle(
        Subject="Ticket subject",
        Body="Ticket body...",
        ContentType="text/plain; charset=utf-8",
        From_="customer@example.com",
    ),
)

response = client.ticket.create(payload=payload)
print(response.json())
```

### Get a ticket by ID

```python
# default endpoint is GET /Ticket/{ticket_id}
response = client.ticket.get(ticket_id=1234)
print(response.json())
```

### Update a ticket

```python
response = client.ticket.update(
    ticket_id=1234,
    Ticket={"State": "open"},
)
print(response.json())
```

### Customize endpoints

If your Znuny instance uses different paths, set them with the endpoint setter.

```python
# Example: custom ticket get endpoint and identifier
client.set_endpoint.ticket_get(endpoint="Tickets/{id}", identifier="id")

response = client.ticket.get(ticket_id=1234)
```

## Notes

- When `username` and `password` are provided, the client logs in and stores
  `session_id` automatically.
- You can pass a pre-configured `httpx.Client` via `client=...` if needed.

## License

MIT
