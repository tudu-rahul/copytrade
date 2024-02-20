from login import Login
from trading_symbols import TradingSymbols
from typing import Optional
from account import Account
import logging
import command_driver as Driver


logging.basicConfig(filename='all.log', encoding='utf-8', level=logging.WARNING)


if __name__ == '__main__':
    """
    This is the main function which handles the entry point to all commands
    
    Sample commands:
        entry:
            ENTRY <index> <strike> <expiry>
            ENTRY MIDCPNIFTY 10525CE 29JAN24
        exit:
            EXIT <index> <strike> <expiry>
            EXIT MIDCPNIFTY 10525CE 29JAN24
        details:
            DETAILS
        p&l:
            PNL
    """
    print("\n")
    accounts, my_account_id = Login.read_credentials_and_login()
    if my_account_id is None:
        exit(1)
    TradingSymbols.initialize()
    total_balance: float = 0.0
    my_account: Optional[Account] = None
    for account in accounts:
        if account.account_id == my_account_id:
            my_account = account
        total_balance += account.balance
        name: str = str(account.account_name)
        name = name[:3] + "*****"
        print(name + " successfully logged in")
        print("Capital to use: Rs " + str(account.capital_to_use))
        print("Balance: Rs " + str(account.balance) + "\n")
    print("\n")
    # print("Total balance: Rs " + str(total_balance))
    print("Total valid clients: " + str(len(accounts)))
    print("------------------------------------------------------------\n")
    while True:
        print("Command: ")
        command: str = input()
        Driver.driver(command=command, accounts=accounts, my_account=my_account)
