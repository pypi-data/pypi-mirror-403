from enum import Enum


class AssetId(str, Enum):
    ETH = "eth"
    BNB = "bnb"
    AVAX = "avax"
    POL = "pol"
    CRO = "cro"
    TRX = "trx"
    SOL = "sol"
    BTC = "btc"
    LTC = "ltc"
    DOGE = "doge"
    XMR = "xmr"
    BCH = "bch"
    TON = "ton"
    XRP = "xrp"
    ADA = "ada"
    SUI = "sui"
    DOT = "dot"
    HYPE = "hype"
    USDT = "usdt"
    USDC = "usdc"
    USD1 = "usd1"
    XLM = "xlm"
    VET = "vet"
    DASH = "dash"
    HBAR = "hbar"
    XTZ = "xtz"
    ZEC = "zec"
    FIL = "fil"
    ALGO = "algo"
    ATOM = "atom"
    APT = "apt"
    ETC = "etc"
    NEAR = "near"
    XPL = "xpl"
    OKB = "okb"
    IP = "ip"
    MON = "mon"


class NetworkId(str, Enum):
    ETHEREUM = "ethereum"
    BASE = "base"
    BINANCE_SMART_CHAIN = "binance_smart_chain"
    AVALANCHE_C_CHAIN = "avalanche_c_chain"
    POLYGON = "polygon"
    CRONOS = "cronos"
    TRON = "tron"
    SOLANA = "solana"
    BITCOIN = "bitcoin"
    BITCOIN_LN = "bitcoin_ln"
    LITECOIN = "litecoin"
    DOGECOIN = "dogecoin"
    MONERO = "monero"
    BITCOIN_CASH = "bitcoin_cash"
    TON = "ton"
    RIPPLE = "ripple"
    CARDANO = "cardano"
    SUI = "sui"
    POLKADOT = "polkadot"
    HYPERLIQUID = "hyperliquid"
    ARBITRUM_ONE = "arbitrum_one"
    OPTIMISM = "optimism"
    STELLAR = "stellar"
    VECHAIN = "vechain"
    DASH = "dash"
    HEDERA = "hedera"
    TEZOS = "tezos"
    ZCASH = "zcash"
    FILECOIN = "filecoin"
    ALGORAND = "algorand"
    COSMOS = "cosmos"
    APTOS = "aptos"
    ETHEREUM_CLASSIC = "ethereum_classic"
    AVALANCHE_X_CHAIN = "avalanche_x_chain"
    NEAR = "near"
    PLASMA = "plasma"
    ABSTRACT = "abstract"
    HYPEREVM = "hyperevm"
    INK = "ink"
    X_LAYER = "x_layer"
    STORY = "story"
    MONAD = "monad"


class ExchangerId(str, Enum):
    BINANCE = "binance"
    BYBIT = "bybit"
    GATE = "gate"
    HUOBI = "huobi"
    KUCOIN = "kucoin"
    MEXC = "mexc"
    COINSTORE = "coinstore"
    KRAKEN = "kraken"
    HITBTC = "hitbtc"
    WHITEBIT = "whitebit"
    ALFACASH = "alfacash"
    BITCOINVN = "bitcoinvn"
    BITSWAP = "bitswap"
    BITXCHANGE = "bitxchange"
    CCECASH = "ccecash"
    CHANGEE = "changee"
    CHANGEHERO = "changehero"
    CHANGELLY = "changelly"
    CHANGENOW = "changenow"
    COINCRADDLE = "coincraddle"
    EASYBIT = "easybit"
    ETZ = "etz"
    EXCH = "exch"
    EXOLIX = "exolix"
    EXPLACE = "explace"
    EXWELL = "exwell"
    FIXEDFLOAT = "fixedfloat"
    FLYPME = "flypme"
    FUGUSWAP = "fuguswap"
    GODEX = "godex"
    GOEXME = "goexme"
    GUARDEX = "guardex"
    HELLEX = "hellex"
    KRYPTOSWAP = "kryptoswap"
    LETSEXCHANGE = "letsexchange"
    LIZEX = "lizex"
    NANSWAP = "nanswap"
    NEVERKYC = "neverkyc"
    NEXCHANGE = "nexchange"
    OCTOSWAP = "octoswap"
    PEGASUSSWAP = "pegasusswap"
    QUICKEX = "quickex"
    SECURESHIFT = "secureshift"
    SHAMAN = "shaman"
    SHAPEBTC = "shapebtc"
    SIDESHIFT = "sideshift"
    SILKBYTE = "silkbyte"
    SIMPLESWAP = "simpleswap"
    SNAPSWAP = "snapswap"
    SPLITOTC = "splitotc"
    STEALTHEX = "stealthex"
    SWAPGATE = "swapgate"
    SWAPONIX = "swaponix"
    SWAPPIX = "swappix"
    SWAPSPACE = "swapspace"
    SWAPTAXI = "swaptaxi"
    SWAPTER = "swapter"
    SWAPTRADE = "swaptrade"
    SWAPUZ = "swapuz"
    THECHANGE = "thechange"
    WIZARDSWAP = "wizardswap"
    XCHANGE = "xchange"
    XGRAM = "xgram"


