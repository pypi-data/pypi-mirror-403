import requests


def is_accessible(
    url,
    timeout: int = 3,
) -> bool:
    try:
        response = requests.get(
            url,
            timeout=timeout,
        )
        return response.status_code == 200
    except:
        return False
