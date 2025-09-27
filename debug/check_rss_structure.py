#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

def check_rss_structure(rss_num):
    """Проверяем структуру RSS года"""
    url = f"https://www.roboticsproceedings.org/rss{rss_num:02d}/index.html"
    print(f"\n=== RSS {rss_num:02d} ===")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем заголовок
        title = soup.find('title')
        if title:
            print(f"Заголовок: {title.get_text()}")
        
        # Ищем таблицу
        table = soup.find('table')
        if table:
            print("✓ Таблица найдена")
            rows = table.find_all('tr')
            print(f"Количество строк: {len(rows)}")
            
            # Показываем первые 3 строки
            for i, row in enumerate(rows[:3]):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    title_cell = cells[0]
                    title_link = title_cell.find('a')
                    if title_link:
                        print(f"  Строка {i+1}: {title_link.get_text()[:50]}...")
        else:
            print("✗ Таблица НЕ найдена")
            
            # Ищем другие элементы
            h2_tags = soup.find_all('h2')
            if h2_tags:
                print("Найдены заголовки H2:")
                for h2 in h2_tags:
                    print(f"  - {h2.get_text()}")
            
            # Ищем любые таблицы
            all_tables = soup.find_all('table')
            print(f"Всего таблиц на странице: {len(all_tables)}")
            
    except Exception as e:
        print(f"Ошибка: {e}")

# Проверяем несколько RSS годов
for rss_num in [20, 19, 18, 17, 16, 15]:
    check_rss_structure(rss_num)
