# 都道府県の市町村別 高齢化率を棒グラフにする
# 対象の都道府県は config.py の PREF_NAME で切り替える

from config import PREF, PREF_NAME, 保存先
import urllib.request
import urllib.parse
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['font.family'] = 'Hiragino Sans'


def run():
    plt.close("all")  # 前の図が残らないようにクリア（main.pyで連続実行するため）

    # appid.txt からAPIキーを読み込む
    appid = open("appid.txt").read().strip()

    # APIに渡す条件（割合・65歳以上・男女総数）を設定
    params = {
        "appId": appid,
        "statsDataId": "0003448299",
        "cdTab": "105",
        "cdCat01": "130",
        "cdCat02": "100",
        "limit": 100000,
    }
    url = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData?" + urllib.parse.urlencode(params)

    # APIにアクセスし、返ってきたJSONを受け取る
    res = urllib.request.urlopen(url)
    data = json.loads(res.read())

    値リスト = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
    クラス一覧 = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["CLASS_INF"]["CLASS_OBJ"]

    # 地域コード→市町村名 の変換表を作る
    地域名 = {}
    for 軸 in クラス一覧:
        if 軸["@id"] == "area":
            for c in 軸["CLASS"]:
                地域名[c["@code"]] = c["@name"]

    # 指定県の市町村だけ取り出してリストに格納
    行リスト = []
    for v in 値リスト:
        code = v["@area"]
        if code.startswith(PREF) and len(code) == 5 and code != PREF + "000":
            name = 地域名[code]
            rate = round(float(v["$"]), 1)
            行リスト.append({"市町村": name, "高齢化率": rate})

    表 = pd.DataFrame(行リスト)

    # 高齢化率の低い順に並べ、市町村数に応じて高さを自動調整して描画・保存
    表 = 表.sort_values("高齢化率", ascending=True)
    plt.figure(figsize=(10, len(表) * 0.3))
    plt.barh(表["市町村"], 表["高齢化率"])

    plt.title(f"{PREF_NAME}市町村別高齢化率")
    plt.ylabel("市町村")
    plt.xlabel("65歳以上人口の割合 (%)")

    for 番号, 値 in enumerate(表["高齢化率"]):
        plt.text(値, 番号, f"{値}%")

    plt.margins(y=0.01)
    plt.tight_layout()
    plt.savefig(f"{保存先}/{PREF_NAME}_高齢化_棒グラフ.png")

    # 最も高い・低い市町村と差を計算して表示
    high = 表.iloc[-1]
    low = 表.iloc[0]
    print(f"最も高い：{high['市町村']}({high['高齢化率']}%)")
    print(f"最も低い：{low['市町村']}({low['高齢化率']}%)")
    差 = high["高齢化率"] - low["高齢化率"]
    print(f"差：{round(差, 1)}ポイント")


if __name__ == "__main__":
    run()
