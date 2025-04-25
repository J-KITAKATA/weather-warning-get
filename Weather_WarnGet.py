# 処理管制用

import requests
from bs4 import BeautifulSoup
import xmltodict
import time
import json
import os
import pref_data as p_d
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re

# .envファイルを読み込む
load_dotenv(dotenv_path="config/test.env")
# Weather_WrnGet

# 環境変数からトークンを取得
TOKEN = os.getenv("DISCORD_TOKEN")

# インテントの設定
intents = discord.Intents.default()
intents.guilds = True # サーバー（ギルド）の情報を取得
intents.members = True # サーバーメンバーの情報を取得したい場合
intents.messages = True # メッセージ関連のイベントを取得。
intents.message_content = True # メッセージの内容を取得。プレフィックスによるコマンドを使う際に必要。

# コマンド検出用の接頭辞と、Botに付与する権限の設定
bot = commands.Bot(command_prefix="w!", intents=intents)
# 上記の "w!" がプレフィックス（コマンド開始の目印）

# 震度の情報
e_Scale = {10:"震度1", 20:"震度2", 30:"震度3", 40:"震度4", 45:"震度5弱", 50:"震度5強", 55:"震度6弱", 60:"震度6強", 70:"震度7"}

@bot.command(brief = "Show Bot Version")
async def ver(ctx):
    V = "Ver.1.2.1"
    await ctx.send(V)

@bot.command(brief = "Show list of wng arguments")
async def l(ctx):
    msg = "Check link"
    l_url = "https://github.com/J-KITAKATA/weather-warning-get/blob/main/wng-list.txt"
    msg = f"{msg}\n{l_url}"
    await ctx.send(msg)

@bot.command(
        brief = "<pref:str> [area:str]",
        help = "指定した都道府県（pref）と、任意で地域名（area）を指定して気象警報情報を取得\n引数の組み合わせについては'w!l'を参照"
        )
