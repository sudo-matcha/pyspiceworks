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
    **A minimal python wrapper for the internal Spiceworks Cloud IT Help Desk API**

    Default geckodriver path is `/snap/bin/geckodriver/`. If yours is different, pass it as a `kwarg`.
    Pass `manual=True` to initialize and login and everythnig yourself.
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
        
        if not kwargs.get("maunal", False):
            self.init_driver(geckodriver=self.geckodriver_path, spiceworks_email=self.SPICEWORKS_EMAIL, spiceworks_password=self.SPICEWORKS_PASSWORD)
            self.login()

    def init_driver(self, **kwargs) -> None:
        '''
        Initializes the webdriver (used for getting access tokens and whatnot) (this is necessary !!)
        '''
        print("\x1b[2m[INFO] \x1b[0;1;35mInitializing Webdriver...\x1b[0m")
        driver_service = FirefoxService(executable_path=self.geckodriver_path)
        ff_options = FirefoxOptions()
        if kwargs.get("headless", True):
            ff_options.add_argument("--headless")
        self.driver = webdriver.Firefox(service=driver_service, options=ff_options)

    def login(self) -> bool:
        print("\x1b[2m[INFO] \x1b[0;1;34mLogging In...\x1b[0m")
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
    
    def get_ticket_req_headers(self) -> str | None:
        wait = WebDriverWait(self.driver, 10)

        print("\x1b[2m[INFO] \x1b[0;1;34mGetting headers...\x1b[0m")
        wait.until(
            EC.url_matches(r"https\:\/\/on\.spiceworks\.com\/tickets\/.+")
        )
        self.driver.refresh()
        request = self.driver.wait_for_request("/api/main/tickets")
        self.CSRF_token = request.headers.get("X-CSRF-TOKEN")
        self.tickets_headers = request.headers
        return request.headers

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
        self.get_ticket_req_headers()
        try:
            resp = requests.get(url=url, cookies=cookies, headers=self.tickets_headers)
        except Exception as e:
            print(e)
            return False
        
        tickets = resp.json()
        return tickets