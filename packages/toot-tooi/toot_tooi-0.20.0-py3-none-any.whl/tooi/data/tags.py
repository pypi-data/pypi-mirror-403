from tooi.api import tags
from tooi.entities import Tag
from tooi.utils.from_dict import from_response


async def get(name: str) -> Tag:
    response = await tags.get(name)
    return await from_response(Tag, response)


async def follow(name: str) -> Tag:
    response = await tags.follow(name)
    return await from_response(Tag, response)


async def unfollow(name: str) -> Tag:
    response = await tags.unfollow(name)
    return await from_response(Tag, response)


async def feature(name: str) -> Tag:
    response = await tags.feature(name)
    return await from_response(Tag, response)


async def unfeature(name: str) -> Tag:
    response = await tags.unfeature(name)
    return await from_response(Tag, response)
