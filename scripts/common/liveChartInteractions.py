from datetime import datetime
import json
from time import sleep
from scripts.config import config
from scripts.common.commonFunctions import CommonFunctions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By


class LiveChartInteractions:
    """Class for livechart.me interactions"""
    anime_url: str

    def __init__(self, anime_url: str):
        self.logger = config.logger
        self.anime_url = anime_url
        self.username = config.liveChartUsername
        self.password = config.liveChartPassword
        self.common_functions = CommonFunctions()
        options = Options()
        # options.add_argument("--headless")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.default_notes_json = {
                            "name": "",
                            "dir_name": "",
                            "english_name": "",
                            "current_season": "",
                            "current_episode": "",
                            "torrent_provider": ""
                        }
        self.notes_json = self.default_notes_json

    def getDayOfTheWeekFromUnix(self):
        countdown_bar = self.driver.find_elements(By.XPATH, "//div[@data-controller='countdown-bar']")[0]
        unix_timestamp = countdown_bar.get_attribute("data-countdown-bar-timestamp")
        # print(unix_timestamp)
        dt = datetime.fromtimestamp(int(unix_timestamp))
        day_of_week = dt.strftime("%u")

        return day_of_week

    def get_value(self, data_to_check, attribute):
        if data_to_check == "":
            anime_details = self.driver.find_elements(By.XPATH,"//div[@class='flex mx-auto my-4 px-4 w-full max-w-5xl gap-x-6']")[0]
            data_to_check = anime_details.get_attribute(attribute)
        return data_to_check


    def anime_login(self):
        self.driver.get(self.anime_url)

        self.common_functions.retryOnException(lambda: self.driver.find_elements(By.XPATH, "//p[text()='Do not consent']")[0].click(), delay=2)
        self.logger.debug("Clicked consent_b")

        # self.common_functions.retryOnException(lambda: self.driver.find_elements(By.XPATH, "//button[text()='Skip']")[0].click(), delay=2)
        # self.logger.debug("Clicked skip_b")

        login_b = self.driver.find_elements(By.XPATH, "//a[text()='Log in']")[1]
        login_b.click()

        email_i = self.driver.find_elements(By.ID, "user_email")[0]
        email_i.send_keys(self.username)

        password_i = self.driver.find_elements(By.ID, "user_password")[0]
        password_i.send_keys(self.password)

        login_i = self.driver.find_elements(By.XPATH, "//input[@type='submit']")[0]
        login_i.click()


    def get_notes(self, already_logged_in):
        if not already_logged_in:
            self.anime_login()

        self.common_functions.retryOnException(lambda: self.driver.find_elements(By.XPATH, "//button[@class='-mr-4 btn btn-circle btn-ghost']")[0].click(), delay=2)

        sleep(1)

        notes_t = self.driver.find_elements(By.ID, "library_editor_notes")[0]
        if notes_t.text != "":
            self.notes_json = json.loads(notes_t.text)
        else:
            self.notes_json = self.default_notes_json
            close_button = self.driver.find_elements(By.XPATH, "//button[@data-library-editor-target='closeButton']")
            close_button[0].click()
            sleep(1)
        name = self.notes_json["name"]
        dir_name = self.notes_json["dir_name"]
        english_name = self.notes_json["english_name"]
        current_season = self.notes_json["current_season"] if self.notes_json["current_season"] != "" else "1"
        current_episode = self.notes_json["current_episode"] if self.notes_json["current_episode"] != "" else "1"
        torrent_provider = self.notes_json["torrent_provider"] if self.notes_json["torrent_provider"] != "" else "SubsPlease"

        images = self.driver.find_elements(By.XPATH, "//img[@class='overflow-hidden rounded']")[0].get_attribute("srcset")
        images_split = images.split(",")
        if len(images_split) > 1:
            image = images_split[1].strip().split(" ")[0]
        else:
            image = images_split[0].split(" ")[0]

        try:
            download_day = self.getDayOfTheWeekFromUnix()
        except:
            download_day = ""

        name = self.get_value(name, "data-anime-details-romaji-title")
        dir_name = self.get_value(dir_name, "data-anime-details-romaji-title")
        english_name = self.get_value(english_name, "data-anime-details-english-title")
        if english_name is None:
            english_name = name

        # print(name, dir_name, english_name, current_season, current_episode, torrent_provider, image, download_day)

        if not already_logged_in:
            self.driver.quit()

        return name, dir_name, english_name, current_season, current_episode, torrent_provider, image, download_day

    def get_watching_anime(self):
        self.anime_login()

        article_list = self.driver.find_elements(By.XPATH, "//article[@data-library-status='watching']")
        original_window = self.driver.current_window_handle

        for article in article_list:
            anime_id = article.get_attribute("data-anime-id")

            self.driver.execute_script("window.open('about:blank', '_blank');")
            sleep(1)

            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(f"https://www.livechart.me/anime/{anime_id}")
            sleep(2)

            library_notes = self.get_notes(True)
            print(anime_id, library_notes)
            self.driver.close()
            self.driver.switch_to.window(original_window)

        self.driver.quit()