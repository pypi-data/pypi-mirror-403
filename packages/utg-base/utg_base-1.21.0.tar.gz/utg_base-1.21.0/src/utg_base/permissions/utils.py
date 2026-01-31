import traceback
from typing import Literal

from django.http import HttpRequest
from django.urls import URLResolver, URLPattern, get_resolver
from django_redis import get_redis_connection
from redis.client import Redis
from rest_framework.request import Request

from utg_base.constants import AccessibilityType
from utg_base.env import env
from utg_base.u_services import u_requests
from utg_base.u_services.constants import UServices
from utg_base.utils import to_snake_case
from utg_base.utils.data import safe_get


def generate_perm_cache_key(user_id: str):
    return f"user:{user_id}:permissions"


def has_perm(user_id, perm, request=None):
    if (request is not None and isinstance(request, Request)
            and (request.user.is_superuser or safe_get(request, 'user.accessibility') == AccessibilityType.ADMIN)):
        return True
    redis_conn: Redis = get_redis_connection("shared")
    perm = f"{to_snake_case(env('APP_NAME'))}:{perm}"
    return bool(redis_conn.sismember(generate_perm_cache_key(user_id), perm))


def has_perms(user_id: str, perms: list[str], operator: Literal["OR", "AND"] = "OR", request=None):
    if (request is not None and isinstance(request, Request)
            and (request.user.is_superuser or safe_get(request, 'user.accessibility') == AccessibilityType.ADMIN)):
        return True
    redis_conn: Redis = get_redis_connection("shared")
    perms = [f"{to_snake_case(env('APP_NAME'))}:{perm}" for perm in perms]
    result = redis_conn.smismember(generate_perm_cache_key(user_id), perms)

    if operator == "OR":
        return any(result)
    return all(result)


def get_user_perms(user_id: str):
    redis_conn: Redis = get_redis_connection("shared")
    perms = redis_conn.smembers(generate_perm_cache_key(user_id))
    return [perm.decode() for perm in perms]


def get_permissions(url_patterns):
    permissions = set()

    for item in url_patterns:
        if isinstance(item, URLPattern):
            view = item.callback

            view_cls = safe_get(view, 'view_class')
            # for View
            if view_cls:
                for method_name in ["get", "post", "put", "patch", "delete"]:
                    perms = safe_get(view_cls, f'{method_name}._perms', set())
                    permissions.update(perms)
            # for ViewSet
            else:
                view_cls = safe_get(view, 'cls')
                actions: dict = safe_get(view, 'actions', {})
                for method_name in actions.values():
                    perms = safe_get(view_cls, f'{method_name}._perms', set())
                    permissions.update(perms)

        elif isinstance(item, URLResolver):
            permissions.update(get_permissions(
                item.url_patterns
            ))

    return permissions


def sync_permissions():
    resolver = get_resolver()
    perm_codes = list(get_permissions(resolver.url_patterns))

    request = Request(HttpRequest())
    try:
        response = u_requests.post(request, UServices.USER_MANAGEMENT, '/api/permissions/', data={
            "service": to_snake_case(env('APP_NAME')),
            "codes": perm_codes
        })
        print('[INFO] sync_permissions:', response.json())
    except Exception as e:
        traceback.print_exc()
