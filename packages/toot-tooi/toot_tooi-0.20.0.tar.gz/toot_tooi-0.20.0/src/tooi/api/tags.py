"""
Tags API
https://docs.joinmastodon.org/methods/tags/
"""

from aiohttp import ClientResponse
from tooi.http import request


async def get(name: str) -> ClientResponse:
    """
    Show a hashtag and its associated information
    https://docs.joinmastodon.org/methods/tags/#get
    """
    return await request("GET", f"/api/v1/tags/{name}")


async def follow(name: str) -> ClientResponse:
    """
    Follow a hashtag.
    https://docs.joinmastodon.org/methods/tags/#follow
    """
    return await request("POST", f"/api/v1/tags/{name}/follow")


async def unfollow(name: str) -> ClientResponse:
    """
    Unfollow a hashtag.
    https://docs.joinmastodon.org/methods/tags/#unfollow
    """
    return await request("POST", f"/api/v1/tags/{name}/unfollow")


async def feature(name: str) -> ClientResponse:
    """
    Feature the hashtag on your profile.
    https://docs.joinmastodon.org/methods/tags/#feature
    """
    return await request("POST", f"/api/v1/tags/{name}/feature")


async def unfeature(name: str) -> ClientResponse:
    """
    Stop featuring the hashtag on your profile.
    https://docs.joinmastodon.org/methods/tags/#unfeature
    """
    return await request("POST", f"/api/v1/tags/{name}/unfeature")
