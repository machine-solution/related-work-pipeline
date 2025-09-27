#!/usr/bin/env python3
"""
Скрипт для скачивания PDF статей из финальной таблицы
"""

import pandas as pd
import requests
import os
import time
import argparse
from urllib.parse import urlparse
import re

class FinalPapersDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 YaBrowser/25.8.0.0 Safari/537.36',
            'Accept': 'application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ru,en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.downloaded_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
    def load_final_papers(self, csv_file='output/found/final_papers_table.csv'):
        """Загрузка финальной таблицы статей"""
        if not os.path.exists(csv_file):
            print(f"Файл {csv_file} не найден")
            return pd.DataFrame()
        
        df = pd.read_csv(csv_file)
        print(f"Загружено {len(df)} статей из {csv_file}")
        return df
    
    def sanitize_filename(self, filename):
        """Очистка имени файла от недопустимых символов"""
        # Убираем недопустимые символы для файловой системы
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Убираем лишние пробелы и ограничиваем длину
        filename = re.sub(r'\s+', ' ', filename).strip()
        if len(filename) > 200:
            filename = filename[:200]
        return filename
    
    def is_pdf_content(self, response):
        """Проверка что ответ содержит PDF"""
        content_type = response.headers.get('content-type', '').lower()
        if 'application/pdf' in content_type:
            return True
        
        # Проверяем первые байты на PDF сигнатуру
        if response.content.startswith(b'%PDF'):
            return True
        
        return False
    
    def download_pdf(self, pdf_url, title, index, year, conference):
        """Скачивание PDF файла"""
        if not pdf_url or pd.isna(pdf_url):
            print(f"    ❌ Нет ссылки на PDF")
            return False
        
        try:
            print(f"    📄 Проверяю: {pdf_url}")
            
            # Создаем имя файла и проверяем, не скачан ли уже
            safe_title = self.sanitize_filename(title)
            filename = f"{index}_{conference}_{year}_{safe_title}.pdf"
            
            # Создаем папку если не существует
            os.makedirs('output/papers', exist_ok=True)
            filepath = os.path.join('output/papers', filename)
            
            # Проверяем, не скачан ли уже файл
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"    ⏭️ Уже скачан: {filename} ({file_size:,} байт)")
                return True
            
            # Делаем HEAD запрос для проверки доступности
            head_response = self.session.head(pdf_url, timeout=10, allow_redirects=True)
            
            if head_response.status_code != 200:
                print(f"    ❌ HTTP {head_response.status_code}: недоступен")
                return False
            
            # Проверяем content-type - должен быть PDF, не HTML
            content_type = head_response.headers.get('content-type', '').lower()
            if 'text/html' in content_type:
                print(f"    ❌ HTML страница вместо PDF (IEEE заблокирован): пропускаю")
                return False
            
            if 'application/pdf' not in content_type:
                print(f"    ⚠️ Неизвестный content-type: {content_type}, проверю содержимое")
            
            # Скачиваем файл
            print(f"    ⬇️ Скачиваю PDF...")
            response = self.session.get(pdf_url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # Проверяем что это действительно PDF
            if not self.is_pdf_content(response):
                print(f"    ❌ Не PDF контент: пропускаю")
                return False
            
            # Сохраняем файл
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"    ✅ Скачан: {filename} ({file_size:,} байт)")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"    ❌ Ошибка сети: {e}")
            return False
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")
            return False
    
    def download_all_papers(self, df):
        """Скачивание всех доступных PDF"""
        if df.empty:
            print("Нет данных для скачивания")
            return
        
        print(f"Начинаю скачивание {len(df)} статей")
        print("=" * 80)
        
        for i in range(len(df)):
            row = df.iloc[i]
            index = row['index']
            title = row['title']
            year = row['year']
            conference = row['conference']
            pdf_url = row['pdf_url']
            
            print(f"[{i+1}/{len(df)}] {title[:60]}...")
            
            success = self.download_pdf(pdf_url, title, index, year, conference)
            
            if success:
                self.downloaded_count += 1
            else:
                self.skipped_count += 1
            
            # Пауза между запросами
            time.sleep(0.5)
        
        print(f"\n📊 Статистика скачивания:")
        print(f"✅ Скачано: {self.downloaded_count}")
        print(f"⏭️ Пропущено: {self.skipped_count}")
        print(f"❌ Ошибок: {self.error_count}")

def main():
    parser = argparse.ArgumentParser(description='Скачивание PDF статей из финальной таблицы')
    parser.add_argument('--input', default='output/found/final_papers_table.csv', help='Входной CSV файл')
    
    args = parser.parse_args()
    
    downloader = FinalPapersDownloader()
    
    # Загружаем данные
    df = downloader.load_final_papers(args.input)
    
    if df.empty:
        return
    
    # Скачиваем PDF
    downloader.download_all_papers(df)

if __name__ == "__main__":
    main()
