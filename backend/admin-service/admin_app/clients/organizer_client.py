import os
import requests
from requests.exceptions import RequestException

class OrganizerClient:
    def __init__(self):
        # We pull the URL from our .env file
        self.base_url = os.getenv('ORGANIZER_SERVICE_URL', 'http://127.0.0.1:8001')
        self.timeout = 5  # 5 seconds timeout (Best practice!)

    def update_organizer_status(self, organizer_id, new_status):
        """
        Calls the Organizer Service to validate or suspend an account.
        """
        url = f"{self.base_url}/api/organizers/{organizer_id}/status/"
        payload = {"status": new_status}
        
        try:
            # We send a PATCH request (because we are updating a status)
            response = requests.patch(url, json=payload, timeout=self.timeout)
            
            # If the response is a 4xx or 5xx error, raise an exception
            response.raise_for_status()
            
            return True, response.json()
            
        except RequestException as e:
            # In Phase 6, we will handle this properly. For now, we just return the error.
            return False, str(e)