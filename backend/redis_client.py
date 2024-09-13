import asyncio

from redis import asyncio as aioredis
from backend.config_reader import config

redis_client = aioredis.Redis(host=config.redis_host.get_secret_value(), port=int(config.redis_port.get_secret_value()), password=config.redis_password.get_secret_value(), db=3)


async def main():
    print(await redis_client.info())
    print(await redis_client.keys())

if __name__ == "__main__":
    asyncio.run(main())
