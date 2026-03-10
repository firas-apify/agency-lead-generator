from apify import Actor

from scraper import run_scraper


async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}
        start_url = actor_input.get("start_url")
        if not start_url:
            raise ValueError("start_url is required")
        max_items = int(actor_input.get("max_items", 50))

        Actor.log.info(f"Starting with URL: {start_url}, max_items: {max_items}")

        proxy_config = await Actor.create_proxy_configuration()
        proxy_url = await proxy_config.new_url() if proxy_config else None

        items = await run_scraper(
            start_url=start_url,
            max_items=max_items,
            proxy_url=proxy_url,
        )

        for item in items:
            await Actor.push_data(item)

        Actor.log.info(f"Finished. Total items pushed: {len(items)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
