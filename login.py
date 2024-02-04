import codecs
from SmartApi import SmartConnect
import pyotp
from account import Account
from typing import List, Dict, Optional
import logging
import constants as Const
from time import sleep
import sys

log = logging.getLogger()


class Login:
    """
    Manages all login related tasks

    ...

    Methods
    -------
    login(api_key:str = None, totp_qr: str = None, username: str = None, pin: str = None) ->
        (Optional[SmartConnect], Optional[str], Optional[str], Dict[str, bool]):
        Login to Angel One for any particular account
    read_credentials_and_login() -> (List[Account], Optional[str]):
        Read credentials from file and login
    """

    @staticmethod
    def login(api_key: str = None, totp_qr: str = None, username: str = None, pin: str = None) -> (
            Optional[SmartConnect], Optional[str], Optional[str], Dict[str, bool]):
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
        Optional[SmartConnect], Optional[str], Optional[str], Dict[str, bool]:
            smartapi, refresh token, account name, exception type
        """
        totp: str = pyotp.TOTP(totp_qr).now()
        exception_type: Dict[str, bool] = {}
        try:
            smartapi: SmartConnect = SmartConnect(api_key)
            data: Optional[Dict] = smartapi.generateSession(username, pin, totp)["data"]
        except Exception as exp:
            log.exception("Session generation exception: " + str(exp))
            exception_type[Const.SESSION_GENERATION_EXCEPTION] = True
            return None, None, None, exception_type
        if data is None:
            return None, None, None, exception_type
        refresh_token: str = data["refreshToken"]
        try:
            profile: Optional[Dict] = smartapi.getProfile(refresh_token)["data"]
        except Exception as exp:
            log.exception("Profile fetching exception: " + str(exp))
            exception_type[Const.PROFILE_FETCHING_EXCEPTION] = True
            return None, None, None, exception_type
        if profile is None:
            return None, None, None, exception_type
        try:
            smartapi.generateToken(refresh_token)
        except Exception as exp:
            log.exception("Token generation exception: " + str(exp))
            exception_type[Const.TOKEN_GENERATION_EXCEPTION] = True
            return None, None, None, exception_type

        return smartapi, refresh_token, profile["name"], exception_type

    @staticmethod
    def read_credentials_and_login() -> (List[Account], Optional[str]):
        """
        Read credentials from file and login

        For each account, username, api key, pin and totp_qr are fetched and an attempt to login is made.
        If successful, a smartconnect object and refresh token are generated.
        All credentials are stored in credentials.txt

        Returns
        -------
        List[Account], Optional[str]:
            List of account objects, my account id
        """
        credentials_file = codecs.open("credentials.txt", "r")
        accounts: List[Account] = []
        api_key: Optional[str] = None
        username: Optional[str] = None
        pin: Optional[str] = None
        my_account_id: Optional[str] = None
        exception_present: bool = False
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
                exception_count: int = 0
                while True:
                    smartapi, refresh_token, name, exception_type = Login.login(api_key=api_key,
                                                                            totp_qr=totp_qr,
                                                                            username=username,
                                                                            pin=pin)
                    if exception_type != {}:
                        if not exception_present:
                            exception_present = True
                            print("Login exception occurring: " + list(exception_type.keys())[0]
                                  + ": " + str(exception_count))
                        else:
                            exception_count += 1
                            sys.stdout.write("\033[F")
                            sys.stdout.write("\033[K")
                            print("Login exception occurring: " + list(exception_type.keys())[0]
                                  + ": " + str(exception_count))
                    elif exception_type == {}:
                        if exception_present:
                            exception_present = False
                            print("Login exception solved.\n")
                        break
                    sleep(1)
                if smartapi is None or refresh_token is None or name is None:
                    continue
                current_account: Account = Account()
                current_account.account_id = username
                exception_count = 0
                rms_exception_present: bool = False
                while True:
                    try:
                        rms: Optional[Dict] = smartapi.rmsLimit()["data"]
                        if rms_exception_present:
                            print("RMS exception solved.\n")
                            rms_exception_present = False
                        break
                    except Exception as exp:
                        log.exception("RMS exception: " + str(exp))
                        exception_count += 1
                        if rms_exception_present:
                            sys.stdout.write("\033[F")
                            sys.stdout.write("\033[K")
                        rms_exception_present = True
                        print("RMS exception occurring: " + str(exception_count))
                    sleep(1)
                if rms is None:
                    continue
                current_account.balance = float(rms["availablecash"])
                current_account.account_name = name
                current_account.smartapi = smartapi
                current_account.refresh_token = refresh_token
                accounts.append(current_account)
            else:
                break
        credentials_file.close()

        return accounts, my_account_id
