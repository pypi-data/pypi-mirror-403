import requests
from typing import Dict, Any, Optional

class FonnteService:
    def __init__(self, token: str, base_url: str = 'https://api.fonnte.com'):
        self.token = token
        self.base_url = base_url

    def send(self, target: str, message: str) -> Dict[str, Any]:
        """
        Send WhatsApp message via Fonnte.
        
        :param target: Target phone number
        :param message: Message content
        :return: Response dict
        """
        if not self.token:
            return {'status': False, 'message': 'Fonnte token not configured'}

        try:
            response = requests.post(
                f"{self.base_url}/send",
                headers={'Authorization': self.token},
                json={
                    'target': target,
                    'message': message
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if e.response is not None:
                error_msg = e.response.text
            raise Exception(f"Fonnte API Error: {error_msg}")
