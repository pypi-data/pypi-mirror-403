import requests


def make_tor_session(port: int) -> requests.Session:
    socks = f'socks5h://127.0.0.1:{port}'
    s = requests.Session()
    s.proxies = {
        'http': socks,
        'https': socks,
    }
    return s
