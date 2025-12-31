from app import try_recipe_scrapers, extract_json_ld, extract_cleaned_html, HEADERS
import requests
from bs4 import BeautifulSoup
import json

url = "https://www.webteb.com/diet/recipes/%D8%A7%D9%84%D9%84%D8%AD%D9%85%D8%A9-%D8%A7%D9%84%D9%85%D8%AD%D9%85%D8%B1%D8%A9-%D8%A8%D8%A7%D9%84%D8%AB%D9%88%D9%85_1350"

print(f"Testing URL: {url}")

# 1. Try recipe-scrapers
print("\n--- Attempting recipe-scrapers ---")
try:
    data = try_recipe_scrapers(url)
    if data:
        print("Success with recipe-scrapers!")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("recipe-scrapers returned None")
except Exception as e:
    print(f"recipe-scrapers failed: {e}")

# 2. Fetch page manualy
print("\n--- Fetching Page ---")
try:
    response = requests.get(url, headers=HEADERS, timeout=15)
    print(f"Status Code: {response.status_code}")
    soup = BeautifulSoup(response.content, "lxml")
    json_ld = extract_json_ld(soup)
    
    # SIMULATE ENHANCEMENT
    print("\n--- Simulating Enhancement ---")
    data = json_ld if json_ld else {}
    
    # Enrich Ingredients
    if not data.get("recipeIngredient") or isinstance(data.get("recipeIngredient"), str):
        ingredients_div = soup.find(id="ingredients")
        if ingredients_div:
            items = [li.get_text(strip=True) for li in ingredients_div.find_all("li")]
            if items:
                data["recipeIngredient"] = items
                print(f"Enriched Ingredients: {items}")

    # Enrich Instructions
    if not data.get("recipeInstructions"):
        steps_div = soup.find(id="steps")
        if steps_div:
            steps = [
                {"@type": "HowToStep", "text": li.get_text(strip=True)}
                for li in steps_div.find_all("li")
            ]
            if steps:
                data["recipeInstructions"] = steps
                print(f"Enriched Instructions: {len(steps)} steps found")

    print(json.dumps(data, indent=2, ensure_ascii=False))


except Exception as e:
    print(f"Manual fetch failed: {e}")
