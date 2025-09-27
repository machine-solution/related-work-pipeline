#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск статей с CoRL (Conference on Robot Learning) конференции
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import os
from typing import List, Dict, Any
from urllib.parse import urljoin
import re # Added missing import for re

# Константы
BASE_URL = "https://proceedings.mlr.press"
CONFERENCE_NAME = "Conference on Robot Learning"

# Тома CoRL для парсинга (номер тома, год)
CORL_VOLUMES = [
    (155, 2020),  # CoRL 2020
    (164, 2021),  # CoRL 2021
    (205, 2022),  # CoRL 2022
    (229, 2023),  # CoRL 2023
    (270, 2024),  # CoRL 2024
]

class CORLConferenceSearch:
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

    def parse_corl_volume(self, volume_num: int, year: int) -> List[Dict[str, Any]]:
        """Парсинг одного тома CoRL"""
        papers = []
        
        try:
            volume_url = f"{BASE_URL}/v{volume_num}/"
            print(f"Парсинг CoRL том v{volume_num} (год {year}): {volume_url}")
            
            response = requests.get(volume_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем все ссылки на странице
            article_links = soup.find_all('a', href=True)
            
            current_title = ""
            current_html_url = ""
            current_pdf_url = ""
            
            for link in article_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                # Если это ссылка на HTML статьи (abstract)
                if href and text == 'abs' and 'html' in href:
                    # Получаем название статьи из предыдущего элемента или родительского
                    parent = link.parent
                    if parent:
                        # Ищем название статьи в родительском элементе
                        title_elem = parent.find_previous_sibling() or parent.find_previous()
                        if title_elem:
                            current_title = title_elem.get_text(strip=True)
                            current_html_url = urljoin(volume_url, href)
                            current_pdf_url = ""  # Сбрасываем PDF URL
                
                # Если это ссылка на PDF
                elif href and text == 'Download PDF' and href.endswith('.pdf'):
                    current_pdf_url = urljoin(volume_url, href)
                    
                    # Теперь у нас есть полная информация о статье
                    if current_title and current_html_url:
                        paper = self._create_paper_from_links(
                            current_title, current_html_url, current_pdf_url, year
                        )
                        if paper:
                            papers.append(paper)
                        
                        # Сбрасываем для следующей статьи
                        current_title = ""
                        current_html_url = ""
                        current_pdf_url = ""
            
            print(f"Найдено статей в CoRL v{volume_num} (год {year}): {len(papers)}")
            
        except Exception as e:
            print(f"Ошибка при парсинге CoRL тома v{volume_num} (год {year}): {e}")
        
        return papers

    def _create_paper_from_links(self, title: str, html_url: str, pdf_url: str, year: int) -> Dict[str, Any]:
        """Создание статьи из найденных ссылок"""
        try:
            # Получаем дополнительную информацию из HTML страницы статьи
            paper_info = self._get_paper_details(html_url)
            
            # Используем заголовок из HTML страницы, если он есть
            final_title = paper_info.get('title', title)
            if not final_title:
                final_title = title
            
            paper = {
                'title': final_title.replace(',', ';'),
                'authors': paper_info.get('authors', '').replace(',', ';'),
                'author_affiliations': '',  # CoRL обычно не содержит аффилиации
                'publication_year': str(year),
                'publication_title': CONFERENCE_NAME,
                'pdf_url': pdf_url,
                'doi': paper_info.get('doi', ''),
                'access_status': 'Открыто',  # CoRL обычно открытый доступ
                'abstract': paper_info.get('abstract', '').replace(',', ';')  # Добавляем abstract
            }
            
            return paper
            
        except Exception as e:
            print(f"Ошибка при создании статьи '{title}': {e}")
            return None

    def _get_paper_details(self, html_url: str) -> Dict[str, str]:
        """Получение деталей статьи из HTML страницы"""
        try:
            response = requests.get(html_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем заголовок статьи на странице
            title_elem = soup.find('title')
            page_title = ""
            if title_elem:
                page_title = title_elem.get_text().strip()
            
            # Ищем авторов в теге span с классом "authors"
            authors = ""
            authors_elem = soup.find('span', class_='authors')
            if authors_elem:
                authors = authors_elem.get_text().strip()
                # Заменяем &nbsp; на обычные пробелы
                authors = authors.replace('\xa0', ' ')
            
            # Ищем DOI в тексте
            doi = ""
            doi_match = re.search(r'10\.\d{4,}/[^\s]+', soup.get_text())
            if doi_match:
                doi = doi_match.group()
            
            # Ищем abstract в div с классом "abstract"
            abstract = ""
            abstract_elem = soup.find('div', class_='abstract')
            if abstract_elem:
                abstract = abstract_elem.get_text().strip()
            
            return {
                'title': page_title,
                'authors': authors,
                'doi': doi,
                'abstract': abstract
            }
            
        except Exception as e:
            print(f"Ошибка при получении деталей статьи {html_url}: {e}")
            return {'title': '', 'authors': '', 'doi': '', 'abstract': ''}

    def search_papers(self) -> List[Dict[str, Any]]:
        """Основной поиск статей"""
        print("Начинаю поиск статей CoRL...")
        
        all_papers = []
        
        # Парсим каждый том CoRL
        for volume_num, year in CORL_VOLUMES:
            print(f"\nОбрабатываю том v{volume_num} (год {year})")
            
            papers = self.parse_corl_volume(volume_num, year)
            all_papers.extend(papers)
            
            print(f"Всего статей на данный момент: {len(all_papers)}")
            
            # Небольшая задержка между запросами
            time.sleep(0.5)
        
        print(f"\nПоиск завершен. Всего найдено статей: {len(all_papers)}")
        return all_papers

    def save_to_csv(self, papers: List[Dict[str, Any]], filename: str = 'output/downloaded/papers_corl.csv'):
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
    print("Поиск статей CoRL (Conference on Robot Learning)")
    print("=" * 60)
    print(f"Тома: {[f'v{v[0]} ({v[1]})' for v in CORL_VOLUMES]}")
    print(f"Конференция: {CONFERENCE_NAME}")
    print("=" * 60)
    
    # Создаем экземпляр поисковика
    searcher = CORLConferenceSearch()
    
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
