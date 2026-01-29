"""Operating system utilities."""

import logging
import socket
from os import environ


log = logging.getLogger(__name__)


def is_sudo() -> bool:
    """Process is running as sudo."""
    try:
        environ['SUDO_USER']
    except KeyError:
        return False
    return True


def internet(host: str = '8.8.8.8', port: int = 53, timeout: int = 3) -> bool:
    """
    Is there an internet connection?
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    https://stackoverflow.com/questions/3764291/how-can-i-see-if-theres-an-available-and-active-network-connection-in-python
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError as ex:
        log.debug('internet test result: %s', ex)
        return False


# todo tests
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print('internet', internet())
