import trade_entry
import trade_exit
import trade_auto_exit
import trade_details
import trade_pnl
from typing import List
from account import Account


def driver(command: str = None, accounts: List[Account] = None, my_account: Account = None) -> None:
    """
    This driver is for processing a command and perform necessary actions

    Parameters
    ----------
    command: str, default: None
        The command
    accounts: List[Account], default: None
        List of accounts to trade
    my_account: Account, default: None
        My primary trading account
    """
    if command is None or accounts is None or my_account is None:
        print("Missing data")
        print("\n")
        return
    command = command.strip()
    command_type: str = command.split(' ')[0]
    if command_type == "ENTRY":
        trade_entry.trade_entry(command=command, accounts=accounts, my_account=my_account)
    elif command_type == "EXIT":
        trade_exit.trade_exit(command=command, accounts=accounts)
    elif command_type == "AUTOEXIT":
        trade_auto_exit.trade_auto_exit(command=command, accounts=accounts, my_account=my_account)
    elif command_type == "DETAILS":
        trade_details.details(accounts=accounts, my_account=my_account)
    elif command_type == "PNL":
        trade_pnl.pnl(accounts=accounts)
    else:
        print("Wrong command\n")
    return None
