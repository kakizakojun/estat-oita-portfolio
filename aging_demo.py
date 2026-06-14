# -*- coding: utf-8 -*-
# 大分県の市町村別 高齢化率（65歳以上の割合）を可視化する
# ※このファイルのデータは「デモ用のサンプル値」です。
#   仕組みを理解したあと、e-Statでダウンロードした本物のデータに差し替えます。

import pandas as pd                  # 表（データ）を扱うための道具
import matplotlib.pyplot as plt      # グラフを描くための道具
import matplotlib                    # 日本語フォント設定のため
from matplotlib import font_manager

# 日本語が「□□□」と文字化けしないようにフォントを指定する
matplotlib.rcParams['font.family'] = 'Hiragino Sans'

# --- 1. データを用意する（今はデモ用の手入力。あとで本物に差し替え）---
# 市町村名と、65歳以上人口の割合(%)のペア
data = {
    "市町村": ["大分市", "別府市", "中津市", "日田市", "佐伯市", "臼杵市",
              "津久見市", "竹田市", "豊後高田市", "杵築市", "宇佐市", "豊後大野市",
              "由布市", "国東市", "姫島村", "日出町", "九重町", "玖珠町"],
    "高齢化率": [27.5, 35.8, 30.2, 38.1, 41.5, 39.7,
              44.2, 45.6, 40.3, 37.9, 36.4, 43.8,
              33.1, 42.0, 47.3, 28.6, 41.1, 38.5],
}

# pandasの「DataFrame」という表の形に変換する
df = pd.DataFrame(data)

# --- 2. データを加工する（高齢化率が高い順に並べ替え）---
df = df.sort_values("高齢化率", ascending=True)  # 横棒グラフ用に昇順

# --- 3. グラフを描く ---
plt.figure(figsize=(10, 8))                       # グラフの大きさ
plt.barh(df["市町村"], df["高齢化率"], color="#4C72B0")  # 横棒グラフ
plt.xlabel("65歳以上人口の割合 (%)")               # 横軸のラベル
plt.title("大分県 市町村別の高齢化率（デモ用サンプルデータ）")  # タイトル

# 各棒の右端に数値を書き込む
for i, value in enumerate(df["高齢化率"]):
    plt.text(value + 0.3, i, f"{value}%", va="center")

plt.tight_layout()                                # レイアウトを整える
plt.savefig("aging_demo.png", dpi=120)            # 画像ファイルとして保存
print("グラフを aging_demo.png に保存しました。")

# --- 4. 簡単な考察を数字で出す ---
top = df.iloc[-1]    # 最も高い市町村
bottom = df.iloc[0]  # 最も低い市町村
print(f"最も高齢化率が高い: {top['市町村']} ({top['高齢化率']}%)")
print(f"最も高齢化率が低い: {bottom['市町村']} ({bottom['高齢化率']}%)")
print(f"県内の差: {round(top['高齢化率'] - bottom['高齢化率'], 1)} ポイント")