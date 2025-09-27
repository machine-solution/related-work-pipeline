#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пост-обработка загруженных статей IEEE Xplore, RSS и CoRL
"""

import pandas as pd
import os
import re
from typing import Dict, List, Any

class PapersProcessor:
    def __init__(self):
        self.input_files = {
            'ieee': 'output/downloaded/papers_ieee.csv',
            'rss': 'output/downloaded/papers_rss.csv',
            'corl': 'output/downloaded/papers_corl.csv'
        }
        self.output_dir = 'output/filtered'
    
    def _clean_highlight_markers(self, text: str) -> str:
        """Очистка текста от маркеров highlight [::слово::]"""
        if pd.isna(text) or not text:
            return text
        return re.sub(r'\[::([^:]+)::\]', r'\1', str(text))
    
    def _clean_for_csv(self, text: str) -> str:
        """Подготовка текста для CSV: замена запятых на точку с запятой"""
        if pd.isna(text) or not text:
            return text
        return str(text).replace(',', ';')
    
    def _convert_to_direct_pdf_url(self, pdf_url: str, source: str) -> str:
        """Преобразование URL в прямую ссылку на PDF"""
        if pd.isna(pdf_url) or not pdf_url:
            return pdf_url
        
        if source == 'ieee':
            # Для IEEE используем document URL вместо stamp URL
            if 'stamp/stamp.jsp' in pdf_url:
                # Извлекаем arnumber из URL
                arnumber_match = re.search(r'arnumber=(\d+)', pdf_url)
                if arnumber_match:
                    arnumber = arnumber_match.group(1)
                    # Используем document URL, который ведет к странице статьи
                    return f"https://ieeexplore.ieee.org/document/{arnumber}/"
            return pdf_url
            
        elif source in ['rss', 'corl']:
            # Для RSS и CoRL URL уже прямые
            return pdf_url
            
        return pdf_url
    
    def _extract_conference_code(self, publication_title: str, source: str) -> str:
        """Определение короткого кода конференции"""
        if pd.isna(publication_title):
            return 'unnamed'
        
        title_lower = publication_title.lower()
        
        # Для старого файла - определяем по названию публикации
        if source == 'old':
            if 'international conference on robotics and automation' in title_lower:
                return 'ICRA'
            elif 'international conference on intelligent robots and systems' in title_lower:
                return 'IROS'
            elif 'robotics: science and systems' in title_lower:
                return 'RSS'
            elif 'robotics science and systems' in title_lower:
                return 'RSS'
            elif 'conference on robot learning' in title_lower:
                return 'CoRL'
            else:
                return 'unnamed'
        
        # Для RSS конференции
        elif source == 'rss':
            if 'robotics: science and systems' in title_lower:
                return 'RSS'
            else:
                return 'RSS'  # RSS файл содержит только RSS конференции
        
        # Для CoRL конференции
        elif source == 'corl':
            if 'conference on robot learning' in title_lower:
                return 'CoRL'
            else:
                return 'CoRL'  # CoRL файл содержит только CoRL конференции
        
        # Для IEEE конференций
        elif source == 'ieee':
            if 'international conference on robotics and automation' in title_lower:
                return 'ICRA'
            elif 'international conference on intelligent robots and systems' in title_lower:
                return 'IROS'
            elif 'robotics: science and systems' in title_lower:
                return 'RSS'
            elif 'robotics science and systems' in title_lower:
                return 'RSS'
            elif 'conference on robot learning' in title_lower:
                return 'CoRL'
            else:
                return 'unnamed'
        
        return 'unnamed'
        
    def load_papers(self) -> pd.DataFrame:
        """Загрузка загруженных статей из всех источников"""
        all_dfs = []
        
        for source, file_path in self.input_files.items():
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                # Добавляем метку источника
                df['source'] = source
                all_dfs.append(df)
                print(f"Загружено {len(df)} статей из {source.upper()}")
            else:
                print(f"Файл {file_path} не найден, пропускаем")
        
        if not all_dfs:
            raise FileNotFoundError("Не найдено ни одного файла с данными")
        
        # Объединяем все данные
        combined_df = pd.concat(all_dfs, ignore_index=True)
        print(f"Всего загружено {len(combined_df)} статей")
        
        return combined_df
    
    def normalize_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Нормализация заголовков столбцов и обработка данных"""
        # Приводим к стандартному виду
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Очищаем маркеры highlight и подготавливаем для CSV
        text_columns = ['title', 'authors', 'author_affiliations', 'publication_title', 'abstract']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].apply(self._clean_highlight_markers)
                df[col] = df[col].apply(self._clean_for_csv)
        
        # Сохраняем article_number если есть и конвертируем в строку
        if 'article_number' not in df.columns:
            df['article_number'] = ''
        else:
            # Конвертируем article_number из float в int, затем в строку, обрабатывая NaN
            df['article_number'] = df['article_number'].apply(
                lambda x: str(int(x)) if pd.notna(x) and x != '' else ''
            )
        
        # Преобразуем PDF URL в прямые ссылки
        df['pdf_url'] = df.apply(
            lambda row: self._convert_to_direct_pdf_url(row['pdf_url'], row['source']), 
            axis=1
        )
        
        # Добавляем код конференции с учетом источника (только если его еще нет)
        if 'conference_code' not in df.columns or df['conference_code'].isna().all():
            df['conference_code'] = df.apply(
                lambda row: self._extract_conference_code(row['publication_title'], row['source']), 
                axis=1
            )
        else:
            print("conference_code уже существует, пропускаем его определение")
        
        print("Заголовки нормализованы и данные обработаны")
        return df
    
    def cluster_conferences(self, df: pd.DataFrame) -> pd.DataFrame:
        """Кластеризация по конференциям"""
        # Группируем по коду конференции
        conference_stats = df['conference_code'].value_counts()
        print("\nСтатистика по конференциям:")
        print(conference_stats)
        
        # Статистика по источникам
        source_stats = df['source'].value_counts()
        print("\nСтатистика по источникам:")
        print(source_stats)
        
        # Добавляем информацию о типе публикации
        df['publication_type'] = df['conference_code'].apply(
            lambda x: 'conference' if x != 'unnamed' else 'journal'
        )
        
        return df
    
    def apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Применение фильтров по ключевым словам"""
        print(f"\nДо фильтрации: {len(df)} статей")
        
        # Ключевые слова только для манипуляторов
        robot_keywords = ['manipulator', 'multi-arm', 'multi arm', 'robotic arm', 'end effector']
        
        # Ключевые слова для машинного обучения
        ml_keywords = ['learning', 'deep', 'ai-based', 'artificial intelligence', 'reinforcement', 'neural network']
        
        # Функция для проверки наличия ключевых слов в названии ИЛИ абстракте
        def has_robot_keywords(title, abstract):
            if pd.isna(title) and pd.isna(abstract):
                return False
            
            title_text = str(title).lower() if pd.notna(title) else ""
            abstract_text = str(abstract).lower() if pd.notna(abstract) else ""
            combined_text = f"{title_text} {abstract_text}"
            
            return any(keyword in combined_text for keyword in robot_keywords)
        
        def has_ml_keywords(title, abstract):
            if pd.isna(title) and pd.isna(abstract):
                return False
            
            title_text = str(title).lower() if pd.notna(title) else ""
            abstract_text = str(abstract).lower() if pd.notna(abstract) else ""
            combined_text = f"{title_text} {abstract_text}"
            
            return any(keyword in combined_text for keyword in ml_keywords)
        
        # Применяем фильтры: должны быть И манипуляторы И МЛ (в названии ИЛИ абстракте)
        df_filtered = df[
            df.apply(lambda row: has_robot_keywords(row['title'], row['abstract']), axis=1) & 
            df.apply(lambda row: has_ml_keywords(row['title'], row['abstract']), axis=1)
        ]
        
        print(f"После фильтрации по ключевым словам: {len(df_filtered)} статей")
        
        # Дополнительный фильтр: только ICRA, IROS, RSS и CoRL
        df_filtered = df_filtered[df_filtered['conference_code'].isin(['ICRA', 'IROS', 'RSS', 'CoRL'])]
        
        print(f"После фильтрации по конференциям (только ICRA/IROS/RSS/CoRL): {len(df_filtered)} статей")
        
        # Фильтр по годам: только 2020-2024
        df_filtered = df_filtered[df_filtered['publication_year'].astype(int).between(2020, 2024)]
        
        print(f"После фильтрации по годам (2020-2024): {len(df_filtered)} статей")
        print(f"Всего отфильтровано: {len(df) - len(df_filtered)} статей")
        
        # Показываем примеры отфильтрованных статей
        if len(df_filtered) > 0:
            print("\nПримеры отфильтрованных статей:")
            for i, (_, row) in enumerate(df_filtered.head(5).iterrows()):
                print(f"{i+1}. {row['title']}")
                print(f"   Год: {row['publication_year']}, Конференция: {row['conference_code']}, Источник: {row['source']}")
                print()
        
        return df_filtered
    
    def save_processed(self, df: pd.DataFrame, filename: str = 'processed_papers.csv'):
        """Сохранение обработанных данных"""
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, filename)
        
        df.to_csv(output_path, index=False)
        print(f"Обработанные данные сохранены в {output_path}")
        
        return output_path
    
    def process(self):
        """Основной процесс обработки"""
        print("Начинаю пост-обработку статей IEEE, RSS и CoRL...")
        
        # Загружаем данные
        df = self.load_papers()
        
        # Нормализуем заголовки
        df = self.normalize_headers(df)
        
        # Кластеризуем по конференциям
        df = self.cluster_conferences(df)
        
        # Применяем фильтры
        df = self.apply_filters(df)
        
        # Сохраняем результат
        self.save_processed(df)
        
        print("Пост-обработка завершена!")

def main():
    processor = PapersProcessor()
    processor.process()

if __name__ == "__main__":
    main()
