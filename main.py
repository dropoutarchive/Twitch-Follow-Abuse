import os
import sys
import base64
import random
import asyncio
import logging
import json as jsn
from tasksio import TaskPool
from aiohttp import ClientSession

if sys.platform == "linux":
    os.system("clear")
else:
    os.system("cls")

logging.basicConfig(
    level=logging.INFO,
    format=f"\x1b[38;5;61m[\x1b[0m%(asctime)s\x1b[38;5;61m]\x1b[0m -> \x1b[38;5;61m%(message)s\x1b[0m",
    datefmt="%H:%M:%S",
)

class Main:

    def __init__(self, token: str, categorys: list, loop: int):
        self.token = token
        self.loop = loop
        self.categorys = categorys
        self.scraped = []
        self.total_viewers = 0

    async def follow(self, id):
        headers = {
            "Client-Id": "kimne78kx3ncx6brgo4mv6wki5h1ko",
            "Authorization": f"OAuth %s" % (self.token)
        }
        json = [
            {
                "operationName": "FollowButton_FollowUser",
                "variables": {
                    "input": {
                        "disableNotifications": False,
                        "targetID": id
                    }
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "3efee1acda90efdff9fef6e6b4a29213be3ee490781c5b54469717b6131ffdfe"
                    }
                }
            }
        ]
        try:
            async with ClientSession(headers=headers) as session:
                async with session.post("https://gql.twitch.tv/gql", json=json) as response:
                    if "followUser" in await response.text():
                        logging.info("Successfully followed %s" % (id))
                    else:
                        logging.error("Failed to follow %s" % (id))
        except Exception:
            logging.error("Failed to execute request")

    async def unfollow(self, id):
        headers = {
            "Client-Id": "kimne78kx3ncx6brgo4mv6wki5h1ko",
            "Authorization": f"OAuth %s" % (self.token)
        }
        json = [
            {
                "operationName": "FollowButton_UnfollowUser",
                "variables": {
                    "input": {
                        "disableNotifications": False,
                        "targetID": id
                    }
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "3efee1acda90efdff9fef6e6b4a29213be3ee490781c5b54469717b6131ffdfe"
                    }
                }
            }
        ]
        try:
            async with ClientSession(headers=headers) as session:
                async with session.post("https://gql.twitch.tv/gql", json=json) as response:
                    if "followUser" in await response.text():
                        logging.info("Successfully unfollowed %s" % (id))
                    else:
                        logging.error("Failed to unfollow %s" % (id))
        except Exception:
            logging.error("Failed to execute request")

    async def scrape(self, query, limit, offset):
        cursor_json = {
            "b": None,
            "a": {
                "Offset": offset
            }
        }
        cursor = base64.b64encode(jsn.dumps(cursor_json).encode()).decode()
        headers = {
            "Client-Id": "kimne78kx3ncx6brgo4mv6wki5h1ko",
            "Authorization": f"OAuth %s" % (self.token)
        }
        json = [
            {
                "operationName": "DirectoryPage_Game",
                "variables": {
                    "name": query,
                    "options": {
                        "includeRestricted": [
                            "SUB_ONLY_LIVE"
                        ],
                        "sort": "RELEVANCE",
                        "recommendationsContext": {
                            "platform": "web"
                        },
                        "requestID": "JIRA-VXP-2397",
                        "tags": []
                    },
                    "sortTypeIsRecency": False,
                    "limit": limit,
                    "cursor": "%s" % (cursor)
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "d5c5df7ab9ae65c3ea0f225738c08a36a4a76e4c6c31db7f8c4b8dc064227f9e"
                    }
                }
            }
        ]
        async with ClientSession(headers=headers) as session:
            async with session.post("https://gql.twitch.tv/gql", json=json) as response:
                json = await response.json()
                try:
                    edges = json[0]["data"]["game"]["streams"]["edges"]
                    for stream in edges:
                        node = stream["node"]
                        host = node["broadcaster"]
                        title = node["title"]
                        type = node["type"]
                        if type != "live":
                            logging.info("\"%s\" is not live, skipping" % (title))
                        else:
                            partner = host["roles"]["isPartner"]
                            name = host["displayName"]
                            id = host["id"]
                            view_count = node["viewersCount"]
                            if partner:
                                logging.info("\"%s\" is live, and is a partner. Their ID is %s and they have %s viewers" % (name, id, view_count))
                            else:
                                logging.info("\"%s\" is live, and is not a partner. Their ID is %s and they have %s viewers" % (name, id, view_count))
                            if not id in self.scraped:
                                self.scraped.append(id)
                                self.total_viewers += int(view_count)
                except Exception:
                    logging.error("Failed to prase data with api response ~ %s" % (json))

    async def start(self):
        for x in range(self.loop):
            self.total_viewers = 0
            logging.info("Starting loop %s/%s" % (x+1, self.loop))
            print()
            for category in self.categorys:
                await self.scrape(
                    query=category.lower(),
                    limit=100,
                    offset=random.randint(1, 100)
                )
            print()
            logging.info("Starting to follow/unfollow users")
            print()
            async with TaskPool(1_000) as pool:
                for user in self.scraped:
                    await pool.put(self.follow(user))
                    await pool.put(self.unfollow(user))
            print()
            logging.info("Followed/unfollowed %s users" % (len(self.scraped)))
            logging.info("With a total of %s viewers" % (self.total_viewers))
            print()
            await asyncio.sleep(5)

if __name__ == "__main__":
    twitch = Main(
        token="qx1afmdv6b89t0z3ibzxn1gwcsan48",
        categorys=[
            "asmr",
            "who wants to be a millionaire",
            "counter-strike"
            "league of legends",
            "valorant",
            "rainbow six siege",
            "rocket league",
            "fall guys",
            "minecraft",
            "iracing",
            "special events",
            "pokemon unite",
            "sports",
            "new world",
            "fortnite",
            "grand theft auto v",
            "call of duty",
            "just chatting"
        ],
        loop=1337
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(twitch.start())
