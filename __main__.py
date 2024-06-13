#!/usr/bin/env python

import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from yaml import safe_load as load, safe_dump as dump

load_dotenv()


import asyncio
from torrentp import TorrentDownloader

from tpblite import TPB
from tpblite.models.torrents import Torrent
from deck.api import NextCloudDeckAPI
from deck.models import Board, Card, Stack, Label

BOARD_ID = int(os.environ["NEXTCLOUD_BOARD_ID"])
STACK_ID = int(os.environ["NEXTCLOUD_STACK_ID"])
DOWNLOADED_STACK_ID = int(os.environ["NEXTCLOUD_DOWNLOADED_STACK_ID"])
LABEL_ID = int(os.environ["NEXTCLOUD_LABEL_ID"])

t = TPB(os.environ["TPB_URL"])
nc = NextCloudDeckAPI(
    os.environ["NEXTCLOUD_URL"],
    HTTPBasicAuth(os.environ["NEXTCLOUD_USER"], os.environ["NEXTCLOUD_PASSWORD"]),
    ssl_verify=True,
)


def get_torrent(card: Card) -> Torrent | None:
    torrents = t.search(card.title)
    print(torrents)
    return torrents.getBestTorrent(
        min_seeds=1, min_filesize=os.environ["MIN_FILESIZE"], max_filesize=os.environ["MAX_FILESIZE"]
    )


def enrich_description(card: Card, torrent: Torrent | None):
    if not card.description:
        return add_torrent_number(card, torrent)
    description = load(card.description)
    if description:
        if "torrents" in description:
            return card
    return add_torrent_number(card, torrent, description)


def add_torrent_number(card: Card, torrent: Torrent | None, description={}):
    torrents = t.search(card.title)
    description["torrents"] = len(torrents)
    if len(torrents) == 0:
        nc.assign_label_to_card(
            label_id=LABEL_ID, card_id=card.id, board_id=BOARD_ID, stack_id=STACK_ID
        )
        description["found"] = False
    else:
        if torrent:
            # description["magnetlink"] = torrent.magnetlink.encode("utf-8")
            description["title"] = torrent.title
            description["seeds"] = torrent.seeds
            description["filesize"] = torrent.filesize
            description["uploader"] = torrent.uploader
            description["found"] = True
        else:
            description["found"] = False

    updated_card = nc.update_card(
        board_id=BOARD_ID,
        stack_id=STACK_ID,
        card_id=card.id,
        title=card.title,
        description=dump(description),
        owner=card.owner,
    )
    return updated_card


# async def async_download(func):
#     print()
#     await func


def should_download(card: Card, torrent: Torrent) -> bool:
    """Should check if label "no torrent" available"""
    if not torrent:
        return False
    # load(card.description)
    return True


async def download(torrent: Torrent):
    print("magnet:", torrent.magnetlink)
    torrent_file = TorrentDownloader(
        torrent.magnetlink, os.environ["DOWNLOAD_DIRECTORY"]
    )
    # start_download() is a asynchronous method
    await torrent_file.start_download()


def move_card_downloaded(card: Card) -> Card:
    return nc.update_card(
        board_id=BOARD_ID,
        stack_id=DOWNLOADED_STACK_ID,
        card_id=card.id,
        title=card.title,
        description=card.description,
        owner=card.owner,
    )


# movie board
# board: Board = nc.get_board(board_id=BOARD_ID)
# print(board)


async def main():
    cards = nc.get_cards_from_stack(board_id=BOARD_ID, stack_id=STACK_ID)
    card: Card
    for card in cards:
        print("card:", card.title, card.description)
        torrent = get_torrent(card)
        card = enrich_description(card, torrent)
        if should_download(card, torrent):
            print("torrent:", torrent)
            # await download(torrent)  # download one by one pls
            move_card_downloaded(card)
        else:
            print("no torrent skip")
    print("done")


if __name__ == "__main__":
    asyncio.run(main())
