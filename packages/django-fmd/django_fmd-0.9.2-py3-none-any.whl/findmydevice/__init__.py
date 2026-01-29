"""
    created 04.07.2022 by Jens Diemer <opensource@jensdiemer.de>
    :copyleft: 2022 by the django-fmd team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


from pathlib import Path

from bx_py_utils.path import assert_is_dir


__version__ = '0.9.2'
__author__ = 'Jens Diemer <git@jensdiemer.de>'


WEB_PATH = Path(__file__).parent / 'web'
assert_is_dir(WEB_PATH)
