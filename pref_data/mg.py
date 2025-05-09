import requests
from bs4 import BeautifulSoup
import xmltodict
import os
import json

# エリアのキーとコード
area_id = {"ES":"040011", "IS":"040012", "EO":"040013", "KN":"040014", "ESN":"040015", "KR":"040016", "WS":"040021", "WSN":"040022", "WO":"040023", "WK":"040024"}

# 警報
warn = {"02":"暴風雪", "03":"大雨", "04":"洪水", "05":"暴風", "06":"大雪", "07":"波浪", "08":"高潮"}

# 注意報
atn = {"10":"大雨", "12":"大雪", "13":"風雪", "14":"雷", "15":"強風", "16":"波浪", "17":"融雪", "18":"洪水", "19":"高潮", "20":"濃霧", "21":"乾燥", "22":"なだれ", "23":"低温", "24":"霜", "25":"着氷", "26":"着雪", "27":"その他"}

# 特別警報
S_warn = {"32":"暴風雪", "33":"大雨", "35":"暴風", "36":"大雪", "37":"波浪", "38":"高潮"}

# キャッシュを保存するファイル名
CACHE_FILE = "./cache/miyagi_cache.json"
# フォルダを作成（すでにあればスルー）
# os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

safe_text = "警報・注意報の発表なし" # 発表されていない時用の出力

pn = "宮城県"

