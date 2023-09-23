import ssl
import socks
from imaplib import IMAP4
from imap_tools import BaseMailBox
from tenacity import retry, stop_after_attempt, wait_fixed

# To be optimized later to support better protocol handling as the errors being thrown by core libraries in this file such as imaplib imaptools or socks aren't proprely
# handled which could lead to unexepcted behaviour in parent programs like mailkit and upper layer..

class SocksIMAP4(IMAP4):
    """
    IMAP service through SOCKS proxy. PySocks module required.
    """

    PROXY_TYPES = {"socks4": socks.PROXY_TYPE_SOCKS4,
                   "socks5": socks.PROXY_TYPE_SOCKS5,
                   "http": socks.PROXY_TYPE_HTTP}

    def __init__(self, host, port=993, proxy_addr=None, proxy_port=None,
                 rdns=True, username=None, password=None, proxy_type="HTTP", timeout=None):
        self.proxy_addr = proxy_addr
        self.proxy_port = proxy_port
        self.rdns = rdns
        self.username = username
        self.password = password
        self.proxy_type = SocksIMAP4.PROXY_TYPES[proxy_type.lower()]

        IMAP4.__init__(self, host, port, timeout)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
    def _create_socket(self, timeout=None):
        return socks.create_connection((self.host, self.port), proxy_type=self.proxy_type, proxy_addr=self.proxy_addr,
                                       proxy_port=self.proxy_port, proxy_rdns=self.rdns, proxy_username=self.username,
                                       proxy_password=self.password, timeout=10)


class SocksIMAP4SSL(SocksIMAP4):

    def __init__(self, host='', port=993, keyfile=None, certfile=None, ssl_context=None, proxy_addr=None,
                 proxy_port=None, rdns=True, username=None, password=None, proxy_type="http", timeout=None):

        if ssl_context is not None and keyfile is not None:
            raise ValueError("ssl_context and keyfile arguments are mutually "
                             "exclusive")
        if ssl_context is not None and certfile is not None:
            raise ValueError("ssl_context and certfile arguments are mutually "
                             "exclusive")

        self.keyfile = keyfile
        self.certfile = certfile
        if ssl_context is None:
            ssl_context = ssl._create_stdlib_context(certfile=certfile,
                                                     keyfile=keyfile)
        self.ssl_context = ssl_context

        SocksIMAP4.__init__(self, host, port, proxy_addr=proxy_addr, proxy_port=proxy_port,
                            rdns=rdns, username=username, password=password, proxy_type=proxy_type, timeout=timeout)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
    def _create_socket(self, timeout=None):
        sock = SocksIMAP4._create_socket(self, timeout=timeout)
        server_hostname = self.host if ssl.HAS_SNI else None
        return self.ssl_context.wrap_socket(sock, server_hostname=server_hostname)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
    def open(self, host='', port=993, timeout=None):
        SocksIMAP4.open(self, host, port, timeout)



class MailBoxProxy(BaseMailBox):

    def __init__(self,
                 host: str = "",
                 port: int = 993,
                 keyfile=None,
                 certfile=None,
                 ssl_context=None,
                 p_timeout: int = None,
                 p_proxy_type: str = 'http',
                 p_proxy_addr: str = None,
                 p_proxy_port: int = None,
                 p_proxy_rdns=True,
                 p_proxy_username: str = None,
                 p_proxy_password: str = None
                 ):
        self._host = host
        self._port = port
        self._keyfile = keyfile
        self._certfile = certfile
        self._ssl_context = ssl_context
        self._p_timeout = p_timeout
        self._p_proxy_type = p_proxy_type
        self._p_proxy_addr = p_proxy_addr
        self._p_proxy_port = p_proxy_port
        self._p_proxy_rdns = p_proxy_rdns
        self._p_proxy_username = p_proxy_username
        self._p_proxy_password = p_proxy_password
        super().__init__()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
    def _get_mailbox_client(self):
        return SocksIMAP4SSL(
            host=self._host,
            port=self._port,
            keyfile=self._keyfile,
            certfile=self._certfile,
            ssl_context=self._ssl_context,
            proxy_addr=self._p_proxy_addr,
            proxy_port=self._p_proxy_port,
            rdns=self._p_proxy_rdns,
            username=self._p_proxy_username,
            password=self._p_proxy_password,
            proxy_type=self._p_proxy_type,
            timeout=self._p_timeout)



if __name__ == '__main__':
    with MailBoxProxy(host='imap.rambler.ru',
                  p_proxy_type='HTTP',
                  p_proxy_addr='eepé_address',
                  p_proxy_port=12323,
                  p_proxy_username='useruh',
                  p_proxy_password='passruh').login('lizimail', 'emailpass', initial_folder='INBOX') as mailbox:
        for msg in mailbox.fetch(limit=5):
            print(msg.subject)
