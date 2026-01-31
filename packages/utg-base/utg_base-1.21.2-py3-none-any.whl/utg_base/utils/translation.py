import requests
from django.utils.translation import get_language

from utg_base.constants import AVAILABLE_LANGUAGES
from utg_base.env import env


def translate(key: str) -> str:
    base_url = env('TRANSLATION_SERVICE_URL')
    lang = get_language()
    if lang == 'uz-cyr':
        lang = 'crl'
    if lang not in AVAILABLE_LANGUAGES:
        lang = 'ru'
    return requests.get(f'{base_url}/api/translations/{key}', params={
        'lang': lang
    }).text