async def wng(ctx, pref:str, area:str = ""):

    # 大文字に変換
    pref = pref.upper()
    area = area.upper()

    # キャッシュを保存するファイル名
    CACHE_FILE = "cache/main_cache.json"
    # フォルダを作成（すでにあればスルー）
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    pref_url = None # 各都道府県のURL格納場所

    # キャッシュ用の変数
    cached_data = None
    last_fetched_time = 0  # 最後にデータを取得した時刻（初期値: 0）

    current_time = time.time() # 現在時刻

    outData = None # 出力データ用

    # 地域・エリア(基本は都道府県)ごとのキーとコード
    pref_id ={"SY":"011000", "KM":"012000", "RM":"012000", "AKM":"013000", "NM": "014100", "KS":"014100", "TK":"014030", "IB":"015000", "HD":"015000", "ISK":"016000", "SR":"016000", "SB":"016000", "WS":"017000", "HY":"017000", "AO":"020000", "IW":"030000", "MG":"040000", "AT":"050000", "YA":"060000", "FS":"070000", "IG":"080000", "TG":"090000", "GM":"100000", "ST":"110000", "CB":"120000","TO":"130000","KN":"140000", "NG":"150000", "TY":"160000", "IK":"170000", "FI":"180000", "YN": "190000", "NN":"200000", "GF":"210000", "SZ":"220000", "AC":"230000", "ME":"240000", "SI":"250000", "KT":"260000", "OS":"270000", "HG":"280000", "NR":"290000", "WK":"300000", "TT":"310000", "SN":"320000", "OY":"330000", "HS":"340000", "YU":"350000", "TS":"360000", "KA":"370000", "EH":"380000", "KC":"390000", "FO":"400000", "SA":"410000", "NS":"420000", "KU":"430000", "OT":"440000", "MZ":"450000", "KO":"460100", "AM":"460040", "ON":"471000", "DT":"472000", "MK":"473000", "YY":"474000"}

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

    # 最後に情報を取得してから630秒経っていたら新しくダウンロードする
    if (current_time - last_fetched_time) > 630:
        print("新しいデータを取得中...") #debug
        # 気象庁のデータフィードURL
        feed_url = 'https://www.data.jma.go.jp/developer/xml/feed/extra_l.xml'
        feed_xml = requests.get(feed_url) # XMLデータを取得

        # XMLデータを解析して文字列に変換
        feed_soup = str(BeautifulSoup(feed_xml.content, "xml"))
        feed_dict = xmltodict.parse(feed_soup) # XMLを辞書型（dict）に変換

        # キャッシュを更新
        cached_data = feed_dict
        last_fetched_time = current_time

        # キャッシュをファイルに保存
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"timestamp": last_fetched_time, "data": cached_data}, f, ensure_ascii=False, indent=4)

    elif (current_time - last_fetched_time) <= 630:
        print("キャッシュデータを使用") # debug

    # 取得したデータをtxtファイルに保存（デバッグやログ用）
    #with open("test_sample.txt", "w", encoding="utf-8") as f:
    #    f.write(str(cached_data))

    # cached_dataの中身を処理
    # cached_data の構造を確認し、"id" を取り出す処理
    if cached_data:

        # prefがpref_idに存在しないときに例外処理を実行させる
        if pref not in  pref_id:
            pref_url = None
            pass

        else:
            # 本当は r はいらないけど、後から見たら忘れるから書く
            # JSONファイルをUTF-8の文字コードに指定して読み込み
            # dict型で処理したいからあえてJSONの再読み込みを実施
            with open(CACHE_FILE, mode='r', encoding='utf-8') as f: 
                cache_json = json.load(f) # JSON -> dict型

            # cache_json 内のデータ（仮に data にリストが格納されていると仮定）
            data_list = cache_json.get("data", [])

            # "data" 内の各要素から "id" を取り出す
            # 実際のデータは "feed":{"entry":[{}, {}]} の構造になっている
            entries = data_list["feed"]["entry"]

            # 条件に一致するエントリをフィルタリングし、"updated" フィールドで最新のものを取得
            latest_entry = max(
                (item for item in entries if "VPWW53" in item.get("id", "") and pref_id[pref] in item.get("id", "")),
                key=lambda x: x.get("updated", ""),
                default=None
            )

            # 最新エントリの "id" を取得
            if latest_entry:
                pref_url = latest_entry.get("id", None)
            else:
                pref_url = None

    if pref_url is None:
        print("該当するURLが見つかりませんでした。")
    else:
        print(f"取得したURL: {pref_url}") # debug

    # 各地域の処理に移行
    if pref == "SY": # 宗谷地方(北海道)
        outData = p_d.sy.pros(pref_url, area, current_time)

    elif pref == "KM": # 上川地方(北海道)
        outData = p_d.km.pros(pref_url, area, current_time)

    elif pref == "RM": # 留萌地方(北海道)
        outData = p_d.rm.pros(pref_url, area, current_time)

    elif pref == "AKM": # 網走・北見・紋別地方(北海道)
        outData = p_d.akm.pros(pref_url, area, current_time)

    elif pref == "NM": # 根室地方(北海道)
        outData = p_d.nm.pros(pref_url, area, current_time)

    elif pref == "KS": # 釧路地方(北海道)
        outData = p_d.ks.pros(pref_url, area, current_time)

    elif pref == "TK": # 十勝地方(北海道)
        outData = p_d.tk.pros(pref_url, area, current_time)

    elif pref == "IB": # 胆振地方(北海道)
        outData = p_d.ib.pros(pref_url, area, current_time)

    elif pref == "HD": # 日高地方(北海道)
        outData = p_d.hd.pros(pref_url, area, current_time)

    elif pref == "ISK": # 石狩地方(北海道)
        outData = p_d.isk.pros(pref_url, area, current_time)

    elif pref == "SR": # 空知地方(北海道)
        outData = p_d.sr.pros(pref_url, area, current_time)

    elif pref == "SB": # 後志地方(北海道)
        outData = p_d.sb.pros(pref_url, area, current_time)

    elif pref == "WS": # 渡島地方(北海道)
        outData = p_d.ws.pros(pref_url, area, current_time)

    elif pref == "HY": # 檜山地方(北海道)
        outData = p_d.hy.pros(pref_url, area, current_time)

    elif pref == "AO": # 青森県
        outData = p_d.ao.pros(pref_url, area, current_time)

    elif pref == "IW": # 岩手県
        outData = p_d.iw.pros(pref_url, area, current_time)

    elif pref == "MG": # 宮城県
        outData = p_d.mg.pros(pref_url, area, current_time)

    elif pref == "AT": # 秋田県
        outData = p_d.at.pros(pref_url, area, current_time)

    elif pref == "YA": # 山形県
        outData = p_d.ya.pros(pref_url, area, current_time)

    elif pref == "FS": # 福島県
        outData = p_d.fs.pros(pref_url, area, current_time)

    elif pref == "IG": # 茨城県
        outData = p_d.ig.pros(pref_url, area, current_time)

    elif pref == "TG": # 栃木県
        outData = p_d.tg.pros(pref_url, area, current_time)

    elif pref == "GM": # 群馬県
        outData = p_d.gm.pros(pref_url, area, current_time)

    elif pref == "ST": # 埼玉県
        outData = p_d.st.pros(pref_url, area, current_time)

    elif pref == "CB": # 千葉県
        outData = p_d.cb.pros(pref_url, area, current_time)

    elif pref == "TO": # 東京都
        outData = p_d.to.pros(pref_url, area, current_time)

    elif pref == "KN": # 神奈川県
        outData = p_d.kn.pros(pref_url, area, current_time)

    elif pref == "NG": # 新潟県
        outData = p_d.ng.pros(pref_url, area, current_time)

    elif pref == "TY": # 富山県
        outData = p_d.ty.pros(pref_url, area, current_time)

    elif pref == "IK": # 石川県
        outData = p_d.ik.pros(pref_url, area, current_time)

    elif pref == "FI": # 福井県
        outData = p_d.fi.pros(pref_url, area, current_time)

    elif pref == "YN": # 山梨県
        outData = p_d.yn.pros(pref_url, area, current_time)

    elif pref == "NN": # 長野県
        outData = p_d.nn.pros(pref_url, area, current_time)

    elif pref == "GF": # 岐阜県
        outData = p_d.gf.pros(pref_url, area, current_time)

    elif pref == "SZ": # 静岡県
        outData = p_d.sz.pros(pref_url, area, current_time)

    elif pref == "AC": # 愛知県
        outData = p_d.ac.pros(pref_url, area, current_time)

    elif pref == "ME": # 三重県
        outData = p_d.me.pros(pref_url, area, current_time)

    elif pref == "SI": # 滋賀県
        outData = p_d.si.pros(pref_url, area, current_time)

    elif pref == "KT": # 京都府
        outData = p_d.kt.pros(pref_url, area, current_time)

    elif pref == "OS": # 大阪府
        outData = p_d.os.pros(pref_url, area, current_time)

    elif pref == "HG": # 兵庫県
        outData = p_d.hg.pros(pref_url, area, current_time)

    elif pref == "NR": # 奈良県
        outData = p_d.nr.pros(pref_url, area, current_time)

    elif pref == "WK": # 和歌山県
        outData = p_d.wk.pros(pref_url, area, current_time)

    elif pref == "TT": # 鳥取県
        outData = p_d.tt.pros(pref_url, area, current_time)

    elif pref == "SN": # 島根県
        outData = p_d.sn.pros(pref_url, area, current_time)

    elif pref == "OY": # 岡山県
        outData = p_d.oy.pros(pref_url, area, current_time)

    elif pref == "HS": # 広島県
        outData = p_d.hs.pros(pref_url, area, current_time)

    elif pref == "YU": # 山口県
        outData = p_d.yu.pros(pref_url, area, current_time)

    elif pref == "TS": # 徳島県
        outData = p_d.ts.pros(pref_url, area, current_time)

    elif pref == "KA": # 香川県
        outData = p_d.ka.pros(pref_url, area, current_time)

    elif pref == "EH": # 愛媛県
        outData = p_d.eh.pros(pref_url, area, current_time)

    elif pref == "KC": # 高知県
        outData = p_d.kc.pros(pref_url, area, current_time)

    elif pref == "FO": # 福岡県
        outData = p_d.fo.pros(pref_url, area, current_time)

    elif pref == "SA": # 佐賀県
        outData = p_d.sa.pros(pref_url, area, current_time)

    elif pref == "NS": # 長崎県
        outData = p_d.ns.pros(pref_url, area, current_time)

    elif pref == "KU": # 熊本県
        outData = p_d.ku.pros(pref_url, area, current_time)

    elif pref == "OT": # 大分県
        outData = p_d.ot.pros(pref_url, area, current_time)

    elif pref == "MZ": # 宮崎県
        outData = p_d.mz.pros(pref_url, area, current_time)

    elif pref == "KO": # 鹿児島県(除く：奄美地方)
        outData = p_d.ko.pros(pref_url, area, current_time)

    elif pref == "AM": # 奄美地方(鹿児島県)
        outData = p_d.am.pros(pref_url, area, current_time)

    elif pref == "ON": # 沖縄本島地方(沖縄県)
        outData = p_d.on.pros(pref_url, area, current_time)

    elif pref == "DT": # 大東島地方(沖縄県)
        outData = p_d.dt.pros(pref_url, area, current_time)

    elif pref == "MK": # 宮古島地方(沖縄県)
        outData = p_d.mk.pros(pref_url, area, current_time)

    elif pref == "YY": # 八重山地方(沖縄県)
        outData = p_d.yy.pros(pref_url, area, current_time)

    else:
        outData = "該当する地域が見つかりませんでした。"

    await ctx.send(outData)

