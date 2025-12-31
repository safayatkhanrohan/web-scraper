from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from recipe_scrapers import scrape_me
import json

app = FastAPI(
    title="Recipe Scraper API",
    version="1.0.0",
    description="A simple recipe scraper that returns raw data",
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


class ScrapeRequest(BaseModel):
    url: str


def try_recipe_scrapers(url: str) -> dict | None:
    """Try using recipe-scrapers library first."""
    try:
        scraper = scrape_me(url)
        return scraper.to_json()
    except Exception:
        return None


def is_recipe_data(data: dict) -> bool:
    """Check if a dictionary contains recipe-like data."""
    item_type = data.get("@type", "")
    if item_type in ["Recipe", "FoodRecipe"] or "recipe" in str(item_type).lower():
        return True
    recipe_fields = ["recipeIngredient", "ingredients", "recipeInstructions"]
    return any(field in data for field in recipe_fields)


def extract_json_ld(soup) -> dict | None:
    """Extract raw JSON-LD recipe schema data as-is."""
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and is_recipe_data(item):
                        return item

            elif isinstance(data, dict):
                if is_recipe_data(data):
                    return data

                if "@graph" in data and isinstance(data["@graph"], list):
                    for item in data["@graph"]:
                        if isinstance(item, dict) and is_recipe_data(item):
                            return item

        except (json.JSONDecodeError, TypeError):
            continue
    return None


def extract_cleaned_html(soup) -> str:
    """Remove non-content tags and return cleaned text content."""
    for tag in soup(
        [
            "script",
            "style",
            "header",
            "footer",
            "nav",
            "aside",
            "noscript",
            "iframe",
            "svg",
        ]
    ):
        tag.decompose()

    text_content = soup.get_text(separator=" ", strip=True)
    text_content = " ".join(text_content.split())
    return text_content


def enhance_recipe_data(soup, data: dict) -> dict:
    """Enhance recipe data by scraping HTML for missing fields."""
    if not data:
        return data

    # Enrich Ingredients if missing or simple string
    if not data.get("recipeIngredient") or isinstance(data.get("recipeIngredient"), str):
        ingredients_div = soup.find(id="ingredients")
        if ingredients_div:
            items = [li.get_text(strip=True) for li in ingredients_div.find_all("li")]
            if items:
                data["recipeIngredient"] = items

    # Enrich Instructions if missing
    if not data.get("recipeInstructions"):
        steps_div = soup.find(id="steps")
        if steps_div:
            steps = [
                {"@type": "HowToStep", "text": li.get_text(strip=True)}
                for li in steps_div.find_all("li")
            ]
            if steps:
                data["recipeInstructions"] = steps
    
    return data


@app.post("/scrape")
async def scrape_recipe(request: ScrapeRequest):
    """
    Scrape recipe data from a URL.

    Tries in order:
    1. recipe-scrapers library
    2. JSON-LD schema extraction (enhanced with HTML scraping)
    3. Cleaned HTML text (for AI processing)

    Returns raw data without formatting.
    """
    # Step 1: Try recipe-scrapers library first
    recipe_data = try_recipe_scrapers(request.url)
    if recipe_data:
        return {"source": "recipe-scrapers", "url": request.url, "data": recipe_data}

    # Step 2 & 3: Fetch HTML and try JSON-LD, then fallback to cleaned HTML
    try:
        response = requests.get(request.url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching URL: {str(e)}")

    soup = BeautifulSoup(response.content, "lxml")

    # Step 2: Try JSON-LD extraction
    json_ld_data = extract_json_ld(soup)
    if json_ld_data:
        enhanced_data = enhance_recipe_data(soup, json_ld_data)
        return {"source": "json-ld", "url": request.url, "data": enhanced_data}

    # Step 3: Return cleaned HTML text for AI processing
    cleaned_text = extract_cleaned_html(soup)
    if not cleaned_text:
        raise HTTPException(
            status_code=404, detail="Could not extract any content from URL"
        )

    return {"source": "html", "url": request.url, "data": cleaned_text}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
