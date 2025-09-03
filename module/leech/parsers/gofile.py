import time
import httpx
from urllib.parse import urlparse
from module.i18n.services.i18n_manager import I18nManager

from tool.utils import get_redis_unique_key
from config.config import BOT_DOWNLOAD_LOCATION
from tool.user_agents import get_random_user_agent
from module.leech.beans.leech_file import LeechFile
from module.leech.interfaces.parser import IParser
from module.leech.beans.leech_gofile_file import LeechGofileFile
from module.leech.decorators.parse import catch_parse_exception, create_document


class Gofile(IParser):
    def __init__(self):
        self.token = None
        self.expire_at = 0

    def parse_link_filter(self, link: str) -> bool:
        return 'gofile' in link

    @catch_parse_exception
    @create_document
    def parse_link(self, link: str, **kwargs) -> list[LeechFile]:
        parse_result = urlparse(link)
        password = getattr(kwargs, 'password', None)
        links = []

        if self.token is None or time.time() > self.expire_at:
            token, expire_at = get_token()
            self.token = token
            self.expire_at = expire_at

        response = httpx.get(''.join([
            'https://api.gofile.io/contents/',
            parse_result.path.replace('/d/', ''),
            '?wt=4fd6sg89d7s6&cache=true',
            f'&password={password}' if password else ''
        ]), headers={
            'User-Agent': get_random_user_agent(),
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Authorization': f'Bearer {self.token}'
        }).json()

        if response['status'] != 'ok':
            return []

        data = response['data']

        if data['type'] == 'folder':
            children = data['children']

            for child_id in list(children.keys()):
                child = children[child_id]

                if child['type'] == 'folder' and child['canAccess']:
                    links.extend(self.parse_link(child['id'], token=self.token, password=password))

                elif child['type'] == 'file':
                    leech_file = LeechGofileFile(
                        link=child['link'],
                        name=child['name'],
                        remote_folder=data['name'],
                        token=self.token
                    )
                    leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'
                    links.append(leech_file)
        else:
            leech_file = LeechGofileFile(
                link=data['link'],
                name=data['name'],
                token=self.token
            )
            leech_file.location = f'{BOT_DOWNLOAD_LOCATION}/{get_redis_unique_key(leech_file)}'
            links.append(leech_file)

        return links


# I18nManager().translate('leech.prompt.token_acquisition')
def get_token() -> (str, int):
    response = httpx.post('https://api.gofile.io/accounts', headers={
        'User-Agent': get_random_user_agent(),
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': '*/*',
        'Connection': 'keep-alive',
    }).json()

    return '' if response['status'] != 'ok' else response['data']['token'], int(time.time()) + 60 * 60


instance = Gofile()

parse_link_filter = instance.parse_link_filter
parse_link = instance.parse_link
