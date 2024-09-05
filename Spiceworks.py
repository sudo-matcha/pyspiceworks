import requests
import json
import os
import re
from seleniumwire import webdriver
from selenium.webdriver import FirefoxOptions, FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from relative_datetime import DateTimeUtils
from pybetterloader.Loader import Loader

class Spiceworks:
    '''
    **A minimal wrapper for the internal Spiceworks Cloud IT Help Desk**

    Default geckodriver path is `/snap/bin/geckodriver/`. If yours is different, pass it as a `kwarg`.
    '''
    def __init__(self, **kwargs):
        self.driver = None

        if kwargs.get("geckodriver", False):
            self.geckodriver_path = kwargs.get("geckodriver")
        else:
            self.geckodriver_path = "/snap/bin/geckodriver"

        if kwargs.get("spiceworks_email", False):
            self.SPICEWORKS_EMAIL = kwargs.get("spiceworks_email")
        else:
            self.SPICEWORKS_EMAIL = os.getenv("SPICEWORKS_EMAIL")

        if kwargs.get("spiceworks_password", False):
            self.SPICEWORKS_PASSWORD = kwargs.get("spiceworks_password")
        else:
            self.SPICEWORKS_PASSWORD = os.getenv("SPICEWORKS_PASSWORD")

    def init_driver(self, **kwargs) -> None:
        '''
        Initializes the webdriver (used for getting access tokens and whatnot) (this is necessary !!)
        '''
        driver_service = FirefoxService(executable_path=self.geckodriver_path)
        ff_options = FirefoxOptions()
        if kwargs.get("headless", True):
            ff_options.add_argument("--headless")
        self.driver = webdriver.Firefox(service=driver_service, options=ff_options)

    def login(self) -> bool:
        if not (bool(self.SPICEWORKS_EMAIL) & bool(self.SPICEWORKS_PASSWORD)):
            raise ValueError("\x1b[1;31mMissing SPICEWORKS_EMAIL and/or SPICEWORKS_PASSWORD.\nYou can pass them as arguments or set them as environment variables.\x1b[0m")
            return False
        try:
            self.driver.get("https://accounts.spiceworks.com/sign_in?policy=hosted_help_desk&success=https://on.spiceworks.com")
            self.driver.find_element(By.CLASS_NAME, "text").send_keys(self.SPICEWORKS_EMAIL)
            self.driver.find_element(By.CLASS_NAME, "password").send_keys(self.SPICEWORKS_PASSWORD)
            self.driver.find_element(By.CLASS_NAME, "submit-bttn").click()
        except Exception as e:
            print(e)
            return False
        return True

    def get_cookies(self):
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.url_matches(r"^https\:\/\/on\.spiceworks\.com\/tickets\/.+?$"))
        return self.driver.get_cookies()
    
    def get_tron_session(self) -> dict:
        cookies = self.get_cookies()
        for cookie in cookies:
            if cookie["name"] == "_tron_session":
                self.tron_session_cookie = cookie
                self.tron_session = cookie['value']
                break
        
        tron_expire_unix = self.tron_session_cookie['expiry']
        tron_expire_dt = datetime.utcfromtimestamp(tron_expire_unix)
        relstring = DateTimeUtils.relative_datetime(tron_expire_dt)[0]
        print(f"\x1b[2m[INFO] \x1b[0;1;35mGot _tron_session id!\x1b[0;1m This expires in \x1b[34m{relstring}.\x1b[0;1m Renew it before then!\x1b[0m")
        return self.tron_session
    
    def get_ticket_CSRF_token(self) -> str | None:
        wait = WebDriverWait(self.driver, 10)

        wait.until(
            EC.url_matches(r"https\:\/\/on\.spiceworks\.com\/tickets\/.+")
        )
        self.driver.refresh()
        print(self.driver.current_url)
        request = self.driver.wait_for_request("/api/main/tickets")
        self.CSRF_token = request.headers.get("X-CSRF-TOKEN")
        return request.headers.get("X-CSRF-TOKEN")

    def kill_driver(self):
        '''
        Kills the webdriver :(
        if you like having memory, make sure to kill the driver once youre done using it!
        '''
        self.driver.quit()
    
    def tickets(self, page: int = 1, limit: int = 50) -> dict | bool:
        '''
        Gets your tickets!

        Tip: Spicework's page numbers are 1-indexed
        '''

        url = f"https://on.spiceworks.com/api/main/tickets?page[number]={page}&page[size]={limit}"
        try:
            if self.tron_session:
                cookies = {
                    "_tron_session": self.tron_session
                }
            else:
                cookies = {}
        except AttributeError:
            cookies = {}
            
        headers = {
            "Host": "on.spiceworks.com",
            "Referer": f"https://on.spiceworks.com/tickets/open/{page}",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "DNT": "1"
        }
        if self.CSRF_token:
            headers.update({"X-CSRF-TOKEN": self.CSRF_token})

        try:
            resp = requests.get(url=url, cookies=cookies, headers=headers)
        except Exception as e:
            print(e)
            return False
        
        print(resp.text)
        print(resp.headers)
        tickets = resp.json()
        # tickets = {}
        return tickets