import json
from typing import Optional, Dict

symbol_map: Dict = {}


class TradingSymbols:
    """
    A class to manage trading symbols
    download link: https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json

    ...

    Methods
    -------
    initialize() -> None:
        Initializes the symbol map
    get_token(symbol: str = None) -> Optional[str]:
        Returns token for a given symbol
    """

    @staticmethod
    def initialize() -> None:
        """
        Initializes the symbol map

        Returns
        -------
        None
        """
        symbol_file = open("tokens.json")
        data = json.load(symbol_file)
        for row in data:
            curr_row = dict(row)
            symbol = curr_row["symbol"]
            symbol_map[symbol] = curr_row["token"]
        symbol_file.close()

        return None

    @staticmethod
    def get_token(symbol: str = None) -> Optional[str]:
        """
        Returns token for a given symbol

        Parameters
        ----------
        symbol : str
            The symbol for which token is required

        Returns
        -------
        Optional[str]:
            Token of the symbol provided
        """
        if symbol in symbol_map:
            return symbol_map[symbol]

        return None
