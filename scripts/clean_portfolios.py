import json, sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/portfolios.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Only remove entries that are VERY clearly NOT game TA
# Be conservative - keep borderline entries
exclude_bvids = {
    'BV1GK411s7tT',  # SM作曲家俞永镇作品集 - composer
    'BV1uj411v7Sj',  # LISZT piano technical study - music
    'BV1bRw4z7E25',  # PLAVE demo - music/dance
    'BV16NwweNE8W',  # 万能青年旅店 album - music
    'BV1Ag411X7kA',  # BTS I NEED U demo - music
    'BV11zfKY2EBG',  # 苏丹游戏菜单音乐 - game music
    'BV1PySfBwEQp',  # 一半一半 demo - music
    'BV1AzD7B7EZn',  # 心愿便利贴 demo - music
    'BV1HSDyBsE3L',  # Danielle demo - music
    'BV1okXZBWEE7',  # 罗大佑 demo - music
    'BV1XiYSeMEBx',  # 李羲承 demo - music
    'BV1DF411N7eN',  # Portfolio Selection finance - finance
    'BV1Ka4y147ju',  # FactSet Portfolio Analysis - finance
    'BV1bc411M7nD',  # Portfolio build Nuxt/GraphQL - web dev
    'BV1734y157b8',  # Figma设计作品集 - portfolio tutorial
    'BV19o4y1o7AK',  # Brown University portfolio - college
    'BV1sx411g7Yh',  # RMIT portfolio - animation school
    'BV1R7411v77v',  # 建筑学学生作品集 - architecture
    'BV1iM411H7AW',  # 电商设计作品集 - e-commerce
    'BV19s411Q7Az',  # Advertisement media portfolio - ad
    'BV1FoQEBUEYs',  # Video Production portfolio - film
    'BV1ov2UB1Eer',  # Geometry Dash competitive - game content
    'BV1DbPSznEnj',  # 23份作品集点评 - portfolio critique
    'BV18CPsesEEc',  # 设计人作品集全攻略 - design guide
    'BV1oG4y1Z7Vh',  # 游戏美术行业薪资 - industry
    'BV1jy4y1T7fz',  # 游戏原画应聘准备 - art tips
    'BV1mUDDBJESd',  # 光影积累 - light reference
    'BV1ea7SzxE11',  # Who is TA - explanation
    'BV1uF411b79q',  # Origin水印 - software tip
    'BV1TfQ7BtEAk',  # 游戏买量视频设计师 - marketing, not TA
    'BV1ZM4m127zR',  # 绝区零美术和动画分析 - game analysis, not portfolio
    'BV1ZmE5w4EJW',  # 歌曲demo - music (if exists)
}

kept = []
removed = 0

for p in data['portfolios']:
    bvid = p.get('bvid', '')
    if bvid in exclude_bvids:
        removed += 1
        print(f"REMOVE: {bvid} | {p.get('title', '')[:50]}")
        continue
    kept.append(p)

print(f"\nKept: {len(kept)}, Removed: {removed}, Total: {len(data['portfolios'])}")

data['portfolios'] = kept
data['updated'] = '2026-04-18'

with open('data/portfolios.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done")
