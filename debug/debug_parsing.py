#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

def debug_parsing():
    """Детальная отладка парсинга"""
    url = "https://www.roboticsproceedings.org/rss20/index.html"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        print(f"Status: {response.status_code}")
        print(f"Encoding: {response.encoding}")
        print(f"Content length: {len(response.text)}")
        
        # Парсим как в основном скрипте
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"\nПоиск таблицы через soup.find('table'):")
        table = soup.find('table')
        if table:
            print("✓ Таблица найдена через find('table')")
        else:
            print("✗ Таблица НЕ найдена через find('table')")
        
        print(f"\nПоиск всех таблиц через soup.find_all('table'):")
        all_tables = soup.find_all('table')
        print(f"Найдено таблиц: {len(all_tables)}")
        
        if all_tables:
            for i, table in enumerate(all_tables):
                print(f"  Таблица {i+1}:")
                rows = table.find_all('tr')
                print(f"    Строк: {len(rows)}")
                if rows:
                    first_row = rows[0]
                    cells = first_row.find_all('td')
                    print(f"    Ячеек в первой строке: {len(cells)}")
        
        # Показываем начало HTML
        print(f"\nПервые 500 символов HTML:")
        print(response.text[:500])
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    debug_parsing()