@bot.command(brief = "[sc:str]",
             help = "scの引数に対して'U5-'を入力すると最大震度5弱以上の最新の地震情報を表示します。"
             )
async def eq(ctx, sc:str = ""):
    eq_url = ""
    sc = sc.upper()

    # キャッシュ用の変数
    cached_data = None
    last_fetched_time = 0  # 最後にデータを取得した時刻（初期値: 0）
    current_time = time.time() # 現在時刻

    outData = None # 出力データ用

    if sc == "" or sc == None:
        # 最新の地震情報を取得
        eq_url = "https://api.p2pquake.net/v2/history?codes=551&limit=1"

        # キャッシュを保存するファイル名
        E_CACHE_FILE = "cache/E_cache.json"
        t = 5
        h_msg = "**最新の地震情報**"

    elif sc == "U5-":
        # 最大震度5弱以上が観測された最新の地震情報を取得
        eq_url = "https://api.p2pquake.net/v2/jma/quake?limit=1&order=-1&quake_type=DetailScale&min_scale=45"

        # キャッシュを保存するファイル名
        E_CACHE_FILE = "cache/E-U5_cache.json"
        t = 15
        h_msg = "**最新の最大震度5弱以上の地震情報**"

    else:
        # U5-以外の引数が呼ばれたときには処理を強制終了する
        await ctx.send("情報が存在しません")
        return

    # フォルダを作成（すでにあればスルー）
    os.makedirs(os.path.dirname(E_CACHE_FILE), exist_ok=True)

    # キャッシュデータをファイルから読み込む
    # 空でないか確認 and キャッシュファイルが存在するかチェック
    if os.path.exists(E_CACHE_FILE) and os.path.getsize(E_CACHE_FILE) > 0:
        with open(E_CACHE_FILE, "r", encoding="utf-8") as f:
            try:
                cache_content = json.load(f)  # JSONデータを読み込む
                cached_data = cache_content.get("data")  # 保存されていたデータを取得
                last_fetched_time = cache_content.get("timestamp", 0)  # 最後の取得時刻を取得（なければ0）
            except json.JSONDecodeError: # JSONファイル読み込みエラー時の処理
                cached_data = None  # JSONが壊れていた場合はNoneに
                last_fetched_time = 0  # 取得時刻もリセット

    # 最後に取得してから5秒経過していたら情報を取得する
    if (current_time - last_fetched_time) > t:
        print("(EQ_Mode)新しいデータを取得中...") #debug
        feed_json = requests.get(eq_url).json() # JSONデータを取得
        # キャッシュを更新
        cached_data = feed_json
        last_fetched_time = current_time

        # キャッシュをファイルに保存
        with open(E_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"timestamp": last_fetched_time, "data": cached_data}, f, ensure_ascii=False, indent=4)

    elif (current_time - last_fetched_time) <= t:
        print("(EQ_Mode)キャッシュデータを使用") # debug
        
    EQ_Name = cached_data[0]["earthquake"]["hypocenter"]["name"] # 震源地(震央)
    Depth = cached_data[0]["earthquake"]["hypocenter"]["depth"] # 震源の深さ
    Lat = cached_data[0]["earthquake"]["hypocenter"]["latitude"] # 緯度
    Lon = cached_data[0]["earthquake"]["hypocenter"]["longitude"] # 経度
    Mag = cached_data[0]["earthquake"]["hypocenter"]["magnitude"] # マグニチュード
    M_Scale = cached_data[0]["earthquake"]["maxScale"] # 最大震度
    Occ_time = cached_data[0]["earthquake"]["time"] # 発生時刻

    # 震源の深さの情報を整理
    if Depth == "0":
        Depth = "ごく浅い"
    elif Depth == "-1":
        Depth = "不明"
    elif Depth != "0" and Depth != "-1":
        Depth = f"{Depth}km"
    else:
        Depth = "不明"

    # 緯度・経度の情報を整理
    if Lat == "-200" or Lon == "-200":
        G_map = ""
    elif Lat != "-200" and Lon != "-200":
        G_map = f"[Google Map](https://www.google.com/maps?q={Lat},{Lon})"
    else:
        G_map = ""

    # マグニチュードの情報を整理
    if Mag == "-1":
        Mag = "不明"
    elif Mag != "-1":
        Mag = f"M{Mag}"
    else:
        Mag = "不明"

    # 最大震度の情報を整理
    if M_Scale == "-1":
        M_Scale = "不明"
    elif M_Scale != "-1":
        M_Scale = e_Scale[M_Scale]
    else:
        M_Scale = "不明"

    outData = f"{h_msg}\n発生時刻：{Occ_time}\n震源地：{EQ_Name}\n震源の深さは{Depth}\nマグニチュードは{Mag}で、最大震度は{M_Scale}\n{G_map}"

    await ctx.send(outData)