def pros(url, area, n_time):
    #ローカル変数
    cached_data = None # キャッシュ用の変数
    # キャッシュ保持時間：630秒
    last_fetched_time = 0 # 最後にデータを取得した時刻（初期値: 0）
    p_data = "" # 文章用変数を初期化

    # 結果を格納するリスト(初期化)
    atn_data = [] # 注意報
    warn_data = [] # 警報
    S_warn_data = [] # 特別警報

    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    # キャッシュデータをファイルから読み込む
    # 空でないか確認 and キャッシュファイルが存在するかチェック
    if os.path.exists(CACHE_FILE) and os.path.getsize(CACHE_FILE) > 0:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            try:
                cache_content = json.load(f)  # JSONデータを読み込む
                cached_data = cache_content.get("data")  # 保存されていたデータを取得
                last_fetched_time = cache_content.get("timestamp", 0)  # 最後の取得時刻を取得（なければ0）
            except json.JSONDecodeError: # JSONファイル読み込みエラー時の処理
                cached_data = None  # JSONが壊れていた場合はNoneに
                last_fetched_time = 0  # 取得時刻もリセット

    if not url == None:
        if (n_time - last_fetched_time) > 630:
            print("(MG)新しいデータを取得中...")
            # 気象庁のデータフィードURL
            feed_xml = requests.get(url) # XMLデータを取得

            # XMLデータを解析して文字列に変換
            feed_soup = str(BeautifulSoup(feed_xml.content, "xml"))
            feed_dict = xmltodict.parse(feed_soup) # XMLを辞書型（dict）に変換

            # キャッシュを更新
            cached_data = feed_dict
            last_fetched_time = n_time

            # キャッシュをファイルに保存
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"timestamp": last_fetched_time, "data": cached_data}, f, ensure_ascii=False, indent=4)

        elif (n_time - last_fetched_time) <= 630:
            print("(MG)キャッシュデータを使用")

    else:
        print("No Data")

    # キャッシュデータファイルから情報を読み取る
    if cached_data:
        with open(CACHE_FILE, mode="r", encoding="utf-8") as f:
            cache_json = json.load(f) # JSON -> dict型
    
    # cache_json 内のデータ(data に辞書型で格納)
    data_list = cache_json.get("data", [])

    # 内部データ構造： 
    # "data":{"jmx.Report":{"Head":{"Headline":{"Information":[]}]}}}}
    entries = data_list["jmx:Report"]["Head"]["Headline"]["Information"]

    #print(entries)

    if area == None or area == "":
        # 東部
        p_data = "**" + pn + " 東部**\n"
        target_code = "040010" # 東部のターゲットコード

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        #print(atn_data) # debug
        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"
        
        #print(p_data) # debug
        
        # 西部
        p_data = p_data + "\n" + "**" + pn + " 西部**\n"
        target_code = "040020" # 西部のターゲットコード

        # データ格納部の初期化
        atn_data = [] # 注意報
        warn_data = [] # 警報
        S_warn_data = [] # 特別警報

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        
        
        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"
    
        return p_data
    
    elif area == "ES":
        # 東部仙台
        p_data = "**" + pn + " 東部仙台**\n"
        target_code = area_id[area] # 東部仙台のターゲットコード

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"

        return p_data
    
    elif area == "IS":
        # 石巻地域
        p_data = "**" + pn + " 石巻地域**\n"
        target_code = area_id[area] # 石巻地域のターゲットコード

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"

        return p_data
    
    elif area == "EO":
        # 東部大崎
        p_data = "**" + pn + " 東部大崎**\n"
        target_code = area_id[area] # 東部大崎のターゲットコード

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"

        return p_data
    
    elif area == "KN":
        # 気仙沼地域
        p_data = "**" + pn + " 気仙沼地域**\n"
        target_code = area_id[area] # 気仙沼地域のターゲットコード

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"

        return p_data
    
    elif area == "ESN":
        # 東部仙南
        p_data = "**" + pn + " 東部仙南**\n"
        target_code = area_id[area] # 東部仙南のターゲットコード

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"

        return p_data
    
    elif area == "KR":
        # 登米・東部栗原
        p_data = "**" + pn + " 登米・東部栗原**\n"
        target_code = area_id[area] # 登米・東部栗原のターゲットコード

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"

        return p_data
    
    elif area == "WS":
        # 西部仙台
        p_data = "**" + pn + " 西部仙台**\n"
        target_code = area_id[area] # 西部仙台のターゲットコード

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"

        return p_data
    
    elif area == "WSN":
        # 西部仙南
        p_data = "**" + pn + " 西部仙南**\n"
        target_code = area_id[area] # 西部仙南のターゲットコード

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"

        return p_data
    
    elif area == "WO":
        # 西部大崎
        p_data = "**" + pn + " 西部大崎**\n"
        target_code = area_id[area] # 西部大崎のターゲットコード

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"

        return p_data
    
    elif area == "WK":
        # 西部栗原
        p_data = "**" + pn + " 西部栗原**\n"
        target_code = area_id[area] # 西部栗原のターゲットコード

        # entries をループして指定地域のデータを抽出
        for entry in entries:
            items = entry.get("Item", [])
            if not isinstance(items, list):  # Item がリストでない場合はリストに変換
                items = [items]

            for item in items:
                area_d = item.get("Areas", {}).get("Area", {})
                if isinstance(area_d, list):  # Area がリストの場合
                    for sub_area in area_d:
                        if sub_area.get("Code") == target_code: # == target_code
                            kinds = item.get("Kind", [])
                            if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                                kinds = [kinds]
                            for kind in kinds:
                                code = kind.get("Code")
                                if code in atn:
                                    atn_data.append(atn[code])
                                elif code in warn:
                                    warn_data.append(warn[code])
                                elif code in S_warn:
                                    S_warn_data.append(S_warn[code])
                elif area_d.get("Code") == target_code:  # Area が辞書の場合
                    kinds = item.get("Kind", [])
                    if not isinstance(kinds, list):  # Kind がリストでない場合はリストに変換
                        kinds = [kinds]
                    for kind in kinds:
                        code = kind.get("Code")
                        if code in atn:
                            atn_data.append(atn[code])
                        elif code in warn:
                            warn_data.append(warn[code])
                        elif code in S_warn:
                            S_warn_data.append(S_warn[code])

        # 重複を削除
        atn_data = list(dict.fromkeys(atn_data))
        warn_data = list(dict.fromkeys(warn_data))
        S_warn_data = list(dict.fromkeys(S_warn_data))

        # 注意報・警報・特別警報の出力部
        if atn_data:
            p_data = p_data + f"注意報:{', '.join(atn_data)}\n"
        if warn_data:
            p_data = p_data + f"警報:{', '.join(warn_data)}\n"
        if S_warn_data:
            p_data = p_data + f"特別警報:{', '.join(S_warn_data)}\n"
        if not atn_data and not warn_data and not S_warn_data:
            p_data = p_data + safe_text + "\n"

        return p_data
    
    else:
        msg = pn + "に指定した地域・エリアが存在しません"
        return msg