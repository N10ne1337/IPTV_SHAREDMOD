# Имя файла: update_playlist.py
# ВЕРСИЯ 2.0 - УЛУЧШЕННАЯ И НАДЕЖНАЯ

import requests
import re

# --- НАСТРОЙКИ ---
UPSTREAM_URL = "https://raw.githubusercontent.com/IPTVSHARED/iptv/main/IPTV_SHARED.m3u"
LOCAL_FILE = "IPTV_SHARED.m3u"
# --- КОНЕЦ НАСТРОЕК ---

def get_channels_from_content(content):
    """
    НОВЫЙ, БОЛЕЕ НАДЕЖНЫЙ СПОСОБ чтения каналов.
    Читает файл построчно, чтобы избежать ошибок парсинга.
    """
    channels = {}
    lines = content.splitlines()
    
    current_extinf = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('#EXTINF'):
            current_extinf = line
        elif line.startswith('http') and current_extinf:
            # Пытаемся извлечь tvg-name из строки #EXTINF
            match = re.search(r'tvg-name="(.*?)"', current_extinf)
            if match:
                channel_name = match.group(1).strip()
                # Сохраняем полную информацию: строку #EXTINF и ссылку на следующей строке
                full_channel_block = f"{current_extinf}\n{line}"
                channels[channel_name] = full_channel_block
            # Сбрасываем, чтобы искать следующую пару
            current_extinf = None
            
    return channels

def main():
    print(">>> Начинаю процесс обновления плейлиста (v2.0 - Надежный режим)...")

    # 1. Скачиваем актуальный плейлист из оригинального репозитория
    try:
        print(f"[*] Скачиваю оригинальный плейлист из: {UPSTREAM_URL}")
        response = requests.get(UPSTREAM_URL, timeout=30)
        response.raise_for_status()
        upstream_content = response.text
        upstream_channels = get_channels_from_content(upstream_content)
        print(f"[+] Найдено {len(upstream_channels)} каналов в оригинальном плейлисте. (Корректный подсчет)")
        if len(upstream_channels) < 500: # Проверка на адекватность
            print("[!] Внимание: из оригинала загружено подозрительно мало каналов. Прерываю, чтобы не сломать ваш плейлист.")
            exit(1)
    except requests.exceptions.RequestException as e:
        print(f"[!] Ошибка при скачивании оригинального плейлиста: {e}")
        exit(1)

    # 2. Читаем ваш локальный плейлист
    try:
        print(f"[*] Читаю ваш локальный файл: {LOCAL_FILE}")
        with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
            local_content = f.read()
        local_channels = get_channels_from_content(local_content)
        print(f"[+] Найдено {len(local_channels)} каналов в вашем текущем плейлисте.")
    except FileNotFoundError:
        print(f"[!] Локальный файл {LOCAL_FILE} не найден. Пропускаем этот шаг.")
        local_channels = {}

    # 3. Находим ваши уникальные каналы
    custom_channels_to_add = []
    print("[*] Сравниваю плейлисты и ищу ваши уникальные каналы...")
    for name, info in local_channels.items():
        if name not in upstream_channels:
            print(f"    -> Найден ваш уникальный канал: '{name}'. Он будет сохранен.")
            custom_channels_to_add.append(info)

    # 4. Формируем новый плейлист
    print("[*] Формирую новый объединенный плейлист...")
    
    # Берем весь оригинальный контент как есть, чтобы сохранить его структуру
    final_playlist_content = upstream_content.strip()

    # Если нашли уникальные каналы, добавляем их в конец
    if custom_channels_to_add:
        print(f"[+] Добавляю {len(custom_channels_to_add)} ваших уникальных каналов в конец плейлиста.")
        # Добавляем пустую строку для разделения
        final_playlist_content += "\n\n"
        final_playlist_content += "\n".join(custom_channels_to_add)

    # 5. Записываем результат в ваш файл
    try:
        with open(LOCAL_FILE, 'w', encoding='utf-8') as f:
            f.write(final_playlist_content)
        print(f"[✓] Готово! Объединенный плейлист успешно сохранен в файл {LOCAL_FILE}.")
    except Exception as e:
        print(f"[!] Не удалось записать файл: {e}")
        exit(1)

if __name__ == "__main__":
    main()
