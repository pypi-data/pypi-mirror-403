from itertools import count
from unittest.mock import MagicMock, patch

from django.template.defaulttags import CsrfTokenNode


class MocksBase:
    mocks = None  # Should be set in __init__ !

    def __enter__(self):
        assert self.mocks
        for mock in self.mocks:
            mock.__enter__()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for mock in self.mocks:
            mock.__exit__(exc_type, exc_val, exc_tb)


class DefaultMocks(MocksBase):
    def __init__(self):
        version_mock = MagicMock()
        version_mock.__str__.return_value = 'MockedVersion'
        self.mocks = [
            patch.object(CsrfTokenNode, 'render', return_value='MockedCsrfTokenNode'),
            # patch.object(context_processors, '__version__', new=version_mock),
        ]


class ShortIdGenerator:
    def __init__(self, ids: list):
        self.ids = ids
        self._pos = count(start=0)

    def __call__(self):
        try:
            return self.ids[next(self._pos)]
        except IndexError:
            return self.ids[-1]
