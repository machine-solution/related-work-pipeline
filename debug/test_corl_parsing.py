#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование парсинга одной статьи CoRL
"""

import requests
from bs4 import BeautifulSoup
import re

def test_corl_parsing():
    """Тестирование парсинга одной статьи CoRL"""
    
    # URL одной статьи для тестирования
    article_url = "https://proceedings.mlr.press/v155/huang21a.html"
    
    print(f"Тестирую парсинг: {article_url}")
    
    try:
        response = requests.get(article_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем заголовок статьи на странице
        title_elem = soup.find('title')
        page_title = ""
        if title_elem:
            page_title = title_elem.get_text().strip()
            print(f"Заголовок страницы: {page_title}")
        
        # Получаем весь текст
        text = soup.get_text()
        print(f"Длина текста: {len(text)} символов")
        
        # Ищем заголовок в тексте
        title_pos = text.find(page_title)
        print(f"Позиция заголовка: {title_pos}")
        
        if title_pos != -1:
            # Ищем "Proceedings of" после заголовка
            proceedings_pattern = r'Proceedings of the \d{4} Conference on Robot Learning'
            proceedings_match = re.search(proceedings_pattern, text[title_pos:])
            
            if proceedings_match:
                proceedings_pos = title_pos + proceedings_match.start()
                print(f"Позиция 'Proceedings of': {proceedings_pos}")
                
                # Берем текст между заголовком и Proceedings
                authors_section = text[title_pos + len(page_title):proceedings_pos].strip()
                print(f"Секция авторов (сырая): '{authors_section}'")
                
                # Очищаем от лишних символов
                authors_clean = re.sub(r'[^\w\s,\.]', '', authors_section).strip()
                authors_clean = re.sub(r'\s+', ' ', authors_clean).strip()
                print(f"Секция авторов (очищенная): '{authors_clean}'")
                
                # Проверяем, что это похоже на список авторов
                if ',' in authors_clean and len(authors_clean.split(',')) >= 2:
                    print(f"✓ Найдены авторы: {authors_clean}")
                else:
                    print("✗ Не похоже на список авторов")
            else:
                print("✗ Не найден паттерн 'Proceedings of'")
        
        # Альтернативный поиск в строках
        print("\nАльтернативный поиск в строках:")
        lines = text.split('\n')
        for i, line in enumerate(lines[:20]):
            line = line.strip()
            if line and page_title in line:
                print(f"Строка {i+1}: {line}")
                after_title = line[line.find(page_title) + len(page_title):].strip()
                if after_title and ',' in after_title:
                    print(f"  После заголовка: {after_title}")
                    authors_clean = re.sub(r'[^\w\s,\.]', '', after_title).strip()
                    if len(authors_clean.split(',')) >= 2:
                        print(f"  ✓ Авторы: {authors_clean}")
                    else:
                        print(f"  ✗ Не авторы: {authors_clean}")
                break
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_corl_parsing()
