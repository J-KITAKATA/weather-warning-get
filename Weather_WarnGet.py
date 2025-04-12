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
from typing import Optional

# .envファイルを読み込む
load_dotenv(dotenv_path="config/Weather_WrnGet.env")

# 環境変数からトークンを取得
TOKEN = os.getenv("DISCORD_TOKEN")

# インテントの設定
intents = discord.Intents.default()
intents.guilds = True # サーバー（ギルド）の情報を取得
intents.members = True          # サーバーメンバーの情報を取得したい場合
intents.messages = True # メッセージ関連のイベントを取得します。
intents.message_content = True # メッセージの内容を取得します。プレフィックスによるコマンドを使う際に必要。

# コマンド検出用の接頭辞と、Botに付与する権限の設定
bot = commands.Bot(command_prefix="w!", intents=intents)
# 上記の "w!" がプレフィックス（コマンド開始の目印）

@bot.command()
async def ver(ctx):
    V = "Ver.0.9.1"
    await ctx.send(V)

@bot.command()
async def l(ctx):
    await ctx.send("EMPTY")

@bot.command()
async def wng(ctx, pref:str, area:Optional[str] = None):

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
    cache_duration = 630  # キャッシュ保持時間（秒）

    current_time = time.time() # 現在時刻

    ids = [] # id用
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
    with open("test_sample.txt", "w", encoding="utf-8") as f:
        f.write(str(cached_data))

    # cached_dataの中身を処理
    # cached_data の構造を確認し、"id" を取り出す処理
    if cached_data:

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

bot.run(TOKEN)