class QuoteType(str, Enum):
    FLOATING_RATE = "floating_rate"
    FIXED_RATE = "fixed_rate"
    MIXED_RATE = "mixed_rate"


class APIOrderStatus(str, Enum):
    # Get picked up by clearinghouse
    PENDING_DEPOSIT_WALLET = "pending_deposit_wallet"
    # Create deposit wallet
    CREATING_DEPOSIT_WALLET = "creating_deposit_wallet"
    CREATING_DEPOSIT_WALLET_FAILED = "creating_deposit_wallet_failed"
    CREATING_DEPOSIT_WALLET_HALTED = "creating_deposit_wallet_halted"
    CREATING_DEPOSIT_WALLET_COMPLETED = "creating_deposit_wallet_completed"
    # Monitor user deposit
    USER_DEPOSIT_PENDING = "user_deposit_pending"
    USER_DEPOSIT_DETECTED = "user_deposit_detected"
    USER_DEPOSIT_EXPIRED = "user_deposit_expired"
    USER_DEPOSIT_FAILED = "user_deposit_failed"
    USER_DEPOSIT_HALTED = "user_deposit_halted"
    USER_DEPOSIT_COMPLETED = "user_deposit_completed"
    # Send from hot wallet (ONLY IF deposit wallet needs gas)
    SENDING_TO_DEPOSIT_WALLET = "sending_to_deposit_wallet"
    SENDING_TO_DEPOSIT_WALLET_FAILED = "sending_to_deposit_wallet_failed"
    SENDING_TO_DEPOSIT_WALLET_HALTED = "sending_to_deposit_wallet_halted"
    SENDING_TO_DEPOSIT_WALLET_COMPLETED = "sending_to_deposit_wallet_completed"
    # Send to hot wallet (from deposit wallet)
    SENDING_TO_HOT_WALLET = "sending_to_hot_wallet"
    SENDING_TO_HOT_WALLET_FAILED = "sending_to_hot_wallet_failed"
    SENDING_TO_HOT_WALLET_HALTED = "sending_to_hot_wallet_halted"
    SENDING_TO_HOT_WALLET_COMPLETED = "sending_to_hot_wallet_completed"
    # Send to gas wallet (from deposit wallet) (ONLY IF deposit wallet needed gas)
    SENDING_TO_GAS_WALLET = "sending_to_gas_wallet"
    SENDING_TO_GAS_WALLET_FAILED = "sending_to_gas_wallet_failed"
    SENDING_TO_GAS_WALLET_HALTED = "sending_to_gas_wallet_halted"
    SENDING_TO_GAS_WALLET_COMPLETED = "sending_to_gas_wallet_completed"
    # Send to fee wallet (from hot wallet)
    SENDING_TO_FEE_WALLET = "sending_to_fee_wallet"
    SENDING_TO_FEE_WALLET_FAILED = "sending_to_fee_wallet_failed"
    SENDING_TO_FEE_WALLET_HALTED = "sending_to_fee_wallet_halted"
    SENDING_TO_FEE_WALLET_COMPLETED = "sending_to_fee_wallet_completed"
    # Create order legs
    CREATING_ORDER_LEGS = "creating_order_legs"
    CREATING_ORDER_LEGS_FAILED = "creating_order_legs_failed"
    CREATING_ORDER_LEGS_HALTED = "creating_order_legs_halted"
    CREATING_ORDER_LEGS_COMPLETED = "creating_order_legs_completed"
    # Send to provider deposit wallet(s) (from hot wallet)
    SETTLING_ORDER_LEGS = "settling_order_legs"
    SETTLING_ORDER_LEGS_FAILED = "settling_order_legs_failed"
    SETTLING_ORDER_LEGS_HALTED = "settling_order_legs_halted"
    SETTLING_ORDER_LEGS_COMPLETED = "settling_order_legs_completed"
    # Monitoring provider orders
    MONITORING = "monitoring"
    # Results
    EXPIRED = "expired"
    HALTED = "halted"
    FAILED = "failed"
    REFUNDED = "refunded"
    COMPLETED = "completed"


