"""
    Will be called from "update_fmdserver_files.sh"
"""
import inspect
from pathlib import Path

from bs4 import BeautifulSoup
from bx_py_utils.path import assert_is_dir, assert_is_file

import findmydevice


BASE_PATH = Path(findmydevice.__file__).parent
assert_is_dir(BASE_PATH)

FMD_WEB_PATH = BASE_PATH / 'web'
assert_is_dir(FMD_WEB_PATH)

EXTERNAL_DIR_NAME = 'fmd_externals'
STATIC_EXTERNAL_PATH = BASE_PATH / 'static' / EXTERNAL_DIR_NAME
assert_is_dir(STATIC_EXTERNAL_PATH)

# TODO: https://gitlab.com/jedie/django-find-my-device/-/issues/7
STATIC_URL_PREFIX = f'static/{EXTERNAL_DIR_NAME}'


class FilePatcher:
    def __init__(self, file_path: Path):
        print('_' * 100)
        assert_is_file(file_path)
        self.file_path = file_path

    def __enter__(self):
        self.content = self.file_path.read_text(encoding='utf-8')
        return self

    def patch(self, old, new):
        if old not in self.content:
            print(f'Warning: {old!r} not found in "{self.file_path}" !')
        elif new not in self.content:
            self.content = self.content.replace(old, new)

    def patch_urls(self, url_patcher):
        soup = BeautifulSoup(self.content, 'html.parser')

        pachted = set()

        for tag in soup.find_all(href=True):
            old_url = tag['href']
            if old_url in pachted:
                continue
            pachted.add(old_url)
            if new_url := url_patcher(old_url):
                if new_url != old_url:
                    print(f'Patching URL: {old_url!r} -> {new_url!r}')
                    self.content = self.content.replace(old_url, new_url)

        for tag in soup.find_all(src=True):
            old_url = tag['src']
            if old_url in pachted:
                continue
            pachted.add(old_url)
            if new_url := url_patcher(old_url):
                if new_url != old_url:
                    print(f'Patching URL: {old_url!r} -> {new_url!r}')
                    self.content = self.content.replace(old_url, new_url)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            raise
        self.file_path.write_text(self.content, encoding='utf-8')
        print(f' *** {self.file_path} patched ***')
        print('-' * 100)


def patch_html_files():
    def url_patcher(old_url: str) -> str | None:
        if '://' in old_url:
            # Don't change absolute URLs
            return None
        if old_url.startswith(f'./{STATIC_URL_PREFIX}/'):
            # Already patched
            return None
        return f'./{STATIC_URL_PREFIX}/{old_url}'

    for file_path in FMD_WEB_PATH.glob('*.html'):
        with FilePatcher(file_path=file_path) as patcher:
            patcher.patch(
                'https://gitlab.com/fmd-foss/fmd-server/',
                'https://gitlab.com/jedie/django-find-my-device',
            )

            # It's not the original FMD Server:
            patcher.patch('<title>FMD</title>', '<title>Django Find My Device</title>')
            patcher.patch('<title>FMD Server</title>', '<title>Django Find My Device</title>')

            patcher.patch_urls(url_patcher)

            patcher.patch(
                'FMD Server</h2>',
                inspect.cleandoc("""\
                    Django Find My Device</h2>
                    <p class="center-column"><a href="/admin/">Go into Django Admin</a></p>
                """),
            )


def patch_js_files():
    with FilePatcher(file_path=STATIC_EXTERNAL_PATH / 'node_modules/argon2-browser/lib/argon2.js') as patcher:
        patcher.patch("'node_modules/", f"'./{STATIC_URL_PREFIX}/node_modules/")


def create_config_js():
    """
    The origin FMD Server creates a "config.js" dynamically.
    """
    config_js_path = STATIC_EXTERNAL_PATH / 'config.js'
    config_js_path.write_text(
        inspect.cleandoc("""
            /* js config creatred by update_fmdserver_files.py */
            const tileServerUrl = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
        """)
    )
    print(f' *** {config_js_path} created ***')


if __name__ == '__main__':
    patch_html_files()
    patch_js_files()
    create_config_js()
