import hashlib
import pickle
import re
import zlib
from urllib.parse import urljoin

import MySQLdb
import bs4
import requests

conn = MySQLdb.connect(host='127.0.0.1', port=3306,
                       user='root', password='root',
                       database='vote', charset='utf8',
                       autocommit=True)


def write_to_db(url, page, digest):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'insert into tb_explore (url, page, digest) values (%s, %s, %s) ',
                (url, page, digest)
            )
    except MySQLdb.MySQLError as err:
        print(err)


def main():
    base_url = 'https://www.zhihu.com/'
    seed_url = urljoin(base_url, 'explore')
    headers = {'user-agent': 'Baiduspider'}
    try:
        resp = requests.get(seed_url, headers=headers)
        soup = bs4.BeautifulSoup(resp.text, 'lxml')
        href_regex = re.compile(r'^/question')
        for a_tag in soup.find_all('a', {'href': href_regex}):
            href = a_tag.attrs['href']
            full_url = urljoin(base_url, href)
            digest = hashlib.sha1(full_url.encode()).hexdigest()
            html_page = requests.get(full_url, headers=headers).text
            zipped_page = zlib.compress(pickle.dumps(html_page))
            write_to_db(full_url, zipped_page, digest)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
