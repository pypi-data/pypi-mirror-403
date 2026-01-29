import requests


def get_public_ip(session: requests.Session, timeout: int) -> str:
    r = session.get(url='https://api.ipify.org/', timeout=timeout)
    r.raise_for_status()
    return r.text.strip()


def is_tor_exit(session: requests.Session, timeout: int) -> bool:
    r = session.get(url='https://check.torproject.org/api/ip', timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return bool(data.get('IsTor', False))
