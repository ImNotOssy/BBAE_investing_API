import os

import requests
import uuid
from time import time
from PIL import Image, UnidentifiedImageError
from io import BytesIO


def current_epoch_time_as_hex():
    epoch_time = str("%.18f" % time())
    split = epoch_time.split(".")
    hex1 = hex(int(split[0]))[2:]
    hex2 = hex(int(split[1]))[2:]
    return f"{hex1}+{hex2}"


class BBAEAPI:
    def __init__(self, user, password, filename="BBAE_CREDENTIALS.txt", creds_path="./creds/"):
        self.user = user
        self.password = password
        self.filename = filename
        self.creds_path = creds_path
        self.cookies = self._load_cookies()
        print(f"BBAEAPI Initialized for {self.user}")

    def _save_cookies(self, cookies):
        filename = self.filename
        filename = os.path.join(self.creds_path, filename)
        print(f"Saving cookies to {filename}")
        if not os.path.exists(self.creds_path):
            os.makedirs(self.creds_path)
        with open(filename, 'w') as file:
            for key, value in cookies.items():
                file.write(f"{key}={value}\n")
        print("Cookies saved successfully.")

    def _load_cookies(self):
        cookies = {}
        filename = self.filename
        filename = os.path.join(self.creds_path, filename)
        if not os.path.exists(self.creds_path):
            os.makedirs(self.creds_path)
        if os.path.exists(filename):
            print(f"Loading cookies from {filename}")
            with open(filename, 'r') as file:
                for line in file:
                    key, value = line.strip().split('=')
                    cookies[key] = value
            print("Cookies loaded successfully.")
        else:
            print(f"No cookies found at {filename}, starting fresh.")
        return cookies

    def make_initial_request(self):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/system/inform?guest=1&_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; sdk_gphone64_x86_64 Build/SE1A.211212.001.B1)',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        print(f"Making initial request to {url}")
        response = requests.get(url, headers=headers)
        self.cookies.update(response.cookies.get_dict())
        self._save_cookies(self.cookies)
        print(f"Initial request complete with status code {response.status_code}")
        return response.json()

    def generate_login_ticket_email(self, sms_code=None):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/multipleFactors/authentication/generateLoginTicket?guest=1&_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; sdk_gphone64_x86_64 Build/SE1A.211212.001.B1)',
            'Content-Type': 'application/json; charset=UTF-8',
            'Cookie': "; ".join([f"{key}={value}" for key, value in self.cookies.items()])
        }
        data = {
            "password": self.password,
            "type": "EMAIL",
            "userName": self.user,
        }
        if sms_code is not None:
            data.update({"smsInputText": sms_code})
        print(f"Requesting SMS login ticket for {self.user}")
        response = requests.post(url, headers=headers, json=data)
        print(f"Response from login ticket request: {response.json()}")
        return response.json()

    def generate_login_ticket_sms(self, sms_code=None):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/multipleFactors/authentication/generateLoginTicket?guest=1&_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; sdk_gphone64_x86_64 Build/SE1A.211212.001.B1)',
            'Content-Type': 'application/json; charset=UTF-8',
            'Cookie': "; ".join([f"{key}={value}" for key, value in self.cookies.items()])
        }
        data = {
            "password": self.password,
            "type": "MOBILE",
            "userName": self.user,
            "areaCodeId": "5"
        }
        if sms_code is not None:
            data.update({"smsInputText": sms_code})
        print(f"Requesting SMS login ticket for {self.user}")
        response = requests.post(url, headers=headers, json=data)
        print(f"Response from login ticket request: {response.json()}")
        return response.json()

    def request_captcha(self):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/security/captcha?_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; sdk_gphone64_x86_64 Build/SE1A.211212.001.B1)',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        print("Requesting captcha image...")
        response = requests.get(url, headers=headers, cookies=self.cookies)
        if response.status_code == 200 and 'image' in response.headers['Content-Type']:
            try:
                image = Image.open(BytesIO(response.content))
                return image
            except UnidentifiedImageError as e:
                print(f"Error opening CAPTCHA image: {e}")
        print(f"Failed to get captcha: {response.status_code}")
        return None

    def request_email_code(self, captcha_input=None):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/tools/nonLogin/sms?guest=1&_v=6.6.0&_s={hex_time}'
        headers = {
            'Content-Type': 'application/json',
            'Cookie': "; ".join([f"{key}={value}" for key, value in self.cookies.items()])
        }
        data = {
            "email": self.user,
            "type": "EMAIL",
            "updateType": "EMAIL",
            "verifyType": "LOGIN",
        }
        if captcha_input is not None:
            data.update({
                "captchaInputText": captcha_input,
            })
        print("Requesting SMS code...")
        response = requests.post(url, headers=headers, json=data)
        print(f"Response from SMS code request: {response.json()}")
        return response.json()

    def request_sms_code(self, captcha_input=None):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/tools/nonLogin/sms?guest=1&_v=6.6.0&_s={hex_time}'
        headers = {
            'Content-Type': 'application/json',
            'Cookie': "; ".join([f"{key}={value}" for key, value in self.cookies.items()])
        }
        data = {
            "mobile": self.user,
            "type": "MOBILE",
            "updateType": "MOBILE",
            "verifyType": "LOGIN",
            "areaCodeId": "5"
        }
        if captcha_input is not None:
            data.update({
                "captchaInputText": captcha_input,
            })
        print("Requesting SMS code...")
        response = requests.post(url, headers=headers, json=data)
        print(f"Response from SMS code request: {response.json()}")
        return response.json()

    def login_with_ticket(self, ticket):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/security/login?guest=1&_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; sdk_gphone64_x86_64 Build/SE1A.211212.001.B1)',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': "; ".join([f"{key}={value}" for key, value in self.cookies.items()])
        }
        data = {
            'ticket': ticket
        }
        print(f"Logging in with ticket for {self.user}")
        response = requests.post(url, headers=headers, data=data)
        self.cookies.update(response.cookies.get_dict())
        self._save_cookies(self.cookies)
        print(f"Login response: {response.json()}")
        return response.json()

    def get_account_assets(self):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/account/assetByUser?_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; sdk_gphone64_x86_64 Build/SE1A.211212.001.B1)',
            'Tz': '-360',
            'Tzname': 'America/Chicago',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        print(f"Fetching account assets for {self.user}")
        response = requests.get(url, headers=headers, cookies=self.cookies)
        print(f"Account assets response: {response.json()}")
        return response.json()

    def get_account_holdings(self):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/trade/positions?paged=false&skip=0&take=400&version=1&spac=false&_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; sdk_gphone64_x86_64 Build/SE1A.211212.001.B1)',
            'Tz': '-360',
            'Tzname': 'America/Chicago',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        print(f"Fetching account holdings for {self.user}")
        response = requests.get(url, headers=headers, cookies=self.cookies)
        print(f"Account holdings response: {response.json()}")
        return response.json()

    def get_account_info(self):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/account/info?_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; sdk_gphone64_x86_64 Build/SE1A.211212.001.B1)',
            'Tz': '-360',
            'Tzname': 'America/Chicago',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        print(f"Fetching account info for {self.user}")
        response = requests.get(url, headers=headers, cookies=self.cookies)
        print(f"Account info response: {response.json()}")
        return response.json()

    def validate_buy(self, symbol, amount, order_side, account_number):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/us/trade/validateBuy?_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; sdk_gphone64_x86_64 Build/SE1A.211212.001.B1)',
            'Accept-Language': 'en',
            'Content-Type': 'application/json; charset=UTF-8',
        }
        data = {
            "allowExtHrsFill": False,
            "displayAmount": amount,
            "entrustAmount": amount,
            "fractions": False,
            "fractionsType": 0,
            "isCombinedOption": False,
            "isOption": False,
            "orderSide": order_side,
            "orderSource": 0,
            "orderTimeInForce": "DAY",
            "symbol": symbol,
            "tradeNativeType": 0,
            "type": "MARKET",
            "usAccountId": account_number
        }
        print(f"Validating buy for {amount} shares of {symbol}")
        response = requests.post(url, headers=headers, json=data, cookies=self.cookies)
        print(f"Validation response: {response.json()}")
        return response.json()

    def execute_buy(self, symbol, amount, account_number, dry_run=True):
        # Determine the order side (1 for buy, 0 for sell)
        order_side = 1

        # Validate the buy order
        validation_response = self.validate_buy(symbol, amount, order_side, account_number)

        if validation_response['Outcome'] != 'Success':
            print("Buy validation failed.")
            return validation_response

        if dry_run:
            # For a dry run, just print the simulated order details
            total_cost = validation_response['Data']['totalWithCommission']
            entrust_amount = validation_response['Data']['entrustAmount']
            print(f"Simulated buy: {entrust_amount} shares of {symbol} for a total of ${total_cost}")
            return validation_response

        # Proceed to actual buy if not a dry run
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/trade/buy?_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; sdk_gphone64_x86_64 Build/SE1A.211212.001.B1)',
            'Accept-Language': 'en',
            'Content-Type': 'application/json; charset=UTF-8',
        }
        data = {
            "allowExtHrsFill": validation_response['Data']['allowExtHrsFill'],
            "displayAmount": validation_response['Data']['displayAmount'],
            "entrustAmount": validation_response['Data']['entrustAmount'],
            "entrustPrice": validation_response['Data']['entrustPrice'],
            "fractions": validation_response['Data']['fractions'],
            "fractionsType": validation_response['Data']['fractionsType'],
            "idempotentId": str(uuid.uuid4()),  # Generates a unique ID for idempotency
            "isCombinedOption": False,
            "isOption": False,
            "orderSide": order_side,
            "orderSource": 0,
            "orderTimeInForce": validation_response['Data']['orderTimeInForce'],
            "symbol": symbol,
            "tradeNativeType": 0,
            "type": validation_response['Data']['type'],
            "usAccountId": account_number
        }
        print(f"Executing buy for {amount} shares of {symbol} at ${data['entrustPrice']}")
        response = requests.post(url, headers=headers, json=data, cookies=self.cookies)
        print(f"Buy response: {response.json()}")
        return response.json()
