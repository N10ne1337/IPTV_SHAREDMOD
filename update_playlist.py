# Имя файла: update_playlist.py

import requests
import re
import os

# --- НАСТРОЙКИ ---
# URL оригинального плейлиста, откуда берем обновления
UPSTREAM_URL = "https://raw.githubusercontent.com/IPTVSHARED/iptv/main/.m3u"
# Имя вашего файла плейлиста в репозитории
LOCAL_FILE = "iptv.m3u"
# --- КОНЕЦ НАСТРОЕК ---

def get_channels_from_content(content):
    """
    Извлекает каналы из текста плейлиста.
    Каждый канал - это пара строк: #EXTINF и ссылка.
    Возвращает словарь, где ключ - название канала, а значение - полная информация о канале.
    """
    channels = {}
    # Ищем блоки, начинающиеся с #EXTINF, содержащие tvg-name, и заканчивающиеся ссылкой
    # Это регулярное выражение более устойчиво к разным форматам #EXTINF
    pattern = re.compile(r'(#EXTINF:-1.*?tvg-name="(.*?)".*?(\n|\r\n))(http.*?)(?=\n#EXTINF|\Z)', re.DOTALL)
    for match in pattern.finditer(content):
        extinf_line, channel_name, newline, url_line = match.groups()
        full_channel_block = f"{extinf_line.strip()}{newline}{url_line.strip()}"
        channels[channel_name.strip()] = full_channel_block
    return channels

def main():
    print(">>> Начинаю процесс обновления плейлиста...")

    # 1. Скачиваем актуальный плейлист из оригинального репозитория
    try:
        print(f"[*] Скачиваю оригинальный плейлист из: {UPSTREAM_URL}")
        response = requests.get(UPSTREAM_URL, timeout=30)
        response.raise_for_status()
        upstream_content = response.text
        upstream_channels = get_channels_from_content(upstream_content)
        print(f"[+] Найдено {len(upstream_channels)} каналов в оригинальном плейлисте.")
    except requests.exceptions.RequestException as e:
        print(f"[!] Ошибка при скачивании оригинального плейлиста: {e}")
        # Если не удалось скачать, прекращаем работу, чтобы не сломать ваш плейлист
        exit(1)

    # 2. Читаем ваш локальный плейлист, чтобы найти уникальные каналы
    try:
        print(f"[*] Читаю ваш локальный файл: {LOCAL_FILE}")
        with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
            local_content = f.read()
        local_channels = get_channels_from_content(local_content)
        print(f"[+] Найдено {len(local_channels)} каналов в вашем плейлисте.")
    except FileNotFoundError:
        print(f"[!] Локальный файл {LOCAL_FILE} не найден. Это первый запуск? Создаю его...")
        local_channels = {}

    # 3. Находим ваши уникальные каналы (те, что есть у вас, но нет в оригинале)
    custom_channels_to_add = []
    print("[*] Ищу уникальные каналы в вашем плейлисте...")
    for name, info in local_channels.items():
        if name not in upstream_channels:
            print(f"    -> Найден ваш уникальный канал: '{name}'. Он будет сохранен.")
            custom_channels_to_add.append(info)

    # 4. Формируем новый плейлист
    # Сначала берем заголовок (#EXTM3U) и все свежие каналы из скачанного оригинала
    final_playlist_parts = []
    # Добавляем заголовок из оригинала
    if upstream_content.startswith("#EXTM3U"):
        final_playlist_parts.append(upstream_content.splitlines()[0])

    # Добавляем все каналы из оригинала в том же порядке
    final_playlist_parts.extend(upstream_channels.values())

    # Если нашли уникальные каналы, добавляем их в конец
    if custom_channels_to_add:
        print(f"[+] Добавляю {len(custom_channels_to_add)} ваших уникальных каналов в конец плейлиста.")
        final_playlist_parts.extend(custom_channels_to_add)

    # Собираем всё в одну строку с переносами
    final_playlist_content = "\n".join(final_playlist_parts)

    # 5. Записываем результат в ваш файл iptv.m3u
    try:
        with open(LOCAL_FILE, 'w', encoding='utf-8') as f:
            f.write(final_playlist_content)
        print(f"[✓] Готово! Объединенный плейлист успешно сохранен в файл {LOCAL_FILE}.")
    except Exception as e:
        print(f"[!] Не удалось записать файл: {e}")
        exit(1)

if __name__ == "__main__":
    main()
