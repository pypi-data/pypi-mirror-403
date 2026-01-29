import time
from typing import Any, Dict, List, Optional, Union

import requests

from splitnow.enums import (
    AssetId,
    NetworkId,
    QuoteType,
)
from splitnow.models import (
    Asset,
    AssetLimit,
    Exchanger,
    QuoteInput,
    QuoteOutput,
    Quote,
    Order,
    CreateOrderResponse,
    QuoteData,
    OrderData,
    OrderStatusData,
    WalletDistribution,
)
from splitnow.exceptions import (
    SplitNowError,
    SplitNowAuthError,
    SplitNowForbiddenError,
    SplitNowNotFoundError,
    SplitNowValidationError,
    SplitNowRateLimitError,
    SplitNowServerError,
)

class SplitNow:
    DEFAULT_BASE_URL = "https://splitnow.io/api"

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 30
    ):
        if not api_key:
            raise ValueError('Invalid or missing SplitNOW API key!')

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        url = f"{self.base_url}{endpoint}"

        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout
            )

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    message = error_data.get("message", "Request failed")
                except Exception:
                    message = response.text or "Request failed"

                self._raise_for_status(response.status_code, message)

            if endpoint == "/health/":
                return response.text

            json_response = response.json()

            if endpoint.startswith('/quotes') or endpoint.startswith('/orders'):
                if not json_response.get('success', True):
                    error_message = json_response.get('error', 'Failed to make request')
                    raise SplitNowError(f'Failed to make request: "{error_message}"')
                return json_response.get('data', json_response)

            return json_response

        except requests.exceptions.Timeout:
            raise SplitNowError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise SplitNowError("Connection error")
        except SplitNowError:
            raise
        except Exception as e:
            raise SplitNowError(f"Request failed: {str(e)}")

    def _raise_for_status(self, status_code: int, message: str) -> None:
        if status_code in (400, 422):
            raise SplitNowValidationError(message, status_code)
        if status_code == 401:
            raise SplitNowAuthError(message, status_code)
        if status_code == 403:
            raise SplitNowForbiddenError(message, status_code)
        if status_code == 404:
            raise SplitNowNotFoundError(message, status_code)
        if status_code == 429:
            raise SplitNowRateLimitError(message, status_code)
        if status_code >= 500:
            raise SplitNowServerError(message, status_code)

        raise SplitNowError(message, status_code)

    def get_health(self) -> bool:
        response = self._request("GET", "/health/")
        return response == "OK"

    def get_assets(self) -> List[Asset]:
        response = self._request("GET", "/assets/")
        return [Asset.from_dict(asset) for asset in response["assets"]]

    def get_asset_prices(self) -> Dict[str, Optional[float]]:
        response = self._request("GET", "/assets/prices/")
        return response["prices"]

    def get_asset_deposit_limits(self) -> List[AssetLimit]:
        response = self._request("GET", "/assets/limits/")
        return [AssetLimit.from_dict(limit) for limit in response["limits"]]

    def get_exchangers(self) -> List[Exchanger]:
        response = self._request("GET", "/exchangers/")
        return [Exchanger.from_dict(e) for e in response["exchangers"]]

    def get_quote(self, quote_id: str) -> Quote:
        data = self._request("GET", f"/quotes/{quote_id}")
        return Quote.from_dict(data)

    def get_order(self, order_id: str) -> Order:
        data = self._request("GET", f"/orders/{order_id}")
        return Order.from_dict(data)

    def create_and_fetch_quote(
        self,
        from_amount: float,
        from_asset_id: Union[str, AssetId],
        from_network_id: Union[str, NetworkId],
        to_asset_id: Union[str, AssetId],
        to_network_id: Union[str, NetworkId],
        wait_time: float = 1.0
    ) -> QuoteData:
        data = {
            "type": QuoteType.FLOATING_RATE.value,
            "quoteInput": QuoteInput(
                from_amount=from_amount,
                from_asset_id=from_asset_id,
                from_network_id=from_network_id
            ).to_dict(),
            "quoteOutputs": [
                QuoteOutput(
                    to_pct_bips=10000,
                    to_asset_id=to_asset_id,
                    to_network_id=to_network_id
                ).to_dict()
            ]
        }

        quote_id = self._request("POST", "/quotes/", json_data=data)

        time.sleep(wait_time)

        quote = self.get_quote(quote_id)
        return QuoteData.from_quote(quote_id, quote)

    def create_and_fetch_order(
        self,
        quote_id: str,
        from_amount: float,
        from_asset_id: Union[str, AssetId],
        from_network_id: Union[str, NetworkId],
        wallet_distributions: List[WalletDistribution],
        wait_time: float = 1.0
    ) -> OrderData:
        limits = self.get_asset_deposit_limits()

        asset_id_str = from_asset_id.value if isinstance(from_asset_id, AssetId) else from_asset_id
        
        limit = next(
            (l for l in limits if l.asset_id == asset_id_str),
            None
        )

        if limit is None:
            raise SplitNowValidationError(
                f"No deposit limits found for asset {asset_id_str}"
            )

        min_per_wallet = limit.min_deposit
        min_amount = min_per_wallet * len(wallet_distributions)

        if from_amount < min_amount:
            raise SplitNowValidationError(
                f"Failed to create order: Minimum deposit is {min_amount} {asset_id_str.upper()} "
                f"({min_per_wallet} * {len(wallet_distributions)} wallets)"
            )

        data = {
            "type": QuoteType.FLOATING_RATE.value,
            "quoteId": quote_id,
            "orderInput": QuoteInput(
                from_amount=from_amount,
                from_asset_id=from_asset_id,
                from_network_id=from_network_id
            ).to_dict(),
            "orderOutputs": [wd.to_order_output().to_dict() for wd in wallet_distributions]
        }

        response_data = self._request("POST", "/orders/", json_data=data)
        order_response = CreateOrderResponse.from_dict(response_data)

        time.sleep(wait_time)
        
        order = self.get_order(order_response.short_id)
        return OrderData.from_order(order)

    def get_order_status(self, order_id: str) -> OrderStatusData:
        order = self.get_order(order_id)
        return OrderStatusData.from_order(order)
