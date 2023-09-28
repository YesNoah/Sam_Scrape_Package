from gui import GrantScraperGUI
from grant_scraper import GrantScraper
if __name__ == "__main__":
    app = GrantScraperGUI(GrantScraper)
    app.mainloop()