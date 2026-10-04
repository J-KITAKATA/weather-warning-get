import requests
from bs4 import BeautifulSoup
import xmltodict
import os
import json

# エリアのキーとコード
area_id = {"MO":"030011", "NN":"030012", "HN":"030013", "TO":"030014", "OK":"030015", "RB":"030016", "KJ":"030021", "MK":"030022", "KI":"030031", "OF":"030032"}

# 警報
warn = {"02":"暴風雪", "03":"レベル3大雨", "04":"洪水", "05":"暴風", "06":"大雪", "07":"波浪", "08":"レベル3高潮", "09":"レベル3土砂災害"}

# 注意報
atn = {"10":"レベル2大雨", "12":"大雪", "13":"風雪", "14":"雷", "15":"強風", "16":"波浪", "17":"融雪", "18":"洪水", "19":"レベル2高潮", "20":"濃霧", "21":"乾燥", "22":"なだれ", "23":"低温", "24":"霜", "25":"着氷", "26":"着雪", "27":"その他", "29":"レベル2土砂災害"}

# 危険警報
U_warn = {"43":"レベル4大雨", "48":"レベル4高潮", "49":"レベル4土砂災害"}

# 特別警報
S_warn = {"32":"暴風雪", "33":"レベル5大雨", "35":"暴風", "36":"大雪", "37":"波浪", "38":"レベル5高潮", "39":"レベル5土砂災害"}

safe_text = "警報・注意報の発表なし" # 発表されていない時用の出力

pn = "岩手県"

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

    #print(entries)

    if area == None or area == "":
        # 内陸
        p_data = "**" + pn + " 内陸**\n"
        target_code = "030010" # 内陸のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        # 沿岸北部
        p_data = p_data + "\n" + "**" + pn + " 沿岸北部**\n"
        target_code = "030020" # 沿岸北部のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        # 沿岸南部
        p_data = p_data + "\n" + "**" + pn + " 沿岸南部**\n"
        target_code = "030030" # 沿岸南部のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "MO":
        # 盛岡地域
        p_data = "**" + pn + " 盛岡地域**\n"
        target_code = area_id[area] # 盛岡地域のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "NN":
        # 二戸地域
        p_data = "**" + pn + " 二戸地域**\n"
        target_code = area_id[area] # 二戸地域のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "HN":
        # 花北地域
        p_data = "**" + pn + " 花北地域**\n"
        target_code = area_id[area] # 花北地域のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "TO":
        # 遠野地域
        p_data = "**" + pn + " 遠野地域**\n"
        target_code = area_id[area] # 遠野地域のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "OK":
        # 奥州金ケ崎地域
        p_data = "**" + pn + " 奥州金ケ崎地域**\n"
        target_code = area_id[area] # 奥州金ケ崎地域のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "RB":
        # 両磐地域
        p_data = "**" + pn + " 両磐地域**\n"
        target_code = area_id[area] # 両磐地域のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "KJ":
        # 久慈地域
        p_data = "**" + pn + " 久慈地域**\n"
        target_code = area_id[area] # 久慈地域のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "MK":
        # 宮古地域
        p_data = "**" + pn + " 宮古地域**\n"
        target_code = area_id[area] # 宮古地域のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "KI":
        # 釜石地域
        p_data = "**" + pn + " 釜石地域**\n"
        target_code = area_id[area] # 釜石地域のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    elif area == "OF":
        # 大船渡地域
        p_data = "**" + pn + " 大船渡地域**\n"
        target_code = area_id[area] # 群馬県 前橋・桐生地域のターゲットコード

        # 指定地域のデータを抽出
        result = search_vpws50(data_list, target_code)

        p_data += make_warning_text(result)

        return p_data
    
    else:
        msg = pn + "に指定した地域・エリアが存在しません"
        return msg