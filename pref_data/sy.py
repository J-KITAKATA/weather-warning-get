# 宗谷地方(北海道)処理用

import requests
from bs4 import BeautifulSoup
import xmltodict
import os
import json

# エリアのキーとコード
area_id = {"SN":"011011", "SS":"011012", "RR":"011013"}

# 警報
warn = {"02":"暴風雪", "03":"レベル3大雨", "04":"洪水", "05":"暴風", "06":"大雪", "07":"波浪", "08":"レベル3高潮", "09":"レベル3土砂災害"}

# 注意報
atn = {"10":"レベル2大雨", "12":"大雪", "13":"風雪", "14":"雷", "15":"強風", "16":"波浪", "17":"融雪", "18":"洪水", "19":"レベル2高潮", "20":"濃霧", "21":"乾燥", "22":"なだれ", "23":"低温", "24":"霜", "25":"着氷", "26":"着雪", "27":"その他", "29":"レベル2土砂災害"}

# 危険警報
U_warn = {"43":"レベル4大雨", "48":"レベル4高潮", "49":"レベル4土砂災害"}

# 特別警報
S_warn = {"32":"暴風雪", "33":"レベル5大雨", "35":"暴風", "36":"大雪", "37":"波浪", "38":"レベル5高潮", "39":"レベル5土砂災害"}

safe_text = "警報・注意報の発表なし" # 発表されていない時用の出力

syh = "北海道 宗谷地方" # 地域・エリアの名前

def search_vpws50(data_list, target_code):
    """
    VPWS50のHeadline内にあるInformationをすべて検索し、
    target_codeに一致するAreaの警報・注意報を取得する。
    """

    # 結果を格納するリスト
    atn_data = []
    warn_data = []
    U_warn_data = []
    S_warn_data = []

    # ----------------------------------------
    # Head → Headline → Information
    # ----------------------------------------
    headline = data_list["jmx:Report"]["Head"]["Headline"]

    informations = headline.get("Information", [])

    # Informationが1個しかない場合にも対応
    if not isinstance(informations, list):
        informations = [informations]

    # ----------------------------------------
    # 3種類あるInformationを全部調べる
    # ----------------------------------------
    for information in informations:

        items = information.get("Item", [])

        # Itemが1個だけの場合にも対応
        if not isinstance(items, list):
            items = [items]

        # ----------------------------------------
        # Itemを調べる
        # ----------------------------------------
        for item in items:

            # Item → Areas → Area
            areas = item.get("Areas", {}).get("Area", [])

            # Areaが1個だけの場合にも対応
            if not isinstance(areas, list):
                areas = [areas]

            # ----------------------------------------
            # AreaのCodeを調べる
            # ----------------------------------------
            for sub_area in areas:

                code = str(sub_area.get("Code", ""))

                # target_codeと一致しなければ次へ
                if code != str(target_code):
                    continue

                # ----------------------------------------
                # 該当AreaのKindを取得
                # ----------------------------------------
                kinds = item.get("Kind", [])

                # Kindが1個だけの場合にも対応
                if not isinstance(kinds, list):
                    kinds = [kinds]

                # ----------------------------------------
                # 警報・注意報を分類
                # ----------------------------------------
                for kind in kinds:

                    warning_code = kind.get("Code")

                    # Codeが存在しないものは無視
                    if warning_code is None:
                        continue

                    warning_code = str(warning_code)

                    # 注意報
                    if warning_code in atn:
                        atn_data.append(atn[warning_code])

                    # 警報
                    elif warning_code in warn:
                        warn_data.append(warn[warning_code])

                    # 危険警報
                    elif warning_code in U_warn:
                        U_warn_data.append(U_warn[warning_code])

                    # 特別警報
                    elif warning_code in S_warn:
                        S_warn_data.append(S_warn[warning_code])

    # ----------------------------------------
    # 重複削除
    # ----------------------------------------
    atn_data = list(dict.fromkeys(atn_data))
    warn_data = list(dict.fromkeys(warn_data))
    U_warn_data = list(dict.fromkeys(U_warn_data))
    S_warn_data = list(dict.fromkeys(S_warn_data))

    return atn_data, warn_data, U_warn_data, S_warn_data

def make_warning_text(result):
    """
    search_vpws50()の結果を出力用文字列に変換する
    """

    atn_data, warn_data, U_warn_data, S_warn_data = result

    p_data = ""

    if atn_data:
        p_data += f"注意報:{', '.join(atn_data)}\n"

    if warn_data:
        p_data += f"警報:{', '.join(warn_data)}\n"

    if U_warn_data:
        p_data += f"危険警報:{', '.join(U_warn_data)}\n"

    if S_warn_data:
        p_data += f"特別警報:{', '.join(S_warn_data)}\n"

    if not atn_data and not warn_data and not U_warn_data and not S_warn_data:
        p_data += safe_text + "\n"

    return p_data

def pros(CACHE_FILE, area):
    #ローカル変数
    # キャッシュ保持時間：630秒
    last_fetched_time = 0 # 最後にデータを取得した時刻（初期値: 0）
    p_data = "" # 文章用変数を初期化

    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    # キャッシュデータファイルから情報を読み取る
    with open(CACHE_FILE, mode="r", encoding="utf-8") as f:
        cache_json = json.load(f) # JSON -> dict型

    # cache_json 内のデータ(data に辞書型で格納)
    data_list = cache_json.get("data", [])

    if area == None or area == "":
        # 宗谷地方
        p_data = "**" + syh + "**\n"
        target_code = "011000" # 宗谷地方のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data

    elif area == "SN":
        # 宗谷北部
        p_data = "**" + syh + " 宗谷北部**\n"
        target_code = area_id[area] # 宗谷北部 のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "SS":
        # 宗谷南部
        p_data = "**" + syh + " 宗谷南部**\n"
        target_code = area_id[area] # 宗谷南部 のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "RR":
        # 利尻・礼文
        p_data = "**" + syh + " 利尻・礼文**\n"
        target_code = area_id[area] # 利尻・礼文 のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    else:
        msg = syh + "に指定した地域・エリアが存在しません"
        return msg