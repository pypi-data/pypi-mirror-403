import requests
from rest_framework.request import Request

from .constants import UServices
from .models import UService


def u_request(
        method: str,
        request: Request,
        u_service: UServices,
        prefix: str,
        params: dict = None,
        data: dict | list = None
):
    headers = {
        'Authorization': request.headers.get('Authorization'),
        'Accept-Language': request.headers.get('Accept-Language'),
    }
    return requests.request(
        method=method,
        url=UService.get_by_name(u_service.value).get_url(prefix),
        params=params,
        json=data,
        headers=headers,
    )


def get(request: Request, u_service: UServices, prefix: str, params: dict = None):
    return u_request(method='get', request=request, u_service=u_service, prefix=prefix, params=params)


def post(request: Request, u_service: UServices, prefix: str, params: dict = None, data: dict | list = None):
    return u_request(method='post', request=request, u_service=u_service, prefix=prefix, params=params, data=data)


def put(request: Request, u_service: UServices, prefix: str, params: dict = None, data: dict | list = None):
    return u_request(method='put', request=request, u_service=u_service, prefix=prefix, params=params, data=data)


def patch(request: Request, u_service: UServices, prefix: str, params: dict = None, data: dict | list = None):
    return u_request(method='patch', request=request, u_service=u_service, prefix=prefix, params=params, data=data)


def delete(request: Request, u_service: UServices, prefix: str, params: dict = None):
    return u_request(method='delete', request=request, u_service=u_service, prefix=prefix, params=params)
