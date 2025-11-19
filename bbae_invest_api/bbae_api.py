import os
import pickle
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
    def __init__(self, user, password, filename="BBAE_CREDENTIALS.pkl", creds_path="./creds/", debug=False):
        self.user = r"" + user
        self.password = r"" + password
        self.filename = filename
        self.creds_path = creds_path
        self.debug = debug
        self.cookies = self._load_cookies()
        self._debug_print(f"BBAEAPI Initialized for {self.user}")

    def _debug_print(self, text):
        if self.debug:
            print(text)

    def _save_cookies(self, cookies):
        filename = self.filename
        filepath = os.path.join(self.creds_path, filename)
        self._debug_print(f"Saving cookies to {filepath}")
        if not os.path.exists(self.creds_path):
            os.makedirs(self.creds_path)
        with open(filepath, 'wb') as file:
            pickle.dump(cookies, file)
        self._debug_print("Cookies saved successfully.")

    def _load_cookies(self):
        filename = self.filename
        filepath = os.path.join(self.creds_path, filename)
        cookies = {}
        if os.path.exists(filepath):
            self._debug_print(f"Loading cookies from {filepath}")
            try:
                with open(filepath, 'rb') as file:
                    cookies = pickle.load(file)
                self._debug_print("Cookies loaded successfully.")
            except (FileNotFoundError, EOFError, pickle.UnpicklingError) as e:
                self._debug_print(f"Error loading cookies: {e}")
        else:
            self._debug_print(f"No cookies found at {filepath}, starting fresh.")
        return cookies

    def make_initial_request(self):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/system/inform?guest=1&_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        self._debug_print(f"Making initial request to {url}")
        response = requests.get(url, headers=headers)
        self.cookies.update(response.cookies.get_dict())
        self._save_cookies(self.cookies)
        self._debug_print(f"Initial request complete with status code {response.status_code}")
        return response.json()

    def generate_login_ticket_email(self, sms_code=None):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/multipleFactors/authentication/generateLoginTicket?guest=1&_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
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
        self._debug_print(f"Requesting SMS login ticket for {self.user}")
        response = requests.post(url, headers=headers, json=data)
        self._debug_print(f"Response from login ticket request: {response.json()}")
        return response.json()

    def generate_login_ticket_sms(self, sms_code=None):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/multipleFactors/authentication/generateLoginTicket?guest=1&_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
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
        self._debug_print(f"Requesting SMS login ticket for {self.user}")
        response = requests.post(url, headers=headers, json=data)
        self._debug_print(f"Response from login ticket request: {response.json()}")
        return response.json()

    def request_captcha(self):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/security/captcha?_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        self._debug_print("Requesting captcha image...")
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
        self._debug_print("Requesting SMS code...")
        response = requests.post(url, headers=headers, json=data)
        self._debug_print(f"Response from SMS code request: {response.json()}")
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
        self._debug_print("Requesting SMS code...")
        response = requests.post(url, headers=headers, json=data)
        self._debug_print(f"Response from SMS code request: {response.json()}")
        return response.json()

    def login_with_ticket(self, ticket):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/security/login?guest=1&_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': "; ".join([f"{key}={value}" for key, value in self.cookies.items()])
        }
        data = {
            'ticket': ticket
        }
        self._debug_print(f"Logging in with ticket for {self.user}")
        response = requests.post(url, headers=headers, data=data)
        self.cookies.update(response.cookies.get_dict())
        self._save_cookies(self.cookies)
        self._debug_print(f"Login response: {response.json()}")
        return response.json()

    def get_account_assets(self):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/account/assetByUser?_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
            'Tz': '-360',
            'Tzname': 'America/Chicago',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        self._debug_print(f"Fetching account assets for {self.user}")
        response = requests.get(url, headers=headers, cookies=self.cookies)
        self._debug_print(f"Account assets response: {response.json()}")
        return response.json()

    def get_account_holdings(self):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/trade/positions?paged=false&skip=0&take=400&version=1&spac=false&_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
            'Tz': '-360',
            'Tzname': 'America/Chicago',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        self._debug_print(f"Fetching account holdings for {self.user}")
        response = requests.get(url, headers=headers, cookies=self.cookies)
        self._debug_print(f"Account holdings response: {response.json()}")
        return response.json()

    def get_account_info(self):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/account/info?_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
            'Tz': '-360',
            'Tzname': 'America/Chicago',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        self._debug_print(f"Fetching account info for {self.user}")
        response = requests.get(url, headers=headers, cookies=self.cookies)
        self._debug_print(f"Account info response: {response.json()}")
        return response.json()

    def get_simple_stock_info(self, symbol):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/market/getSimpleStockInfo?symbols={symbol}&_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
            'Tz': '-360',
            'Tzname': 'America/Chicago',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        self._debug_print(f"Fetching stock info for {symbol}")
        response = requests.get(url, headers=headers, cookies=self.cookies)
        self._debug_print(f"Stock info response: {response.json()}")
        return response.json()

    def validate_buy(self, symbol, amount, order_side, account_number, order_type="MARKET", entrust_price=None):
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/us/trade/validateBuy?_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
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
            "type": order_type,
            "usAccountId": account_number
        }
        # Add entrustPrice to the request if it's a LIMIT order and price is provided
        if order_type == "LIMIT" and entrust_price is not None:
            data["entrustPrice"] = entrust_price

        self._debug_print(f"Validating {order_type} buy for {amount} shares of {symbol}")
        response = requests.post(url, headers=headers, json=data, cookies=self.cookies)
        self._debug_print(f"Validation response: {response.json()}")
        return response.json()

    def execute_buy(self, symbol, amount, account_number, dry_run=True, validation_response=None):
        # Determine the order side (1 for buy, 0 for sell)
        order_side = 1

        # If no validation response is passed, this function is being called incorrectly by the new logic
        if validation_response is None:
            self._debug_print("execute_buy ERROR: validation_response is missing.")
            return {"Outcome": "Failed", "Message": "execute_buy called without validation_response."}
        
        if validation_response['Outcome'] != 'Success':
            print("Buy validation failed.")
            return validation_response
        
        # Get all data from the successful validation
        validation_data = validation_response['Data']
        order_type = validation_data['type']
        entrust_price = validation_data['entrustPrice']

        if dry_run:
            total_cost = validation_data['totalWithCommission']
            entrust_amount = validation_data['entrustAmount']
            self._debug_print(f"Simulated {order_type} buy: {entrust_amount} shares of {symbol} for a total of ${total_cost}")
            return validation_response

        # Proceed to actual buy if not a dry run
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/trade/buy?_v=6.6.0&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
            'Accept-Language': 'en',
            'Content-Type': 'application/json; charset=UTF-8',
        }
        data = {
            "allowExtHrsFill": validation_data['allowExtHrsFill'],
            "displayAmount": validation_data['displayAmount'],
            "entrustAmount": validation_data['entrustAmount'],
            "entrustPrice": entrust_price,
            "fractions": validation_data['fractions'],
            "fractionsType": validation_data['fractionsType'],
            "idempotentId": str(uuid.uuid4()),  # Generates a unique ID for idempotency
            "isCombinedOption": False,
            "isOption": False,
            "orderSide": order_side,
            "orderSource": 0,
            "orderTimeInForce": validation_data['orderTimeInForce'],
            "symbol": symbol,
            "tradeNativeType": 0,
            "type": order_type,
            "usAccountId": account_number
        }
        self._debug_print(f"Executing {order_type} buy for {amount} shares of {symbol} at ${data['entrustPrice']}")
        response = requests.post(url, headers=headers, json=data, cookies=self.cookies)
        self._debug_print(f"Buy response: {response.json()}")
        return response.json()

    def check_stock_holdings(self, symbol, account_number):
        """Check if the stock is currently held and return the available amount."""
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/trade/closeTradeAmount?_v=5.4.1&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json; charset=UTF-8',
        }
        data = {
            "fractions": False,
            "fractionsType": 0,
            "orderSide": 2,  # 2 for checking amount held before selling
            "symbol": symbol,
            "usAccountId": account_number
        }
        response = requests.post(url, headers=headers, json=data, cookies=self.cookies)
        return response.json()

    def validate_sell(self, symbol, amount, account_number):
        """Validate the sell order."""
        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/us/trade/validateSell?_v=5.4.1&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
            'Accept-Language': 'en',
            'Content-Type': 'application/json; charset=UTF-8',
        }
        data = {
            "allowExtHrsFill": False,
            "displayAmount": str(amount),
            "entrustAmount": str(amount),
            "fractions": False,
            "fractionsType": 0,
            "isCombinedOption": False,
            "isOption": False,
            "orderSide": 2,  # 2 for selling
            "orderSource": 0,
            "orderTimeInForce": "DAY",
            "symbol": symbol,
            "tradeNativeType": 0,
            "type": "MARKET",
            "usAccountId": account_number
        }
        response = requests.post(url, headers=headers, json=data, cookies=self.cookies)
        return response.json()

    def execute_sell(self, symbol, amount, account_number, entrust_price, dry_run=True):
        """Execute the sell order."""
        if dry_run:
            self._debug_print(f"Simulated sell: {amount} shares of {symbol}")
            return {"Outcome": "Success", "Message": "Dry Run Success"}

        hex_time = current_epoch_time_as_hex()
        url = f'https://api.bbaepro.com/api/v2/trade/sell?_v=5.4.1&_s={hex_time}'
        headers = {
            'User-Agent': 'BBAEPRO Dalvik/2.1.0 (Linux; U; Android 12; SM-S928U1 Build/SE1A.211212.001.B1)',
            'Accept-Language': 'en',
            'Content-Type': 'application/json; charset=UTF-8',
        }
        data = {
            "allowExtHrsFill": False,
            "displayAmount": str(amount),
            "entrustAmount": str(amount),
            "entrustPrice": entrust_price,
            "fractions": False,
            "fractionsType": 0,
            "idempotentId": str(uuid.uuid4()),
            "isCombinedOption": False,
            "isOption": False,
            "orderSide": 2,  # 2 for selling
            "orderSource": 0,
            "orderTimeInForce": "DAY",
            "symbol": symbol,
            "tradeNativeType": 0,
            "type": "MARKET",
            "usAccountId": account_number
        }
        response = requests.post(url, headers=headers, json=data, cookies=self.cookies)
        return response.json()
