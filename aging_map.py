# 都道府県の市町村別 高齢化率を地図に色分け（コロプレス図）する
# 対象の都道府県は config.py の PREF_NAME で切り替える

from config import PREF, PREF_NAME, 保存先
import urllib.request
import urllib.parse
import json
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patheffects as pe

matplotlib.rcParams['font.family'] = 'Hiragino Sans'


def run():
    plt.close("all")  # 前の図が残らないようにクリア（main.pyで連続実行するため）

    # 境界データ（GeoJSON）をURLから読み込む
    url = f"https://raw.githubusercontent.com/smartnews-smri/japan-topography/main/data/municipality/geojson/s0010/N03-21_{PREF}_210101.json"
    地図 = gpd.read_file(url)

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
    api_url = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData?" + urllib.parse.urlencode(params)
    data = json.loads(urllib.request.urlopen(api_url).read())
    値リスト = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]

    # コードと高齢化率を取り出して表にする
    行リスト = []
    for v in 値リスト:
        code = v["@area"]
        if code.startswith(PREF) and len(code) == 5 and code != PREF + "000":
            rate = round(float(v["$"]), 1)
            行リスト.append({"コード": code, "高齢化率": rate})

    高齢化 = pd.DataFrame(行リスト)

    # 地図と高齢化率を市町村コードで結合する
    地図 = 地図.merge(高齢化, left_on="N03_007", right_on="コード")

    # 高齢化率で色分けし、各市町村名を重ねて描画
    ax = 地図.plot(column="高齢化率", cmap="OrRd", legend=True, edgecolor="black", figsize=(10, 10))
    for idx, row in 地図.iterrows():
        中心 = row["geometry"].centroid
        ax.text(中心.x, 中心.y, row["N03_004"], ha="center", fontsize=7,
                path_effects=[pe.withStroke(linewidth=2, foreground="white")])

    # 東京都だけ：本土にズームし、離島を別枠（インセット）で表示する
    # （島が連続して連なる県は自動処理が難しいため、多島地域は東京のみ個別対応）
    if PREF == "13":
        中心x = 地図.geometry.centroid.x
        中心y = 地図.geometry.centroid.y

        def 範囲(座標):
            q1 = 座標.quantile(0.25)
            q3 = 座標.quantile(0.75)
            iqr = q3 - q1
            return q1 - 1.5 * iqr, q3 + 1.5 * iqr

        x0, x1 = 範囲(中心x)
        y0, y1 = 範囲(中心y)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)

        離島 = 地図[(中心x < x0) | (中心x > x1) | (中心y < y0) | (中心y > y1)]
        if len(離島) > 0:
            内枠 = ax.inset_axes([0.62, 0.02, 0.36, 0.36])
            離島.plot(ax=内枠, column="高齢化率", cmap="OrRd", edgecolor="black",
                      vmin=地図["高齢化率"].min(), vmax=地図["高齢化率"].max())
            内枠.set_xticks([])
            内枠.set_yticks([])
            内枠.set_title("離島", fontsize=9)

    plt.title(f"{PREF_NAME} 市町村別の高齢化率（令和2年 国勢調査）")
    plt.savefig(f"{保存先}/{PREF_NAME}_高齢化_地図.png")


if __name__ == "__main__":
    run()
