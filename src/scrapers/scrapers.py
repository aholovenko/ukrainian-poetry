import argparse
import time
import json
import os
import gzip
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool

BASE_URL = 'https://virshi.com.ua'


def find_author_links(author_name, soup):
    return [link.get('href', '') for link in soup.find_all('a') if author_name in link.get('href', '')]


def get_request(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    source = requests.get(url, headers=headers)
    if not source.ok:
        raise StopIteration
    return source


def get_soup(source):
    return BeautifulSoup(source.text, 'html.parser')


def get_author_links(url, author_name):
    all_links = []
    for page_num in range(1, 100):
        if page_num > 1:
            url += f'page/{page_num}/'
        try:
            source = get_request(url)
        except StopIteration:
            break
        soup = get_soup(source)
        all_links += find_author_links(author_name, soup)
    print(f'Found {len(all_links)} links for {author_name}.')
    return all_links


def scrape_author(author_name):
    base_url = f'{BASE_URL}/{author_name}/'
    all_links = get_author_links(base_url, author_name)
    all_texts = []
    for poem_link in all_links:
        if poem_link.startswith(base_url) or poem_link.startswith(base_url + 'page/'):
            continue
        source = get_request(poem_link)
        soup = get_soup(source)
        if not soup:
            print('break1', poem_link)
            continue
        text_div = soup.find("div", {"class": "poem-text"})
        if not text_div:
            print('break2', poem_link)
            continue
        text_paragraphs = text_div.find_all('p')
        text = '\n'.join([p.text for p in text_paragraphs])
        poem_json = {
            'author': author_name,
            'source_link': poem_link,
            'title': poem_link.split('/')[-2],
            'text': text,
        }
        all_texts.append(poem_json)
    print(f'Found {len(all_texts)} texts for {author_name}.')
    return all_texts


def save_author_file(author_name, output_dir='output'):
    os.makedirs(output_dir, exist_ok=True)
    all_texts = scrape_author(author_name)
    with open(os.path.join(output_dir, f'{author_name}.json'), 'w') as output_file:
        json.dump(all_texts, output_file)
    print(f'Finished writing file for {author_name} with {len(all_texts)} items.')
    return all_texts


def write_author_files(authors, output_dir):
    with Pool() as pool:
        pool.starmap(save_author_file, [(author_name, output_dir) for author_name in authors])


def write_poems_file(output_file, output_dir):
    poems = []
    for author_file in os.listdir(output_dir):
        poems += json.load(open(os.path.join(output_dir, author_file)))
    output_file_path = os.path.join(output_dir, output_file)
    with gzip.open(output_file_path, 'wt') as output_file:
        for ukrainian_poem in poems:
            output_file.write(json.dumps(ukrainian_poem) + '\n')
    print(f'Finished writing file for ukrainian_poems with {len(poems)} items.')


def main():
    t0 = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_dir', dest='output_dir', type=str, default='data')
    parser.add_argument('-f', '--output_file', dest='output_file', type=str, default='ukrainian_poems.json.gz')
    parser.add_argument('-a', '--authors', dest='authors', type=json.loads, default=None)
    args = parser.parse_args()
    output_dir = args.output_dir
    output_file = args.output_file
    authors = args.authors or [
        'taras-shevchenko', 'ivan-franko', 'lesya-ukrayinka', 'lina-kostenko',
        'vasyl-symonenko', 'volodymyr-sosyura', 'maksym-rylskyj', 'vasyl-stus',
        'leonid-glibov', 'oleksandr-oles', 'pavlo-tychyna', 'pavlo-glazovyj',
        'grygorij-skovoroda'
    ]
    write_author_files(authors, output_dir)
    write_poems_file(output_file, output_dir)
    print(f'Took {(time.time() - t0)}//60 mins')


if __name__ == '__main__':
    main()
