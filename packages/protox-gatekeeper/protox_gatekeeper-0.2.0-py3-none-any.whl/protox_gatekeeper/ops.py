import os

import requests


def download_file(
        session: requests.Session,
        url: str,
        target_path: str,
        timeout: int,
        chunk_size: int
) -> None:
    if not isinstance(session, requests.Session):
        raise TypeError('A verified requests.Session is required.')

    dir_path = os.path.dirname(target_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    response = session.get(url, stream=True, timeout=timeout)
    response.raise_for_status()

    with open(target_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
