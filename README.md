Mailkit is a light library for email scraping, uses imap_tools and some extras under the hood to make it more
seamless to use.





## Capabilities

* Check email login 
* Scrap emails with either subject, sender, keyword
* Proxy support HTTP/S and SOCKS5
* Command line version


## Use cases
Those uses cases are educational.

* Account registration bots
* Invoice download from emails
* Scrap general links from emails
* Fetch notifications


## Compatible email providers (flexible):


| Provider       | Compatibility |
| -------------- |:-------------:|
| Gmail          | ✅            |
| Yahoo          | ✅            |
| Mail.com       | ✅            |
| GMX            | ✅            |
| Mail.ru        | ✅            |
| Rambler.ru     | ✅            |
| Autorambler.ru | ✅            |
| Outlook        | ✅            |
| Hotmail        | ✅            |
| AOL            | ✅            |

> Gmail has deprecated imap.



## Installation

for now clone this repository and import mailkit, later on i'll be packaging this proprely in pypi.

You also have the requirements.txt to install teh required dependencies 




## Usage


as a module it can be used like this.

```python
# Import the MailKit class
from mailkit import MailKit

# Initialize the MailKit object
# Replace 'your_username', 'your_password' with your email and password
# Replace 'your_proxy_config' with your proxy configuration if you have one, otherwise set it to None
mailkit_instance = MailKit(user='your_username', password='your_password', proxy='your_proxy_config')

# Use the scrap method to search for emails
# Replace 'your_subject', 'your_sender', 'your_keyword' with the subject, sender, and keyword you want to search for
result = mailkit_instance.scrap(scrapsub='your_subject', sender='your_sender', keyword='your_keyword')

# Display the result
if result:
    print(f"Found {len(result)} emails matching the criteria.")
else:
    print("No emails found matching the criteria.")
```

## CLI
as for the command line version, checking is currently the only way but scrapping one is not really helpful yet i'll consider adding ways to export content to a file or some IPC.


* Check if a given email is valid

```python
python main.py --check -e your_email@gmail.com -p your_password
```

* Scrap emails with a specific subject

```python
python main.py -e your_email@gmail.com -p your_password --scrap "Your Subject Here"
```

* Use a proxy with HTTP type:

```python
python main.py -e your_email@gmail.com -p your_password --scrap "Your Subject Here"
```

* Use a proxy with SOCKS5 type and authentication:

```python
python main.py -e your_email@gmail.com -p your_password --proxy_type SOCKS5
--proxy_addr 192.168.1.1 --proxy_port 8080 --proxy_username your_username --proxy_password your_password

```



## To be implemented in the future:

* Export scraped content to a text file or an IPC buffer
* Send email over STMP
* HTTP server to manage emails and have active checking and managment
* Publish over pypi
* Add Gmail auth and email managment backend as having only single instance is detrimental to performance

