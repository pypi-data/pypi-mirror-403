from django.middleware.locale import LocaleMiddleware as DjangoLocaleMiddleware
from django.utils import translation

from utg_base.constants import AVAILABLE_LANGUAGES


class LocaleMiddleware(DjangoLocaleMiddleware):
    def process_request(self, request):
        if lang_from_header := request.headers.get('accept-language'):
            if lang_from_header and lang_from_header not in AVAILABLE_LANGUAGES:
                lang_from_header = 'ru'
        translation.activate(lang_from_header)
        request.LANGUAGE_CODE = translation.get_language()
