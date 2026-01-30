"""AlterLab Python SDK.

A production-ready Python client for the AlterLab Scraping API with full feature support.

Example:
    import asyncio
    from alterlab import AlterLab, AdvancedOptions, CostControls

    async def main():
        async with AlterLab(api_key="sk_test_...") as client:
            # Simple scraping
            result = await client.scrape("https://example.com")
            print(result['content'])

            # Advanced scraping with cost controls
            result = await client.scrape(
                "https://example.com",
                mode="js",
                advanced=AdvancedOptions(render_js=True, screenshot=True),
                cost_controls=CostControls(max_credits=5)
            )

    asyncio.run(main())

For synchronous usage:
    from alterlab import AlterLabSync

    with AlterLabSync(api_key="sk_test_...") as client:
        result = client.scrape("https://example.com")
        print(result['content'])
"""

from alterlab.client import (
    AlterLab,
    AlterLabSync,
    AdvancedOptions,
    CostControls,
    AlterLabError,
    AlterLabAPIError,
    AlterLabTimeoutError,
    AlterLabValidationError
)

__version__ = "2.0.0"
__all__ = [
    "AlterLab",
    "AlterLabSync",
    "AdvancedOptions",
    "CostControls",
    "AlterLabError",
    "AlterLabAPIError",
    "AlterLabTimeoutError",
    "AlterLabValidationError"
]
