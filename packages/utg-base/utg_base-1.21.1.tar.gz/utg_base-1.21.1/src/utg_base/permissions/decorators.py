from functools import wraps
from typing import Literal, Dict, Union, List

from rest_framework.exceptions import PermissionDenied

from .utils import has_perms as has_permissions


def has_perm(*permission: str, operator: Literal["OR", "AND"] = "OR"):
    """
    Usage:
        has_perm('PERM1')
        has_perm('PERM1', 'PERM2')

    :param permission: One or many permissions.
    """
    def decorator(view_func):
        view_func._perms = permission
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            if not has_permissions(user_id=request.user.id, perms=list(permission), operator=operator, request=request):
                self.permission_denied(request)
            return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator


def has_class_perm(permissions_map: Dict[str, Union[str, List[str]]], operator: Literal["OR", "AND"] = "OR"):
    """
    Usage:
        @has_class_perm({
            'list': ['perm1', 'perm2'],
            'create': 'perm3',
            'update': ['perm4']
        })
    """
    def decorator(cls):
        for action, perms in permissions_map.items():
            if isinstance(perms, str):
                perms = [perms]

            if hasattr(cls, action):
                method = getattr(cls, action)
                setattr(method, "_perms", perms)
        original_initial = cls.initial

        @wraps(original_initial)
        def new_initial(self, request, *args, **kwargs):
            action = getattr(self, 'action', None) or request.method.lower()

            if action in permissions_map:
                required_perms = permissions_map[action]

                if isinstance(required_perms, str):
                    required_perms = [required_perms]

                if not has_permissions(user_id=request.user.id, perms=required_perms, operator=operator, request=request):
                    self.permission_denied(request)

            return original_initial(self, request, *args, **kwargs)

        cls.initial = new_initial
        return cls

    return decorator
