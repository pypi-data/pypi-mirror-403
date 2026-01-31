# pymes

A simple, lightweight Python wrapper for the Facebook Messenger API.

## Installation

No installation command is available yet as this package is not yet published to PyPI. 
Once published, you will be able to install it via pip:

```bash
pip install pymes-api
```

## Usage

### Basic Example

```python
from pymes import MessengerClient, Text, Attachment

# Initialize the client
sender = MessengerClient(page_access_token="YOUR_PAGE_ACCESS_TOKEN")

# Send a text message
sender.send(recipient_id="USER_ID", message=Text("Hello, world!"))

# Send an attachment (Image)
sender.send("USER_ID", Attachment("image", "https://example.com/image.jpg"))

# Mark as seen
sender.send("USER_ID", action="mark_seen")
```

### Supported Message Types

- `Text`: Simple text messages.
- `Attachment`: Images, files, audio, video.
- `QuickReply`: Messages with quick reply buttons.
- `GenericTemplate`: Carousel-like templates with images and buttons.

## Requirements

- Python 3.7+
- `requests` library

## License

MIT License
