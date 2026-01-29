import logging

import requests

from protox_gatekeeper.session import make_tor_session
from protox_gatekeeper.verify import is_tor_exit, get_public_ip
from protox_gatekeeper.ops import download_file as _download
from protox_gatekeeper.geo import geo_lookup

logger = logging.getLogger(__name__)


class GateKeeper:
    def __init__(self, socks_port: int = 9150, geo=False, timeout: int = 10):
        """
        GateKeeper constructor.

        Args:
            socks_port (int, optional): The socks port to use. Defaults to 9150.
            geo (bool, optional): Whether to use geo. Defaults to False.
            timeout (int, optional): The timeout to wait for a response. Defaults to 10.
        """

        self._session: requests.Session
        self.exit_ip: str
        self.clearnet_ip: str

        # 1) Measure clearnet IP (no proxies)
        clearnet = requests.Session()
        self.clearnet_ip = get_public_ip(session=clearnet, timeout=timeout)

        # 2) Create Tor session
        self._session = make_tor_session(port=socks_port)

        # 3) Verify Tor routing
        if not is_tor_exit(session=self._session, timeout=timeout):
            raise RuntimeError('Tor verification failed. Execution aborted.')

        # 4) Measure Tor exit IP
        self.exit_ip = get_public_ip(session=self._session, timeout=timeout)

        # 5) Log the transition
        logger.info(f'Tor verified: {self.clearnet_ip} -> {self.exit_ip}')

        # 6) Location data
        if geo:
            location = geo_lookup(self.exit_ip)
            if location:
                logger.info(f'Tor exit location: {location}')
            else:
                logger.info('Tor exit location: Unavailable')

    def __repr__(self) -> str:
        return f'<GateKeeper: {self.clearnet_ip} -> tor_exit: {self.exit_ip}>'

    def __enter__(self) -> "GateKeeper":
        return self

    def __exit__(self, exc_type, exc, tb):
        self._session.close()

    @property
    def session(self) -> requests.Session:
        """ Exposes the verified session if needed. """
        return self._session

    @property
    def tor_exit(self) -> str:
        """ Returns the Tor exit IP address. """
        return self.exit_ip

    def download(self, url: str, target_path: str, timeout: int = 30,
                 chunk_size: int = 8192):
        """
        Attempts to download the given url to the target path.

        Args:
            url (str): The url to download.
            target_path (str): The target path.
            timeout (int, optional): The timeout to wait for a response.
            chunk_size (int, optional): The chunk size to use for download.
        """
        logger.info(
            f'[Tor {self.tor_exit}] downloading {url} -> {target_path}')

        return _download(
            session=self._session,
            url=url,
            target_path=target_path,
            timeout=timeout,
            chunk_size=chunk_size
        )
