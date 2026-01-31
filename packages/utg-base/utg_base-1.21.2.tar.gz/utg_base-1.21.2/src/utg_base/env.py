import os
import typing
from functools import wraps

import dotenv
import hvac
from django.conf import settings
from environs import Env, _StrType, EnvError

dotenv.load_dotenv(settings.BASE_DIR / '.env')

assert os.environ.get('VAULT_URL') is not None, "VAULT_URL not defined, please set VAULT_URL on .env file"
assert os.environ.get('VAULT_TOKEN') is not None, "VAULT_TOKEN not defined, please set VAULT_TOKEN on .env file"
assert os.environ.get('VAULT_PATH') is not None, "VAULT_PATH not defined, please set VAULT_PATH on .env file"

client = hvac.Client(
    url=os.environ.get("VAULT_URL"),
    token=os.environ.get("VAULT_TOKEN"),
    verify=False
)
if not client.is_authenticated():
    raise Exception("Vault authentication failed")

envs = client.secrets.kv.read_secret_version(
    path=os.environ.get("VAULT_PATH"),
    mount_point="utg-scada"
)['data']['data']


class VaultEnv(Env):
    _wrap_methods = {
        'int', 'bool', 'str', 'float', 'decimal',
        'list', 'dict', 'json',
        'datetime', 'date', 'time', 'timedelta',
        'path', 'log_level', 'uuid', 'url', 'enum',
        'dj_db_url', 'dj_email_url', 'dj_cache_url'
    }

    def __call__(self, key, default=None, **kwargs):
        try:
            return super().__call__(key, default=default, **kwargs)
        except EnvError:
            return default

    def __getattribute__(self, name):
        attr = super().__getattribute__(name)

        if callable(attr) and name in self._wrap_methods:
            @wraps(attr)
            def wrapper(*args, **kwargs):
                if len(args) < 2:
                    kwargs.setdefault("default", None)
                return attr(*args, **kwargs)

            return wrapper

        return attr

    def _get_value(self, env_key: _StrType, default: typing.Any) -> typing.Any:
        if env_key in os.environ:
            return os.environ.get(env_key, default)
        else:
            return envs.get(env_key, default)


env = VaultEnv()
