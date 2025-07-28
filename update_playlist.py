import requests
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# --- НАСТРОЙКИ ---
SOURCE_URL = "https://gitlab.com/iptv135435/iptvshared/-/raw/main/IPTV_SHARED.m3u"
MY_PLAYLIST_FILE = "IPTV_SHARED.m3u"
SPECIAL_OPS_FILE = "channels_to_protect.json"
MAX_WORKERS = 10
URL_TIMEOUT = 10

# --- ЛОГИКА ---

def parse_simple_playlist(text):
    """Извлекает все URL из простого плейлиста."""
    return set(re.findall(r'^(http.*)$', text, re.MULTILINE))

def scrape_m3u8_from_site(page_url, identifier):
    """Запускает шпиона-невидимку для извлечения .m3u8 ссылки с сайта."""
    print(f"🕵️‍♂️ [ШПИОН] Внедряюсь на {page_url}...")
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        caps = DesiredCapabilities.CHROME
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}

        driver = webdriver.Chrome(options=chrome_options, desired_capabilities=caps)
        driver.get(page_url)
        time.sleep(15)  # Даем время плееру запуститься и запросить плейлист

        logs = driver.get_log('performance')
        driver.quit()

        for entry in logs:
            log = json.loads(entry['message'])['message']
            if 'Network.requestWillBeSent' in log['method']:
                url = log['params']['request']['url']
                if '.m3u8' in url and identifier in url:
                    print(f"  ✅ [ШПИОН] Секретные данные добыты: ...{url[-50:]}")
                    return url
        
        print(f"  ❌ [ШПИОН] Не удалось найти ссылку с идентификатором '{identifier}'.")
        return None
    except Exception as e:
        print(f"  🔥 [ШПИОН] Миссия провалена! Ошибка: {e}")
        return None

def check_url(url):
    """Проверяет URL на работоспособность."""
    if not url: return None
    try:
        response = requests.head(url, timeout=URL_TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            print(f"  👍 Ссылка жива: {url.split('/')[-1]}")
            return url
    except requests.RequestException:
        pass
    print(f"  👎 Ссылка мертва: {url.split('/')[-1]}")
    return None

def main():
    print("🚀 Запускаю протокол 'ТЕРМИНАТОР'!")
    
    # Шаг 1: Задание для шпионов
    final_urls = {}
    try:
        with open(SPECIAL_OPS_FILE, 'r', encoding='utf-8') as f:
            special_channels = json.load(f).get("special_channels", [])
        
        for channel in special_channels:
            url = scrape_m3u8_from_site(channel["page_url"], channel["stream_identifier"])
            if url:
                final_urls[channel["name"]] = url
    except FileNotFoundError:
        print("ℹ️ Досье на спецагентов не найдено. Пропускаю шпионскую миссию.")

    # Шаг 2: Сбор плейлиста из публичного источника
    source_urls = set()
    try:
        response = requests.get(SOURCE_URL, timeout=20)
        if response.status_code == 200:
            source_urls = parse_simple_playlist(response.text)
        print(f"📥 Загружен публичный плейлист. Найдено {len(source_urls)} кандидатов.")
    except Exception as e:
        print(f"⚠️ Не удалось скачать публичный плейлист: {e}")

    # Шаг 3: Тотальная проверка обычных ссылок
    print(f"🔥 Проверяю {len(source_urls)} ссылок из источника...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(check_url, url) for url in source_urls]
        for future in as_completed(futures):
            result_url = future.result()
            if result_url:
                name = result_url.split('/')[-1].split('.')[0] or "Канал"
                if name not in final_urls: # Не перезаписываем ссылки от шпионов
                    final_urls[name] = result_url
    
    # Шаг 4: Финальная сборка
    if not final_urls:
        print("🔴 Не найдено ни одного рабочего канала. Файл не будет изменен.")
        return

    print(f"\n📝 Собираю финальный плейлист из {len(final_urls)} каналов...")
    sorted_names = sorted(final_urls.keys())
    with open(MY_PLAYLIST_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for name in sorted_names:
            url = final_urls[name]
            f.write(f"#EXTINF:-1,{name}\n")
            f.write(f"{url}\n")
            
    print("✅ Протокол 'ТЕРМИНАТОР' выполнен успешно!")

if __name__ == "__main__":
    main()
