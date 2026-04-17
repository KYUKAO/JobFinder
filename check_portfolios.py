import json
with open('portfolios.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'portfolios count: {len(data.get("portfolios", []))}')
print(f'updated: {data.get("updated")}')
