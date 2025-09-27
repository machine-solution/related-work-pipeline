#!/usr/bin/env python3
"""
Скрипт для поиска статей на arXiv и создания сводной таблицы
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import quote_plus, urljoin
import argparse

class ArxivSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 YaBrowser/25.8.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ru,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        })
        
        self.base_url = "https://arxiv.org/search/"
        self.found_papers = []
        
    def search_papers(self, query, max_results=100):
        """Поиск статей на arXiv по запросу"""
        print(f"Поиск статей на arXiv: '{query}'")
        print(f"Максимум результатов: {max_results}")
        
        start = 0
        batch_size = 50
        
        while start < max_results:
            print(f"Загружаю результаты {start+1}-{min(start+batch_size, max_results)}...")
            
            # Формируем URL для поиска
            params = {
                'query': query,
                'searchtype': 'all',
                'abstracts': 'show',
                'order': '-announced_date_first',
                'size': str(batch_size),
                'start': str(start)
            }
            
            try:
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                # Парсим HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Ищем статьи в результатах
                papers = self._parse_search_results(soup)
                
                if not papers:
                    print("Больше результатов не найдено")
                    break
                
                self.found_papers.extend(papers)
                print(f"Найдено {len(papers)} статей в этой партии")
                
                start += batch_size
                time.sleep(1)  # Пауза между запросами
                
            except requests.exceptions.RequestException as e:
                print(f"Ошибка при запросе: {e}")
                break
        
        print(f"Всего найдено статей: {len(self.found_papers)}")
        return self.found_papers
    
    def _parse_search_results(self, soup):
        """Парсинг результатов поиска arXiv"""
        papers = []
        
        # Ищем блоки с результатами
        results = soup.find_all('li', class_='arxiv-result')
        
        for result in results:
            try:
                paper = self._extract_paper_info(result)
                if paper:
                    papers.append(paper)
            except Exception as e:
                print(f"Ошибка при парсинге статьи: {e}")
                continue
        
        return papers
    
    def _extract_paper_info(self, result_element):
        """Извлечение информации о статье из HTML элемента"""
        paper = {}
        
        # Заголовок и ссылка
        title_elem = result_element.find('p', class_='title')
        if title_elem:
            title_link = title_elem.find('a')
            if title_link:
                paper['title'] = title_link.get_text(strip=True)
                paper['arxiv_url'] = urljoin('https://arxiv.org', title_link.get('href'))
                
                # Извлекаем arXiv ID из URL
                arxiv_id_match = re.search(r'abs/(\d+\.\d+)', paper['arxiv_url'])
                if arxiv_id_match:
                    paper['arxiv_id'] = arxiv_id_match.group(1)
                    paper['pdf_url'] = f"https://arxiv.org/pdf/{paper['arxiv_id']}.pdf"
                else:
                    paper['pdf_url'] = paper['arxiv_url'].replace('/abs/', '/pdf/') + '.pdf'
        
        # Авторы
        authors_elem = result_element.find('p', class_='authors')
        if authors_elem:
            authors = []
            for author_link in authors_elem.find_all('a'):
                authors.append(author_link.get_text(strip=True))
            paper['authors'] = '; '.join(authors)
        
        # Дата публикации
        date_elem = result_element.find('p', class_='is-size-7')
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            # Извлекаем год из даты
            year_match = re.search(r'(\d{4})', date_text)
            if year_match:
                paper['year'] = int(year_match.group(1))
        
        # Abstract
        abstract_elem = result_element.find('span', class_='abstract-full')
        if abstract_elem:
            paper['abstract'] = abstract_elem.get_text(strip=True)
        else:
            # Пробуем найти краткий abstract
            abstract_elem = result_element.find('span', class_='abstract-short')
            if abstract_elem:
                paper['abstract'] = abstract_elem.get_text(strip=True)
        
        # Категории
        subjects_elem = result_element.find('div', class_='tags')
        if subjects_elem:
            subjects = []
            for subject_link in subjects_elem.find_all('a'):
                subjects.append(subject_link.get_text(strip=True))
            paper['subjects'] = '; '.join(subjects)
        
        # Определяем конференцию по категориям и заголовку
        paper['conference'] = self._determine_conference(paper.get('subjects', ''), paper.get('title', ''))
        
        return paper if paper.get('title') else None
    
    def _determine_conference(self, subjects, title):
        """Определение конференции по категориям и заголовку"""
        subjects_lower = subjects.lower()
        title_lower = title.lower()
        
        # Проверяем категории arXiv
        if 'cs.ro' in subjects_lower:  # Robotics
            if 'learning' in title_lower or 'neural' in title_lower or 'deep' in title_lower:
                return 'arXiv Robotics + ML'
            else:
                return 'arXiv Robotics'
        elif 'cs.lg' in subjects_lower:  # Machine Learning
            if 'robot' in title_lower or 'manipulat' in title_lower:
                return 'arXiv ML + Robotics'
            else:
                return 'arXiv ML'
        elif 'cs.ai' in subjects_lower:  # Artificial Intelligence
            return 'arXiv AI'
        else:
            return 'arXiv Other'
    
    def save_to_csv(self, filename='output/found/arxiv_papers.csv'):
        """Сохранение найденных статей в CSV"""
        if not self.found_papers:
            print("Нет данных для сохранения")
            return
        
        # Создаем папку если не существует
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Создаем DataFrame
        df = pd.DataFrame(self.found_papers)
        
        # Упорядочиваем колонки
        columns_order = ['title', 'authors', 'year', 'conference', 'abstract', 'arxiv_url', 'pdf_url', 'arxiv_id', 'subjects']
        df = df.reindex(columns=[col for col in columns_order if col in df.columns])
        
        # Сохраняем
        df.to_csv(filename, index=False)
        print(f"Сохранено {len(df)} статей в {filename}")
        
        return filename

def main():
    parser = argparse.ArgumentParser(description='Поиск статей на arXiv')
    parser.add_argument('query', help='Поисковый запрос')
    parser.add_argument('--max-results', type=int, default=100, help='Максимальное количество результатов')
    parser.add_argument('--output', default='output/found/arxiv_papers.csv', help='Файл для сохранения результатов')
    
    args = parser.parse_args()
    
    searcher = ArxivSearcher()
    searcher.search_papers(args.query, args.max_results)
    searcher.save_to_csv(args.output)

if __name__ == "__main__":
    main()
