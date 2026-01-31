import requests
from .message import *
from .exceptions import MessengerException

class MessengerClient:
    def __init__(self, page_access_token, app_id="", api_version="v24.0"):
        self.page_access_token = page_access_token
        self.app_id = app_id
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}/me/messages"

    def _send_request(self, payload: dict):
        """Send a request to the Facebook Graph API"""
        try:
            response = requests.post(self.base_url, params={"access_token": self.page_access_token}, json=payload)
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise MessengerException(data["error"]["message"])
            return data
        except requests.exceptions.HTTPError as e:
            try:
                error_data = response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    raise MessengerException(error_data["error"]["message"]) 
            except ValueError:
                pass # JSON decode failed
            raise MessengerException(str(e))

    def send(self, recipient_id, message: Message | None = None, action: str | None = None):
        """Send a message to a recipient"""
        
        if message:
            payload = {
                "recipient": {
                    "id": recipient_id
                },
                "message": message.to_dict()
            }
        elif action:
            valid_actions = ["typing_on", "typing_off", "mark_seen"]
            if action not in valid_actions:
                raise ValueError(f"Invalid action. Must be one of {valid_actions}")
            
            payload = {
                "recipient": {
                    "id": recipient_id
                },
                "sender_action": action
            }
        else:
            raise ValueError("No message or action provided")
        
        return self._send_request(payload)


    def fetch_user_profile(self, user_id):
        """Fetch user profile from Facebook Graph API"""
        url = f"https://graph.facebook.com/{self.api_version}/{user_id}"
        params = {"fields": "id,name,picture", "access_token": self.page_access_token}
        response = requests.get(url, params=params)
        return response.json()