class APIOrderLegStatus(str, Enum):
    # Waiting for creation
    WAITING = "waiting"
    # Get picked up by clearinghouse
    PENDING_PROVIDER_ORDER = "pending_provider_order"
    # Call API provider
    CREATING_PROVIDER_ORDER = "creating_provider_order"
    CREATING_PROVIDER_ORDER_FAILED = "creating_provider_order_failed"
    CREATING_PROVIDER_ORDER_HALTED = "creating_provider_order_halted"
    CREATING_PROVIDER_ORDER_COMPLETED = "creating_provider_order_completed"
    # Send from hot wallet to provider wallet
    SENDING_TO_PROVIDER_DEPOSIT = "sending_to_provider_deposit"
    SENDING_TO_PROVIDER_DEPOSIT_FAILED = "sending_to_provider_deposit_failed"
    SENDING_TO_PROVIDER_DEPOSIT_HALTED = "sending_to_provider_deposit_halted"
    SENDING_TO_PROVIDER_DEPOSIT_COMPLETED = "sending_to_provider_deposit_completed"
    # Monitor provider order
    PENDING = "pending"
    PROVIDER_DEPOSIT_DETECTED = "provider_deposit_detected"
    PROVIDER_DEPOSIT_CONFIRMED = "provider_deposit_confirmed"
    PROVIDER_EXCHANGE_CONFIRMED = "provider_exchange_confirmed"
    PROVIDER_WITHDRAWAL_CONFIRMED = "provider_withdrawal_confirmed"
    # Results
    EXPIRED = "expired"
    HALTED = "halted"
    FAILED = "failed"
    REFUNDED = "refunded"
    COMPLETED = "completed"


class OrderStatus(str, Enum):
    PENDING = "pending"
    SENDING = "sending"
    MONITORING = "monitoring"
    EXPIRED = "expired"
    HALTED = "halted"
    FAILED = "failed"
    REFUNDED = "refunded"
    COMPLETED = "completed"


class OrderLegStatus(str, Enum):
    WAITING = "waiting"
    PENDING = "pending"
    SENDING = "sending"
    CONFIRMING = "confirming"
    EXCHANGING = "exchanging"
    WITHDRAWING = "withdrawing"
    EXPIRED = "expired"
    HALTED = "halted"
    FAILED = "failed"
    REFUNDED = "refunded"
    COMPLETED = "completed"


class OrderStatusText(str, Enum):
    PENDING = "Awaiting Deposit"
    SENDING = "Settling Order Legs"
    MONITORING = "Monitoring Order Legs"
    EXPIRED = "Order Expired"
    HALTED = "Order Halted"
    FAILED = "Order Failed"
    REFUNDED = "Order Refunded"
    COMPLETED = "Order Completed"


class OrderLegStatusText(str, Enum):
    WAITING = "Awaiting Creation"
    PENDING = "Awaiting Deposit"
    SENDING = "Sending Deposit"
    CONFIRMING = "Confirming Deposit"
    EXCHANGING = "Exchanging Funds"
    WITHDRAWING = "Withdrawing Funds"
    EXPIRED = "Order Leg Expired"
    HALTED = "Order Leg Halted"
    FAILED = "Order Leg Failed"
    REFUNDED = "Order Leg Refunded"
    COMPLETED = "Order Leg Completed"

