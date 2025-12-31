import requests
import json

url = "http://localhost:8000/scrape"
payload = {"url": "https://www.webteb.com/diet/recipes/%D8%A7%D9%84%D9%84%D8%AD%D9%85%D8%A9-%D8%A7%D9%84%D9%85%D8%AD%D9%85%D8%B1%D8%A9-%D8%A8%D8%A7%D9%84%D8%AB%D9%88%D9%85_1350"}

try:
    response = requests.post(url, json=payload)
    data = response.json()
    
    # Check if instructions are present
    if "recipeInstructions" in data["data"] and data["data"]["recipeInstructions"]:
        print("Success! Instructions found.")
        print(f"Number of steps: {len(data['data']['recipeInstructions'])}")
    else:
        print("Failure: Instructions missing.")

    # Check ingredients
    if "recipeIngredient" in data["data"] and isinstance(data["data"]["recipeIngredient"], list) and len(data["data"]["recipeIngredient"]) > 1:
        print("Success! Ingredients found and is a list.")
        print(f"Number of ingredients: {len(data['data']['recipeIngredient'])}")
    else:
        print(f"Failure: Ingredients issue. Value: {data['data'].get('recipeIngredient')}")

    # Print full dump for user
    # print(json.dumps(data, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"Error: {e}")