@bot.command(brief = "[cl:str]", help = "clの引数に対してhを入力すると簡易的な長周期地震動階級の説明を見ることができます")
async def lgm(ctx, cl:str = ""):

    LGM_CACHE_FILE = "cache/LGM_cache.json"

    # フォルダを作成（すでにあればスルー）
    os.makedirs(os.path.dirname(LGM_CACHE_FILE), exist_ok=True)

    if cl == "h":
        t_msg = "**長周期地震動階級の説明**"
        link = "[長周期地震動について | 気象庁](https://www.jma.go.jp/jma/kishou/know/jishin/choshuki/)"
        msg = f"{t_msg}\n階級1：やや大きな揺れ\n階級2：大きな揺れ\n階級3：非常に大きな揺れ\n階級4：極めて大きな揺れ\n\n{link}"

    else:
        N_time = time.time()  # 現在時刻

        lgm_cache = {}
        if os.path.exists(LGM_CACHE_FILE) and os.path.getsize(LGM_CACHE_FILE) > 0:
            with open(LGM_CACHE_FILE, "r", encoding="utf-8") as f:
                try:
                    lgm_cache = json.load(f)
                except json.JSONDecodeError:
                    lgm_cache = {}

        saved_time = lgm_cache.get("save_time", 0)

        if (N_time - saved_time) <= 720:
            print("(LGM_Mode)キャッシュ使用")
            Name = lgm_cache["cName"]
            Mag = lgm_cache["cMag"]
            M_Lg = lgm_cache["cM_Lg"]
            T_data = lgm_cache["cT_data"]
            Depth = lgm_cache["cDepth"]
            Lat = lgm_cache["cLat"]
            Lon = lgm_cache["cLon"]
            G_map = lgm_cache["cG_map"]
            url = lgm_cache["c_url"]

        elif (N_time - saved_time) > 720:
            print("(LGM_Mode)データ取得")

            lgm_cache["save_time"] = N_time  # 読み込んだ時の時間を記録

            # 長周期地震動に関する観測情報のアーカイブサイトにアクセス
            url = "https://www.data.jma.go.jp/eew/data/ltpgm_explain/data/past/past_list.html"
            res = requests.get(url)
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")  # サイトのHTMLコードの読み込み
            Tables = soup.find("table", class_="data2_ltpgm")
            T_rows = Tables.find_all("tr")
            SP_rows = T_rows[1]
            cells = SP_rows.find_all("td")

            last_cell = cells[-1]  # Next URL
            link_tag = last_cell.find("a")
            url = link_tag.attrs["href"]
            url = f"https://www.data.jma.go.jp/{url}"  # 出力にも使う
            lgm_cache["c_url"] = url

            Name = cells[1].contents[0]  # 震源地
            lgm_cache["cName"] = Name

            Mag = cells[2].contents[0]  # マグニチュード
            lgm_cache["cMag"] = Mag

            M_Lg = cells[3].contents[0]  # 最大長周期地震動階級
            lgm_cache["cM_Lg"] = M_Lg

            T_data = cells[0].contents[0]  # 発生時刻
            lgm_cache["cT_data"] = T_data

            # ==========ここから別ページ==========
            res = requests.get(url)
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")  # サイトのHTMLコードの読み込み
            Tables = soup.find("div", class_="tablelist")
            text = Tables.get_text(separator="\n")  # <br>を改行に変換
            matches = re.findall(r"深さ\s+(\S+)", text)
            Depth = matches[0]  # 震源の深さ
            lgm_cache["cDepth"] = Depth

            # 緯度
            scripts = soup.find("script", type="text/javascript").string
            Lat_match = re.search(r"const hypoLat = \"([^\"]+)\";", scripts)

            if Lat_match:
                Lat = Lat_match.group(1)  # 取得した情報からマッチした情報を抽出
            else:
                Lat = ""
            lgm_cache["cLat"] = Lat

            # 経度
            Lon_match = re.search(r"const hypoLon = \"([^\"]+)\";", scripts)

            if Lon_match:
                Lon = Lon_match.group(1)  # 取得した情報からマッチした情報を抽出
            else:
                Lon = ""
            lgm_cache["cLon"] = Lon

            # Google MapのURLを貼るかどうかの判別
            if Lat == "" or Lon == "":
                G_map = ""
            else:
                G_map = f"[Google Map](https://www.google.com/maps?q={Lat},{Lon})"
            lgm_cache["cG_map"] = G_map

            # キャッシュファイルの内容を更新
            with open(LGM_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(lgm_cache, f, ensure_ascii=False, indent=4)

        else:
            await ctx.send("Check Code!\nThat's probably unintended behavior!")
            return

        msg = f"**最新の長周期地震動に関する観測情報**\n発生時刻：{T_data}\n震源地：{Name}\n震源の深さ：{Depth}\nマグニチュード：M{Mag}\n最大長周期地震動階級：{M_Lg}\n{G_map}\n\n出典：[気象庁]({url})"

    await ctx.send(msg)

bot.run(TOKEN)