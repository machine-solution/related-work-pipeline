#!/usr/bin/env python3
import requests

# Скачиваем RSS20 страницу
url = 'https://www.roboticsproceedings.org/rss20/index.html'
response = requests.get(url)
response.encoding = 'utf-8'

# Сохраняем в файл
with open('rss20_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print(f'Страница сохранена в rss20_page.html')
print(f'Размер: {len(response.text)} символов')
print(f'Кодировка: {response.encoding}')
