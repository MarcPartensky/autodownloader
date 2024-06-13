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
from groq import Groq

# optional
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

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
if GROQ_API_KEY:
    groq = Groq(
        # This is the default and can be omitted
        api_key=os.environ.get("GROQ_API_KEY"),
    )


def get_torrent(card: Card) -> Torrent | None:
    torrents = t.search(card.title)
    print(torrents)
    return torrents.getBestTorrent(
        min_seeds=1,
        min_filesize=os.environ["MIN_FILESIZE"],
        max_filesize=os.environ["MAX_FILESIZE"],
    )


def enrich_director(card: Card, description: dict):
    """Find the director of the movie"""
    director = ask(
        f"Give me the name of the director of the movie and nothing more: {card.title}",
    )
    sure = ask(
        f"Are you sure that the director of this movie: {card.title} is {director}? Just answer by yes or no.",
    ).lower()
    if "yes" in sure:
        description["director"] = director


def enrich_description(card: Card, torrent: Torrent | None):
    """Enrich the description of the card"""
    description = load(card.description or "") or {}

    # Check if there is already label "no torrents" so we dont check twice the same card
    if card.labels:
        for label in card.labels:
            if label.id == LABEL_ID:
                return card

    # # Otherwise enrich
    # torrents = t.search(card.title)
    # description["torrents"] = len(torrents)

    # If no torrent is found add the "no torrents" label
    if not torrent:
        nc.assign_label_to_card(
            label_id=LABEL_ID, card_id=card.id, board_id=BOARD_ID, stack_id=STACK_ID
        )
    else:  # Otherwise enrich descriptions
        if GROQ_API_KEY:
            enrich_director(card, description)
        # description["magnetlink"] = torrent.magnetlink.encode("utf-8")
        description["title"] = torrent.title
        description["seeds"] = torrent.seeds
        description["filesize"] = torrent.filesize
        description["uploader"] = torrent.uploader

    print("enriched description:", description)

    updated_card = nc.update_card(
        board_id=BOARD_ID,
        stack_id=STACK_ID,
        card_id=card.id,
        title=card.title,
        description=dump(description) or "",
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
    """Download the movie"""
    print("magnet:", torrent.magnetlink)
    torrent_file = TorrentDownloader(
        torrent.magnetlink, os.environ["DOWNLOAD_DIRECTORY"]
    )
    # start_download() is a asynchronous method
    await torrent_file.start_download()


def move_card_downloaded(card: Card) -> Card:
    """Recreate the card to the downloaded stack"""
    card = nc.create_card(
        board_id=BOARD_ID,
        stack_id=DOWNLOADED_STACK_ID,
        title=card.title,
        description=card.description,
    )
    nc.delete_card(
        board_id=BOARD_ID,
        stack_id=STACK_ID,
        card_id=card.id,
    )
    return card


def ask(message: str) -> str:
    """Ask llama3"""
    chat_completion = groq.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ],
        model="llama3-8b-8192",
    )
    answer = chat_completion.choices[0].message.content or ""
    print("groq:", message, "->", answer)
    return answer


def enrich_title(card: Card):
    "Ask llama3 for the true name of the movie and change it"
    answer = ask(
        f"Is this the name of a movie? just give me yes or no: {card.title}"
    ).lower()
    if "yes" in answer:
        return card
    title = ask(
        f"Just say the real complete name of this movie and without formulating a sentence: {card.title}",
    )
    print("old title:", card.title, "new title:", title)
    return nc.update_card(
        board_id=BOARD_ID,
        stack_id=STACK_ID,
        card_id=card.id,
        title=title,
        description=card.description or "",
        owner=card.owner,
    )


# movie board
# board: Board = nc.get_board(board_id=BOARD_ID)
# print(board)


async def main():

    cards = nc.get_cards_from_stack(board_id=BOARD_ID, stack_id=STACK_ID)
    card: Card
    for card in cards:
        if GROQ_API_KEY:
            card = enrich_title(card)
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
