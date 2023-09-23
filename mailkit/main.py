import logging
import os
import sys
from argparse import ArgumentParser
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional
import socks
from bs4 import BeautifulSoup
from colorlog import ColoredFormatter
from imap_tools import MailBox, AND, MailboxLoginError
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed
from proxification_v2 import MailBoxProxy

providers = {"gmail.com": 'imap.gmail.com',
             "yahoo.com": 'imap.mail.yahoo.com',
             "mail.com": 'imap.mail.com',
             "gmx.com": 'imap.gmx.com',
             "mail.ru": 'imap.mail.ru',
             "rambler.ru": 'imap.rambler.ru',
             "autorambler.ru": 'imap.rambler.ru',
             "outlook.com": 'outlook.office365.com',
             "hotmail.com": 'outlook.office365.com',
             "aol.com": "imap.aol.com", }


class ProxyConfig(BaseModel):
    """
    Proxy configuration for MailKit.
    """
    proxy_type: str = Field(..., description="Type of the proxy, either 'HTTP' or 'SOCKS5'", example="HTTP")
    proxy_addr: str = Field(..., description="IP address or hostname of the proxy", example="192.168.1.1")
    proxy_port: int = Field(..., description="Port number of the proxy", example=8080, ge=1, le=65535)
    proxy_username: Optional[str] = Field(None, description="Username for proxy authentication", example="username")
    proxy_password: Optional[str] = Field(None, description="Password for proxy authentication", example="password")
    timeout: Optional[int] = Field(10, description="Timeout for the proxy connection in seconds", example=10, ge=1)


