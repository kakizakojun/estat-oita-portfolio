
# 大分県の市町村別　高齢化率をAPIから取得してグラフにする

import urllib.request
import urllib.parse
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['font.family'] = 'Hiragino Sans'

# appid.txtからAPIキー取得

appid = open("appid.txt").read().strip()

# APIに渡す条件を設定

params = {
    "appId": appid,
    "statsDataId": "0003448299",
    "cdTab": "105",
    "cdCat01": "130",
    "cdCat02": "100",
    "limit": 100000,
}

url =  "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData?" + urllib.parse.urlencode(params)

# APIにアクセス。返ってきたJSONを受け取る

res = urllib.request.urlopen(url)
data = json.loads(res.read())

値リスト = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
クラス一覧 = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["CLASS_INF"]["CLASS_OBJ"]

# 地域コードを市町村名に変換した表の作成

地域名 = {}

for 軸 in クラス一覧:
    if 軸["@id"] == "area":
        地域軸 = 軸

        for c in 地域軸["CLASS"]:
            地域名[c["@code"]] = c["@name"]

# 大分県の市町村だけ取り出しリストに格納
# 値リストのKeyは、print(値リスト[0].keys())で確認

行リスト = []
for v in 値リスト:
    code = v["@area"]
    if code.startswith("44") and len(code) == 5 and code != "44000":
        name = 地域名[code]
        rate = round(float(v["$"]), 1)
        行リスト.append({"市町村": name, "高齢化率": rate})

表 = pd.DataFrame(行リスト)

# 高齢化率の低い順に並べ、画像保存

表 = 表.sort_values("高齢化率", ascending = True)
横 = plt.barh(表["市町村"], 表["高齢化率"])

plt.title("大分県市町村別高齢化率")
plt.ylabel("市町村")
plt.xlabel("65歳以上人口の割合 (%)")

for 番号 , 値 in enumerate(表["高齢化率"]):
    plt.text(値,番号,f"{値}%")

plt.savefig("oita_aging.png")

# 最も高い、低い市町村と差を計算

high = 表.iloc[-1]
low = 表.iloc[0]

print(f"最も高い：{high['市町村']}({high['高齢化率']}%)")
print(f"最も低い：{low['市町村']}({low['高齢化率']}%)")

差 = high["高齢化率"] - low["高齢化率"]
print(f"差：{round(差,1)}ポイント")