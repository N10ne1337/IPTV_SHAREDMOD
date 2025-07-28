# Имя файла: update_playlist.py
# ВЕРСИЯ 5.1 - ЖЕЛЕЗОБЕТОННАЯ СТАТИСТИКОЙ

import requests
import re

# --- НАСТРОЙКИ ---
UPSTREAM_URL = "https://raw.githubusercontent.com/IPTVSHARED/iptv/main/IPTV_SHARED.m3u"
LOCAL_FILE = "IPTV_SHARED.m3u"
# --- КОНЕЦ НАСТРОЕК ---


def parse_playlist_content_bulletproof(content):
    channels = {}
    lines = content.splitlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('#EXTINF'):
            # Пытаемся извлечь имя канала
            name_match = re.search(r'tvg-name="(.*?)"', line)
            id_match = re.search(r'tvg-id="(.*?)"', line)
            raw_name = name_match.group(1) if name_match else None
            channel_id = id_match.group(1) if id_match else None

            # Если ничего не найдено — берем из самой строки EXTINF
            if not raw_name:
                raw_name_match = re.search(r'#EXTINF:-?\d+,(.*)', line)
                raw_name = raw_name_match.group(1).strip() if raw_name_match else None

            if not raw_name:
                continue  # Совсем без имени — пропускаем

            # Формируем уникальный ключ: предпочтение id > name
            unique_key = channel_id if channel_id else raw_name

            # Ищем ссылку
            for j in range(i + 1, min(i + 6, len(lines))):
                next_line = lines[j].strip()
                if next_line.startswith('http'):
                    full_channel_block = f"{line}\n{next_line}"
                    channels[unique_key] = full_channel_block
                    break

    return channels


def main():
    print(">>> Запуск обновления (v5.1 - Железобетонная версия с точной статистикой)...")

    # 1. Скачиваем оригинал
    try:
        print(f"[*] Скачиваю плейлист из: {UPSTREAM_URL}")
        response = requests.get(UPSTREAM_URL, timeout=60)
        response.raise_for_status()

        upstream_content = response.text
        upstream_channels = parse_playlist_content_bulletproof(upstream_content)

        upstream_count = len(upstream_channels)
        print(f"[+] УСПЕХ! Найдено {upstream_count} каналов в оригинальном плейлисте.")

        if upstream_count < 1000:
            print(f"[!] ВНИМАНИЕ: Маловато ({upstream_count}) каналов. Прерываю.")
            exit(1)

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
    final_playlist_content = upstream_content.strip()

    if custom_channels_to_add:
        final_playlist_content += "\n\n" + "\n".join(custom_channels_to_add)
        print(f"[+] Добавлено {len(custom_channels_to_add)} уникальных каналов.")
    else:
        print("[-] Уникальных каналов не найдено.")

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
