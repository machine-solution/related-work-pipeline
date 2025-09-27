#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск статей по запросам через IEEE Xplore API
"""

import requests
import json
import csv
import time
from typing import List, Dict, Any
import os
import re

# Константы
MAX_PAGES = 100  # Ограничение по количеству страниц (None = без ограничений)

EXTRA_PAGES = 100

class IEEESearch:
    def __init__(self):
        self.base_url = "https://ieeexplore.ieee.org/rest/search"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://ieeexplore.ieee.org/',
            'Origin': 'https://ieeexplore.ieee.org',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        self.session.headers.update(self.headers)
    
    def fetch_ieee_abstract(self, article_number: str) -> str:
        """
        Получение полного абстракта со страницы IEEE статьи по article_number.
        Возвращает пустую строку при неудаче.
        """
        if not article_number:
            return ""
        document_url = f"https://ieeexplore.ieee.org/document/{article_number}/"
        try:
            resp = self.session.get(document_url, timeout=30)
            resp.raise_for_status()
            # Попытка 1: JSON в xplGlobal.document.metadata
            json_match = re.search(r'xplGlobal\.document\.metadata\s*=\s*({.*?});', resp.text, re.DOTALL)
            if json_match:
                try:
                    metadata = json.loads(json_match.group(1))
                    abstract = metadata.get('abstract', '')
                    if abstract and abstract != 'true':
                        return abstract
                except json.JSONDecodeError:
                    pass
            # Попытка 2: прямой regex ключа abstract
            abstract_match = re.search(r'"abstract":"([^\"]+)"', resp.text)
            if abstract_match:
                abstract = abstract_match.group(1)
                if abstract and abstract != 'true':
                    return abstract
            # Попытка 3: HTML разметка
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            div_abstract = soup.find('div', class_='abstract')
            if div_abstract:
                return div_abstract.get_text(strip=True)
            div_testid = soup.find('div', { 'data-testid': 'abstract' })
            if div_testid:
                return div_testid.get_text(strip=True)
            return ""
        except requests.exceptions.RequestException:
            return ""
        except Exception:
            return ""
        
    def search_papers(self, query_text: str, max_pages: int = None) -> List[Dict[str, Any]]:
        """
        Поиск статей с пагинацией
        """
        # Сначала заходим на главную страницу для получения cookies
        try:
            print("Получаю cookies с главной страницы...")
            main_page = self.session.get('https://ieeexplore.ieee.org/')
            main_page.raise_for_status()
            print("Cookies получены успешно")
        except Exception as e:
            print(f"Ошибка при получении cookies: {e}")
        
        all_papers = []
        page_number = 1
        
        while True:
            print(f"Загружаю страницу {page_number}...")
            
            # Счетчик попыток для текущей страницы
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                # Используем переданный query_text, если он указан, иначе дефолтный (ICRA/IROS)
                effective_query = query_text.strip() if query_text and query_text.strip() else "(\"Publication Title\":international conference on robotics and automation) OR (\"Publication Title\":international conference on intelligent robots and systems)"

                payload = {
                    "action": "search",
                    "highlight": True,
                    "matchBoolean": True,
                    "matchPubs": True,
                    "newsearch": True,
                    "pageNumber": str(page_number),
                    "queryText": effective_query,
                    "returnFacets": ["ALL"],
                    "returnType": "SEARCH",
                    "rowsPerPage": "100",  # Максимум 100 статей на страницу (ограничение API)
                    "ranges": ["2020_2026_Year"],  # Фильтр по годам: с 2020 года
                    "refinements": ["ContentType:Conferences"]  # Только конференции
                }
            
                try:
                    response = self.session.post(self.base_url, json=payload)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Проверяем, есть ли результаты
                    if not data.get('records') or len(data['records']) == 0:
                        print(f"Страница {page_number} пустая, завершаю поиск")
                        return all_papers
                    
                    # Обрабатываем статьи на текущей странице
                    papers_on_page = self._process_papers(data['records'])
                    all_papers.extend(papers_on_page)
                    
                    print(f"Найдено статей на странице {page_number}: {len(papers_on_page)}")
                    print(f"Всего статей: {len(all_papers)}")
                    
                    # Проверяем, есть ли следующая страница (игнорируем totalPages)
                    # Продолжаем загрузку до тех пор, пока не встретим пустую страницу
                    
                    # Ограничение по количеству страниц
                    if max_pages and page_number >= max_pages:
                        print(f"Достигнуто ограничение в {max_pages} страниц")
                        return all_papers
                    
                    # Небольшая задержка между запросами
                    time.sleep(0.05)
                    
                    # Успешно обработали страницу, выходим из цикла попыток
                    break
                    
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    print(f"Ошибка при запросе страницы {page_number} (попытка {retry_count}/{max_retries}): {e}")
                    if ("502" in str(e) or "503" in str(e) or "504" in str(e)) and retry_count < max_retries:
                        print(f"Сервер перегружен, жду 5 секунд и повторяю...")
                        time.sleep(0.05)
                        continue  # Повторяем текущую попытку
                    else:
                        print("Критическая ошибка сети или превышен лимит попыток, завершаю поиск")
                        return all_papers
                except json.JSONDecodeError as e:
                    retry_count += 1
                    print(f"Ошибка при парсинге JSON страницы {page_number} (попытка {retry_count}/{max_retries}): {e}")
                    if retry_count < max_retries:
                        print("Возможно сервер вернул невалидный ответ, жду 3 секунды и повторяю...")
                        time.sleep(0.05)
                        continue  # Повторяем текущую попытку
                    else:
                        print("Превышен лимит попыток, завершаю поиск")
                        return all_papers
                except Exception as e:
                    print(f"Неожиданная ошибка на странице {page_number}: {e}")
                    return all_papers
            
            # Закрываем цикл while retry_count
            if retry_count >= max_retries:
                print(f"Превышен лимит попыток для страницы {page_number}, завершаю поиск")
                return all_papers
            
            # Успешно обработали страницу, переходим к следующей
            page_number += 1
        
        # Если вышли из основного цикла, возвращаем результаты
        return all_papers
    
    def _process_papers(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Обработка статей из одной страницы
        """
        papers = []
        
        for record in records:
            try:
                article_number_str = ""
                try:
                    article_number_str = str(int(record.get('articleNumber', 0))) if record.get('articleNumber') is not None else ""
                except Exception:
                    article_number_str = ""

                # Сначала базовый abstract из ответа поиска
                api_abstract = record.get('abstract', '')
                if isinstance(api_abstract, str):
                    api_abstract = api_abstract.replace(',', ';')
                else:
                    api_abstract = ''

                # Пытаемся получить полный абстракт со страницы документа (если есть article_number)
                full_ieee_abstract = self.fetch_ieee_abstract(article_number_str) if article_number_str else ''
                final_abstract = (full_ieee_abstract or api_abstract or '')

                paper = {
                    'title': record.get('articleTitle', '').replace(',', ';'),  # Заменяем запятые на точки с запятой
                    'authors': self._extract_authors(record),
                    'author_affiliations': self._extract_affiliations(record),
                    'publication_year': record.get('publicationYear', ''),
                    'publication_title': record.get('publicationTitle', '').replace(',', ';'),  # Заменяем запятые на точки с запятой
                    'pdf_url': self._extract_pdf_url(record),
                    'doi': record.get('doi', ''),
                    'access_status': self._extract_access_status(record),
                    'abstract': final_abstract,
                    'article_number': article_number_str  # Сохраняем articleNumber как строку
                }
                papers.append(paper)
            except Exception as e:
                print(f"Ошибка при обработке статьи: {e}")
                continue
        
        return papers
    
    def _extract_authors(self, record: Dict[str, Any]) -> str:
        """
        Извлечение авторов
        """
        authors = record.get('authors', [])
        if isinstance(authors, list):
            author_names = [author.get('preferredName', '') for author in authors if author.get('preferredName')]
            result = '; '.join(author_names)
            return result.replace(',', ';')  # Заменяем запятые на точки с запятой
        return ''
    
    def _extract_affiliations(self, record: Dict[str, Any]) -> str:
        """
        Извлечение аффилиаций авторов
        """
        authors = record.get('authors', [])
        if isinstance(authors, list):
            affiliations = []
            for author in authors:
                if author.get('affiliations'):
                    for aff in author['affiliations']:
                        if aff.get('affiliationName'):
                            affiliations.append(aff['affiliationName'])
            result = '; '.join(set(affiliations))  # Убираем дубликаты
            return result.replace(',', ';')  # Заменяем запятые на точки с запятой
        return ''
    
    def _extract_pdf_url(self, record: Dict[str, Any]) -> str:
        """
        Извлечение ссылки на PDF
        """
        pdf_url = record.get('pdfLink', '')
        if pdf_url:
            if not pdf_url.startswith('http'):
                pdf_url = 'https://ieeexplore.ieee.org' + pdf_url
        return pdf_url
    
    def _extract_access_status(self, record: Dict[str, Any]) -> str:
        """
        Определение статуса доступа к статье
        """
        access_type = record.get('accessType', {})
        if isinstance(access_type, dict):
            access_type_value = access_type.get('type', '')
            if access_type_value == 'locked':
                return 'Заблокировано'
            elif access_type_value == 'open-access':
                return 'Открыто'
            else:
                return f'Неизвестно ({access_type_value})'
        return 'Неизвестно'
    

    
    def save_to_csv(self, papers: List[Dict[str, Any]], filename: str = 'output/downloaded/papers_ieee.csv'):
        """
        Сохранение статей в CSV файл
        """
        if not papers:
            print("Нет статей для сохранения")
            return
        
        # Создаем папку output если её нет
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        fieldnames = [
            'title', 'authors', 'author_affiliations', 'publication_year',
            'publication_title', 'pdf_url', 'doi', 'access_status', 'abstract', 'article_number'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for paper in papers:
                writer.writerow(paper)
        
        print(f"Сохранено {len(papers)} статей в файл {filename}")

def main():
    print("Поиск статей через IEEE Xplore API")
    print("=" * 50)
    
    # Создаем экземпляр поисковика
    searcher = IEEESearch()
    
    print("Поисковый запрос: только ICRA и IROS конференции")
    
    # Используем константу для ограничения по количеству страниц
    max_pages = MAX_PAGES
    
    if max_pages:
        print(f"Ограничение: максимум {max_pages} страниц")
    else:
        print("Без ограничений по количеству страниц")
    
    print("Начинаю поиск...")
    
    # Ищем статьи (query теперь встроен в payload)
    papers = searcher.search_papers("", max_pages=max_pages)
    
    if papers:
        print(f"\nНайдено всего статей: {len(papers)}")
        
        # Сохраняем в CSV
        searcher.save_to_csv(papers)
        
        # Показываем несколько примеров
        print("\nПримеры найденных статей:")
        for i, paper in enumerate(papers[:3]):
            print(f"\n{i+1}. {paper['title']}")
            print(f"   Авторы: {paper['authors']}")
            print(f"   Год: {paper['publication_year']}")
            print(f"   Журнал: {paper['publication_title']}")
            print(f"   Доступ: {paper['access_status']}")
    else:
        print("Статьи не найдены")

if __name__ == "__main__":
    main()
