# -*- coding: utf-8 -*-
# 大分県の市町村別 高齢化率（65歳以上の割合）を
# 政府統計API（e-Stat API）から自動取得して可視化する。
#
# 使うデータ：令和2年 国勢調査
#   「年齢（3区分），男女別人口及び年齢別割合 － 都道府県，市区町村」
#   statsDataId = 0003448299
#
# 手入力をやめ、APIを叩いて毎回最新の本物データを取りに行く形にした。
# （データが更新されても、このスクリプトを再実行するだけで作り直せる）

import os
import json
import urllib.request
import urllib.parse

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# 日本語が「□□□」と文字化けしないようにフォントを指定
matplotlib.rcParams['font.family'] = 'Hiragino Sans'


# =========================================================
# 0. 設定
# =========================================================

# APIキー（appId）は「パスワード相当」なのでコードに直接書かない。
#   優先順位1: 環境変数 ESTAT_APP_ID
#   優先順位2: 同じフォルダの appid.txt の中身
# どちらも .gitignore でGitHub公開対象から除外する。
def load_app_id():
    app_id = os.environ.get("ESTAT_APP_ID")
    if app_id:
        return app_id.strip()
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "appid.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    raise SystemExit(
        "APIキー（appId）が見つかりません。\n"
        "  ・このフォルダに appid.txt を作り、e-Statで発行したappIdを書き込む\n"
        "  ・または環境変数 ESTAT_APP_ID に設定する\n"
        "のどちらかをしてください。"
    )


APP_ID = load_app_id()
STATS_DATA_ID = "0003448299"  # 令和2年 国勢調査 年齢3区分 都道府県市区町村
BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"


def call_api(endpoint, params):
    """e-Stat APIを呼んでJSON（辞書）を返す共通関数。"""
    params = {"appId": APP_ID, **params}
    url = f"{BASE}/{endpoint}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as res:
        return json.loads(res.read().decode("utf-8"))


# =========================================================
# 1. メタ情報（表の構造）を取得する
#    どの軸（年齢・男女・割合・地域）がどんなコードか、を先に調べる
# =========================================================

def as_list(x):
    """e-StatのJSONは要素が1個だと辞書、複数だとリストになる。常にリストに揃える。"""
    if isinstance(x, list):
        return x
    return [x]


print("① 表の構造（メタ情報）を取得中 ...")
meta = call_api("getMetaInfo", {"statsDataId": STATS_DATA_ID})
class_objs = meta["GET_META_INFO"]["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"]


def find_class(keyword):
    """軸を探す。名前の部分一致、または id の完全一致で見つける。
    （地域軸は名前が『全国，都道府県，市区町村』なので id='area' で探す）"""
    for obj in class_objs:
        if keyword in obj["@name"] or keyword == obj["@id"]:
            return obj
    raise SystemExit(f"軸『{keyword}』が見つかりませんでした。")


def find_code(class_obj, value_name):
    """軸の中から、区分名（例：'65歳以上'）に一致するコードを返す。"""
    for c in as_list(class_obj["CLASS"]):
        if c["@name"] == value_name:
            return c["@code"]
    # 完全一致しない場合は部分一致でも探す
    for c in as_list(class_obj["CLASS"]):
        if value_name in c["@name"]:
            return c["@code"]
    raise SystemExit(f"区分『{value_name}』が見つかりませんでした。")


def filter_param_name(class_obj):
    """軸のidから、絞り込み用パラメータ名を作る。 例: 'cat01' -> 'cdCat01'"""
    cid = class_obj["@id"]
    return "cd" + cid[0].upper() + cid[1:]


# 欲しい組み合わせ：表章項目=割合 / 年齢=65歳以上 / 男女=総数
age_class = find_class("年齢")
sex_class = find_class("男女")
tab_class = find_class("表章")  # 人口 or 割合

age_code = find_code(age_class, "65歳以上")
sex_code = find_code(sex_class, "総数")
tab_code = find_code(tab_class, "割合")

# 地域コード→市町村名の対応表を作る（あとで番号を名前に直すため）
area_class = find_class("area")
area_name = {c["@code"]: c["@name"] for c in as_list(area_class["CLASS"])}

print("  → 年齢『65歳以上』, 男女『総数』, 表章『割合』のコードを特定しました。")


# =========================================================
# 2. 実データを取得する（軸を固定し、地域は全件取ってから大分だけ抽出）
# =========================================================

print("② 実データを取得中 ...")
data_params = {
    "statsDataId": STATS_DATA_ID,
    filter_param_name(tab_class): tab_code,
    filter_param_name(age_class): age_code,
    filter_param_name(sex_class): sex_code,
    "limit": 100000,
}
res = call_api("getStatsData", data_params)
values = res["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]


# =========================================================
# 3. 大分県の市町村だけ取り出して表（DataFrame）にする
# =========================================================
# 大分県の地域コードは 44 で始まる5桁。
#   44000 = 県全体の合計（これだけ除外）
#   それ以外の 44xxx が、18の市町村
#   （この表には郡などの小計行は無いので、県合計を除けば市町村だけになる）
rows = []
for v in values:
    code = v.get("@area", "")
    if len(code) == 5 and code.startswith("44") and code != "44000":
        name = area_name.get(code, code)
        rate = v.get("$", "")
        try:
            rate = round(float(rate), 1)  # 27.89166 → 27.9 に丸めて見やすく
        except ValueError:
            continue  # 「-」など数値でない値はスキップ
        rows.append({"市町村": name, "高齢化率": rate})

df = pd.DataFrame(rows)
if df.empty:
    raise SystemExit("大分県の市町村データが取得できませんでした。条件を確認してください。")

df = df.sort_values("高齢化率", ascending=True)  # 横棒グラフ用に昇順


# =========================================================
# 4. グラフを描いて保存する
# =========================================================
plt.figure(figsize=(10, 8))
plt.barh(df["市町村"], df["高齢化率"], color="#4C72B0")
plt.xlabel("65歳以上人口の割合 (%)")
plt.title("大分県 市町村別の高齢化率（令和2年 国勢調査・e-Stat APIより取得）")

for i, value in enumerate(df["高齢化率"]):
    plt.text(value + 0.3, i, f"{value}%", va="center")

plt.tight_layout()
plt.savefig("oita_aging.png", dpi=120)
print("③ グラフを oita_aging.png に保存しました。")


# =========================================================
# 5. 簡単な考察を数字で出す
# =========================================================
top = df.iloc[-1]
bottom = df.iloc[0]
print(f"   対象: 大分県内 {len(df)} 市町村")
print(f"   最も高齢化率が高い: {top['市町村']} ({top['高齢化率']}%)")
print(f"   最も高齢化率が低い: {bottom['市町村']} ({bottom['高齢化率']}%)")
print(f"   県内の差: {round(top['高齢化率'] - bottom['高齢化率'], 1)} ポイント")
