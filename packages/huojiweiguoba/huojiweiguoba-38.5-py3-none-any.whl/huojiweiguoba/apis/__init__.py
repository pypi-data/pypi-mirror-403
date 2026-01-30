import requests
from requests.utils import add_dict_to_cookiejar
from fake_useragent import UserAgent

class Api:
    def __init__(self):
        self.ask = requests.sessions.Session()
        self.user_agent = UserAgent().random

    def update_cookies(self, cookies: [dict, list]):
        if isinstance(cookies, dict):
            add_dict_to_cookiejar(self.ask.cookies, cookies)
        elif isinstance(cookies, list):
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            add_dict_to_cookiejar(self.ask.cookies, cookies_dict)