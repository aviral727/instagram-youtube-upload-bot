import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import yt_dlp
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from PIL import Image
import pickle
from datetime import datetime, timedelta

COOKIES_FILE = "instagram_cookies.pkl"


def load_cookies(driver, cookies_file="instagram_cookies.pkl"):
    if not os.path.exists(cookies_file):
        raise FileNotFoundError("⚠️ Instagram cookies not found. Run save_instagram_cookies.py first.")

    driver.get("https://www.instagram.com/")
    time.sleep(2)

    with open(cookies_file, "rb") as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)

    driver.get("https://www.instagram.com/")
    time.sleep(2)
    print("🍪 Cookies loaded.")

LOG_FILE = "upload_log.json"
UPLOAD_COOLDOWN_MINUTES = 30
USERNAME = "avirallivin"
INSTAGRAM_REELS_URL = f"https://www.instagram.com/{USERNAME}/reels/"
UPLOADED_LOG = "uploaded_reels.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

def update_video_metadata(youtube, video_id, title, description, location=None, location_description=None):
    body = {
        "id": video_id,
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    if location and location_description:
        body["recordingDetails"] = {
            "location": location,
            "locationDescription": location_description
        }

    print("📤 Sending update to YouTube API:")
    print(json.dumps(body, indent=2))

    request = youtube.videos().update(
        part="snippet,status,recordingDetails" if "recordingDetails" in body else "snippet,status",
        body=body
    )
    response = request.execute()

    print("✅ Update response:")
    print(json.dumps(response, indent=2))

    if "recordingDetails" in response and "location" in response["recordingDetails"]:
        print("📍 Location update successful!")
    else:
        print("⚠️ Location did not update.")

def load_uploaded():
    if os.path.exists(UPLOADED_LOG):
        with open(UPLOADED_LOG, "r") as f:
            return set(json.load(f))
    return set()

def save_uploaded(uploaded):
    with open(UPLOADED_LOG, "w") as f:
        json.dump(list(uploaded), f)

def get_youtube_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)

def scrape_reel_urls():
    print("🔎 Scraping reel URLs...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    load_cookies(driver)
    driver.get(INSTAGRAM_REELS_URL)
    time.sleep(5)

    last_height = driver.execute_script("return document.body.scrollHeight")
    reel_urls = set()

    while True:
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href and "/reel/" in href:
                reel_urls.add(href.split("?")[0])

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height or len(reel_urls) >= 10:
            break
        last_height = new_height

    driver.quit()
    return list(reel_urls)

def download_reel(reel_url):
    print(f"📅 Downloading: {reel_url}")
    ydl_opts = {
        'quiet': True,
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'writethumbnail': True,
        'writeinfojson': False,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'postprocessors': [
            {'key': 'EmbedThumbnail'},
            {'key': 'FFmpegMetadata'}
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(reel_url, download=True)
        filename = ydl.prepare_filename(info)
        title = info.get("title") or "Instagram Reel"
        description = info.get("description") or title
        thumbnail_path = None
        for ext in ['webp', 'jpg', 'png']:
            thumb = f"downloads/{info['id']}.{ext}"
            if os.path.exists(thumb):
                thumbnail_path = thumb
                break
        if thumbnail_path and thumbnail_path.endswith('.webp'):
            jpg_path = thumbnail_path.replace('.webp', '.jpg')
            try:
                im = Image.open(thumbnail_path).convert('RGB')
                im.save(jpg_path, 'JPEG')
                thumbnail_path = jpg_path
                print("🔁 Converted .webp to .jpg for YouTube compatibility.")
            except Exception as e:
                print(f"⚠️ Could not convert thumbnail: {e}")
        return filename, title, description, info.get("id"), thumbnail_path

def upload_to_youtube(youtube, file_path, title, description, thumbnail_path=None):
    print(f"🚀 Uploading to YouTube: {title}")
    request_body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['Instagram', 'Reels'],
            'categoryId': '22',
            'defaultLanguage': 'en',
        },
        'status': {
            'privacyStatus': 'public',
            'madeForKids': False,
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part='snippet,status',
        body=request_body,
        media_body=media
    )
    response = request.execute()
    print(f"✅ Uploaded: https://www.youtube.com/watch?v={response['id']}")

    if thumbnail_path:
        try:
            youtube.thumbnails().set(
                videoId=response['id'],
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("🖼️ Thumbnail uploaded.")
        except Exception as e:
            print(f"⚠️ Thumbnail upload failed: {e}")

    return response['id']

def load_upload_log():
    if not os.path.exists(LOG_FILE):
        return {"last_upload": None, "uploaded": []}
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def save_upload_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def can_upload_now(last_upload_time_str):
    if not last_upload_time_str:
        return True
    last_upload_time = datetime.strptime(last_upload_time_str, "%Y-%m-%d %H:%M:%S")
    return datetime.now() - last_upload_time >= timedelta(minutes=UPLOAD_COOLDOWN_MINUTES)

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def login_instagram(driver, username, password):
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)

    username_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")

    username_input.send_keys(username)
    password_input.send_keys(password)
    password_input.submit()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//nav"))
    )
    print("🔐 Logged in to Instagram.")

def main():
    os.makedirs("downloads", exist_ok=True)
    uploaded = load_uploaded()
    youtube = get_youtube_service()
    reels = scrape_reel_urls()

    for url in reels:
        try:
            reel_id = url.strip("/").split("/")[-1]
            if reel_id in uploaded:
                print(f"⏭️ Already processed: {reel_id}")
                continue

            upload_log = load_upload_log()
            if not can_upload_now(upload_log.get("last_upload")):
                print("⏳ Waiting for cooldown. Skipping this upload cycle.")
                break

            video_path, _, _, reel_id, thumb = download_reel(url)
            title = "Do subscribe while you are here! :) #explore #comedy #funny #reels #bihar"
            desc = "Have a nice day :)"

            video_id = upload_to_youtube(youtube, video_path, title, desc, thumbnail_path=thumb)
            update_video_metadata(youtube, video_id, title, desc)

            uploaded.add(reel_id)
            save_uploaded(uploaded)

            upload_log["last_upload"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            upload_log["uploaded"].append(reel_id)
            save_upload_log(upload_log)

            print("⏱️ Waiting 35 minutes before next upload...")
            time.sleep(35 * 60)

        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
            continue

if __name__ == "__main__":
    main()

