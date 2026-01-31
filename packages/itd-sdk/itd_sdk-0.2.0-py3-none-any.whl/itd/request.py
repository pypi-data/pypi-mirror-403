from requests import Session

s = Session()


def fetch(token: str, method: str, url: str, params: dict = {}, files: dict[str, tuple[str, bytes]] = {}):
    base = f'https://xn--d1ah4a.com/api/{url}'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Authorization": 'Bearer ' + token,
        "Sec-GPC": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }
    method = method.lower()
    if method == "get":
        res = s.get(base, timeout=120 if files else 20, params=params, headers=headers)
    else:
        res = s.request(method.upper(), base, timeout=20, json=params, headers=headers, files=files)

    res.raise_for_status()
    return res.json()

def set_cookies(cookies: str):
    for cookie in cookies.split('; '):
        s.cookies.set(cookie.split('=')[0], cookie.split('=')[-1], path='/', domain='xn--d1ah4a.com.com')

def refresh_auth(cookies: str):
    print('refresh')
    res = s.post(f'https://xn--d1ah4a.com/api/v1/auth/refresh', timeout=10, headers={
        "Host": "xn--d1ah4a.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://xn--d1ah4a.com/",
        "Content-Type": "application/json",
        "Origin": "https://xn--d1ah4a.com",
        "Sec-GPC": "1",
        "Connection": "keep-alive",
        "Cookie": cookies,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=4",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Content-Length": "0",
        "TE": "trailers",
    })
    res.raise_for_status()
    return res.json()['accessToken']
