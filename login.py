import codecs
from SmartApi import SmartConnect
import pyotp
from account import Account
from typing import List, Dict, Optional


class Login:
    """
    Manages all login related tasks

    ...

    Methods
    -------
    login(api_key:str = None, totp_qr: str = None, username: str = None, pin: str = None) ->
        (Optional[SmartConnect], Optional[str], Optional[str]):
        Login to Angel One for any particular account
    read_credentials_and_login() -> (List[Account], int, Optional[str]):
        Read credentials from file and login
    """

    @staticmethod
    def login(api_key: str = None, totp_qr: str = None, username: str = None, pin: str = None) -> (
            Optional[SmartConnect], Optional[str], Optional[str]):
        """
        Login to Angel One for any particular account.

        totp needed for login is made from totp_qr. smartapi, refresh token and the account holder's name is returned.

        Parameters
        ----------
        api_key : str, default : None
            API key for the account
        totp_qr : str, default : None
            QR code to generate TOTP
        username : str, default : None
            Username of the account
        pin : str, default : None
            PIN of the account

        Returns
        -------
        Optional[SmartConnect], Optional[str], Optional[str]:
            smartapi, refresh token, account name
        """
        smartapi: SmartConnect = SmartConnect(api_key)
        totp: str = pyotp.TOTP(totp_qr).now()
        data: Dict = smartapi.generateSession(username, pin, totp)["data"]
        if data is None:
            return None, None, None
        refresh_token: str = data["refreshToken"]
        profile: Dict = smartapi.getProfile(refresh_token)["data"]
        if profile is None:
            return None, None, None
        smartapi.generateToken(refresh_token)

        return smartapi, refresh_token, profile["name"]

    @staticmethod
    def read_credentials_and_login() -> (List[Account], int, Optional[str]):
        """
        Read credentials from file and login

        For each account, username, api key, pin and totp_qr are fetched and an attempt to login is made.
        If successful, a smartconnect object and refresh token are generated. In case any account has balance less than
        1 lakh, that account is not considered for trading. All credentials are stored in credentials.txt

        Returns
        -------
        List[Account], int, Optional[str]:
            List of account objects, total accounts whose balance is less than 1 lakh, my account id
        """
        credentials_file = codecs.open("credentials.txt", "r")
        accounts: List[Account] = []
        api_key: Optional[str] = None
        username: Optional[str] = None
        pin: Optional[str] = None
        defaulters: int = 0
        my_account_id: Optional[str] = None
        for lin in credentials_file:
            if lin[0] == "#":
                continue
            if len(lin.strip()) == 0:
                continue
            key: str = lin.split(':')[0].strip()
            value: str = lin.split(':')[1].strip()
            if key == "my_account_id":
                my_account_id = value
                continue
            if key == "username":
                username = value
            elif key == "api_key":
                api_key = value
            elif key == "pin":
                pin = value
            elif key == "totp_qr":
                totp_qr: str = value
                smartapi, refresh_token, name = Login.login(api_key=api_key, totp_qr=totp_qr, username=username,
                                                            pin=pin)
                current_account: Account = Account()
                current_account.account_id = username
                rms: dict = smartapi.rmsLimit()["data"]
                if rms is None:
                    defaulters += 1
                    continue
                current_account.balance = float(rms["availablecash"])
                if current_account.balance < 100000:
                    defaulters += 1
                    continue
                current_account.account_name = name
                current_account.smartapi = smartapi
                current_account.refresh_token = refresh_token
                accounts.append(current_account)
            else:
                break
        credentials_file.close()

        return accounts, defaulters, my_account_id
