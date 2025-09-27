#!/usr/bin/env python3
"""
Скрипт для скачивания PDF файлов статей из processed_papers.csv
"""

import pandas as pd
import requests
import os
import time
import argparse
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re

class PDFDownloader:
    def __init__(self, csv_file="output/filtered/processed_papers.csv", output_dir="output/papers"):
        self.csv_file = csv_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем сессию для повторного использования соединений
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Статистика
        self.downloaded_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
    def load_papers(self):
        """Загружает данные статей из CSV файла"""
        print(f"Загружаю данные из {self.csv_file}...")
        df = pd.read_csv(self.csv_file)
        print(f"Загружено {len(df)} статей")
        return df
    
    def clean_filename(self, filename):
        """Очищает имя файла от недопустимых символов"""
        # Убираем недопустимые символы для файловой системы
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Убираем лишние пробелы и ограничиваем длину
        filename = filename.strip()[:100]
        return filename
    
    def get_pdf_url(self, row):
        """Получает URL для скачивания PDF"""
        source = row['source']
        pdf_url = row['pdf_url']
        
        if source == 'ieee':
            # Для IEEE нужно получить прямую ссылку на PDF со страницы статьи
            return self._get_ieee_pdf_url(pdf_url)
        else:
            # Для RSS и CoRL URL уже прямые
            return pdf_url
    
    def _get_ieee_pdf_url(self, document_url):
        """Получает прямую ссылку на PDF для IEEE статьи"""
        try:
            # Извлекаем arnumber из document URL
            arnumber_match = re.search(r'/document/(\d+)/', document_url)
            if arnumber_match:
                arnumber = arnumber_match.group(1)
                return f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnumber}&isnumber=&authNumber="
            return document_url
        except:
            return document_url
    
    def download_pdf(self, row, index):
        """Скачивает PDF файл для одной статьи"""
        title = row['title']
        pdf_url = self.get_pdf_url(row)
        source = row['source']
        conference_code = row['conference_code']
        year = row['publication_year']
        
        # Создаем имя файла
        filename = f"{index:03d}_{conference_code}_{year}_{self.clean_filename(title[:50])}.pdf"
        filepath = self.output_dir / filename
        
        # Проверяем, не скачан ли уже файл
        if filepath.exists():
            print(f"[{index}] Пропускаю (уже существует): {title[:60]}...")
            self.skipped_count += 1
            return True
        
        try:
            print(f"[{index}] Скачиваю: {title[:60]}...")
            print(f"    URL: {pdf_url}")
            
            # Специальные заголовки для IEEE
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/pdf,application/octet-stream,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            if source == 'ieee':
                headers['Referer'] = 'https://ieeexplore.ieee.org/'
            
            # Делаем запрос с таймаутом (отключаем автоматическое распаковывание)
            response = self.session.get(pdf_url, timeout=30, stream=True, headers=headers)
            response.raise_for_status()
            
            # Отключаем автоматическое распаковывание для PDF
            if 'pdf' in response.headers.get('content-type', '').lower():
                response.raw.decode_content = False
            
            # Проверяем, что это действительно PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                print(f"    ⚠️  Предупреждение: неожиданный content-type: {content_type}")
            
            # Сохраняем файл
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = filepath.stat().st_size
            print(f"    ✅ Скачан: {filename} ({file_size:,} байт)")
            self.downloaded_count += 1
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"    ❌ Ошибка скачивания: {e}")
            self.failed_count += 1
            return False
        except Exception as e:
            print(f"    ❌ Неожиданная ошибка: {e}")
            self.failed_count += 1
            return False
    
    def download_range(self, start_idx, end_idx):
        """Скачивает PDF файлы для диапазона статей"""
        df = self.load_papers()
        
        # Проверяем границы
        if start_idx < 0 or end_idx >= len(df):
            print(f"Ошибка: индексы должны быть от 0 до {len(df)-1}")
            return
        
        if start_idx > end_idx:
            print("Ошибка: начальный индекс не может быть больше конечного")
            return
        
        print(f"\nСкачивание PDF файлов")
        print(f"Диапазон: статьи {start_idx} - {end_idx} (всего {end_idx - start_idx + 1} статей)")
        print(f"Папка назначения: {self.output_dir}")
        print("=" * 80)
        
        for i in range(start_idx, end_idx + 1):
            row = df.iloc[i]
            self.download_pdf(row, i)
            
            # Небольшая пауза между запросами
            time.sleep(0.5)
        
        # Выводим статистику
        print("\n" + "=" * 80)
        print("СТАТИСТИКА СКАЧИВАНИЯ:")
        print(f"Скачано успешно: {self.downloaded_count}")
        print(f"Пропущено (уже существует): {self.skipped_count}")
        print(f"Ошибок: {self.failed_count}")
        print(f"Всего обработано: {self.downloaded_count + self.skipped_count + self.failed_count}")

def main():
    parser = argparse.ArgumentParser(description='Скачивание PDF файлов статей')
    parser.add_argument('start', type=int, help='Начальный индекс статьи (начиная с 0)')
    parser.add_argument('end', type=int, help='Конечный индекс статьи')
    parser.add_argument('--csv', default='output/filtered/processed_papers.csv', 
                       help='Путь к CSV файлу с данными статей')
    parser.add_argument('--output', default='output/papers', 
                       help='Папка для сохранения PDF файлов')
    
    args = parser.parse_args()
    
    downloader = PDFDownloader(args.csv, args.output)
    downloader.download_range(args.start, args.end)

if __name__ == "__main__":
    main()
