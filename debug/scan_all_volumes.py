#!/usr/bin/env python3
"""
Перебор всех номеров томов MLR для поиска CoRL
"""

import requests
from bs4 import BeautifulSoup
import time

def scan_all_volumes():
    """Перебираем все номера томов и ищем CoRL"""
    
    print("Перебираю все номера томов MLR для поиска CoRL...")
    print("=" * 60)
    
    corl_volumes = []
    
    # Перебираем номера томов (начнем с v1 и дойдем до v300)
    for volume_num in range(1, 301):
        volume_url = f"https://proceedings.mlr.press/v{volume_num}/"
        
        try:
            print(f"Проверяю том v{volume_num}...", end=" ")
            response = requests.get(volume_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('title')
                
                if title:
                    title_text = title.get_text().lower()
                    if 'conference on robot learning' in title_text:
                        print("✓ НАЙДЕН CoRL!")
                        corl_volumes.append((volume_num, volume_url, title.get_text()))
                    else:
                        print("не CoRL")
                else:
                    print("нет заголовка")
            else:
                print(f"ошибка {response.status_code}")
                
            # Небольшая задержка между запросами
            time.sleep(0.1)
            
        except Exception as e:
            print(f"ошибка: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ПОИСКА CoRL:")
    
    if corl_volumes:
        for volume_num, url, title in corl_volumes:
            print(f"✓ Том v{volume_num}: {title}")
            print(f"  URL: {url}")
            print()
    else:
        print("Тома CoRL не найдены")
    
    print(f"Всего проверено томов: 300")
    print(f"Найдено томов CoRL: {len(corl_volumes)}")

if __name__ == "__main__":
    scan_all_volumes()
