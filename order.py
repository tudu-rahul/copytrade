class Order:
    """
    Class to represent an order

    ...

    Attributes
    ----------
    qty: int
        Quantity in integer format
    symbol: str
        Trading symbol
    tradingsymbol: str
        Trading symbol
    exchange: str
        Exchange name
    price: float
        Price if limit order is placed, else 0
    productType: str
        Type of order, right now which is fixed at CARRYFORWARD
    producttype: str
        Type of order, right now which is fixed at CARRYFORWARD
    duration: str
        Duration of validity of the order
    ordertype: str
        Type of order, right now which is fixed at MARKET
    quantity: str
        Quantity in string format
    token: str
        Trading token
    symboltoken: str
        Trading token
    tradeType: str
        Type of trade, either can be BUY or SELL
    transactiontype: str
        Type of trade, either can be BUY or SELL
    variety: str
        Variety of trade, right now which is fixed at NORMAL
    """

    def __init__(self, quantity: int = None, symbol: str = None, token: str = None, tradetype: str = None):
        self.qty: int = quantity
        self.symbol: str = symbol
        self.tradingsymbol: str = symbol
        self.exchange: str = "NFO"
        self.price: float = 0
        self.productType: str = "INTRADAY"
        self.producttype: str = "INTRADAY"
        self.duration: str = "DAY"
        self.ordertype: str = "MARKET"
        self.quantity: str = str(quantity)
        self.token: str = token
        self.symboltoken: str = token
        self.tradeType: str = tradetype
        self.transactiontype: str = tradetype
        self.variety: str = "NORMAL"
