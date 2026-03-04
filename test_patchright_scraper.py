import asyncio
import logging
from patchright_scraper import PatchrightScraper, ScraperConfig

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("Testing Patchright Scraper...")
    
    # Configure scraper with stealth and human simulation enabled
    config = ScraperConfig(
        use_stealth=True,
        simulate_human=True,
        headless=True,  # Set to False to see the browser action
        debug=True
    )
    
    async with PatchrightScraper(config) as scraper:
        url = "https://www.example.com"
        print(f"Fetching {url}...")
        
        results = await scraper.fetch_content(url)
        
        if results and len(results) > 0:
            content = results[0]
            print(f"Successfully fetched content ({len(content)} bytes)")
            if "Example Domain" in content:
                print("✅ Validation successful: Found 'Example Domain' in content.")
            else:
                print("⚠️ Validation warning: 'Example Domain' not found.")
        else:
            print("❌ Failed to fetch content.")

if __name__ == "__main__":
    asyncio.run(main())
