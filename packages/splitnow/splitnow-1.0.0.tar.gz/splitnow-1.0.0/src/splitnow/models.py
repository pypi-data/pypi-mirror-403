from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from splitnow.enums import AssetId, NetworkId, ExchangerId, OrderStatus 

@dataclass
class AssetLimits:
    min: Optional[float] = None
    max: Optional[float] = None


@dataclass
class AssetStatus:
    send: bool = True
    receive: bool = True


@dataclass
class Asset:
    id: str
    url: str
    ca: Optional[str]
    type: str
    asset_id: str
    network_id: str
    network_name: str
    symbol: str
    display_name: str
    decimals: int
    precision: int
    limits: AssetLimits
    status: AssetStatus
    logo_path: str
    asset_color: str
    network_color: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Asset":
        return cls(
            id=data["id"],
            url=data["url"],
            ca=data.get("ca"),
            type=data["type"],
            asset_id=data["assetId"],
            network_id=data["networkId"],
            network_name=data["networkName"],
            symbol=data["symbol"],
            display_name=data["displayName"],
            decimals=data["decimals"],
            precision=data["precision"],
            limits=AssetLimits(
                min=data["limits"].get("min"),
                max=data["limits"].get("max")
            ),
            status=AssetStatus(
                send=data["status"]["send"],
                receive=data["status"]["receive"]
            ),
            logo_path=data["logoPath"],
            asset_color=data["assetColor"],
            network_color=data["networkColor"]
        )


@dataclass
class AssetLimit:
    asset_id: str
    min_deposit: Optional[float]
    max_deposit: Optional[float]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetLimit":
        return cls(
            asset_id=data["assetId"],
            min_deposit=data.get("minDeposit"),
            max_deposit=data.get("maxDeposit")
        )

@dataclass
class Country:
    country_code: str
    country_name: str
    country_flag: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Country":
        return cls(
            country_code=data["countryCode"],
            country_name=data["countryName"],
            country_flag=data["countryFlag"]
        )


@dataclass
class ExchangerAbout:
    country: Country
    year: int
    description: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExchangerAbout":
        return cls(
            country=Country.from_dict(data["country"]),
            year=data["year"],
            description=data.get("description")
        )


@dataclass
class BannerPath:
    light_mode: str
    dark_mode: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BannerPath":
        return cls(
            light_mode=data["lightMode"],
            dark_mode=data["darkMode"]
        )


@dataclass
class ExchangerColors:
    background: str
    foreground: str
    icon: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExchangerColors":
        return cls(
            background=data["background"],
            foreground=data["foreground"],
            icon=data["icon"]
        )


@dataclass
class ExchangerStatus:
    show: bool
    quotes: bool
    orders: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExchangerStatus":
        return cls(
            show=data["show"],
            quotes=data["quotes"],
            orders=data["orders"]
        )


@dataclass
class Exchanger:
    id: str
    name: str
    website: str
    category: str
    about: ExchangerAbout
    logo_path: str
    banner_path: BannerPath
    colors: ExchangerColors
    status: ExchangerStatus
    is_available: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Exchanger":
        return cls(
            id=data["id"],
            name=data["name"],
            website=data["website"],
            category=data["category"],
            about=ExchangerAbout.from_dict(data["about"]),
            logo_path=data["logoPath"],
            banner_path=BannerPath.from_dict(data["bannerPath"]),
            colors=ExchangerColors.from_dict(data["colors"]),
            status=ExchangerStatus.from_dict(data["status"]),
            is_available=data["isAvailable"]
        )

@dataclass
class QuoteInput:
    from_amount: float
    from_asset_id: Union[str, AssetId]
    from_network_id: Union[str, NetworkId]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fromAmount": self.from_amount,
            "fromAssetId": self.from_asset_id.value if isinstance(self.from_asset_id, AssetId) else self.from_asset_id,
            "fromNetworkId": self.from_network_id.value if isinstance(self.from_network_id, NetworkId) else self.from_network_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuoteInput":
        return cls(
            from_amount=data["fromAmount"],
            from_asset_id=data["fromAssetId"],
            from_network_id=data["fromNetworkId"]
        )


