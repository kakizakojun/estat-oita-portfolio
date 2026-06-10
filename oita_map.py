# 大分県の市町村別　高齢化率を地図上に色分け（コロプレス図）する

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patheffects as pe
matplotlib.rcParams['font.family'] = 'Hiragino Sans'

# 境界データ（GeoJSON）をURLから読み込む
url = "https://raw.githubusercontent.com/smartnews-smri/japan-topography/main/data/municipality/geojson/s0010/N03-21_44_210101.json"

地図 = gpd.read_file(url)

import urllib.request
import urllib.parse
import json
import pandas as pd

# e-Stat APIから高齢化率を取得する
appid = open("appid.txt").read().strip()
params = {
    "appId": appid,
    "statsDataId": "0003448299",
    "cdTab": "105",
    "cdCat01": "130",
    "cdCat02": "100",
    "limit": 100000,
}

api_url =  "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData?" + urllib.parse.urlencode(params)
data = json.loads(urllib.request.urlopen(api_url).read())

値リスト = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]

# コードと高齢化率を取得し、表にする
行リスト = []
for v in 値リスト:
    code = v["@area"]
    if code.startswith("44") and len(code) == 5 and code != "44000":
        rate = round(float(v["$"]),1)
        行リスト.append({"コード": code, "高齢化率": rate})

高齢化 = pd.DataFrame(行リスト)

# 地図と高齢化率を結合、表にする
地図 = 地図.merge(高齢化 , left_on= "N03_007", right_on= "コード")
print(地図[["N03_004", "高齢化率"]])

# 高齢化率を市町村ごとに色分け、市町村名も記載し、画像保存する
ax = 地図.plot(column = "高齢化率", cmap="OrRd", legend = True, edgecolor="black", figsize=(10,10))
for idx, row in 地図.iterrows():
    中心 = row["geometry"].centroid
    ax.text(中心.x, 中心.y, row["N03_004"], ha = "center", fontsize=7,
    path_effects=[pe.withStroke(linewidth=2, foreground="white")])

plt.title("大分県 市町村別の高齢化率（令和2年 国勢調査）")
plt.savefig("oita_map.png")