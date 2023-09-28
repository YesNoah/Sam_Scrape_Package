import tkinter as tk
from tkinter import StringVar, IntVar
import threading
from tkinter import ttk
from .grant_scraper import GrantScraper  # Importing GrantScraper from grant_scraper.py

class GrantScraperGUI(tk.Tk):
    def __init__(self, scraper_class):
        super().__init__()
        self.scraper_class = scraper_class
        self.title("Grant Scraper")
        self.geometry("400x300")  # Adjust the size to allow space for progress bars and labels

        self.keyword_entry_label = tk.Label(self, text="Enter keywords (comma separated):")
        self.keyword_entry_label.pack()

        self.keyword_entry = tk.Entry(self, width=50)
        self.keyword_entry.pack()

        self.page_entry_label = tk.Label(self, text="Enter number of pages:")
        self.page_entry_label.pack()

        self.page_entry = tk.Entry(self, width=10)
        self.page_entry.pack()

        self.run_button = tk.Button(self, text="Run", command=self.start_scraper_thread)
        self.run_button.pack()

        self.page_progress_label = tk.Label(self, text="")
        self.page_progress_label.pack()

        self.page_progress = ttk.Progressbar(self, orient="horizontal", length=200, mode="determinate")
        self.page_progress.pack()

        self.download_progress_label = tk.Label(self, text="")
        self.download_progress_label.pack()

        self.download_progress = ttk.Progressbar(self, orient="horizontal", length=200, mode="determinate")
        self.download_progress.pack()

    def update_progress(self, progress, total, stage):
        if stage == 'retrieving':
            self.page_progress['value'] = (progress / total) * 100
            self.page_progress_label['text'] = f'Page Retrieval Progress: {progress}/{total}'
        elif stage == 'downloading':
            self.download_progress['value'] = (progress / total) * 100
            self.download_progress_label['text'] = f'Download Progress: {progress}/{total}'
        self.update_idletasks()  # Update the GUI

    def start_scraper_thread(self):
        # Create a new thread to run the scraper
        scraper_thread = threading.Thread(target=self.run_scraper)
        scraper_thread.start()

    def run_scraper(self):
        keywords_str = self.keyword_entry.get()
        pages_str = self.page_entry.get()

        if not keywords_str or not pages_str.isdigit():
            print("Please enter valid keywords and number of pages.")
            return

        keywords = keywords_str.split(",")
        pages = int(pages_str)

        with self.scraper_class(keywords, progress_callback=self.update_progress) as scraper:  # Pass the progress callback
            scraper.main(pages=pages)

