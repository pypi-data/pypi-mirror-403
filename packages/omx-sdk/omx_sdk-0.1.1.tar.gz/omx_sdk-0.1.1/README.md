# OMX SDK

Python SDK for Oxinion Marketing Exchange (OMX) - A comprehensive toolkit for geotrigger marketing, email campaigns, and webhook management.

## Installation

```bash
pip install omx-sdk
```

## Quick Start

```python
import asyncio
import os
from omx_sdk import OMXClient

async def main():
    # Initialize client
    client = OMXClient(
        api_key=os.getenv("OMX_API_KEY"),
        secret_key=os.getenv("OMX_SECRET_KEY"),
    )

    # Authenticate
    await client.authenticate()

    # Create a geotrigger
    geotrigger = await client.geotriggers.create(
        name="Coffee Shop Downtown",
        latitude=40.7128,
        longitude=-74.0060,
        radius=100
    )

    # Send email
    email_result = await client.email.send(
        to=["user@example.com"],
        subject="Welcome to OMX!",
        content="<h1>Hello from OMX SDK</h1>"
    )

    # Create webhook
    webhook = await client.webhooks.create(
        url="https://your-app.com/webhooks/omx",
        events=["geotrigger.entered", "email.sent"]
    )

    # Clean up
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- 🌍 **Geotrigger Management** - Create and manage location-based triggers
- 📧 **Email Campaigns** - Send targeted email communications
- 🔗 **Webhook Integration** - Real-time event notifications
- 🔐 **Secure Authentication** - API key and secret management
- ⚡ **Async Support** - Built with asyncio for high performance

## Configuration

Set your credentials as environment variables:

```bash
export OMX_API_KEY="your_api_key"
export OMX_SECRET_KEY="your_secret_key"
```

## Documentation

For detailed documentation and API reference, visit: https://github.com/oxinion/omx-sdk

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: support@oxinion.com
- 🐛 Issues: https://github.com/oxinion/omx-sdk/issues
- 📖 Documentation: https://github.com/oxinion/omx-sdk#readme
