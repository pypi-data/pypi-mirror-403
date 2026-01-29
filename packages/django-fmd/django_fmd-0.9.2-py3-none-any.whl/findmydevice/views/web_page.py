import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.static import serve

from findmydevice import WEB_PATH


logger = logging.getLogger(__name__)


class FmdWebPageView(LoginRequiredMixin, View):
    def get(self, request):
        # Note: In real deployment, this is served by the web server directly.
        logger.debug('Serve FMD index.html')
        return serve(request, path='/index.html', document_root=WEB_PATH, show_indexes=False)

    def handle_no_permission(self):
        logger.info('User not logged in, redirect to login page')
        return super().handle_no_permission()
