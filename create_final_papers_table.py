#!/usr/bin/env python3
"""
Скрипт для создания финальной таблицы статей с доступными PDF
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
import argparse
import os
import json

class FinalPapersTable:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 YaBrowser/25.8.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ru,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Priority': 'u=0, i',
            'Referer': 'https://arxiv.org/search/?query=Constraint-based+Task+Specification+and+Trajectory+Optimization+for+Sequential+Manipulation&searchtype=all&source=header',
            'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138", "YaBrowser";v="25.8", "Yowser";v="2.5"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Linux"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.base_url = "https://arxiv.org/search/"
        self.final_papers = []
        
    def load_processed_papers(self, csv_file='output/filtered/processed_papers.csv'):
        """Загрузка обработанных статей"""
        if not os.path.exists(csv_file):
            print(f"Файл {csv_file} не найден")
            return pd.DataFrame()
        
        df = pd.read_csv(csv_file)
        print(f"Загружено {len(df)} статей из {csv_file}")
        return df
    
    def is_pdf_accessible(self, pdf_url, access_status):
        """Проверка доступности PDF"""
        if not pdf_url or pd.isna(pdf_url):
            return False
        
        # Проверяем статус доступа
        if access_status and 'заблокировано' in str(access_status).lower():
            return False
        
        return True
    
    def search_arxiv_by_title(self, title, max_results=5):
        """Поиск статьи на arXiv по названию"""
        # Очищаем название от лишних символов для поиска
        clean_title = re.sub(r'[^\w\s]', ' ', title)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        # Используем полное название, как в рабочем примере
        query = clean_title.replace(' ', '+')
        
        try:
            # Используем точно такой же подход, как в рабочем примере
            url = f"https://arxiv.org/search/?query={query}&searchtype=all&abstracts=show&order=-announced_date_first&size=50"
            
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'ru,en;q=0.9',
                'priority': 'u=0, i',
                'referer': 'https://arxiv.org/search/?query=Constraint-based+Task+Specification+and+Trajectory+Optimization+for+Sequential+Manipulation&searchtype=all&source=header',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "YaBrowser";v="25.8", "Yowser";v="2.5"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 YaBrowser/25.8.0.0 Safari/537.36'
            }
            
            cookies = {'arxiv-search-parameters': '{}'}
            
            response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
            response.raise_for_status()
            
            print(f"    Status: {response.status_code}")
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('li', class_='arxiv-result')
            print(f"    Найдено результатов: {len(results)}")
            
            return self._parse_search_results(results, title)
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при поиске '{title}': {e}")
            return []
    
    def _parse_search_results(self, results, original_title):
        """Парсинг результатов поиска arXiv"""
        found_papers = []
        
        print(f"    🔍 Парсинг {len(results)} результатов...")
        
        for i, result in enumerate(results):
            try:
                paper = self._extract_paper_info(result)
                if paper:
                    # Проверяем схожесть названий
                    similarity = self._calculate_title_similarity(original_title, paper['title'])
                    paper['similarity_score'] = similarity
                    paper['original_title'] = original_title
                    
                    print(f"      {i+1}. Найден: {paper['title'][:60]}... (схожесть: {similarity:.2f})")
                    if similarity >= 0.7:
                        found_papers.append(paper)
                        print(f"         ✅ Добавлен (схожесть ≥ 0.7)")
                    else:
                        print(f"         ❌ Отклонен (схожесть < 0.7)")
                else:
                    print(f"      {i+1}. ❌ Не удалось извлечь информацию о статье")
                        
            except Exception as e:
                print(f"      {i+1}. ❌ Ошибка при парсинге результата: {e}")
                continue
        
        print(f"    📊 Итого найдено подходящих статей: {len(found_papers)}")
        return found_papers
    
    def _extract_paper_info(self, result_element):
        """Извлечение информации о статье из HTML элемента"""
        paper = {}
        
        # Заголовок статьи
        title_elem = result_element.find('p', class_='title is-5 mathjax')
        if title_elem:
            # Простое решение: достаем весь текст и добавляем пробелы между словами
            title_text = ""
            for element in title_elem.descendants:
                if element.string and element.string.strip():
                    # Проверяем, что это не дочерний элемент span тега
                    if element.parent.name != 'span':
                        title_text += element.string.strip() + " "
            paper['title'] = title_text.strip()
        else:
            print(f"        ❌ Не найден title_elem с class='title is-5 mathjax'")
            return None
        
        # arXiv ID и ссылки
        list_title_elem = result_element.find('p', class_='list-title')
        if list_title_elem:
            title_link = list_title_elem.find('a')
            if title_link:
                # Извлекаем arXiv ID из текста ссылки (например, "arXiv:2508.18627")
                arxiv_text = title_link.get_text(strip=True)
                arxiv_id_match = re.search(r'arXiv:(\d+\.\d+)', arxiv_text)
                if arxiv_id_match:
                    paper['arxiv_id'] = arxiv_id_match.group(1)
                    paper['arxiv_url'] = f"https://arxiv.org/abs/{paper['arxiv_id']}"
                    paper['pdf_url'] = f"https://arxiv.org/pdf/{paper['arxiv_id']}.pdf"
                else:
                    paper['arxiv_url'] = urljoin('https://arxiv.org', title_link.get('href'))
                    # Извлекаем arXiv ID из URL
                    arxiv_id_match = re.search(r'abs/(\d+\.\d+)', paper['arxiv_url'])
                    if arxiv_id_match:
                        paper['arxiv_id'] = arxiv_id_match.group(1)
                        paper['pdf_url'] = f"https://arxiv.org/pdf/{paper['arxiv_id']}.pdf"
                    else:
                        paper['pdf_url'] = paper['arxiv_url'].replace('/abs/', '/pdf/') + '.pdf'
            else:
                print(f"        ❌ Не найден title_link в list_title_elem")
                return None
        else:
            print(f"        ❌ Не найден list_title_elem с class='list-title'")
            return None
        
        return paper if paper.get('title') else None
    
    def fetch_ieee_abstract(self, article_number):
        """Получение полного абстракта со страницы IEEE статьи"""
        if not article_number or pd.isna(article_number):
            return None
        
        document_url = f"https://ieeexplore.ieee.org/document/{article_number}/"
        
        try:
            print(f"    📄 Загружаю IEEE страницу: {document_url}")
            response = self.session.get(document_url, timeout=30)
            response.raise_for_status()
            
            # Попытка 1: ищем в JSON данных xplGlobal.document.metadata
            json_match = re.search(r'xplGlobal\.document\.metadata\s*=\s*({.*?});', response.text, re.DOTALL)
            if json_match:
                try:
                    metadata_str = json_match.group(1)
                    metadata = json.loads(metadata_str)
                    abstract = metadata.get('abstract', '')
                    if abstract and abstract != 'true':
                        print(f"    ✅ Найден полный абстракт IEEE: {len(abstract)} символов")
                        return abstract
                except json.JSONDecodeError:
                    pass
            
            # Попытка 2: ищем прямой паттерн "abstract":"текст"
            abstract_match = re.search(r'"abstract":"([^"]+)"', response.text)
            if abstract_match:
                abstract = abstract_match.group(1)
                if abstract and abstract != 'true':
                    print(f"    ✅ Найден полный абстракт IEEE через regex: {len(abstract)} символов")
                    return abstract
            
            # Попытка 3: парсим HTML как запасной вариант
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем по классу abstract
            abstract_elem = soup.find('div', class_='abstract')
            if abstract_elem:
                abstract = abstract_elem.get_text(strip=True)
                print(f"    ✅ Найден полный абстракт IEEE через HTML: {len(abstract)} символов")
                return abstract
            
            # Ищем по data-testid
            abstract_elem = soup.find('div', {'data-testid': 'abstract'})
            if abstract_elem:
                abstract = abstract_elem.get_text(strip=True)
                print(f"    ✅ Найден полный абстракт IEEE через data-testid: {len(abstract)} символов")
                return abstract
            
            print(f"    ❌ Полный абстракт IEEE не найден")
            return None
                
        except requests.exceptions.RequestException as e:
            print(f"    ❌ Ошибка при загрузке IEEE страницы: {e}")
            return None
        except Exception as e:
            print(f"    ❌ Ошибка при парсинге IEEE страницы: {e}")
            return None
    
    def _calculate_title_similarity(self, title1, title2):
        """Вычисление схожести названий статей"""
        # Приводим к нижнему регистру и убираем пунктуацию
        clean1 = re.sub(r'[^\w\s]', ' ', title1.lower())
        clean2 = re.sub(r'[^\w\s]', ' ', title2.lower())
        
        # Разбиваем на слова
        words1 = set(clean1.split())
        words2 = set(clean2.split())
        
        # Убираем стоп-слова
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        if not words1 or not words2:
            return 0.0
        
        # Вычисляем коэффициент Жаккара
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def process_papers(self, df):
        """Обработка статей и создание финальной таблицы"""
        if df.empty:
            print("Нет данных для обработки")
            return
        
        print(f"Обработка {len(df)} статей")
        print("=" * 80)
        
        for i in range(len(df)):
            row = df.iloc[i]
            title = row['title']
            pdf_url = row.get('pdf_url', '')
            access_status = row.get('access_status', '')
            
            print(f"[{i}] Обрабатываю: {title[:60]}...")
            
            # Проверяем доступность PDF
            if self.is_pdf_accessible(pdf_url, access_status):
                print("    ✅ PDF доступен: использую исходные данные")
                # Используем исходные данные
                final_paper = {
                    'index': i,
                    'title': title,
                    'conference': row.get('conference_code', ''),
                    'year': row.get('publication_year', ''),
                    'abstract': row.get('abstract', ''),
                    'pdf_url': pdf_url
                }
                self.final_papers.append(final_paper)
            else:
                print("    🔒 PDF недоступен: ищу на arXiv")
                
                # Получаем полный абстракт для IEEE статей
                full_ieee_abstract = None
                if row['source'] == 'ieee' and 'article_number' in row and pd.notna(row['article_number']) and row['article_number']:
                    article_num_str = str(int(row['article_number'])) if pd.notna(row['article_number']) else ''
                    full_ieee_abstract = self.fetch_ieee_abstract(article_num_str)
                
                # Ищем на arXiv
                arxiv_results = self.search_arxiv_by_title(title)
                
                if arxiv_results:
                    best_match = max(arxiv_results, key=lambda x: x['similarity_score'])
                    print(f"    ✅ Найдена arXiv версия: {best_match['title'][:60]}... (схожесть: {best_match['similarity_score']:.2f})")
                    
                    # Используем данные из arXiv
                    final_paper = {
                        'index': i,
                        'title': title,  # Оставляем оригинальное название
                        'conference': row.get('conference_code', ''),
                        'year': row.get('publication_year', ''),
                        'abstract': best_match.get('abstract', '') or full_ieee_abstract or row.get('abstract', ''),
                        'pdf_url': best_match.get('pdf_url', '')
                    }
                    self.final_papers.append(final_paper)
                else:
                    print("    ❌ arXiv версия не найдена: сохраняю с исходными данными")
                    # Сохраняем с исходными данными, даже если PDF недоступен
                    final_paper = {
                        'index': i,
                        'title': title,
                        'conference': row.get('conference_code', ''),
                        'year': row.get('publication_year', ''),
                        'abstract': full_ieee_abstract or row.get('abstract', ''),
                        'pdf_url': pdf_url
                    }
                    self.final_papers.append(final_paper)
            
            # Пауза между запросами
            time.sleep(1)
        
        print(f"\nОбработано статей: {len(self.final_papers)}")
    
    def save_results(self, filename='output/found/final_papers_table.csv'):
        """Сохранение финальной таблицы"""
        if not self.final_papers:
            print("Нет результатов для сохранения")
            return
        
        # Создаем папку если не существует
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Создаем DataFrame
        df = pd.DataFrame(self.final_papers)
        
        # Сохраняем
        df.to_csv(filename, index=False)
        print(f"Финальная таблица сохранена в {filename}")
        
        return filename

def main():
    parser = argparse.ArgumentParser(description='Создание финальной таблицы статей с доступными PDF')
    parser.add_argument('--input', default='output/filtered/processed_papers.csv', help='Входной CSV файл')
    parser.add_argument('--output', default='output/found/final_papers_table.csv', help='Выходной CSV файл')
    
    args = parser.parse_args()
    
    processor = FinalPapersTable()
    
    # Загружаем данные
    df = processor.load_processed_papers(args.input)
    
    if df.empty:
        return
    
    # Обрабатываем статьи
    processor.process_papers(df)
    
    # Сохраняем результаты
    processor.save_results(args.output)

if __name__ == "__main__":
    main()
