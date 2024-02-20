from spread import Spread
from account import Account
from execute import Execute
from index import Index
from typing import List, Dict
import codecs


def trade_exit(command: str = None, accounts: List[Account] = None) -> None:
    """
    Exits a trade

    Parameters
    ----------
    command: str, default: None
        The command
    accounts: List[Account], default: None
        List of accounts to trade
    """
    parts: List[str] = command.split(' ')
    if len(parts) != 4:
        print("Incomplete command\n")
        return None
    index: str = parts[1].strip()
    strike: str = parts[2].strip()
    index_details: Dict = Index.get_details(index=index)
    if index_details == {}:
        print("Index is wrong or not provided\n")
        return None
    expiry: str = parts[3].strip()
    spread: Spread = Spread()
    spread.create_spread(command=index + " " + strike, expiry=expiry)
    spread.reverse()
    if spread.buying_order is None or spread.selling_order is None:
        print("Wrong trade command")
        return None
    print("\n")
    print("Exit spread details")
    print("Selling symbol: " + str(spread.selling_order.symbol))
    print("Buying symbol: " + str(spread.buying_order.symbol))
    print("\n")
    freeze_quantity: int = index_details["freeze_quantity"]
    for account in accounts:
        result: Dict = account.get_total_number_of_spreads_and_symbols()
        if result is None:
            continue
        if (result["buying_symbol"] != spread.selling_order.symbol
                or result["selling_symbol"] != spread.buying_order.symbol):
            print("Exit order mismatch with entry order for " + str(account.account_id))
            continue
        account_id: str = str(account.account_id)
        account_id = "*****" + account_id[-3:]
        print("Account ID: " + account_id)
        account.create_list_of_orders(spread=spread,
                                      freeze_quantity=freeze_quantity,
                                      total_number_of_spreads=result["total_number_of_spreads"])
        print("\n")
    Execute.place_order(accounts=accounts)
    exit_file = codecs.open("exit_file.txt", "w")
    exit_file.write("")
    exit_file.close()
    return None
