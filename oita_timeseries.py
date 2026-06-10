# 大分県と全国の高齢化率の推移を折れ線グラフにする

import urllib.request
import urllib.parse
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Hiragino Sans'

# e-Stat APIから時系列データ（全国・大分県）を取得
appid = open("appid.txt").read().strip()
params = {
    "appId": appid,
    "statsDataId": "0003410383",
    "cdTab": "105",
    "cdCat01": "130",
    "cdArea": "00000,44000",
    "limit": 100000,
}

api_url =  "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData?" + urllib.parse.urlencode(params)
data = json.loads(urllib.request.urlopen(api_url).read())
値リスト = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]

# 年・地域・高齢化率を取り出して表にする（不詳補完値は除外）
行リスト = []
for v in 値リスト:
    if not v["@time"].endswith("000000"):
        continue
    年 = int(v["@time"][:4])
    率 = round(float(v["$"]),1)
    地域 = "全国" if v["@area"] == "00000" else "大分県"
    行リスト.append({"年": 年, "地域": 地域, "高齢化率": 率})

推移 = pd.DataFrame(行リスト)
print(推移)

# 地域ごとに分けて、2本の折れ線で描く
大分 = 推移[推移["地域"] == "大分県"]
全国 = 推移[推移["地域"] == "全国"]

plt.plot(大分["年"], 大分["高齢化率"], marker = "o", label = "大分県")
plt.plot(全国["年"], 全国["高齢化率"], marker = "o", label = "全国")

plt.legend()
plt.xlabel("年")
plt.ylabel("高齢化率（%）")
plt.title("大分県と全国の高齢化率の推移（1920〜2020年）")
plt.savefig("oita_timeseries.png")