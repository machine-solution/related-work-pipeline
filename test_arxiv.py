#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы с arXiv
"""

import requests
from bs4 import BeautifulSoup

def test_arxiv_search():
    # Используем точно такой же запрос как в рабочем примере
    url = 'https://arxiv.org/search/?query=Constraint-based+Task+Specification+and+Trajectory+Optimization+for+Sequential+Manipulation&searchtype=all&abstracts=show&order=-announced_date_first&size=50'
    
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
    
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('li', class_='arxiv-result')
            print(f'Найдено результатов: {len(results)}')
            
            if results:
                for i, result in enumerate(results[:3]):
                    title_elem = result.find('p', class_='title')
                    if title_elem:
                        title_link = title_elem.find('a')
                        if title_link:
                            title = title_link.get_text(strip=True)
                            print(f'{i+1}. {title[:80]}...')
        else:
            print('Ошибка:', response.text[:200])
            
    except Exception as e:
        print(f'Ошибка: {e}')

if __name__ == "__main__":
    test_arxiv_search()
