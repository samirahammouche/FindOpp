import os
import requests
from requests.exceptions import RequestException

class EventClient:
    def __init__(self):
        self.base_url = os.getenv('EVENT_SERVICE_URL', 'http://127.0.0.1:8002')
        self.timeout = 5

    def update_event_status(self, event_id, new_status):
        """
        Calls the Event Service to approve or reject an event.
        """
        url = f"{self.base_url}/api/events/{event_id}/status/"
        payload = {"status": new_status}
        
        try:
            response = requests.patch(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return True, response.json()
            
        except RequestException as e:
            return False, str(e)