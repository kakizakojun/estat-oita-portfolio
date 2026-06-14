# このファイルを実行すると、4つの分析グラフをまとめて出力する。
# 対象の都道府県は config.py の PREF_NAME を変えるだけで切り替わる。
#   実行: python3 main.py

import aging_bar
import aging_map
import aging_trend
import aging_scatter

from config import PREF_NAME

print(f"=== {PREF_NAME} の分析を開始します ===")

print("① 棒グラフ ...")
aging_bar.run()

print("② 地図（コロプレス図）...")
aging_map.run()

print("③ 時系列（推移）...")
aging_trend.run()

print("④ 散布図（高齢化率×財政力）...")
aging_scatter.run()

print(f"=== 完了：{PREF_NAME} の4つの画像を出力しました ===")
