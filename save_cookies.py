# save_instagram_cookies.py
import os
import time
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

INSTAGRAM_URL = "https://www.instagram.com/"
COOKIES_FILE = "instagram_cookies.pkl"

def save_cookies():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1280,800")
    driver = webdriver.Chrome(options=chrome_options)
    
    print("🔐 Logging into Instagram... (complete the login manually if needed)")
    driver.get(INSTAGRAM_URL)

    # Let user log in manually (for 2FA)
    time.sleep(60)

    cookies = driver.get_cookies()
    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(cookies, f)
    print(f"✅ Cookies saved to {COOKIES_FILE}")
    
    driver.quit()

if __name__ == "__main__":
    save_cookies()
