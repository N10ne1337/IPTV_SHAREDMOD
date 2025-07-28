# Имя файла: update_playlist.py
# ВЕРСИЯ 3.0 - ФИНАЛЬНАЯ, БРОНЕБОЙНАЯ

import requests
import re

# --- НАСТРОЙКИ ---
# ИСПРАВЛЕННЫЙ URL, ведущий на ПРАВИЛЬНЫЙ файл в оригинальном репозитории
UPSTREAM_URL = "https://raw.githubusercontent.com/IPTVSHARED/iptv/main/IPTV_SHARED.m3u"
# Имя вашего файла в вашем репозитории
LOCAL_FILE = "IPTV_SHARED.m3u"
# --- КОНЕЦ НАСТРОЕК ---


def parse_playlist_content(content):
    """
    "Бронебойный" парсер. Читает файл построчно, не делая предположений о структуре.
    1. Находит строку #EXTINF.
    2. Находит СЛЕДУЮЩУЮ за ней строку со ссылкой.
    3. Соединяет их в один блок.
    Это самый надежный способ, который не сломается от пустых строк или нестандартного форматирования.
    """
    channels = {}
    lines = content.splitlines()
    
    for i, line in enumerate(lines):
        if line.strip().startswith('#EXTINF'):
            # Извлекаем название канала из строки #EXTINF
            match = re.search(r'tvg-name="(.*?)"', line)
            if not match:
                continue # Пропускаем, если у канала нет названия
            
            channel_name = match.group(1).strip()
            
            # Ищем ссылку на следующей непустой строке
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line.startswith('http'):
                    full_channel_block = f"{line.strip()}\n{next_line}"
                    channels[channel_name] = full_channel_block
                    
    return channels


def main():
    print(">>> Начинаю процесс обновления плейлиста (v3.0 - Бронебойный режим)...")

    # 1. Скачиваем актуальный плейлист из оригинального репозитория
    try:
        print(f"[*] Скачиваю оригинальный плейлист из ПРАВИЛЬНОГО URL: {UPSTREAM_URL}")
        response = requests.get(UPSTREAM_URL, timeout=60)
        # Проверяем, что сервер ответил "200 ОК", а не "404 Not Found" или другой ошибкой
        response.raise_for_status() 
        
        upstream_content = response.text
        upstream_channels = parse_playlist_content(upstream_content)
        
        channel_count = len(upstream_channels)
        print(f"[+] УСПЕХ! Найдено {channel_count} каналов в оригинальном плейлисте.")

        # Умный предохранитель
        if channel_count < 1000:
            print(f"[!] ВНИМАНИЕ: Загружено всего {channel_count} каналов. Это подозрительно мало.")
            print("[!] Чтобы не сломать ваш плейлист, я прерываю выполнение. Проблема может быть на стороне оригинального репозитория.")
            exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"[!!!] КРИТИЧЕСКАЯ ОШИБКА при скачивании плейлиста: {e}")
        print("[!] Выполнение прервано. Ваш локальный файл не был изменен.")
        exit(1)

    # 2. Читаем ваш локальный плейлист
    try:
        print(f"[*] Читаю ваш локальный файл: {LOCAL_FILE}")
        with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
            local_content = f.read()
        local_channels = parse_playlist_content(local_content)
        print(f"[+] Найдено {len(local_channels)} каналов в вашем текущем плейлисте.")
    except FileNotFoundError:
        print(f"[!] Ваш локальный файл {LOCAL_FILE} не найден. Будут добавлены только каналы из оригинала.")
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
    
    # Берем ВЕСЬ оригинальный контент как есть, чтобы сохранить его точную структуру и заголовок
    final_playlist_content = upstream_content.strip()

    if custom_channels_to_add:
        print(f"[+] Добавляю {len(custom_channels_to_add)} ваших уникальных каналов в конец плейлиста.")
        # Добавляем пустую строку для красивого разделения
        final_playlist_content += "\n\n"
        final_playlist_content += "\n".join(custom_channels_to_add)
    else:
        print("[-] Уникальных каналов для добавления не найдено.")

    # 5. Записываем результат в ваш файл
    try:
        with open(LOCAL_FILE, 'w', encoding='utf-8') as f:
            f.write(final_playlist_content)
        print(f"[✓] ГОТОВО! Плейлист успешно обновлен и сохранен в файл {LOCAL_FILE}.")
    except Exception as e:
        print(f"[!!!] Не удалось записать финальный файл: {e}")
        exit(1)

if __name__ == "__main__":
    main()
