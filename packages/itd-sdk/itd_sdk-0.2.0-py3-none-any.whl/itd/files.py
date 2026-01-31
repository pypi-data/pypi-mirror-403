from itd.request import fetch


def upload_file(token: str, name: str, data: bytes):
    return fetch(token, 'post', 'files/upload', files={'file': (name, data)})