@dataclass
class QuoteOutput:
    to_pct_bips: int
    to_asset_id: Union[str, AssetId]
    to_network_id: Union[str, NetworkId]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "toPctBips": self.to_pct_bips,
            "toAssetId": self.to_asset_id.value if isinstance(self.to_asset_id, AssetId) else self.to_asset_id,
            "toNetworkId": self.to_network_id.value if isinstance(self.to_network_id, NetworkId) else self.to_network_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuoteOutput":
        return cls(
            to_pct_bips=data["toPctBips"],
            to_asset_id=data["toAssetId"],
            to_network_id=data["toNetworkId"]
        )


@dataclass
class QuoteLegLimits:
    min_amount: float
    max_amount: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuoteLegLimits":
        return cls(
            min_amount=data["minAmount"],
            max_amount=data["maxAmount"]
        )


@dataclass
class QuoteLegOutput:
    to_pct_bips: int
    to_amount: float
    to_asset_id: str
    to_network_id: str
    to_exchanger_id: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuoteLegOutput":
        return cls(
            to_pct_bips=data["toPctBips"],
            to_amount=data["toAmount"],
            to_asset_id=data["toAssetId"],
            to_network_id=data["toNetworkId"],
            to_exchanger_id=data["toExchangerId"]
        )


@dataclass
class QuoteLeg:
    status: str
    type: str
    quote_id: Any
    quote_leg_input: QuoteInput
    quote_leg_output: QuoteLegOutput
    limits: QuoteLegLimits
    created_at: Any
    updated_at: Any

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuoteLeg":
        return cls(
            status=data["status"],
            type=data["type"],
            quote_id=data["quoteId"],
            quote_leg_input=QuoteInput.from_dict(data["quoteLegInput"]),
            quote_leg_output=QuoteLegOutput.from_dict(data["quoteLegOutput"]),
            limits=QuoteLegLimits.from_dict(data["limits"]),
            created_at=data["createdAt"],
            updated_at=data["updatedAt"]
        )


@dataclass
class Quote:
    _id: Any
    status: str
    type: str
    user_id: Optional[Any]
    api_key_id: Optional[Any]
    quote_input: QuoteInput
    quote_legs: List[QuoteLeg]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Quote":
        return cls(
            _id=data["_id"],
            status=data["status"],
            type=data["type"],
            user_id=data.get("userId"),
            api_key_id=data.get("apiKeyId"),
            quote_input=QuoteInput.from_dict(data["quoteInput"]),
            quote_legs=[QuoteLeg.from_dict(leg) for leg in data["quoteLegs"]],
        )

@dataclass
class OrderOutput:
    to_address: str
    to_pct_bips: int
    to_asset_id: Union[str, AssetId]
    to_network_id: Union[str, NetworkId]
    to_exchanger_id: Union[str, ExchangerId]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "toAddress": self.to_address,
            "toPctBips": self.to_pct_bips,
            "toAssetId": self.to_asset_id.value if isinstance(self.to_asset_id, AssetId) else self.to_asset_id,
            "toNetworkId": self.to_network_id.value if isinstance(self.to_network_id, NetworkId) else self.to_network_id,
            "toExchangerId": self.to_exchanger_id.value if isinstance(self.to_exchanger_id, ExchangerId) else self.to_exchanger_id
        }


@dataclass
class OrderOutputResponse:
    to_distribution_id: int
    to_address: str
    to_pct_bips: int
    to_amount: float
    to_asset_id: str
    to_network_id: str
    to_exchanger_id: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderOutputResponse":
        return cls(
            to_distribution_id=data["toDistributionId"],
            to_address=data["toAddress"],
            to_pct_bips=data["toPctBips"],
            to_amount=data["toAmount"],
            to_asset_id=data["toAssetId"],
            to_network_id=data["toNetworkId"],
            to_exchanger_id=data["toExchangerId"]
        )


@dataclass
class OrderLegOutput:
    to_distribution_id: int
    to_address: str
    to_pct_bips: int
    to_amount: float
    to_asset_id: str
    to_network_id: str
    to_exchanger_id: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderLegOutput":
        return cls(
            to_distribution_id=data["toDistributionId"],
            to_address=data["toAddress"],
            to_pct_bips=data["toPctBips"],
            to_amount=data["toAmount"],
            to_asset_id=data["toAssetId"],
            to_network_id=data["toNetworkId"],
            to_exchanger_id=data["toExchangerId"]
        )


