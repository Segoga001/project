import os
import requests
from bs4 import BeautifulSoup

from models.database import init_db, service


async def create_db_cities():
    """Инициализация базы данных с городами России из википедии"""

    await init_db()

    url = 'https://ru.wikipedia.org/wiki/Список_городов_России'
    response = requests.get(url)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {'class': 'standard sortable'})
    rows = table.find_all('tr')[1:]
    cities = []
    for row in rows:
        cells = row.find_all('td')
        city = cells[2].text.strip()
        if city[-1] != 'ь':
            cities.append(city.lower())
    for c in set(cities):
        await service.insert_db(c)


async def print_cities():
    s = await service.get_cities()
    print(s)


async def initialize():
    if not os.path.exists('first_run.txt'):
        # Если файл first_run.txt не существует, то это первый запуск
        await create_db_cities()
        # Создаем файл first_run.txt, чтобы пометить, что скрипт уже был выполнен
        with open('first_run.txt', 'w'):
            pass

