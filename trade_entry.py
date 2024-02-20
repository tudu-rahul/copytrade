from spread import Spread
from account import Account
from execute import Execute
from index import Index
from typing import List, Dict
import codecs


def trade_entry(command: str = None, accounts: List[Account] = None, my_account: Account = None) -> None:
    """
    Enters a trade

    Parameters
    ----------
    command: str, default: None
        The command
    accounts: List[Account], default: None
        List of accounts to trade
    my_account: Account, default: None
        My primary trading account
    """
    parts: List[str] = command.split(' ')
    if len(parts) != 4:
        print("Incomplete command")
        return None
    index: str = parts[1].strip()
    strike: str = parts[2].strip()
    index_details: Dict = Index.get_details(index=index)
    if index_details == {}:
        print("Index is wrong or not provided")
        print("\n")
        return None
    expiry: str = parts[3].strip()
    exit_command: str = "EXIT" + " " + index + " " + strike + " " + expiry
    spread: Spread = Spread()
    spread.create_spread(command=index + " " + strike, expiry=expiry)
    spread.get_margin_per_lot(smartapi=my_account.smartapi)
    if spread.buying_order is None or spread.selling_order is None:
        print("Wrong trade command\n")
        return None
    print("\n")
    print("Entry spread details")
    print("Buying symbol: " + str(spread.buying_order.symbol))
    print("Selling symbol: " + str(spread.selling_order.symbol))
    print("Margin per lot: Rs " + str(spread.margin_per_lot))
    print("\n")
    freeze_quantity: int = index_details["freeze_quantity"]
    for account in accounts:
        account_id: str = account.account_id
        account_id = "*****" + account_id[-3:]
        print("Account ID: " + account_id)
        account.create_list_of_orders(spread=spread, freeze_quantity=freeze_quantity)
        print("\n")
    Execute.place_order(accounts=accounts)
    exit_file = codecs.open("exit_file.txt", "w")
    exit_file.write(exit_command)
    exit_file.close()
    return None