class MailKit:
    """
       A class used to represent a mailbox.
       ...

       Attributes
       ----------
       u : str
           the username (email address) used for authentication

       pw : str
           the password used for authentication

       mailbox : MailBox object
           the mailbox object to interact with, defaults to None

       proxy : ProxyConfig object
           the proxy configuration, defaults to None

       Methods
       -------
       connect_and_login():
           Connects to the mailbox and logs in with the given user credentials.

    scrap():
        method is also available for this class. It takes in three parameters:

    scrapsub : str
        The subject line to search for in the emails

    sender : str
        The sender of the email

    keyword : str
        The keyword to search for in the HTML of the email body

    It searches the mailbox for emails that match the conditions and returns a BeautifulSoup object of the email body HTML.
       """

    def __init__(self, user, password, proxy):
        """
             Constructs all the necessary attributes for the MailKit object.
             Parameters
             ----------
                 user : str
                     the username (email address) used for authentication
                 password : str
                     the password used for authentication
                 proxy : ProxyConfig, optional
                     the proxy configuration, by default None

             Note
             ----
             If a proxy is specified, the MailBox connection will be routed through the proxy.
             The proxy configuration must be an instance of the ProxyConfig class, with the following attributes:

             proxy_type : str
                 the type of the proxy, should be either 'HTTP' or 'SOCKS5'
             proxy_addr : str
                 the IP address or hostname of the proxy
             proxy_port : int
                 the port number of the proxy
             proxy_username : str, optional
                 the username for proxy authentication, if required
             proxy_password : str, optional
                 the password for proxy authentication, if required
             timeout : int, optional
                 the timeout for the proxy connection in seconds, defaults to 10 if not provided
             """
        self.logger = logging.getLogger('MailKit')
        self.clear_handlers()
        self.logger = logging.getLogger('MailKit')
        if not self.logger.hasHandlers():
            self.setup_logging()
        self.logger.propagate = False
        self.logger.info("Initializing MailKit instance")
        self.setup_logging()
        self.u = user
        self.pw = password
        self.mailbox = None
        self.login_status = False
        self.proxy = proxy
        if self.proxy:
            self.logger.info(f"Loaded proxy {self.proxy.proxy_addr}")
        self.connect_and_login()

    def setup_logging(self, log_level=logging.INFO, log_dir='mailkit_logs'):
        """
        Set up logging configuration.
        :param log_level: logging level
        :param log_dir: directory to store log files
        """

        current_script_directory = os.path.dirname(os.path.abspath(__file__))
        full_log_dir = os.path.join(current_script_directory, log_dir)
        if not os.path.exists(full_log_dir):
            os.makedirs(full_log_dir)
        log_file = os.path.join(full_log_dir, f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)

            log_format = "%(log_color)s%(asctime)s [%(name)s] [%(levelname)s]%(reset)s %(message_log_color)s%(message)s"
            formatter = ColoredFormatter(
                log_format,
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "bold_white",
                    "WARNING": "bold_yellow",
                    "ERROR": "bold_red",
                    "CRITICAL": "bold_white,bg_red",
                },
                secondary_log_colors={
                    "message": {
                        "DEBUG": "cyan",
                        "INFO": "green",
                        "WARNING": "yellow",
                        "ERROR": "red",
                        "CRITICAL": "white",
                    }
                },
            )

            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
    def connect_and_login(self):
        parsed_user = self.u.split('@')
        if len(parsed_user) > 1:
            parsed_user = parsed_user[1]
            try:
                if parsed_user in providers:
                    provider = providers[parsed_user]
                    if self.proxy:
                        if isinstance(self.proxy.proxy_type, str):
                            if self.proxy.proxy_type.upper() == 'HTTP':
                                self.proxy.proxy_type = socks.HTTP
                            elif self.proxy.proxy_type.upper() == 'SOCKS5':
                                self.proxy.proxy_type = socks.SOCKS5
                        else:
                            if self.proxy.proxy_type in [socks.HTTP, socks.SOCKS5]:
                                pass
                            else:
                                raise ValueError(
                                    "Invalid proxy type. Must be either 'HTTP', 'SOCKS5', or a valid socks proxy type.")

                        self.mailbox = MailBoxProxy(
                            host=provider,
                            p_proxy_type='HTTP',
                            p_proxy_addr=self.proxy.proxy_addr,
                            p_proxy_port=self.proxy.proxy_port,
                            p_proxy_username=self.proxy.proxy_username,
                            p_proxy_password=self.proxy.proxy_password,
                            p_timeout=self.proxy.timeout,
                        )
                    else:
                        self.mailbox = MailBox(provider)

                    self.mailbox.login(self.u, self.pw)
                    if self.mailbox.folder.set('INBOX'):
                        self.logger.info(f"Successful login on {self.u}")
                        self.login_status = True
                        return True
                    else:
                        self.logger.error(f"Failed to connect to INBOX on {self.u}")
                        self.login_status = False
                        return False
                else:
                    self.logger.error(f"Please enter an email that is supported in the provider dict.")
                    self.login_status = False
                    return False
            except MailboxLoginError as e:
                self.logger.error(f"Failed login on {self.u}, error: {str(e)}")
                self.login_status = False
                return False
            except Exception as e:
                self.logger.error(str(e))
                return False

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
    def scrap(self, scrapsub=None, sender=None, keyword=None, seen=None, time_diff=None, specific_date=None):
        """
        Parameters
        ----------
        seen : Optional[bool]
            Whether to search for seen or unseen messages. None searches for both.
        time_diff : Optional[timedelta]
            Time difference to filter emails. For example, timedelta(minutes=5) will filter emails received in the last 5 minutes.
        specific_date : Optional[datetime]
            Specific date to filter emails. Emails received on this date will be considered.
            :param specific_date:
            :param time_diff:
            :param seen:
            :param keyword:
            :param sender:
            :param scrapsub:
        """
        soups = []

        if self.mailbox:
            if not any([scrapsub, sender, keyword]):
                raise ValueError("At least one of 'scrapsub', 'sender', 'keyword' must be provided.")

            search_criteria = {}
            if seen is not None:
                search_criteria['seen'] = seen
            if scrapsub:
                search_criteria['subject'] = scrapsub
            if sender:
                search_criteria['from_'] = sender

            try:
                folders = ['INBOX', 'SENT', 'DRAFTS', 'JUNK', 'TRASH', 'ARCHIVE', 'Trash', 'DraftBox', 'Spam',
                           'Sentbox', 'Archive', 'Deleted', 'Drafts', 'Inbox', 'Junk', 'Notes', 'Outbox', 'Sent']
                for i in folders:
                    try:
                        self.mailbox.folder.set(i)
                        messages = self.mailbox.fetch(AND(**search_criteria), mark_seen=True)
                        for msg in messages:
                            msg_time = msg.date
                            if time_diff and datetime.now() - msg_time > time_diff:
                                continue
                            if specific_date and msg_time.date() != specific_date.date():
                                continue
                            if keyword and keyword not in (msg.text or msg.html):
                                continue
                            soup = BeautifulSoup(msg.text or msg.html, features="lxml")
                            soups.append(soup)
                    except BaseException as folder_error:
                        pass
            except Exception as nm:
                self.logger.error(str(nm))
                return nm
            self.logger.info(f"Got a hit on an email from {sender} with keyword {keyword} and subject {scrapsub}")
            return soups if soups else None
        else:
            self.logger.error(f"Authentication Failed on {self.u}")
            return None

    def clear_handlers(self):
        if hasattr(self, 'logger'):
            handlers = self.logger.handlers[:]
            for handler in handlers:
                handler.close()
                self.logger.removeHandler(handler)

    def __enter__(self):
        """
        Enter the runtime context for the MailKit object.
        This method is automatically called when entering a `with` block.

        Returns:
            self : MailKit object
                The MailKit object itself is returned so that it can be used in the `with` block.
        """
        self.connect_and_login()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the runtime context for the MailKit object.
        This method is automatically called when exiting a `with` block.

        Parameters:
            exc_type : type
                The type of exception raised (if any).
            exc_value : Exception
                The instance of exception raised (if any).
            traceback : traceback
                A traceback object encapsulating the call stack at the point where the exception was raised (if any).

        Returns:
            None
        """
        if self.mailbox:
            try:
                self.mailbox.logout()
            except Exception as e:
                self.logger.error(f"Failed to logout: {str(e)}")
        self.clear_handlers()


def main():
    proxy_config = None
    if args.proxy_addr and args.proxy_port:
        proxy_config = ProxyConfig(
            proxy_type=args.proxy_type if args.proxy_type else 'HTTP',
            proxy_addr=args.proxy_addr,
            proxy_port=args.proxy_port,
            proxy_username=args.proxy_username if args.proxy_username else None,
            proxy_password=args.proxy_password if args.proxy_password else None,
            timeout=args.timeout if args.timeout else 10,
        )
    mailkit = MailKit(args.e, args.p, proxy=proxy_config)
    if args.scrap or args.sender or args.keyword:
        print(mailkit.scrap(args.scrap, args.sender, args.keyword))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Check if a given email is valid")
    parser.add_argument("-e", type=str, help="Email address", required=True)
    parser.add_argument("-p", type=str, help="Email address password", required=True)
    parser.add_argument("--scrap", type=str, default=None, help="Subject of the email to scrap")
    parser.add_argument("--sender", type=str, default=None, help="Sender of the email to scrap")
    parser.add_argument("--keyword", type=str, default=None, help="Keyword to search for in the email to scrap")
    parser.add_argument("--proxy_type", type=str, help="Type of the proxy, either 'HTTP' or 'SOCKS5'")
    parser.add_argument("--proxy_addr", type=str, help="IP address or hostname of the proxy")
    parser.add_argument("--proxy_port", type=int, help="Port number of the proxy")
    parser.add_argument("--proxy_username", type=str, help="Username for proxy authentication")
    parser.add_argument("--proxy_password", type=str, help="Password for proxy authentication")
    parser.add_argument("--timeout", type=int, help="Timeout for the proxy connection in seconds")
    args = parser.parse_args()
    main()