ORDER_STATUS_MAP: dict[str, OrderStatus] = {
    APIOrderStatus.PENDING_DEPOSIT_WALLET.value: OrderStatus.PENDING,
    APIOrderStatus.CREATING_DEPOSIT_WALLET.value: OrderStatus.PENDING,
    APIOrderStatus.CREATING_DEPOSIT_WALLET_FAILED.value: OrderStatus.PENDING,
    APIOrderStatus.CREATING_DEPOSIT_WALLET_HALTED.value: OrderStatus.HALTED,
    APIOrderStatus.CREATING_DEPOSIT_WALLET_COMPLETED.value: OrderStatus.PENDING,
    APIOrderStatus.USER_DEPOSIT_PENDING.value: OrderStatus.PENDING,
    APIOrderStatus.USER_DEPOSIT_DETECTED.value: OrderStatus.PENDING,
    APIOrderStatus.USER_DEPOSIT_EXPIRED.value: OrderStatus.PENDING,
    APIOrderStatus.USER_DEPOSIT_FAILED.value: OrderStatus.PENDING,
    APIOrderStatus.USER_DEPOSIT_HALTED.value: OrderStatus.HALTED,
    APIOrderStatus.USER_DEPOSIT_COMPLETED.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_DEPOSIT_WALLET.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_DEPOSIT_WALLET_FAILED.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_DEPOSIT_WALLET_HALTED.value: OrderStatus.HALTED,
    APIOrderStatus.SENDING_TO_DEPOSIT_WALLET_COMPLETED.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_HOT_WALLET.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_HOT_WALLET_FAILED.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_HOT_WALLET_HALTED.value: OrderStatus.HALTED,
    APIOrderStatus.SENDING_TO_HOT_WALLET_COMPLETED.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_GAS_WALLET.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_GAS_WALLET_FAILED.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_GAS_WALLET_HALTED.value: OrderStatus.HALTED,
    APIOrderStatus.SENDING_TO_GAS_WALLET_COMPLETED.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_FEE_WALLET.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_FEE_WALLET_FAILED.value: OrderStatus.SENDING,
    APIOrderStatus.SENDING_TO_FEE_WALLET_HALTED.value: OrderStatus.HALTED,
    APIOrderStatus.SENDING_TO_FEE_WALLET_COMPLETED.value: OrderStatus.SENDING,
    APIOrderStatus.CREATING_ORDER_LEGS.value: OrderStatus.SENDING,
    APIOrderStatus.CREATING_ORDER_LEGS_FAILED.value: OrderStatus.SENDING,
    APIOrderStatus.CREATING_ORDER_LEGS_HALTED.value: OrderStatus.HALTED,
    APIOrderStatus.CREATING_ORDER_LEGS_COMPLETED.value: OrderStatus.SENDING,
    APIOrderStatus.SETTLING_ORDER_LEGS.value: OrderStatus.SENDING,
    APIOrderStatus.SETTLING_ORDER_LEGS_FAILED.value: OrderStatus.SENDING,
    APIOrderStatus.SETTLING_ORDER_LEGS_HALTED.value: OrderStatus.HALTED,
    APIOrderStatus.SETTLING_ORDER_LEGS_COMPLETED.value: OrderStatus.MONITORING,
    APIOrderStatus.MONITORING.value: OrderStatus.MONITORING,
    APIOrderStatus.EXPIRED.value: OrderStatus.EXPIRED,
    APIOrderStatus.HALTED.value: OrderStatus.HALTED,
    APIOrderStatus.FAILED.value: OrderStatus.FAILED,
    APIOrderStatus.REFUNDED.value: OrderStatus.REFUNDED,
    APIOrderStatus.COMPLETED.value: OrderStatus.COMPLETED,
}

