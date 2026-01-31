from typing import Literal

from django_redis import get_redis_connection
from redis.client import Redis


def generate_folder_cache_key(user_id: str):
    return f"user:{user_id}:folders"


def has_folder_perm(user_id, folder_perm):
    redis_conn: Redis = get_redis_connection("shared")
    return bool(redis_conn.sismember(generate_folder_cache_key(user_id), folder_perm))


def has_folder_perms(user_id: str, folder_perms: list[str], operator: Literal["OR", "AND"] = "OR"):
    redis_conn: Redis = get_redis_connection("shared")
    result = redis_conn.smismember(generate_folder_cache_key(user_id), folder_perms)

    if operator == "OR":
        return any(result)
    return all(result)
