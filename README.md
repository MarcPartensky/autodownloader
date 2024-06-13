# Auto Downloader
https://github.com/marcpartensky/autodownloader

Download movies from a Nextcloud deck stack with PirateBay

```
# tpblite
TPB_URL="https://tpb.party"
MIN_FILESIZE="1 GiB"
MAX_FILESIZE="4 GiB"

# nextcloud-deck
NEXTCLOUD_URL="https://nextcloud.example.com"
NEXTCLOUD_USER="exampleuser"
NEXTCLOUD_PASSWORD="examplepassword"
NEXTCLOUD_BOARD_ID=1
NEXTCLOUD_STACK_ID=2
NEXTCLOUD_DOWNLOADED_STACK_ID=3
NEXTCLOUD_NOTORRENTS_LABEL_ID=4
NEXTCLOUD_TITLEWRONG_LABEL_ID=5

# groq
GROQ_API_KEY="gsk_1111111111111111111111111111111111111111111111111111"

# torrentp
DOWNLOAD=1 # should download?
DOWNLOAD_DIRECTORY="."
```

## Docs
- https://deck.readthedocs.io/en/latest/API/
- https://github.com/kprestel/nextcloud-deck/blob/master/tests/test_api.py
- https://console.groq.com/
- https://github.com/groq/groq-python
- https://pypi.org/project/tpblite/
- https://pydigger.com/pypi/torrentp
- https://jellyfin.org/docs/general/server/media/movies/
