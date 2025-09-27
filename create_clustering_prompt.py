#!/usr/bin/env python3
"""
Скрипт для создания промпта для кластеризации работ по задачам и методам
"""

import os
import pandas as pd
import argparse
from pathlib import Path

def load_papers_table(csv_path):
    """Загружает таблицу с работами"""
    df = pd.read_csv(csv_path)
    print(f"Загружено {len(df)} работ из {csv_path}")
    return df

def load_summaries(summary_dir):
    """Загружает саммари из папки"""
    summaries = {}
    summary_path = Path(summary_dir)
    
    if not summary_path.exists():
        print(f"Папка {summary_dir} не существует")
        return summaries
    
    for file_path in summary_path.glob("*.txt"):
        try:
            # Извлекаем номер из имени файла
            filename = file_path.stem
            if filename.isdigit():
                index = int(filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                summaries[index] = content
                print(f"Загружено саммари для работы {index}")
        except Exception as e:
            print(f"Ошибка при загрузке {file_path}: {e}")
    
    print(f"Всего загружено {len(summaries)} саммари")
    return summaries

def create_clustering_prompt(papers_df, summaries):
    """Создает промпт для кластеризации работ"""
    
    prompt_parts = []
    num_papers = len(papers_df)
    
    # Заголовок
    prompt_parts.append("# Clustering of Manipulation and Machine Learning Papers")
    prompt_parts.append("")
    prompt_parts.append("Analyze the following papers and identify the main tasks and methods. Group the works by similar tasks and approaches.")
    prompt_parts.append("")
    prompt_parts.append(f"Total papers: {num_papers}. Every paper must be clustered; none should be left unassigned.")
    prompt_parts.append("")
    
    # Инструкции
    prompt_parts.append("## Instructions:")
    prompt_parts.append("1. Identify the main tasks")
    prompt_parts.append("2. Determine the key methods")
    prompt_parts.append("3. Group the works by similar tasks and methods. You must define the groups yourself based on the content of the works")
    prompt_parts.append("4. You must produce a set of clusters (groups) covering all papers.")
    prompt_parts.append("5. For each group, provide:")
    prompt_parts.append("   - Group name")
    prompt_parts.append("   - Description of tasks and methods")
    prompt_parts.append("   - Paper indices in this group")
    prompt_parts.append("   - Titles of all papers")
    prompt_parts.append("6. Assign every paper to exactly one cluster (no leftovers).")
    prompt_parts.append("7. Create 10–15 clusters in total, each containing at least 10 papers.")
    prompt_parts.append("")
    
    # Работы
    prompt_parts.append("## Papers for analysis:")
    prompt_parts.append("")
    
    for index, row in papers_df.iterrows():
        paper_id = row['index']
        title = row['title']
        year = row['year']
        conference = row['conference']
        abstract = row['abstract']
        
        prompt_parts.append(f"### Paper #{paper_id}")
        prompt_parts.append(f"**Title:** {title}")
        prompt_parts.append(f"**Abstract:** {abstract}")
        
        # Добавляем саммари если есть
        if paper_id in summaries:
            prompt_parts.append(f"**Summary:** {summaries[paper_id]}")
        
        prompt_parts.append("")
    
    # Заключение
    prompt_parts.append("## Expected output:")
    prompt_parts.append("Return ONLY the clusters in the following Markdown format (no preamble, no justification):")
    prompt_parts.append("")
    prompt_parts.append("### Clusters")
    prompt_parts.append("")
    prompt_parts.append("#### Cluster <number>: <Group name>")
    prompt_parts.append("- Summary: <2–4 sentences describing the tasks and methods>")
    prompt_parts.append("- Papers:")
    prompt_parts.append("  - [<index>] <title>")
    prompt_parts.append("  - [<index>] <title>")
    prompt_parts.append("  - ...")
    prompt_parts.append("")
    prompt_parts.append("Repeat for 10–15 clusters so that ALL papers are assigned exactly once.")
    prompt_parts.append("")
    
    return "\n".join(prompt_parts)

def main():
    parser = argparse.ArgumentParser(description='Создание промпта для кластеризации работ')
    parser.add_argument('--papers', default='output/found/final_papers_table.csv', 
                       help='Путь к CSV с работами')
    parser.add_argument('--summaries', default='output/papers_summary', 
                       help='Папка с саммари')
    parser.add_argument('--output', default='related_work_prompt.txt', 
                       help='Выходной файл с промптом')
    
    args = parser.parse_args()
    
    print("=== Создание промпта для кластеризации работ ===")
    
    # Загружаем данные
    papers_df = load_papers_table(args.papers)
    summaries = load_summaries(args.summaries)
    
    # Создаем промпт
    prompt = create_clustering_prompt(papers_df, summaries)
    
    # Сохраняем промпт
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    print(f"\n✅ Промпт сохранен в {args.output}")
    print(f"📊 Обработано {len(papers_df)} работ")
    print(f"📝 Использовано {len(summaries)} саммари")

if __name__ == "__main__":
    main()
