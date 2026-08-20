import asyncio
import urllib.parse
import re
from bs4 import BeautifulSoup
import httpx
from apify import Actor

async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}
        search_query = actor_input.get("searchQuery", "Coffee Shops in New York")
        max_results = actor_input.get("maxResults", 50)

        Actor.log.info(f"Starting Google Maps Lead Extractor for: '{search_query}' (max results: {max_results})")

        encoded_query = urllib.parse.quote_plus(search_query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}+google+maps+phone+address"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        leads = []
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
                res = await client.get(search_url)
                soup = BeautifulSoup(res.text, "html.parser")
                results = soup.find_all("div", class_="result__body")

                for item in results:
                    if len(leads) >= max_results:
                        break

                    title_elem = item.find("a", class_="result__url")
                    snippet_elem = item.find("a", class_="result__snippet")

                    title = title_elem.text.strip() if title_elem else "Business Lead"
                    snippet = snippet_elem.text.strip() if snippet_elem else ""

                    phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", snippet)
                    phone = phone_match.group(0) if phone_match else "N/A"

                    website_match = re.search(r"https?://[^\s>]+", snippet)
                    website = website_match.group(0) if website_match else "N/A"

                    rating_match = re.search(r"(\d\.\d)\s*\((\d+)\)", snippet)
                    rating = rating_match.group(1) if rating_match else "N/A"
                    reviews = rating_match.group(2) if rating_match else "N/A"

                    lead = {
                        "business_name": title.replace(" - Google Maps", "").strip(),
                        "search_query": search_query,
                        "phone": phone,
                        "website": website,
                        "rating": rating,
                        "review_count": reviews,
                        "snippet": snippet,
                    }
                    leads.append(lead)

            Actor.log.info(f"Successfully extracted {len(leads)} B2B leads.")
            await Actor.push_data(leads)

        except Exception as e:
            Actor.log.error(f"Scraper error: {e}")
            raise e

if __name__ == "__main__":
    asyncio.run(main())
