import os
import shutil
import subprocess
from pathlib import Path

from bx_py_utils.path import assert_is_file
from cli_base.cli_tools.code_style import assert_code_style
from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from manageprojects.test_utils.project_setup import check_editor_config, get_py_max_line_length
from packaging.version import Version

import findmydevice
from findmydevice import __version__
from manage import BASE_PATH


PACKAGE_ROOT = Path(findmydevice.__file__).parent.parent


def assert_file_contains_string(file_path, string):
    with file_path.open('r') as f:
        for line in f:
            if string in line:
                return
    raise AssertionError(f'File {file_path} does not contain {string!r} !')


def test_version(package_root=None, version=None):
    if package_root is None:
        package_root = PACKAGE_ROOT

    if version is None:
        version = findmydevice.__version__

    if 'dev' not in version and 'rc' not in version:
        version_string = f'v{version}'

        assert_file_contains_string(
            file_path=Path(package_root, 'README.md'), string=version_string
        )

    assert_file_contains_string(
        file_path=Path(package_root, 'pyproject.toml'), string=f'version = "{version}"'
    )


def test_poetry_check(package_root=None):
    if package_root is None:
        package_root = PACKAGE_ROOT

    poerty_bin = shutil.which('poetry')

    output = subprocess.check_output(
        [poerty_bin, 'check'],
        text=True,
        env=os.environ,
        stderr=subprocess.STDOUT,
        cwd=str(package_root),
    )
    print(output)
    assert output == 'All set!\n'


class ProjectSettingsTestCase(TestCase):
    def test_base_path(self):
        base_path = settings.BASE_PATH
        assert base_path.is_dir()
        assert Path(base_path, 'findmydevice').is_dir()
        assert Path(base_path, 'findmydevice_project').is_dir()

    def test_template_dirs(self):
        assert len(settings.TEMPLATES) == 1
        dirs = settings.TEMPLATES[0].get('DIRS')
        assert len(dirs) == 1
        template_path = Path(dirs[0]).resolve()
        assert template_path.is_dir()

    def test_cache(self):
        # django cache should work in tests, because some tests "depends" on it
        cache_key = 'a-cache-key'
        self.assertIs(cache.get(cache_key), None)
        cache.set(cache_key, 'the cache content', timeout=1)
        self.assertEqual(cache.get(cache_key), 'the cache content', f'Check: {settings.CACHES=}')
        cache.delete(cache_key)
        self.assertIs(cache.get(cache_key), None)

    def test_settings(self):
        self.assertEqual(settings.SETTINGS_MODULE, 'findmydevice_project.settings.tests')
        middlewares = [entry.rsplit('.', 1)[-1] for entry in settings.MIDDLEWARE]
        assert 'AlwaysLoggedInAsSuperUserMiddleware' not in middlewares
        assert 'DebugToolbarMiddleware' not in middlewares

    def test_version(self):
        self.assertIsNotNone(__version__)

        version = Version(__version__)  # Will raise InvalidVersion() if wrong formatted
        self.assertEqual(str(version), __version__)

        manage_bin = BASE_PATH / 'manage.py'
        assert_is_file(manage_bin)

        output = subprocess.check_output([manage_bin, 'version'], text=True)
        self.assertIn(__version__, output)

    def test_manage(self):
        manage_bin = BASE_PATH / 'manage.py'
        assert_is_file(manage_bin)

        output = subprocess.check_output([manage_bin, 'project_info'], text=True)
        self.assertIn('findmydevice_project', output)
        self.assertIn('findmydevice_project.settings.local', output)
        self.assertIn('findmydevice_project.settings.tests', output)
        self.assertIn(__version__, output)

        output = subprocess.check_output([manage_bin, 'check'], text=True)
        self.assertIn('System check identified no issues (0 silenced).', output)

        output = subprocess.check_output([manage_bin, 'makemigrations'], text=True)
        self.assertIn("No changes detected", output)

    def test_code_style(self):
        return_code = assert_code_style(package_root=BASE_PATH)
        self.assertEqual(return_code, 0, 'Code style error, see output above!')

    def test_check_editor_config(self):
        check_editor_config(package_root=BASE_PATH)

        max_line_length = get_py_max_line_length(package_root=BASE_PATH)
        self.assertEqual(max_line_length, 119)