ORDER_LEG_STATUS_MAP: dict[str, OrderLegStatus] = {
    APIOrderLegStatus.WAITING.value: OrderLegStatus.WAITING,
    APIOrderLegStatus.PENDING_PROVIDER_ORDER.value: OrderLegStatus.SENDING,
    APIOrderLegStatus.CREATING_PROVIDER_ORDER.value: OrderLegStatus.SENDING,
    APIOrderLegStatus.CREATING_PROVIDER_ORDER_FAILED.value: OrderLegStatus.SENDING,
    APIOrderLegStatus.CREATING_PROVIDER_ORDER_HALTED.value: OrderLegStatus.HALTED,
    APIOrderLegStatus.CREATING_PROVIDER_ORDER_COMPLETED.value: OrderLegStatus.SENDING,
    APIOrderLegStatus.SENDING_TO_PROVIDER_DEPOSIT.value: OrderLegStatus.SENDING,
    APIOrderLegStatus.SENDING_TO_PROVIDER_DEPOSIT_FAILED.value: OrderLegStatus.SENDING,
    APIOrderLegStatus.SENDING_TO_PROVIDER_DEPOSIT_HALTED.value: OrderLegStatus.HALTED,
    APIOrderLegStatus.SENDING_TO_PROVIDER_DEPOSIT_COMPLETED.value: OrderLegStatus.SENDING,
    APIOrderLegStatus.PENDING.value: OrderLegStatus.PENDING,
    APIOrderLegStatus.PROVIDER_DEPOSIT_DETECTED.value: OrderLegStatus.CONFIRMING,
    APIOrderLegStatus.PROVIDER_DEPOSIT_CONFIRMED.value: OrderLegStatus.EXCHANGING,
    APIOrderLegStatus.PROVIDER_EXCHANGE_CONFIRMED.value: OrderLegStatus.WITHDRAWING,
    APIOrderLegStatus.PROVIDER_WITHDRAWAL_CONFIRMED.value: OrderLegStatus.COMPLETED,
    APIOrderLegStatus.EXPIRED.value: OrderLegStatus.EXPIRED,
    APIOrderLegStatus.HALTED.value: OrderLegStatus.HALTED,
    APIOrderLegStatus.FAILED.value: OrderLegStatus.FAILED,
    APIOrderLegStatus.REFUNDED.value: OrderLegStatus.REFUNDED,
    APIOrderLegStatus.COMPLETED.value: OrderLegStatus.COMPLETED,
}

ORDER_STATUS_TEXT_MAP: dict[OrderStatus, OrderStatusText] = {
    OrderStatus.PENDING: OrderStatusText.PENDING,
    OrderStatus.SENDING: OrderStatusText.SENDING,
    OrderStatus.MONITORING: OrderStatusText.MONITORING,
    OrderStatus.EXPIRED: OrderStatusText.EXPIRED,
    OrderStatus.HALTED: OrderStatusText.HALTED,
    OrderStatus.FAILED: OrderStatusText.FAILED,
    OrderStatus.REFUNDED: OrderStatusText.REFUNDED,
    OrderStatus.COMPLETED: OrderStatusText.COMPLETED,
}

ORDER_LEG_STATUS_TEXT_MAP: dict[OrderLegStatus, OrderLegStatusText] = {
    OrderLegStatus.WAITING: OrderLegStatusText.WAITING,
    OrderLegStatus.PENDING: OrderLegStatusText.PENDING,
    OrderLegStatus.SENDING: OrderLegStatusText.SENDING,
    OrderLegStatus.CONFIRMING: OrderLegStatusText.CONFIRMING,
    OrderLegStatus.EXCHANGING: OrderLegStatusText.EXCHANGING,
    OrderLegStatus.WITHDRAWING: OrderLegStatusText.WITHDRAWING,
    OrderLegStatus.EXPIRED: OrderLegStatusText.EXPIRED,
    OrderLegStatus.HALTED: OrderLegStatusText.HALTED,
    OrderLegStatus.FAILED: OrderLegStatusText.FAILED,
    OrderLegStatus.REFUNDED: OrderLegStatusText.REFUNDED,
    OrderLegStatus.COMPLETED: OrderLegStatusText.COMPLETED,
}


def get_order_status(api_status: str) -> OrderStatus:
    # Convert an API order status to a simplified OrderStatus.
    return ORDER_STATUS_MAP.get(api_status, OrderStatus.PENDING)


def get_order_leg_status(api_status: str) -> OrderLegStatus:
    # Convert an API order leg status to a simplified OrderLegStatus.
    return ORDER_LEG_STATUS_MAP.get(api_status, OrderLegStatus.WAITING)


def get_order_status_text(status: OrderStatus) -> str:
    # Get human friendly text for an order status.
    return ORDER_STATUS_TEXT_MAP.get(status, OrderStatusText.PENDING).value


def get_order_leg_status_text(status: OrderLegStatus) -> str:
    # Get human friendly text for an order leg status.
    return ORDER_LEG_STATUS_TEXT_MAP.get(status, OrderLegStatusText.WAITING).value