@dataclass
class OrderLeg:
    status: str
    status_short: str
    status_text: str
    type: str
    order_id: Any
    order_leg_input: QuoteInput
    order_leg_output: OrderLegOutput
    created_at: Any
    updated_at: Any

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderLeg":
        return cls(
            status=data["status"],
            status_short=data["statusShort"],
            status_text=data["statusText"],
            type=data["type"],
            order_id=data["orderId"],
            order_leg_input=QuoteInput.from_dict(data["orderLegInput"]),
            order_leg_output=OrderLegOutput.from_dict(data["orderLegOutput"]),
            created_at=data["createdAt"],
            updated_at=data["updatedAt"]
        )


@dataclass
class Order:
    _id: Any
    status: str
    status_short: str
    status_text: str
    type: str
    short_id: str
    user_id: Optional[Any]
    api_key_id: Optional[Any]
    quote_id: Any
    order_input: QuoteInput
    order_outputs: List[OrderOutputResponse]
    order_legs: List[OrderLeg]
    expired_at: Any
    created_at: Any
    updated_at: Any
    deposit_wallet_address: Optional[str]
    deposit_amount: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        return cls(
            _id=data["_id"],
            status=data["status"],
            status_short=data["statusShort"],
            status_text=data["statusText"],
            type=data["type"],
            short_id=data["shortId"],
            user_id=data.get("userId"),
            api_key_id=data.get("apiKeyId"),
            quote_id=data["quoteId"],
            order_input=QuoteInput.from_dict(data["orderInput"]),
            order_outputs=[OrderOutputResponse.from_dict(o) for o in data["orderOutputs"]],
            order_legs=[OrderLeg.from_dict(leg) for leg in data["orderLegs"]],
            expired_at=data["expiredAt"],
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
            deposit_wallet_address=data.get("depositWalletAddress"),
            deposit_amount=data["depositAmount"]
        )


@dataclass
class CreateOrderResponse:
    order_id: str
    short_id: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CreateOrderResponse":
        return cls(
            order_id=data["orderId"],
            short_id=data["shortId"]
        )

@dataclass
class ExchangeRate:
    exchange_id: str
    exchange_rate: float

    @classmethod
    def from_quote_leg(cls, quote_leg: QuoteLeg) -> "ExchangeRate":
        return cls(
            exchange_id=quote_leg.quote_leg_output.to_exchanger_id,
            exchange_rate=round(quote_leg.quote_leg_output.to_amount * 0.99, 3)
        )


@dataclass
class QuoteData:
    quote_id: str
    rates: List[ExchangeRate]

    @classmethod
    def from_quote(cls, quote_id: str, quote: Quote) -> "QuoteData":
        return cls(
            quote_id=quote_id,
            rates=[ExchangeRate.from_quote_leg(leg) for leg in quote.quote_legs]
        )


@dataclass
class OrderData:
    order_id: str
    deposit_address: Optional[str]
    deposit_amount: float

    @classmethod
    def from_order(cls, order: Order) -> "OrderData":
        return cls(
            order_id=order.short_id,
            deposit_address=order.deposit_wallet_address,
            deposit_amount=order.order_input.from_amount
        )


@dataclass
class OrderStatusData:
    order_id: str
    order_status: OrderStatus
    order_status_text: str

    @classmethod
    def from_order(cls, order: Order) -> "OrderStatusData":
        try:
            status = OrderStatus(order.status_short)
        except ValueError:
            status = OrderStatus.PENDING
        
        return cls(
            order_id=order.short_id,
            order_status=status,
            order_status_text=order.status_text
        )


@dataclass 
class WalletDistribution:
    to_address: str
    to_pct_bips: int
    to_asset_id: Union[str, AssetId]
    to_network_id: Union[str, NetworkId]
    to_exchanger_id: Union[str, ExchangerId]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "toAddress": self.to_address,
            "toPctBips": self.to_pct_bips,
            "toAssetId": self.to_asset_id.value if isinstance(self.to_asset_id, AssetId) else self.to_asset_id,
            "toNetworkId": self.to_network_id.value if isinstance(self.to_network_id, AssetId) else self.to_network_id,
            "toExchangerId": self.to_exchanger_id.value if isinstance(self.to_exchanger_id, ExchangerId) else self.to_exchanger_id
        }

    def to_order_output(self) -> OrderOutput:
        return OrderOutput(
            to_address=self.to_address,
            to_pct_bips=self.to_pct_bips,
            to_asset_id=self.to_asset_id,
            to_network_id=self.to_network_id,
            to_exchanger_id=self.to_exchanger_id
        )
