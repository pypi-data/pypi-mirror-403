# Message Sender

[![Tests Status](https://github.com/sanders41/message-sender/actions/workflows/testing.yml/badge.svg?branch=main&event=push)](https://github.com/sanders41/message-sender/actions?query=workflow%3ATesting+branch%3Amain+event%3Apush)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sanders41/message-sender/main.svg)](https://results.pre-commit.ci/latest/github/sanders41/message-sender/main)
[![Coverage](https://codecov.io/github/sanders41/message-sender/coverage.svg?branch=main)](https://codecov.io/gh/sanders41/message-sender)
[![PyPI version](https://badge.fury.io/py/message-sender.svg)](https://badge.fury.io/py/message-sender)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/message-sender?color=5cc141)](https://github.com/sanders41/message-sender)

Sends messages with different services such as email and Google Chat.

## Installation

```sh
pip install message-sender
```

## Usage

### Google Chat

Send messages to Google Chat via webhooks. To set this up, create a "space" in Google Chat, then go
to Apps & integrations and create a new webhook.

#### Sync Client

```py
from message_sender.google_chat import GoogleChatClient

with GoogleChatClient("https://your-webhook-url.com") as client:
    client.send_message("Some test message")
```

#### Async Client

```py
from message_sender.google_chat import AsyncGoogleChatClient

async with AsyncGoogleChatClient("https://your-webhook-url.com") as client:
    await client.send_message("Some test message")
```

### Discord

Send messages to Discord via webhooks. For setup instructions see
[https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)

#### Sync Client

```py
from message_sender.discord import DiscordClient

with DiscordClient("https://your-webhook-url.com") as client:
    client.send_message("Some test message")
```

#### Async Client

```py
from message_sender.discord import AsyncDiscordClient

async with AsyncDiscordClient("https://your-webhook-url.com") as client:
    await client.send_message("Some test message")
```

### Proton Email

Send emails through Proton Mail's SMTP service. For setup instructions see
[https://proton.me/support/smtp-submission](https://proton.me/support/smtp-submission)

#### Sync Client

```py
from message_sender.email.proton import ProtonEmailClient

client = ProtonEmailClient(
    email_address="smtp_setup_email@proton.me", smtp_token="your-token"
)
client.send_email(
    message="Your message body",
    email_to="someone@email.com",
    subject="Example",
    html_content="<p>Your HTML message body</p>",  # optional
)
```

#### Async Client

```py
from message_sender.email.proton import AsyncProtonEmailClient

client = AsyncProtonEmailClient(
    email_address="smtp_setup_email@proton.me", smtp_token="your-token"
)
await client.send_email(
    message="Your message body",
    email_to="someone@email.com",
    subject="Example",
    html_content="<p>Your HTML message body</p>",  # optional
)
```
