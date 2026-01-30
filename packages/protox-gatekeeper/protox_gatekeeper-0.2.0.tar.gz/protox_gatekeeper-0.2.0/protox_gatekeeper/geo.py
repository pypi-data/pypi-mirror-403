import logging

import requests

logger = logging.getLogger(__name__)


def geo_lookup(ip: str) -> str | None:
    try:
        r = requests.get(
            url=f'https://ipapi.co/{ip}/json',
            timeout=10,
            headers={'User-Agent': 'GateKeeper/0.1.0'}
        )
        if r.status_code != 200:
            return None

        data = r.json()
        city = data.get('city')
        country = data.get('country')
        if city and country:
            return f'{city}, {country}'

    except Exception as e:
        logger.info(f'Unable to get geolocation for {ip}: {e}')
        return None
