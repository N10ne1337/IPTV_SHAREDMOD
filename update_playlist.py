# Имя файла: update_playlist.py
# ВЕРСИЯ 5.0 - ЖЕЛЕЗОБЕТОННАЯ

import requests
import re

# --- НАСТРОЙКИ ---
# ТОЧНЫЙ URL, КОТОРЫЙ ВЫ ДАЛИ. ГЛАВНОЕ ИСПРАВЛЕНИЕ.
UPSTREAM_URL = "https://raw.githubusercontent.com/IPTVSHARED/iptv/main/IPTV_SHARED.m3u"
# Имя вашего файла в репозитории
LOCAL_FILE = "IPTV_SHARED.m3u"
# --- КОНЕЦ НАСТРОЕК ---


def parse_playlist_content_bulletproof(content):
    """
    "Железобетонный" парсер v2.0.
    Логика:
    1. Находит строку #EXTINF.
    2. Начинает сканировать СЛЕДУЮЩИЕ за ней строки.
    3. Первую же строку, которая начинается с 'http', считает ссылкой для этого канала.
    4. Игнорирует все, что между ними (#EXTGRP, пустые строки и т.д.).
    """
    channels = {}
    lines = content.splitlines()
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('#EXTINF'):
            match = re.search(r'tvg-name="(.*?)"', line)
            if not match:
                continue # Пропускаем, если в #EXTINF нет названия
            
            channel_name = match.group(1).strip()
            
            # Ищем ссылку в следующих 5 строках. Этого более чем достаточно.
            for j in range(i + 1, min(i + 6, len(lines))):
                next_line = lines[j].strip()
                if next_line.startswith('http'):
                    # Собираем блок только из ДВУХ нужных строк.
                    full_channel_block = f"{line}\n{next_line}"
                    channels[channel_name] = full_channel_block
                    break # Нашли ссылку, выходим из внутреннего цикла и ищем следующую #EXTINF
                    
    return channels


def main():
    print(">>> Запуск обновления (v5.0 - Железобетонный режим)...")

    # 1. Скачиваем оригинал по ПРАВИЛЬНОМУ URL
    try:
        print(f"[*] Скачиваю плейлист из: {UPSTREAM_URL}")
        response = requests.get(UPSTREAM_URL, timeout=60)
        response.raise_for_status() 
        
        upstream_content = response.text
        upstream_channels = parse_playlist_content_bulletproof(upstream_content)
        
        channel_count = len(upstream_channels)
        print(f"[+] УСПЕХ! Найдено {channel_count} каналов в оригинальном плейлисте.")

        if channel_count < 1000:
            print(f"[!] ВНИМАНИЕ: Загружено всего {channel_count} каналов. Прерываю, чтобы ничего не сломать.")
            exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"[!!!] КРИТИЧЕСКАЯ ОШИБКА при скачивании: {e}")
        exit(1)

    # 2. Читаем ваш файл
    local_channels = {}
    try:
        print(f"[*] Читаю ваш локальный файл: {LOCAL_FILE}")
        with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
            local_content = f.read()
        local_channels = parse_playlist_content_bulletproof(local_content)
        print(f"[+] Найдено {len(local_channels)} каналов в вашем плейлисте.")
    except FileNotFoundError:
        print("[-] Локальный файл не найден. Будут добавлены только каналы из оригинала.")

    # 3. Ищем ваши уникальные каналы
    custom_channels_to_add = []
    print("[*] Ищу ваши уникальные каналы для сохранения...")
    for name, info in local_channels.items():
        if name not in upstream_channels:
            print(f"    -> Найден ваш канал: '{name}'. СОХРАНЯЮ.")
            custom_channels_to_add.append(info)

    # 4. Формируем финальный файл
    print("[*] Формирую финальный плейлист...")
    # Берем ВЕСЬ оригинальный контент как есть
    final_playlist_content = upstream_content.strip()

    if custom_channels_to_add:
        print(f"[+] Добавляю {len(custom_channels_to_add)} ваших каналов в конец файла.")
        # Добавляем пустую строку для разделения и затем ваши каналы
        final_playlist_content += "\n\n" + "\n".join(custom_channels_to_add)
    else:
        print("[-] Новых уникальных каналов в вашем файле не найдено.")

    # 5. Записываем результат
    try:
        with open(LOCAL_FILE, 'w', encoding='utf-8') as f:
            f.write(final_playlist_content)
        print(f"[✓] ГОТОВО! Плейлист сохранен в {LOCAL_FILE}.")
    except Exception as e:
        print(f"[!!!] Не удалось записать финальный файл: {e}")
        exit(1)

if __name__ == "__main__":
    main()
