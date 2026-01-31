import requests
import json
from typing import Optional, Dict, List, Any, Union

class smm:
    """
    SMM API Client
    """
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    def _request(self, action: str, data: Dict[str, Any] = None) -> Any:
        """
        Send a request to the SMM provider
        """
        if data is None:
            data = {}

        form_data = {
            'key': self.api_key,
            'action': action
        }

        for key, value in data.items():
            if value is not None:
                form_data[key] = str(value)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)',
        }

        try:
            response = requests.post(self.api_url, data=form_data, headers=headers)
            response.raise_for_status()

            # Some SMM panels return text/html even for JSON, so we try to parse manually if needed
            # But normally requests.json() handles it if headers are right or content is valid json.
            result = response.json()

            # SMM panels sometimes return 200 OK but contain 'error' field
            if isinstance(result, dict) and result.get('error'):
                raise Exception(result['error'])

            return result

        except requests.exceptions.RequestException as e:
            raise Exception(str(e) or 'Network Request Failed')

    def get_services(self) -> List[Any]:
        """
        Service list
        """
        return self._request('services')

    def get_status(self, order_id: Union[str, int]) -> Dict[str, Any]:
        """
        Order status
        """
        return self._request('status', {'order': order_id})

    def get_multi_status(self, order_ids: List[Union[str, int]]) -> Dict[str, Any]:
        """
        Multiple orders status
        """
        return self._request('status', {'orders': ','.join(map(str, order_ids))})

    def create_refill(self, order_id: Union[str, int]) -> Dict[str, Any]:
        """
        Create refill
        """
        return self._request('refill', {'order': order_id})

    def create_multi_refill(self, order_ids: List[Union[str, int]]) -> List[Any]:
        """
        Create multiple refill
        """
        return self._request('refill', {'orders': ','.join(map(str, order_ids))})

    def get_refill_status(self, refill_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get refill status
        """
        return self._request('refill_status', {'refill': refill_id})

    def get_multi_refill_status(self, refill_ids: List[Union[str, int]]) -> List[Any]:
        """
        Get multiple refill status
        """
        return self._request('refill_status', {'refills': ','.join(map(str, refill_ids))})

    def cancel_orders(self, order_ids: List[Union[str, int]]) -> List[Any]:
        """
        Create cancel
        """
        return self._request('cancel', {'orders': ','.join(map(str, order_ids))})

    def get_balance(self) -> Dict[str, str]:
        """
        User balance
        """
        return self._request('balance')

    def add_order(self, service: Union[int, str], link: str, quantity: int, comments: str = None, runs: int = None, interval: int = None) -> Dict[str, Any]:
        """
        Add a new order
        """
        params = {
            'service': service,
            'link': link,
            'quantity': quantity
        }
        if comments is not None:
            params['comments'] = comments
        if runs is not None:
            params['runs'] = runs
        if interval is not None:
            params['interval'] = interval

        return self._request('add', params)
