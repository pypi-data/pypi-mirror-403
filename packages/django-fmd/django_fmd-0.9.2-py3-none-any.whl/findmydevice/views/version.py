from django.http import HttpResponse
from django.views import View

import findmydevice


class VersionView(View):
    def get(self, request):
        return HttpResponse(f'v{findmydevice.__version__} (Django Find My Device)')
