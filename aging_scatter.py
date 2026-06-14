# 指定県の市町村別に「高齢化率」と「財政力指数」の関係を散布図で見る
# 対象の都道府県は config.py の PREF_NAME で切り替える

from config import PREF, PREF_NAME, 保存先
import urllib.request
import urllib.parse
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

matplotlib.rcParams['font.family'] = 'Hiragino Sans'

# 4象限分割は県内の「中央値」で行う（マトリクス分析の定石。県内で相対的に深刻な市町村が浮かぶ）。
# 加えて、制度・統計に根拠のある2つの値を“文脈線”として併記する。
不交付ライン = 1.0      # 財政力指数1.0＝地方交付税の「不交付/交付」の境界。これより下＝交付（自立できていない）団体
全国平均高齢化率 = 28.6  # 令和2年 国勢調査・全国の65歳以上人口割合（%）。県内の高齢化を全国と比べる基準


def run():
    plt.close("all")  # 前の図が残らないようにクリア（main.pyで連続実行するため）

    appid = open("appid.txt").read().strip()

    # ① 高齢化率を取得（令和2年 国勢調査）
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

    # 地域コード→市町村名 の変換表を作る
    クラス一覧 = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["CLASS_INF"]["CLASS_OBJ"]
    名前 = {}
    for 軸 in クラス一覧:
        if 軸["@id"] == "area":
            for c in 軸["CLASS"]:
                名前[c["@code"]] = c["@name"]

    # 指定県の市町村だけ「コード→高齢化率」の辞書にする
    高齢化 = {}
    for v in 値リスト:
        code = v["@area"]
        if code.startswith(PREF) and len(code) == 5 and code != PREF + "000":
            高齢化[code] = round(float(v["$"]), 1)

    # ② 財政力指数を取得（市区町村データ・2021年度）
    params2 = {
        "appId": appid,
        "statsDataId": "0000020204",
        "cdCat01": "D2201",
        "cdTime": "2021100000",
        "limit": 100000,
    }
    api_url2 = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData?" + urllib.parse.urlencode(params2)
    data2 = json.loads(urllib.request.urlopen(api_url2).read())
    値リスト2 = data2["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]

    # 指定県の市町村だけ「コード→財政力指数」の辞書にする
    財政 = {}
    for v in 値リスト2:
        code = v["@area"]
        if code.startswith(PREF) and len(code) == 5 and code != PREF + "000":
            財政[code] = float(v["$"])

    # 高齢化率と財政力を、両方にある市町村だけ コードを鍵に結合する
    行リスト = []
    for code in 高齢化:
        if code in 財政:
            行リスト.append({
                "市町村": 名前[code],
                "高齢化率": 高齢化[code],
                "財政力": 財政[code],
            })

    表 = pd.DataFrame(行リスト)

    # 4象限の分割線＝県内の中央値（県内で相対的に深刻な市町村を浮かび上がらせる）
    高齢化中央値 = 表["高齢化率"].median()
    財政中央値 = 表["財政力"].median()

    # 「重点支援ゾーン」＝ 高齢化率が県内中央値以上 かつ 財政力が県内中央値以下（右下の象限）
    表["重点支援"] = (表["高齢化率"] >= 高齢化中央値) & (表["財政力"] <= 財政中央値)
    print(表)
    print(f"\n県内中央値：高齢化率 {高齢化中央値:.1f}% / 財政力 {財政中央値:.2f}")
    print(f"重点支援ゾーン（高齢化率≥中央値 かつ 財政力≤中央値）：")
    print("、".join(表[表["重点支援"]]["市町村"].tolist()) or "該当なし")

    fig, ax = plt.subplots(figsize=(9, 7))

    # 軸の範囲（1.0の不交付ラインが必ず見えるよう、上端は1.0より少し上にとる）
    x最小, x最大 = 表["高齢化率"].min() - 2, 表["高齢化率"].max() + 3
    y最大 = max(表["財政力"].max(), 不交付ライン) + 0.08
    ax.set_xlim(x最小, x最大)
    ax.set_ylim(0, y最大)

    # 右下（高齢化率≥中央値 × 財政力≤中央値）を「重点支援ゾーン」として薄く着色
    ax.add_patch(Rectangle((高齢化中央値, 0), x最大 - 高齢化中央値, 財政中央値,
                           facecolor="#e74c3c", alpha=0.07, zorder=0))

    # 主軸：県内中央値の分割線（実線）
    ax.axvline(高齢化中央値, color="#555555", linestyle="-", linewidth=1.2)
    ax.axhline(財政中央値, color="#555555", linestyle="-", linewidth=1.2)
    ax.text(高齢化中央値, y最大, f" 県内中央値 {高齢化中央値:.1f}%", color="#555555",
            fontsize=9, va="top", ha="left")
    ax.text(x最小, 財政中央値, f" 県内中央値 {財政中央値:.2f}", color="#555555",
            fontsize=9, va="bottom", ha="left")

    # 文脈線：財政力1.0＝地方交付税の不交付ライン（点線・薄色）
    ax.axhline(不交付ライン, color="#bbbbbb", linestyle=":", linewidth=1)
    ax.text(x最小, 不交付ライン, " 財政力1.0＝不交付ライン（県内全市町村が下回る＝交付依存）",
            color="#999999", fontsize=8.5, va="bottom", ha="left")

    # 重点支援ゾーンのラベル
    ax.text(x最大 - 0.3, 0.04, "重点支援ゾーン\n（高齢化進行 × 財政ひっ迫）",
            color="#c0392b", fontsize=10.5, ha="right", va="bottom", weight="bold")

    # 点を描く（重点支援ゾーンは赤、それ以外はグレー）
    for _, row in 表.iterrows():
        重点 = row["重点支援"]
        ax.scatter(row["高齢化率"], row["財政力"],
                   color="#e74c3c" if 重点 else "#5b6770",
                   s=48 if 重点 else 30, zorder=3)
        ax.text(row["高齢化率"] + 0.25, row["財政力"], row["市町村"], fontsize=8,
                color="#c0392b" if 重点 else "#333333",
                weight="bold" if 重点 else "normal")

    # 凡例
    ax.legend(handles=[
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#e74c3c",
               markersize=9, label="重点支援ゾーンの市町村"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#5b6770",
               markersize=8, label="その他の市町村"),
    ], loc="upper right", fontsize=9)

    ax.set_xlabel("高齢化率（%）　→ 右ほど高齢化が進む")
    ax.set_ylabel("財政力指数　→ 上ほど財政が自立")
    ax.set_title(f"{PREF_NAME} 市町村別：高齢化率 × 財政力の優先度マトリクス")
    fig.tight_layout()
    fig.savefig(f"{保存先}/{PREF_NAME}_高齢化_財政力.png", dpi=120)


if __name__ == "__main__":
    run()
