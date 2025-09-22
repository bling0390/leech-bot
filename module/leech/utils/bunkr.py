import json
import base64
import operator
import math
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from httpx import Response, _status_codes

from tool.utils import get_redis_unique_key
from tool.user_agents import get_random_user_agent
from config.config import BOT_DOWNLOAD_LOCATION, BUNKR_DOMAIN
from module.leech.beans.leech_bunkr_file import LeechBunkrFile


def get_video_link(soup: BeautifulSoup) -> str:
    if soup.find('video', {'id': 'player'}) is not None:
        return soup.css.select_one("video#player source").get('src')

    return ''


def get_video_links(soup: BeautifulSoup) -> list[str]:
    if soup.find('div', 'relative group/item theItem') is not None:
        return list(map(lambda x: x['href'], soup.css.select("div.theItem a")))

    elif soup.find('a', 'grid-images_box-link') is not None:
        return list(map(lambda x: x['href'], soup.css.select("a.grid-images_box-link")))

    return []


def get_folder_name(soup: BeautifulSoup) -> str:
    if soup.find('h1', {'class': 'truncate'}) is not None:
        return soup.css.select_one('h1.truncate').text

    elif soup.find('h1', {'class': 'text-[20px]'}) is not None:
        return soup.css.select_one('h1.text-[20px]').text

    elif soup.find('h1', {'class': 'text-[24px]'}) is not None:
        return soup.css.select_one('h1.text-[24px]').text

    return ''


def decrypt_link(encrypted_url: str, timestamp: int) -> str:
    char_codes = list(bytes(base64.b64decode(encrypted_url)))

    secret_key_codes = list(bytearray(f'SECRET_KEY_{math.floor(timestamp / 3600)}'.encode('utf-8')))

    return bytearray(list(map(
        lambda x: operator.xor(char_codes[x], secret_key_codes[x % len(secret_key_codes)]),
        range(len(char_codes))
    ))).decode('utf-8')


def parse_bunkr_link(link: str, **kwargs) -> list[LeechBunkrFile]:
    leech_files = []
    parse_result = urlparse(link)
    r: Response = httpx.get(f'{parse_result.scheme}://{BUNKR_DOMAIN}{parse_result.path}')

    if r.status_code != _status_codes.codes.OK:
        return leech_files

    soup = BeautifulSoup(r.text, 'html.parser')
    folder_name = get_folder_name(soup)

    if '/a/' in parse_result.path:
        for video_link in get_video_links(soup):
            parsed_video_link = urlparse(video_link)

            leech_files.append(
                LeechBunkrFile(
                    link=f'{parse_result.scheme}://{BUNKR_DOMAIN}{parsed_video_link.path}',
                    remote_folder=folder_name
                )
            )
    elif '/v/' in parse_result.path:
        actual_link_response = httpx.post(
            f'{parse_result.scheme}://{BUNKR_DOMAIN}/api/gimmeurl',
            content=json.dumps({'slug': parse_result.path.split('/')[-1]}),
            headers={
                'Content-Type': 'application/json',
                'Referer': f'{parse_result.scheme}://{BUNKR_DOMAIN}{parse_result.path}',
                'User-Agent': get_random_user_agent()
            }
        ).json()

        leech_file = LeechBunkrFile(
            name=folder_name,
            link=link,
            actual_link=actual_link_response['data']['newUrl'],
            remote_folder=folder_name
        )

        leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'
        leech_files.append(leech_file)
    elif '/f/' in parse_result.path:
        video_link = get_video_link(soup)

        if not video_link:
            encrypted_link_response = httpx.post(
                f'{parse_result.scheme}://{BUNKR_DOMAIN}/api/vs',
                content=json.dumps({'slug': parse_result.path.split('/')[-1]}),
                headers={
                    'Content-Type': 'application/json',
                    'Referer': f'{parse_result.scheme}://{BUNKR_DOMAIN}{parse_result.path}',
                    'User-Agent': get_random_user_agent()
                }
            ).json()

            video_link = decrypt_link(
                encrypted_link_response['url'],
                encrypted_link_response['timestamp']
            )

        if not video_link and soup.find('a', 'ic-download-01') is not None:
            video_link = BeautifulSoup(
                httpx.get(soup.css.select_one('a.ic-download-01').get('href')).text,
                'html.parser'
            ).css.select_one('a.ic-download-01').get('href')

        leech_file = LeechBunkrFile(
            name=folder_name,
            link=link,
            actual_link=video_link,
            remote_folder=folder_name
        )

        leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'
        leech_files.append(leech_file)

    return leech_files
