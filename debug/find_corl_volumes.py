#!/usr/bin/env python3
"""
Поиск томов CoRL (Conference on Robot Learning) в архиве MLR
"""

import requests
from bs4 import BeautifulSoup
import re

def find_corl_volumes():
    """Ищем все тома CoRL в архиве MLR"""
    
    print("Ищу тома CoRL в архиве MLR...")
    print("=" * 60)
    
    # Главная страница архива
    main_url = "https://proceedings.mlr.press/"
    
    try:
        response = requests.get(main_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем все ссылки на тома
        volume_links = soup.find_all('a', href=True)
        
        corl_volumes = []
        
        for link in volume_links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Ищем ссылки на тома (обычно /vXXX/)
            if href and re.match(r'/v\d+/', href):
                # Проверяем, есть ли в тексте "Conference on Robot Learning"
                if 'conference on robot learning' in text.lower():
                    corl_volumes.append((href, text))
                    print(f"✓ Найден том CoRL: {text}")
                    print(f"   Ссылка: {href}")
        
        if not corl_volumes:
            print("Тома CoRL не найдены на главной странице")
            print("Попробую другой подход...")
            
            # Ищем в тексте страницы упоминания CoRL
            page_text = soup.get_text()
            corl_matches = re.findall(r'Conference on Robot Learning[^.]*', page_text, re.IGNORECASE)
            
            if corl_matches:
                print(f"Найдены упоминания CoRL в тексте:")
                for match in corl_matches[:5]:
                    print(f"  - {match.strip()}")
            else:
                print("CoRL не найден в тексте главной страницы")
        
        print(f"\nВсего найдено томов CoRL: {len(corl_volumes)}")
        
        # Если нашли тома, показываем детали первого
        if corl_volumes:
            first_volume = corl_volumes[0]
            print(f"\nДетали первого тома:")
            print(f"Ссылка: {main_url.rstrip('/')}{first_volume[0]}")
            print(f"Название: {first_volume[1]}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    find_corl_volumes()
