# Имя файла: update_playlist.py
# ВЕРСИЯ 5.2 - УЛУЧШЕННЫЙ ПАРСЕР M3U

import requests
import re

# --- НАСТРОЙКИ ---
UPSTREAM_URL = "https://raw.githubusercontent.com/IPTVSHARED/iptv/main/IPTV_SHARED.m3u"
LOCAL_FILE = "IPTV_SHARED.m3u"
# --- КОНЕЦ НАСТРОЕК ---


def parse_playlist_content_bulletproof(content):
    """Улучшенный парсер M3U плейлистов"""
    channels = {}
    lines = content.splitlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Ищем строку с #EXTINF
        if line.startswith('#EXTINF'):
            # Извлекаем информацию о канале
            name_match = re.search(r'tvg-name="([^"]*)"', line)
            id_match = re.search(r'tvg-id="([^"]*)"', line)
            
            raw_name = name_match.group(1) if name_match else None
            channel_id = id_match.group(1) if id_match else None
            
            # Если нет tvg-name, берем название после запятой
            if not raw_name:
                name_after_comma = re.search(r'#EXTINF:[^,]*,\s*(.+?)(?:\s*$)', line)
                if name_after_comma:
                    raw_name = name_after_comma.group(1).strip()
            
            # Если все еще нет имени, пропускаем
            if not raw_name:
                i += 1
                continue
            
            # Формируем уникальный ключ
            unique_key = channel_id if channel_id else raw_name
            
            # Собираем все строки до следующего #EXTINF или URL
            channel_info_lines = [line]
            j = i + 1
            url_found = False
            
            # Ищем URL, пропуская комментарии и пустые строки
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Если нашли следующий #EXTINF, останавливаемся
                if next_line.startswith('#EXTINF'):
                    break
                
                # Если нашли URL
                if next_line and (next_line.startswith('http') or next_line.startswith('udp://') or 
                                next_line.startswith('rtmp://') or next_line.startswith('rtsp://')):
                    channel_info_lines.append(next_line)
                    url_found = True
                    break
                
                # Добавляем другие #EXT теги (кроме пустых строк)
                elif next_line.startswith('#EXT') and next_line:
                    channel_info_lines.append(next_line)
                
                j += 1
            
            # Если нашли URL, сохраняем канал
            if url_found:
                full_channel_block = '\n'.join(channel_info_lines)
                channels[unique_key] = full_channel_block
            
            i = j  # Переходим к следующей позиции
        else:
            i += 1
    
    return channels


def main():
    print(">>> Запуск обновления (v5.2 - Улучшенный парсер для M3U)...")

    # 1. Скачиваем оригинал
    try:
        print(f"[*] Скачиваю плейлист из: {UPSTREAM_URL}")
        response = requests.get(UPSTREAM_URL, timeout=60)
        response.raise_for_status()

        upstream_content = response.text
        upstream_channels = parse_playlist_content_bulletproof(upstream_content)

        upstream_count = len(upstream_channels)
        print(f"[+] УСПЕХ! Найдено {upstream_count} каналов в оригинальном плейлисте.")

        if upstream_count < 100:  # Снизил порог для тестирования
            print(f"[!] ВНИМАНИЕ: Подозрительно мало ({upstream_count}) каналов.")
            # Для отладки покажем первые несколько каналов
            channel_names = list(upstream_channels.keys())[:10]
            print(f"[DEBUG] Первые найденные каналы: {channel_names}")
            
            # Не прерываем выполнение для отладки
            # exit(1)

    except requests.exceptions.RequestException as e:
        print(f"[!!!] Ошибка при скачивании: {e}")
        exit(1)

    # 2. Читаем локальный файл
    local_channels = {}
    try:
        print(f"[*] Читаю локальный файл: {LOCAL_FILE}")
        with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
            local_content = f.read()
        local_channels = parse_playlist_content_bulletproof(local_content)
        print(f"[+] Найдено {len(local_channels)} каналов в локальном плейлисте.")
    except FileNotFoundError:
        print("[-] Локальный файл не найден. Используем только оригинал.")

    # 3. Сохраняем уникальные каналы
    custom_channels_to_add = []
    print("[*] Ищу уникальные локальные каналы...")
    for name, info in local_channels.items():
        if name not in upstream_channels:
            print(f"    -> Добавляю канал: '{name}'")
            custom_channels_to_add.append(info)

    # 4. Объединяем
    print("[*] Формирую финальный плейлист...")
    
    # Сохраняем заголовок M3U
    final_content_lines = []
    
    # Добавляем заголовок если его нет
    if not upstream_content.strip().startswith('#EXTM3U'):
        final_content_lines.append('#EXTM3U')
    
    # Добавляем оригинальный контент
    final_content_lines.append(upstream_content.strip())
    
    # Добавляем уникальные каналы
    if custom_channels_to_add:
        final_content_lines.extend(custom_channels_to_add)
        print(f"[+] Добавлено {len(custom_channels_to_add)} уникальных каналов.")
    else:
        print("[-] Уникальных каналов не найдено.")

    final_playlist_content = '\n\n'.join(final_content_lines)

    # 5. Записываем результат
    try:
        with open(LOCAL_FILE, 'w', encoding='utf-8') as f:
            f.write(final_playlist_content)
        print(f"[✓] Финальный плейлист сохранён в '{LOCAL_FILE}'")
    except Exception as e:
        print(f"[!!!] Ошибка при записи: {e}")
        exit(1)

    # 6. Финальная статистика
    final_count = len(parse_playlist_content_bulletproof(final_playlist_content))
    print(f"[📊] Финальный отчёт:")
    print(f"      - Каналов в оригинале: {upstream_count}")
    print(f"      - Уникальных ваших: {len(custom_channels_to_add)}")
    print(f"      - Итоговое количество каналов: {final_count}")


if __name__ == "__main__":
    main()
