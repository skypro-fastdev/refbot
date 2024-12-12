import aiohttp


async def send_request(url, data=None):
    async with aiohttp.ClientSession() as session:
        if data:
            async with session.post(url, json=data) as response:
                return await response.json()
        else:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"Error: {response.text()}")
                    return {}
                return await response.json()


async def get_request(url):
    return await send_request(url)


async def post_request(url, data):
    return await send_request(url, data)
