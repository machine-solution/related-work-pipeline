#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск статей с RSS (Robotics: Science and Systems) конференции
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import os
from typing import List, Dict, Any
from urllib.parse import urljoin

# Константы
BASE_URL = "https://www.roboticsproceedings.org"
CONFERENCE_NAME = "Robotics: Science and Systems"

# RSS годы: RSS20=2024, RSS19=2023, RSS18=2022, RSS17=2021, RSS16=2020, RSS15=2019
RSS_YEARS = [
    (20, 2024), (19, 2023), (18, 2022), (17, 2021), (16, 2020), (15, 2019)
]

class RSSConferenceSearch:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)

    def parse_rss_year(self, rss_num: int, year: int) -> List[Dict[str, Any]]:
        """Парсинг одного года RSS"""
        papers = []
        
        try:
            rss_url = f"{BASE_URL}/rss{rss_num:02d}/index.html"
            print(f"Парсинг RSS {rss_num:02d} (год {year}): {rss_url}")
            
            # Используем точно такой же код как в рабочем отладочном скрипте
            response = requests.get(rss_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем таблицу
            table = soup.find('table')
            if not table:
                print(f"Таблица не найдена в RSS {rss_num:02d}")
                return papers
            
            print(f"✓ Таблица найдена")
            
            # Ищем все строки таблицы
            rows = table.find_all('tr')
            print(f"Количество строк: {len(rows)}")
            
            for row in rows:
                try:
                    # Ищем ячейки в строке
                    cells = row.find_all('td')
                    if len(cells) < 2:
                        continue
                    
                    # Первая ячейка: название статьи + авторы
                    title_cell = cells[0]
                    title_link = title_cell.find('a')
                    
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    html_url = urljoin(rss_url, title_link.get('href'))
                    
                    # Ищем авторов (курсивный текст)
                    authors_elem = title_cell.find('i')
                    authors = authors_elem.get_text(strip=True) if authors_elem else ""
                    
                    # Вторая ячейка: ссылка на PDF
                    pdf_cell = cells[1]
                    pdf_link = pdf_cell.find('a')
                    pdf_url = ""
                    
                    if pdf_link and pdf_link.get('href'):
                        pdf_url = urljoin(rss_url, pdf_link.get('href'))
                    
                    # Создаем статью
                    if title and authors:
                        # Получаем abstract из HTML страницы статьи
                        abstract = self._get_abstract_from_html(html_url)
                        
                        paper = {
                            'title': title.replace(',', ';'),
                            'authors': authors.replace(',', ';'),
                            'author_affiliations': '',  # RSS обычно не содержит аффилиации
                            'publication_year': str(year),
                            'publication_title': CONFERENCE_NAME,
                            'pdf_url': pdf_url,
                            'doi': '',  # RSS обычно не содержит DOI
                            'access_status': 'Открыто',  # RSS обычно открытый доступ
                            'abstract': abstract.replace(',', ';')  # Добавляем abstract
                        }
                        papers.append(paper)
                
                except Exception as e:
                    print(f"Ошибка при парсинге строки: {e}")
                    continue
            
            print(f"Найдено статей в RSS {rss_num:02d} (год {year}): {len(papers)}")
            
        except Exception as e:
            print(f"Ошибка при парсинге RSS {rss_num:02d} (год {year}): {e}")
        
        return papers

    def _get_abstract_from_html(self, html_url: str) -> str:
        """Извлечение abstract из HTML страницы статьи"""
        try:
            response = requests.get(html_url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем abstract после тега <b>Abstract:</b>
            abstract_tag = soup.find('b', string='Abstract:')
            if abstract_tag:
                # Ищем следующий параграф после Abstract:
                next_p = abstract_tag.find_next('p')
                if next_p:
                    abstract_text = next_p.get_text(strip=True)
                    return abstract_text
            
            return ''
            
        except Exception as e:
            print(f"Ошибка при получении abstract из {html_url}: {e}")
            return ''

    def search_papers(self) -> List[Dict[str, Any]]:
        """Основной поиск статей"""
        print("Начинаю поиск статей RSS...")
        
        all_papers = []
        
        # Парсим каждый год RSS
        for rss_num, year in RSS_YEARS:
            print(f"\nОбрабатываю RSS {rss_num:02d} (год {year})")
            
            papers = self.parse_rss_year(rss_num, year)
            all_papers.extend(papers)
            
            print(f"Всего статей на данный момент: {len(all_papers)}")
            
            # Небольшая задержка между запросами
            time.sleep(0.5)
        
        print(f"\nПоиск завершен. Всего найдено статей: {len(all_papers)}")
        return all_papers

    def save_to_csv(self, papers: List[Dict[str, Any]], filename: str = 'output/downloaded/papers_rss.csv'):
        """Сохранение статей в CSV файл"""
        if not papers:
            print("Нет статей для сохранения")
            return
        
        # Создаем папку output если её нет
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        fieldnames = [
            'title', 'authors', 'author_affiliations', 'publication_year',
            'publication_title', 'pdf_url', 'doi', 'access_status', 'abstract'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for paper in papers:
                writer.writerow(paper)
        
        print(f"Сохранено {len(papers)} статей в файл {filename}")

def main():
    print("Поиск статей RSS (Robotics: Science and Systems)")
    print("=" * 60)
    print(f"Годы: {RSS_YEARS[-1][1]}-{RSS_YEARS[0][1]}")
    print(f"Конференция: {CONFERENCE_NAME}")
    print("=" * 60)
    
    # Создаем экземпляр поисковика
    searcher = RSSConferenceSearch()
    
    # Ищем статьи
    papers = searcher.search_papers()
    
    if papers:
        print(f"\nНайдено всего статей: {len(papers)}")
        
        # Сохраняем результаты
        searcher.save_to_csv(papers)
        
        # Показываем примеры
        print("\nПримеры найденных статей:")
        print("=" * 60)
        
        for i, paper in enumerate(papers[:5], 1):
            print(f"{i}. {paper['title']}")
            print(f"   Авторы: {paper['authors']}")
            print(f"   Год: {paper['publication_year']}")
            print(f"   DOI: {paper['doi']}")
            print()
    else:
        print("Статьи не найдены")

if __name__ == "__main__":
    main()
