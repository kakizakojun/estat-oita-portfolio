# 大分県の市町村別に「高齢化率」と「財政力指数」の関係を散布図で見る
import urllib.request
import urllib.parse
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['font.family'] = 'Hiragino Sans'

# APIキーをファイルから読み込み
appid = open("appid.txt").read().strip()

# ①高齢化率を取得
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

クラス一覧 = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["CLASS_INF"]["CLASS_OBJ"]

# 地域コード　→ 市町村名に変換表の作成
名前 = {}
for 軸 in クラス一覧:
    if 軸["@id"] == "area":
        for c in 軸["CLASS"]:
            名前[c["@code"]] = c["@name"]

# 大分の１８市町村だけ「コード　→ 高齢化率」の辞書にする
高齢化 = {}
for v in 値リスト:
    code = v["@area"]
    if code.startswith("44") and len(code) == 5 and code != "44000":
        高齢化[code] = round(float(v["$"]),1)

print(高齢化)
print(名前["44201"])

# ②財政力指数を取得
params2 = {
    "appId": appid,
    "statsDataId": "0000020204",
    "cdCat01": "D2201",
    "cdTime": "2021100000",
    "limit": 100000,
}

api_url2 =  "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData?" + urllib.parse.urlencode(params2)
data2 = json.loads(urllib.request.urlopen(api_url2).read())
値リスト2 = data2["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]

# 大分の１８市町村だけ「コード　→ 財政力指数」の辞書にする
財政 = {}
for v in 値リスト2:
    code = v["@area"]
    if code.startswith("44") and len(code) == 5 and code != "44000":
        財政[code] = float(v["$"])

print(財政)

# 高齢化率と財政力を市町村コードをKeyに1つの表へ結合する
行リスト = []
for code in 高齢化:
    行リスト.append({
        "市町村": 名前[code],
        "高齢化率": 高齢化[code],
        "財政力": 財政[code],
    })

表 = pd.DataFrame(行リスト)
print(表)

# 高齢化率 ✖︎　財政力の散布図を描き、各点に市町村名を添えて保存
plt.scatter(表["高齢化率"], 表["財政力"])

for idx, row in 表.iterrows():
    plt.text(row["高齢化率"], row["財政力"], row["市町村"], fontsize = 8)

plt.xlabel("高齢化率(%)")
plt.ylabel("財政力指数")
plt.title("大分県 市町村別：高齢化率と財政力指数の関係")
plt.savefig("oita_finance.png")