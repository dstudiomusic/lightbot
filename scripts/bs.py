import requests
from bs4 import BeautifulSoup
import os


def parse_docs(urls, output_dir):
    """
    Парсит документацию с указанных URL и сохраняет в файлы.

    Args:
        urls (list): Список URL-адресов для парсинга.
        output_dir (str): Путь к директории для сохранения файлов.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Извлекаем текст документации
        content = soup.get_text()

        # Определяем имя файла на основе URL
        filename = os.path.join(output_dir, f"{url.split('/')[-1]}.md")

        # Сохраняем в файл
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)


# Пример использования
urls = [
    'https://example.com/docs/avolites-titan',
    'https://example.com/docs/grandma-manual',
    'https://example.com/docs/hog-user-guide'
]
parse_docs(urls, 'docs/')
