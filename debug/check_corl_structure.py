#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка структуры HTML страницы CoRL
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def check_corl_structure():
    """Проверка структуры HTML страницы CoRL"""
    
    # Проверяем один из томов
    volume_url = "https://proceedings.mlr.press/v155/"
    
    print(f"Проверяю структуру: {volume_url}")
    
    try:
        response = requests.get(volume_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("HTML загружен успешно")
        print(f"Длина HTML: {len(response.text)} символов")
        
        # Ищем все ссылки
        links = soup.find_all('a', href=True)
        print(f"Найдено ссылок: {len(links)}")
        
        # Ищем ссылки на статьи
        article_links = []
        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            if text == 'abs' and 'html' in href:
                article_links.append((href, text))
            elif text == 'Download PDF' and href.endswith('.pdf'):
                article_links.append((href, text))
        
        print(f"Найдено ссылок на статьи: {len(article_links)}")
        
        # Проверяем первую статью
        if article_links:
            first_abs = None
            first_pdf = None
            
            for href, text in article_links:
                if text == 'abs' and not first_abs:
                    first_abs = href
                elif text == 'Download PDF' and not first_pdf:
                    first_pdf = href
                
                if first_abs and first_pdf:
                    break
            
            if first_abs:
                print(f"\nПроверяю первую статью: {first_abs}")
                check_article_structure(urljoin(volume_url, first_abs))
        
    except Exception as e:
        print(f"Ошибка: {e}")

def check_article_structure(article_url):
    """Проверка структуры страницы статьи"""
    
    try:
        response = requests.get(article_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"Страница статьи загружена: {len(response.text)} символов")
        
        # Ищем заголовок
        title_elem = soup.find('title')
        if title_elem:
            print(f"Заголовок страницы: {title_elem.get_text()}")
        
        # Ищем основной контент
        main_content = soup.find('main') or soup.find('div', class_='content') or soup.find('body')
        if main_content:
            text = main_content.get_text()
            print(f"Основной контент: {len(text)} символов")
            
            # Ищем паттерны
            if 'Abstract:' in text:
                print("✓ Найден Abstract")
            
            # Ищем авторов
            lines = text.split('\n')
            for i, line in enumerate(lines[:20]):
                if line.strip():
                    print(f"Строка {i+1}: {line.strip()}")
        
    except Exception as e:
        print(f"Ошибка при проверке статьи: {e}")

if __name__ == "__main__":
    check_corl_structure()
