from requests import Response


# noinspection PyDecorator
@staticmethod
def call_processor(response: Response):
    try:
        data = response.json()
    except Exception as e:
        data = response.text
    return {
        'status': response.status_code,
        'reason': response.reason,
        'response': data,
    }


# noinspection PyDecorator
@staticmethod
def data_processor(response: Response):
    try:
        data = response.json()
    except Exception as e:
        raise Exception({
            'status': response.status_code,
            'reason': response.reason,
            'response': response.text,
            'exception': str(e)
        })

    return data
