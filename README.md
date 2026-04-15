# A Python Handler for the Notesnook Inbox API.

## Features
- Encrypts items locally before they leave your machine.
- Supports self-hosted notesnook servers, even those that do not host an Inbox API server. (This library replaces the need to use the Inbox API server.)
- Supports multiple Notesnook accounts & servers at once.

## Installation

Installation via pip is simple:

`pip install nn-inbox-api`

## Usage
```py
from nn_inbox_api import Notesnook_Inbox
inbox = Notesnook_Inbox(apikey="yourapikey")
inbox_on_selfhosted = Notesnook_Inbox(apikey="yourapikey",server="https://nn-api-server.your-server.tld/inbox/") # the sync server has the functionality to allow users to send pre-encrypted messages at the /inbox/ endpoint.

##########
# The most basic create note is shown below:
# create_note("Title", "Content (html)", "Note Source")
# A full list of attributes is available here: https://help.notesnook.com/inbox-api/getting-started#3-send-data-to-the-inbox

# A realistic example of a note might be...
inbox.create_note("Title", "<h1>Content</h1><p>I'm a paragraph!</p>", "from the nn-inbox-api python script", archived=True)
```

