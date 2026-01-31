"""
pymes is a Python library for Facebook Messenger API

Example:
```python
from pymes import MessengerClient, Text, Attachment
sender = MessengerClient(page_access_token="***")

sender.send(recipient_id="***", message=Text("Hello, world!"))
sender.send("***", action="mark_seen")
```"""

from .client import MessengerClient
from .message import Text, Attachment, QuickReply, GenericTemplate, Element
from .exceptions import MessengerException
