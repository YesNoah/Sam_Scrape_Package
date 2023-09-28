from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import shutil
import zipfile
import os
import time
from selenium.webdriver.common.keys import Keys
import urllib.parse

class GrantScraper:
    def __init__(self, keywords, progress_callback=None):
        self.keywords = keywords
        self.url = self.construct_url()
        self.progress_callback = progress_callback  # Add a callback to update progress
    def update_progress(self, value, max_value, stage):
        if self.progress_callback:
            self.progress_callback(value, max_value, stage)

    def construct_url(self):
        keyword_segments = "".join(
            [f'&sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B{i}%5D%5Bkey%5D={urllib.parse.quote(keyword)}'
             f'&sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B{i}%5D%5Bvalue%5D={urllib.parse.quote(keyword)}'
             for i, keyword in enumerate(self.keywords)]
        )
        url = (
            f'https://sam.gov/search/?index=opp&sort=-relevance&page=1&pageSize=25'
            f'&sfm%5BsimpleSearch%5D%5BkeywordRadio%5D=ANY'
            f'{keyword_segments}'
            f'&sfm%5BsimpleSearch%5D%5BkeywordEditorTextarea%5D='
            f'&sfm%5Bstatus%5D%5Bis_active%5D=true&sfm%5Bstatus%5D%5Bis_inactive%5D=false'
            f'&sfm%5BtypeOfNotice%5D%5B0%5D%5Bkey%5D=p&sfm%5BtypeOfNotice%5D%5B0%5D%5Bvalue%5D=Presolicitation'
            f'&sfm%5BtypeOfNotice%5D%5B1%5D%5Bkey%5D=o&sfm%5BtypeOfNotice%5D%5B1%5D%5Bvalue%5D=Solicitation'
            f'&sfm%5BtypeOfNotice%5D%5B2%5D%5Bkey%5D=s&sfm%5BtypeOfNotice%5D%5B2%5D%5Bvalue%5D=Special%20Notice'
            f'&sfm%5BtypeOfNotice%5D%5B3%5D%5Bkey%5D=r&sfm%5BtypeOfNotice%5D%5B3%5D%5Bvalue%5D=Sources%20Sought'
            f'&sfm%5BtypeOfNotice%5D%5B4%5D%5Bkey%5D=k&sfm%5BtypeOfNotice%5D%5B4%5D%5Bvalue%5D=Combined%20Synopsis%2FSolicitation'
        )
        return url


    def __enter__(self):
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def starting_point(self):
        self.driver.get(self.url)
        self.driver.find_element_by_xpath("//button[text()='OK']").click()
        time.sleep(2)
        select = Select(self.driver.find_element_by_id("options"))
        time.sleep(1)
        select.select_by_value("3: -relevance")
        time.sleep(5)
        elem = self.driver.find_element(By.TAG_NAME, "html")
        elem.send_keys(Keys.END)
        time.sleep(2)
        select2 = Select(self.driver.find_element_by_id("bottomPagination-select"))
        time.sleep(1)
        select2.select_by_value("2: 100")

    def extract_links_on_page(self):
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all('a', class_='usa-link', href=lambda x: x and x.startswith('/opp/'))
        base_url = "https://sam.gov"
        full_links = [urljoin(base_url, link["href"]) for link in links]
        return full_links

    def turn_page(self, page_to_turn_to):
        max_retries = 3  # Set a maximum number of retries
        retries = 0

        while retries < max_retries:
            self.driver.find_element(By.ID, "bottomPagination-currentPage").click()
            self.driver.find_element(By.ID, "bottomPagination-currentPage").send_keys(Keys.DELETE)        
            self.driver.find_element(By.ID, "bottomPagination-currentPage").send_keys(f"\b\b{page_to_turn_to}")
            time.sleep(2)  # Give it some time to load the new page

            # Verify if the page has loaded as expected
            if self.is_page_loaded(page_to_turn_to):
                break  # Break out of the loop if the page has loaded as expected

            # If the page hasn't loaded as expected, retry the starting_point and turn_page methods
            retries += 1
            self.starting_point()
            time.sleep(2)  # Give it some time to load the starting point

        if retries >= max_retries:
            raise Exception(f"Failed to load page {page_to_turn_to} after {max_retries} retries.")

    def is_page_loaded(self, expected_page_number):
        # Verify the page number or check for some element on the page to ensure it has loaded as expected
        current_page_number = self.driver.find_element(By.ID, "bottomPagination-currentPage").get_attribute("value")
        return str(expected_page_number) == current_page_number



    def follow_links_extract_attachments(self, full_links, total_links):
        
        for i, link in enumerate(full_links):
            print(link)
            child_driver = webdriver.Chrome(ChromeDriverManager().install())
            child_driver.get(link)
            time.sleep(3)
            child_driver.find_element_by_xpath("//button[text()='OK']").click()
            time.sleep(3)

            try:
                child_driver.find_element_by_xpath('//*[@id="opp-public-sidenav-attachments-links"]').click()
                time.sleep(2)
                child_driver.find_element_by_xpath('//*[@id="attachments-links"]/div[2]/span[2]/a/span[2]').click()
                time.sleep(1)
                zip_url = child_driver.find_element_by_xpath('//*[@id="attachments-links"]/div[3]/a').get_attribute("href")

                # Extract the opportunity ID from the link
                opp_id = link.replace("https://sam.gov", "").replace("/", "_").strip("_")
                # Create directories
                dir_name = "data2"
                sorted_dir_name = f"data2_sorted_by_opp/{opp_id}"
                os.makedirs(dir_name, exist_ok=True)
                os.makedirs(sorted_dir_name, exist_ok=True)
                
                # Download and save zip file to both directories
                file_path = os.path.join(dir_name, "attachments.zip")
                sorted_file_path = os.path.join(sorted_dir_name, "attachments.zip")
                response = requests.get(zip_url, stream=True)
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(response.raw, f)
                shutil.copy(file_path, sorted_file_path)

                # Extract zip file to both directories
                with zipfile.ZipFile(file_path, "r") as z:
                    z.extractall(dir_name)
                    z.extractall(sorted_dir_name)
            except Exception as e:
                print(e)
                print("No attachments found for this grant.")
            self.update_progress(i + 1, total_links, 'downloading')  # Update progress after each opportunity
            child_driver.quit()
            

    def main(self, pages=5):
        self.starting_point()
        full_links_by_page = []
        pages_ = pages + 1
        total_links = 0
        for i in range(pages_):
            full_links = self.extract_links_on_page()
            full_links_by_page.append(full_links)
            total_links += len(full_links)  # Update total links count
            time.sleep(2)
            page_to_turn_to = i  # Increment by 2 as the first page is already loaded
            if i > 1: self.turn_page(page_to_turn_to)
            time.sleep(2)
            self.update_progress(i + 1, pages, 'retrieving')  # Update progress after each page

        processed_links = 0
        for full_links in full_links_by_page:
            self.follow_links_extract_attachments(full_links, total_links)
            processed_links += len(full_links)
            self.update_progress(processed_links, total_links, 'downloading')  # Update progress after each opportunity

        print("Done!")