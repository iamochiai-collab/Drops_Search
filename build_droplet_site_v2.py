import os, re, json, csv, shutil, zipfile, unicodedata
from pathlib import Path
from collections import defaultdict
from pykakasi import kakasi
import jaconv

ZIP_PATH = Path('/mnt/data/drops(1).zip')
OUT_DIR = Path('/mnt/data/droplet_search_site_v2')
IMG_DIR = OUT_DIR / 'assets' / 'images'
DATA_DIR = OUT_DIR / 'data'

if OUT_DIR.exists():
    shutil.rmtree(OUT_DIR)
IMG_DIR.mkdir(parents=True)
DATA_DIR.mkdir(parents=True)

kks = kakasi()
conv = kks.getConverter()

CATEGORY_MAP = {
    '100': ('人・動植物', '人・動植物'),
    '101': ('人・動植物', '人・家族'),
    '102': ('人・動植物', '職業・役割'),
    '103': ('人・動植物', 'からだ'),
    '104': ('人・動植物', '動物'),
    '200': ('動き・様子', '動き・様子'),
    '201': ('動き・様子', '気持ち'),
    '202': ('動き・様子', 'ことば・状態'),
    '203': ('動き・様子', '基本動作'),
    '204': ('動き・様子', '生活動作・活動'),
    '300': ('飲食物', '飲食物'),
    '301': ('飲食物', '食べ物'),
    '302': ('飲食物', '飲み物'),
    '303': ('飲食物', '調味料・食品'),
    '400': ('家の中・身の回り', '家の中・身の回り'),
    '401': ('家の中・身の回り', '家・部屋'),
    '402': ('家の中・身の回り', '家具・家電'),
    '403': ('家の中・身の回り', '衣服・身につける物'),
    '404': ('家の中・身の回り', '文具・遊び・道具'),
    '405': ('家の中・身の回り', '食器・日用品'),
    '500': ('家の外', '家の外'),
    '501': ('家の外', '乗り物'),
    '502': ('家の外', '施設・店'),
    '503': ('家の外', '自然'),
    '504': ('家の外', '天気・季節'),
    '600': ('文化・社会', '文化・社会'),
    '601': ('文化・社会', '時間・日にち'),
    '602': ('文化・社会', '学校・行事'),
    '603': ('文化・社会', '遊び・スポーツ・文化'),
    '604': ('文化・社会', '社会・都道府県・数字'),
}

# Related-term groups inspired by AAC symbol sites' broad tagging patterns.
SYNONYM_GROUPS = [
    ['男', 'おとこ', '男性', 'だんせい', '男子', 'だんし', 'メンズ'],
    ['女', 'おんな', '女性', 'じょせい', '女子', 'じょし', 'レディース'],
    ['家族', 'かぞく', 'ファミリー'],
    ['お父さん', '父', 'ちち', 'パパ'],
    ['お母さん', '母', 'はは', 'ママ'],
    ['男の子', 'おとこのこ', 'ぼうや', '少年'],
    ['女の子', 'おんなのこ', '少女'],
    ['赤ちゃん', 'あかちゃん', 'ベビー', '乳児'],
    ['おじいさん', '祖父', 'そふ', 'じいちゃん', 'じーじ'],
    ['おばあさん', '祖母', 'そぼ', 'ばあちゃん', 'ばーば'],
    ['わたし', '私', 'ぼく', '僕', 'おれ', '自分', 'じぶん'],
    ['あなた', 'きみ', '君', '相手'],
    ['友達', 'ともだち', '友人', 'ゆうじん'],
    ['きょうだい', '兄弟', '姉妹', 'きょうだい'],
    ['兄', 'あに', 'お兄さん', 'にいちゃん'],
    ['姉', 'あね', 'お姉さん', 'ねえちゃん'],
    ['弟', 'おとうと'],
    ['妹', 'いもうと'],
    ['大人', 'おとな', '成人'],
    ['こども', '子ども', '子供', '子'],
    ['大勢', 'たくさん', '多い', '多数'],
    ['恋人', 'こいびと', '彼氏', '彼女', 'カップル'],
    ['おじさん', '叔父', '伯父'],
    ['おばさん', '叔母', '伯母'],
    ['先生', 'せんせい', '教師', '教員'],
    ['警察官', 'けいさつかん', '警察', 'ポリス'],
    ['医師', 'いし', '医者', 'ドクター'],
    ['看護師', 'かんごし', 'ナース'],
    ['消防士', 'しょうぼうし', '消防', 'レスキュー'],
    ['校長先生', '校長', 'こうちょう'],
    ['保育士', 'ほいくし', '保育園の先生'],
    ['言語聴覚士', 'ST', 'ことばの先生'],
    ['作業療法士', 'OT'],
    ['理学療法士', 'PT'],
    ['歯科医', '歯医者', 'しかい', '歯科'],
    ['神様', 'かみさま'],
    ['サンタクロース', 'サンタ'],
    ['美容師', 'びようし', 'ヘアスタイリスト'],
    ['高校生', 'こうこうせい', '高校'],
    ['顔', 'かお', 'フェイス'],
    ['目', 'め', 'アイ'],
    ['耳', 'みみ'],
    ['鼻', 'はな'],
    ['口', 'くち', 'マウス'],
    ['歯', 'は'],
    ['首', 'くび'],
    ['髪の毛', '髪', 'かみ', 'ヘア'],
    ['腕', 'うで'],
    ['手', 'て'],
    ['指', 'ゆび'],
    ['足', 'あし'],
    ['膝', 'ひざ'],
    ['腹', 'お腹', 'おなか'],
    ['背中', 'せなか'],
    ['尻', 'おしり'],
    ['心臓', 'しんぞう'],
    ['血', 'ち', '血液'],
    ['頭', 'あたま'],
    ['体', 'からだ', '身体'],
    ['犬', 'いぬ', 'ドッグ'],
    ['猫', 'ねこ', 'キャット'],
    ['魚', 'さかな'],
    ['鳥', 'とり'],
    ['昆虫', 'こんちゅう', '虫', 'むし'],
    ['好き', 'すき', 'お気に入り'],
    ['幸せ', 'しあわせ', 'ハッピー'],
    ['悲しい', 'かなしい'],
    ['美味しい', 'おいしい', 'うまい'],
    ['不味い', 'まずい'],
    ['面白い', 'おもしろい', '楽しい'],
    ['つまらない', '退屈', 'たいくつ'],
    ['怒る', 'おこる', '怒り'],
    ['怖い', 'こわい'],
    ['静かに', 'しずかに'],
    ['がっかり', '残念', 'ざんねん'],
    ['易しい', 'やさしい', '簡単'],
    ['難しい', 'むずかしい'],
    ['わからない', '分からない', '理解できない'],
    ['欲しい', 'ほしい'],
    ['寒い', 'さむい'],
    ['暑い', 'あつい'],
    ['痛い', 'いたい'],
    ['眠い', 'ねむい'],
    ['パニック', '混乱'],
    ['はい', 'うん', '肯定'],
    ['いいえ', 'いや', '否定'],
    ['大きい', 'おおきい'],
    ['小さい', 'ちいさい'],
    ['上', 'うえ'],
    ['下', 'した'],
    ['同じ', 'おなじ'],
    ['明るい', 'あかるい'],
    ['暗い', 'くらい'],
    ['熱い', 'あつい'],
    ['冷たい', 'つめたい'],
    ['かたい', '硬い'],
    ['やわらかい', '柔らかい'],
    ['きれい', '綺麗'],
    ['汚い', 'きたない'],
    ['高価', '高い', 'たかい'],
    ['安価', '安い', 'やすい'],
    ['聞く', 'きく'],
    ['話す', 'はなす', 'しゃべる'],
    ['見る', 'みる'],
    ['食べる', 'たべる', '食事'],
    ['飲む', 'のむ'],
    ['立つ', 'たつ'],
    ['座る', 'すわる'],
    ['歩く', 'あるく'],
    ['走る', 'はしる'],
    ['起きる', 'おきる', '起床'],
    ['寝る', 'ねる', '就寝'],
    ['あたえる', 'あげる', '渡す'],
    ['もらう', '受け取る'],
    ['風呂', 'おふろ', '入浴'],
    ['顔を洗う', '洗顔'],
    ['手を洗う', '手洗い'],
    ['開ける', 'あける'],
    ['閉める', 'しめる'],
    ['着る', 'きる'],
    ['脱ぐ', 'ぬぐ'],
    ['こんにちは', 'あいさつ', '挨拶'],
    ['さようなら', 'バイバイ'],
    ['感謝する', 'ありがとう', 'お礼'],
    ['謝る', 'ごめんなさい', '謝罪'],
    ['歌う', 'うたう'],
    ['読む', 'よむ'],
    ['書く', 'かく'],
    ['描く', 'えがく'],
    ['遊ぶ', 'あそぶ'],
    ['勉強する', '学習', 'べんきょう'],
    ['会う', 'あう'],
    ['切る', 'きる'],
    ['助ける', 'たすける'],
    ['褒める', 'ほめる'],
    ['叱る', 'しかる'],
    ['ご飯', 'ごはん', '白米', 'ライス'],
    ['お弁当', 'べんとう'],
    ['おにぎり', 'にぎりめし'],
    ['野菜', 'やさい'],
    ['パン', 'ぱん', 'ブレッド'],
    ['ケーキ', 'けーき', 'スイーツ'],
    ['和食', '日本食'],
    ['中華', '中華料理'],
    ['朝ごはん', '朝食'],
    ['昼ごはん', '昼食', 'ランチ'],
    ['夕ごはん', '夕食', '晩ごはん', 'ディナー'],
    ['おかず', '副菜'],
    ['汁物', 'スープ'],
    ['バナナ', 'ばなな'],
    ['スイカ', 'すいか'],
    ['たまご', '卵', '玉子'],
    ['水', 'みず'],
    ['お茶', 'ちゃ', 'tea'],
    ['牛乳', 'ぎゅうにゅう', 'ミルク'],
    ['お酒', '酒', 'さけ', 'アルコール'],
    ['ビール', 'びーる'],
    ['ジュース', 'じゅーす'],
    ['ワイン', 'わいん'],
    ['ラムネ', 'らむね'],
    ['しょうゆ', '醤油'],
    ['ソース', 'そーす'],
    ['塩', 'しお'],
    ['マヨネーズ', 'まよねーず'],
    ['ケチャップ', 'けちゃっぷ'],
    ['家', 'いえ', 'うち', '自宅'],
    ['ドア', '扉', 'とびら'],
    ['灯り', 'あかり', '電気'],
    ['食堂', 'しょくどう'],
    ['台所', 'だいどころ', 'キッチン'],
    ['階段', 'かいだん'],
    ['手洗い', 'てあらい'],
    ['シャワー', 'しゃわー'],
    ['トイレ', '便所', 'WC', 'お手洗い'],
    ['洗面台', 'せんめんだい'],
    ['庭', 'にわ'],
    ['廊下', 'ろうか'],
    ['椅子', 'いす', 'チェア'],
    ['テーブル', '机', 'つくえ'],
    ['ベッド', 'べっど'],
    ['毛布', 'もうふ'],
    ['冷蔵庫', 'れいぞうこ'],
    ['洗濯機', 'せんたくき'],
    ['テレビ', 'てれび'],
    ['ラジオ', 'らじお'],
    ['電話', 'でんわ'],
    ['エアコン', 'クーラー'],
    ['電子レンジ', 'レンジ'],
    ['パソコン', 'PC'],
    ['シャツ', 'しゃつ'],
    ['ジャンパー', '上着'],
    ['ズボン', 'パンツ'],
    ['スカート', 'すかーと'],
    ['コート', 'こーと'],
    ['靴下', 'くつした', 'ソックス'],
    ['靴', 'くつ', 'シューズ'],
    ['メガネ', 'めがね', '眼鏡'],
    ['手袋', 'てぶくろ'],
    ['お金', '金', 'かね', 'おかね'],
    ['財布', 'さいふ'],
    ['鍵', 'かぎ'],
    ['傘', 'かさ'],
    ['切符', 'きっぷ'],
    ['カメラ', 'かめら'],
    ['鞄', 'かばん', 'バッグ'],
    ['作業着', 'さぎょうぎ'],
    ['エプロン', 'えぷろん'],
    ['マスク', 'ますく'],
    ['本', 'ほん'],
    ['紙', 'かみ'],
    ['鉛筆', 'えんぴつ'],
    ['ハサミ', 'はさみ'],
    ['消しゴム', 'けしごむ'],
    ['玩具', 'おもちゃ'],
    ['CD', 'しーでぃー'],
    ['サッカーボール', 'サッカー'],
    ['野球ボール', '野球'],
    ['色鉛筆', 'いろえんぴつ'],
    ['のり', '糊'],
    ['フラフープ', 'ふらふーぷ'],
    ['一輪車', 'いちりんしゃ'],
    ['キーボード', 'きーぼーど'],
    ['風船', 'ふうせん'],
    ['コップ', 'こっぷ'],
    ['カップ', 'かっぷ'],
    ['皿', 'さら'],
    ['茶碗', 'ちゃわん'],
    ['箸', 'はし'],
    ['スプーン', 'すぷーん'],
    ['フォーク', 'ふぉーく'],
    ['ナイフ', 'ないふ'],
    ['石鹸', 'せっけん'],
    ['歯磨き粉', 'はみがきこ'],
    ['歯ブラシ', 'はぶらし'],
    ['タオル', 'たおる'],
    ['鏡', 'かがみ'],
    ['ティッシュペーパー', 'ティッシュ'],
    ['トイレットペーパー', 'トイペ'],
    ['時計', 'とけい'],
    ['体温計', 'たいおんけい'],
    ['薬', 'くすり'],
    ['自転車', 'じてんしゃ', 'チャリ'],
    ['バイク', '単車'],
    ['車', 'くるま', '自動車'],
    ['バス', 'ばす'],
    ['電車', 'でんしゃ'],
    ['地下鉄', 'ちかてつ'],
    ['新幹線', 'しんかんせん'],
    ['飛行機', 'ひこうき'],
    ['船', 'ふね'],
    ['救急車', 'きゅうきゅうしゃ'],
    ['消防車', 'しょうぼうしゃ'],
    ['車椅子', '車いす', 'くるまいす'],
    ['信号機', '信号', 'しんごう'],
    ['横断歩道', 'おうだんほどう'],
    ['駅', 'えき'],
    ['事故', 'じこ'],
    ['スクールバス', '送迎バス'],
    ['店', 'みせ', 'ショップ'],
    ['レストラン', '飲食店'],
    ['喫茶店', 'カフェ'],
    ['郵便局', 'ゆうびんきょく'],
    ['銀行', 'ぎんこう'],
    ['薬局', 'やっきょく', 'ドラッグストア'],
    ['床屋', 'とこや', '理容室'],
    ['映画館', 'えいがかん'],
    ['託児所', '保育所'],
    ['スーパー', 'すーぱー'],
    ['ガソリンスタンド', 'GS'],
    ['学校', 'がっこう', 'スクール'],
    ['病院', 'びょういん', 'クリニック'],
    ['役所', '市役所', 'やくしょ'],
    ['コンビニ', 'こんびに'],
    ['公園', 'こうえん'],
    ['海', 'うみ'],
    ['山', 'やま'],
    ['川', 'かわ'],
    ['木', 'き'],
    ['花', 'はな'],
    ['森', 'もり'],
    ['田んぼ', 'たんぼ'],
    ['空', 'そら'],
    ['晴れ', 'はれ', '太陽', 'たいよう'],
    ['雨', 'あめ'],
    ['台風', 'たいふう'],
    ['雪', 'ゆき'],
    ['春', 'はる'],
    ['夏', 'なつ'],
    ['秋', 'あき'],
    ['冬', 'ふゆ'],
    ['地球', 'ちきゅう'],
    ['季節', 'きせつ', '四季'],
    ['月', 'つき', 'ムーン'],
    ['星', 'ほし'],
    ['雲', 'くも'],
    ['霧', 'きり'],
    ['虹', 'にじ'],
    ['昨日', 'きのう'],
    ['今日', 'きょう'],
    ['明日', 'あした', 'あす'],
    ['前', 'まえ'],
    ['後', 'あと', 'うしろ'],
    ['朝', 'あさ'],
    ['昼', 'ひる'],
    ['夕', 'ゆうがた'],
    ['日曜日', 'にちようび'],
    ['月曜日', 'げつようび'],
    ['火曜日', 'かようび'],
    ['水曜日', 'すいようび'],
    ['木曜日', 'もくようび'],
    ['金曜日', 'きんようび'],
    ['土曜日', 'どようび'],
    ['教室', 'きょうしつ'],
    ['図書館', 'としょかん'],
    ['体育館', 'たいいくかん'],
    ['保健室', 'ほけんしつ'],
    ['職員室', 'しょくいんしつ'],
    ['会議室', 'かいぎしつ'],
    ['音楽室', 'おんがくしつ'],
    ['相談室', 'そうだんしつ'],
    ['放送室', 'ほうそうしつ'],
    ['視聴覚室', 'しちょうかくしつ'],
    ['昇降口', 'しょうこうぐち'],
    ['下駄箱', 'げたばこ'],
    ['ランチルーム', '給食室'],
    ['給食着', 'きゅうしょくぎ'],
    ['給食帽子', 'きゅうしょくぼうし'],
    ['食缶', 'しょっかん'],
    ['図書袋', 'としょぶくろ'],
    ['交通安全教室', '交通安全'],
    ['学習発表会', '発表会'],
    ['ゴール', 'goal'],
    ['検温', '体温', '体温測定'],
    ['視力検査', '視力', '目の検査'],
    ['心電図検査', '心電図'],
    ['聴力検査', '聴力', '耳の検査'],
    ['検尿', '尿検査'],
    ['ギョウ虫検査', 'ぎょう虫', '寄生虫検査'],
    ['便意', 'べんい'],
    ['下痢便', '下痢'],
    ['硬い便', '便秘', '硬便'],
    ['胃ろう', 'いろう'],
    ['経鼻経管栄養', 'けいびけいかんえいよう'],
    ['吸引器', 'きゅういんき'],
    ['消毒', 'しょうどく'],
    ['絆創膏', 'ばんそうこう'],
    ['湿布', 'しっぷ'],
    ['ガーゼ', 'がーぜ'],
    ['点滴', 'てんてき'],
    ['目薬', 'めぐすり'],
    ['生理用ナプキン', 'ナプキン', '生理用品'],
    ['音楽', 'おんがく'],
    ['野球', 'やきゅう'],
    ['ゲートボール', 'げーとぼーる'],
    ['じゃんけん', 'グー', 'チョキ', 'パー'],
    ['マラソン', '走る'],
    ['水泳', 'すいえい', 'プール'],
    ['テニス', 'てにす'],
    ['ゴルフ', 'ごるふ'],
    ['散歩', 'さんぽ'],
    ['餅つき', 'もちつき'],
    ['新聞', 'しんぶん'],
    ['ニュース', 'にゅーす'],
    ['日本', 'にほん', 'にっぽん'],
    ['都道府県', '地域', '地名'],
]

# Special exact aliases where search intent is likely to vary significantly.
EXACT_ALIASES = {
    '学校': ['学び舎', '通学'],
    '保健室': ['養護教諭', 'けが', '体調不良'],
    '教室': ['クラス', 'ホームルーム'],
    '図書館': ['本を借りる', '図書室'],
    '車椅子': ['車いす', 'wheelchair'],
    '福祉車両': ['リフト車', '送迎車'],
    '手洗い': ['手を洗う'],
    'トイレ(1)': ['トイレ', '便所', 'お手洗い', 'WC'],
    'トイレ(2)': ['トイレ', '便所', 'お手洗い', 'WC'],
    '男子トイレ(1)': ['男子トイレ', '男性トイレ'],
    '男子トイレ(2)': ['男子トイレ', '男性トイレ'],
    '和式トイレ(1)': ['和式トイレ', 'しゃがむトイレ'],
    '和式トイレ(2)': ['和式トイレ', 'しゃがむトイレ'],
    '車': ['自家用車', 'マイカー'],
    'バス停': ['停留所'],
    '役所・市役所': ['役所', '市役所', '行政'],
    '歩行者用信号機': ['歩行者信号', '人用信号'],
    '中・高校': ['中学校', '高校', '中高'],
    '休日': ['休みの日', 'おやすみ'],
}

DIGIT_WORDS = {
    '0': ['０', 'ゼロ', 'れい', '零'],
    '1': ['１', 'いち', '一'],
    '2': ['２', 'に', '二'],
    '3': ['３', 'さん', '三'],
    '4': ['４', 'よん', 'し', '四'],
    '5': ['５', 'ご', '五'],
    '6': ['６', 'ろく', '六'],
    '7': ['７', 'なな', 'しち', '七'],
    '8': ['８', 'はち', '八'],
    '9': ['９', 'きゅう', 'く', '九'],
    '10': ['１０', '十', 'じゅう'],
    '20': ['２０', '二十', 'にじゅう'],
    '30': ['３０', '三十', 'さんじゅう'],
    '40': ['４０', '四十', 'よんじゅう'],
    '50': ['５０', '五十', 'ごじゅう'],
    '60': ['６０', '六十', 'ろくじゅう'],
    '70': ['７０', '七十', 'ななじゅう'],
    '80': ['８０', '八十', 'はちじゅう'],
    '90': ['９０', '九十', 'きゅうじゅう'],
    '100': ['１００', '百', 'ひゃく'],
}

PARTICLE_SPLIT = re.compile(r'(を|に|で|と|へ|から|まで|が|の|や|へ|より)')
SEPARATOR_SPLIT = re.compile(r'[・･,、/／\s　]+')
PAREN_CONTENT = re.compile(r'[（(]([^）)]+)[）)]')
PAREN_REMOVE = re.compile(r'[（(][^）)]*[）)]')
NUM_PREFIX = re.compile(r'^[0-9０-９]+')


def safe_filename(name: str) -> str:
    name = unicodedata.normalize('NFKC', name)
    name = re.sub(r'[^0-9A-Za-z._-]+', '_', name)
    return name.strip('_') or 'file'


def normalize_for_match(text: str) -> str:
    text = unicodedata.normalize('NFKC', text or '').strip().lower()
    text = jaconv.kata2hira(text)
    text = re.sub(r'[\s　・･、。,.，．（）()［\]【】「」『』\-_/／]+', '', text)
    return text


def kana_variants(text: str):
    out = set()
    if not text:
        return out
    t = unicodedata.normalize('NFKC', text)
    out.add(t)
    hira = conv.do(t)
    if hira:
        out.add(hira)
        out.add(jaconv.hira2kata(hira))
        out.add(jaconv.kata2hira(hira))
    return {x for x in out if x}


def parse_title(title: str):
    title = unicodedata.normalize('NFKC', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def title_bases(title: str):
    title = parse_title(title)
    bases = {title}
    no_paren = PAREN_REMOVE.sub('', title).strip()
    no_paren = re.sub(r'\s+', ' ', no_paren)
    bases.add(no_paren)
    no_num_prefix = NUM_PREFIX.sub('', no_paren).strip()
    if no_num_prefix:
        bases.add(no_num_prefix)
    # merge spaces between digits like '1 0'
    merged_digits = re.sub(r'(?<=\d)\s+(?=\d)', '', title)
    bases.add(merged_digits)
    bases.add(PAREN_REMOVE.sub('', merged_digits).strip())
    return [b for b in bases if b]


def split_components(text: str):
    pieces = []
    text = parse_title(text)
    # full title and base w/o parentheses
    for base in title_bases(text):
        if base not in pieces:
            pieces.append(base)
    # parenthetical content
    for c in PAREN_CONTENT.findall(text):
        c = c.strip()
        if c:
            pieces.append(c)
    # separate by separators
    plain = PAREN_REMOVE.sub(' ', text)
    for part in SEPARATOR_SPLIT.split(plain):
        if not part:
            continue
        bits = [b for b in PARTICLE_SPLIT.split(part) if b and b not in {'を', 'に', 'で', 'と', 'へ', 'から', 'まで', 'が', 'の', 'や', 'より'}]
        for b in bits:
            b = b.strip()
            if b:
                pieces.append(b)
    # basic derived verb/object forms
    for p in list(pieces):
        if p.endswith('する') and len(p) > 2:
            pieces.append(p[:-2])
        if p.endswith('している') and len(p) > 4:
            pieces.append(p[:-4])
        if p.endswith('を'):
            pieces.append(p[:-1])
    # dedupe preserving order
    seen = set(); ordered=[]
    for p in pieces:
        p = p.strip()
        if p and p not in seen:
            seen.add(p); ordered.append(p)
    return ordered


def group_expansions(seed_terms):
    seeds_norm = {normalize_for_match(t) for t in seed_terms if t}
    results = set()
    for group in SYNONYM_GROUPS:
        group_norm = {normalize_for_match(t) for t in group}
        if seeds_norm & group_norm:
            results.update(group)
    return results


def extra_pattern_tags(title, category, subcategory, code_prefix):
    tags = set()
    t = parse_title(title)
    if '男子' in t or '男性' in t:
        tags.update(['男子', '男性', '男', 'おとこ'])
    if '女子' in t or '女性' in t:
        tags.update(['女子', '女性', '女', 'おんな'])
    if '枠線あり' in t:
        tags.update(['枠線あり', 'ふちあり', '線あり'])
    if '枠線なし' in t:
        tags.update(['枠線なし', 'ふちなし', '線なし'])
    if '右' in t:
        tags.update(['右', 'みぎ'])
    if '左' in t:
        tags.update(['左', 'ひだり'])
    if '前' in t:
        tags.update(['前', 'まえ'])
    if '後ろ' in t or '後' in t:
        tags.update(['後ろ', 'うしろ'])
    if '教室' in t or category == '文化・社会' and subcategory == '学校・行事':
        tags.update(['学校', 'がっこう'])
    if code_prefix == '301':
        tags.update(['食べ物', 'たべもの', '料理'])
    if code_prefix == '302':
        tags.update(['飲み物', 'のみもの', 'ドリンク'])
    if code_prefix == '303':
        tags.update(['調味料', '食材'])
    if code_prefix == '501':
        tags.update(['乗り物', 'のりもの', '移動'])
    if code_prefix == '502':
        tags.update(['施設', 'しせつ', '建物'])
    if code_prefix == '504':
        tags.update(['天気', 'てんき', '季節'])
    if code_prefix == '601':
        tags.update(['時間', '日にち', '日付'])
    if code_prefix == '603':
        tags.update(['スポーツ', 'あそび', '活動'])
    if code_prefix == '604':
        tags.update(['数字', 'すうじ', '社会'])
    # digits inside title
    for d in re.findall(r'\d+', unicodedata.normalize('NFKC', t)):
        if d in DIGIT_WORDS:
            tags.update(DIGIT_WORDS[d])
    return tags


def build_tags(title, category, subcategory, code):
    ordered = []
    seen_norm = set()

    def add(term):
        if term is None:
            return
        term = str(term).strip()
        if not term:
            return
        n = normalize_for_match(term)
        if not n or n in seen_norm:
            return
        seen_norm.add(n)
        ordered.append(term)

    # Human-friendly core terms first.
    add(title)
    for base in title_bases(title):
        add(base)
    components = split_components(title)
    for part in components:
        add(part)
    add(category)
    add(subcategory)
    add(code)

    seeds = [title, category, subcategory, code] + components
    for term in group_expansions(seeds):
        add(term)
    for base in title_bases(title):
        if base in EXACT_ALIASES:
            for term in EXACT_ALIASES[base]:
                add(term)
    for term in extra_pattern_tags(title, category, subcategory, code[:3]):
        add(term)

    compact = re.sub(r'\s+', '', unicodedata.normalize('NFKC', PAREN_REMOVE.sub('', title)))
    if compact in DIGIT_WORDS:
        for term in DIGIT_WORDS[compact]:
            add(term)

    broad = [category, subcategory]
    if category == '人・動植物':
        broad += ['人物', '人', 'ひと', '生き物']
    elif category == '動き・様子':
        broad += ['動作', '行動', '気持ち']
    elif category == '飲食物':
        broad += ['食事', '食べる', '飲む']
    elif category == '家の中・身の回り':
        broad += ['家', '生活', '身の回り']
    elif category == '家の外':
        broad += ['外', '町', 'まち']
    elif category == '文化・社会':
        broad += ['学校', '社会', '文化']
    for term in broad:
        add(term)

    # Kana / alternate script variants afterwards.
    originals = list(ordered)
    for term in originals:
        for variant in kana_variants(term):
            add(variant)

    return ordered

# Build cards and copy image assets.
cards = []
with zipfile.ZipFile(ZIP_PATH) as zf:
    entries = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        try:
            decoded = info.filename.encode('cp437').decode('shift_jis')
        except Exception:
            decoded = info.filename
        base = decoded.split('/')[-1]
        m = re.match(r'(\d+)_?(.+?)\.(gif|png|jpe?g)$', base, re.IGNORECASE)
        if not m:
            continue
        code, raw_title, ext = m.groups()
        title = parse_title(raw_title)
        entries.append((code, title, ext.lower(), decoded, info))

    entries.sort(key=lambda x: (x[0], x[1]))

    for idx, (code, title, ext, decoded, info) in enumerate(entries, start=1):
        category, subcategory = CATEGORY_MAP.get(code[:3], ('その他', 'その他'))
        img_name = f'drop_{idx:04d}.{ext}'
        out_img = IMG_DIR / img_name
        with zf.open(info) as src, open(out_img, 'wb') as dst:
            shutil.copyfileobj(src, dst)
        tags = build_tags(title, category, subcategory, code)
        cards.append({
            'id': f'drop_{idx:04d}',
            'code': code,
            'title': title,
            'category': category,
            'subcategory': subcategory,
            'tags': tags,
            'originalFile': decoded,
            'image': f'assets/images/{img_name}',
        })

# Write JSON and CSV
with open(DATA_DIR / 'cards.json', 'w', encoding='utf-8') as f:
    json.dump(cards, f, ensure_ascii=False, indent=2)

with open(DATA_DIR / 'cards.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'code', 'title', 'category', 'subcategory', 'tags', 'originalFile', 'image'])
    for c in cards:
        writer.writerow([c['id'], c['code'], c['title'], c['category'], c['subcategory'], '、'.join(c['tags']), c['originalFile'], c['image']])

index_html = r'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ドロップレット検索</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header">
    <div class="wrap">
      <h1>ドロップレット検索</h1>
      <p class="lead">1406枚のドロップレット画像を、カテゴリ・小カテゴリ・あいまいキーワードで検索できるサイト。</p>
      <p class="sublead">ひらがな・カタカナ・漢字のゆれ、関連語・別名・読み方もできるだけ広めに拾うようにしているよ。</p>
      <div class="stats">
        <span class="stat"><strong id="totalCount">-</strong> 画像</span>
        <span class="stat"><strong id="resultCount">-</strong></span>
      </div>
    </div>
  </header>

  <main class="wrap main-layout">
    <section class="panel controls">
      <div class="search-row">
        <label class="sr-only" for="searchInput">検索</label>
        <input id="searchInput" type="search" placeholder="例：おとこ / 先生 / でんしゃ / びょういん / ありがとう" autocomplete="off">
        <button id="clearButton" class="secondary-button" type="button">クリア</button>
      </div>

      <div id="categoryButtons" class="chip-row"></div>

      <div class="filter-grid">
        <label>
          <span>大カテゴリ</span>
          <select id="categorySelect"></select>
        </label>
        <label>
          <span>小カテゴリ</span>
          <select id="subcategorySelect"></select>
        </label>
        <label>
          <span>並び替え</span>
          <select id="sortSelect">
            <option value="score">おすすめ順</option>
            <option value="code">番号順</option>
            <option value="title">タイトル順</option>
          </select>
        </label>
      </div>

      <details class="tips">
        <summary>検索のコツ</summary>
        <ul>
          <li>「おとこ」「男」「男性」みたいな表記ゆれで探せるようにしてある。</li>
          <li>スペース区切りで複数語検索できる。例：「先生 女」</li>
          <li>各画像の右下に、<strong>コピー</strong> と <strong>ダウンロード</strong> のアイコンを付けてある。</li>
        </ul>
      </details>
    </section>

    <section class="panel results-panel">
      <div id="grid" class="grid"></div>
      <button id="moreButton" class="more-button" type="button">もっと見る</button>
    </section>
  </main>

  <dialog id="previewDialog" class="preview-dialog">
    <div class="dialog-top">
      <h2 id="previewTitle"></h2>
      <button id="closeDialog" class="icon-button close-button" type="button" aria-label="閉じる">✕</button>
    </div>
    <div class="preview-body">
      <div class="preview-image-wrap">
        <img id="previewImage" alt="">
      </div>
      <div class="preview-info">
        <p id="previewMeta" class="preview-meta"></p>
        <p id="previewOriginal" class="preview-original"></p>
        <p id="previewTags" class="preview-tags"></p>
        <div class="preview-actions">
          <button id="previewCopy" class="primary-action" type="button"><span class="btn-icon">📋</span>画像をコピー</button>
          <button id="previewDownload" class="primary-action" type="button"><span class="btn-icon">⬇</span>ダウンロード</button>
          <button id="previewOpen" class="secondary-button" type="button">画像だけ開く</button>
        </div>
      </div>
    </div>
  </dialog>

  <div id="toast" class="toast" hidden></div>
  <script src="app.js"></script>
</body>
</html>
'''

styles_css = r''':root {
  --bg: #f4f7fb;
  --card: #ffffff;
  --line: #d6dce5;
  --text: #1e293b;
  --muted: #64748b;
  --primary: #2563eb;
  --primary-soft: #dbeafe;
  --shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--text);
}
.wrap {
  width: min(1200px, calc(100% - 24px));
  margin: 0 auto;
}
.site-header {
  padding: 28px 0 18px;
}
h1 {
  margin: 0 0 8px;
  font-size: clamp(1.7rem, 4vw, 2.6rem);
}
.lead, .sublead {
  margin: 0;
  line-height: 1.6;
  color: var(--muted);
}
.sublead { margin-top: 4px; }
.stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 18px;
}
.stat {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 8px 14px;
  box-shadow: var(--shadow);
}
.main-layout {
  display: grid;
  gap: 18px;
  grid-template-columns: 320px minmax(0, 1fr);
  padding-bottom: 36px;
}
.panel {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 20px;
  box-shadow: var(--shadow);
}
.controls { padding: 18px; position: sticky; top: 12px; align-self: start; }
.search-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}
input[type="search"], select {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 1rem;
  background: #fff;
}
.filter-grid {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}
.filter-grid label span {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 6px;
}
.chip-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}
.chip, .secondary-button, .more-button, .icon-button, .icon-action, .primary-action {
  border: 1px solid var(--line);
  background: #fff;
  color: var(--text);
  border-radius: 12px;
  padding: 10px 14px;
  cursor: pointer;
  font: inherit;
}
.chip.active {
  background: var(--primary-soft);
  border-color: #93c5fd;
  color: #1d4ed8;
}
.secondary-button:hover, .more-button:hover, .icon-button:hover, .icon-action:hover, .primary-action:hover, .chip:hover {
  filter: brightness(0.98);
}
.tips {
  margin-top: 16px;
  border-top: 1px solid var(--line);
  padding-top: 14px;
}
.tips summary {
  cursor: pointer;
  font-weight: 700;
}
.tips ul {
  padding-left: 18px;
  color: var(--muted);
  line-height: 1.7;
}
.results-panel { padding: 16px; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 14px;
}
.card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 12px;
  cursor: pointer;
  min-height: 100%;
}
.card:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06); }
.thumb-wrap {
  aspect-ratio: 1 / 1;
  display: grid;
  place-items: center;
  background: #f8fafc;
  border-radius: 12px;
  overflow: hidden;
}
.thumb {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.title {
  font-weight: 700;
  line-height: 1.4;
}
.meta {
  font-size: 0.84rem;
  color: var(--muted);
}
.card-actions {
  margin-top: auto;
  display: flex;
  gap: 8px;
}
.icon-action {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 10px;
  font-size: 0.92rem;
}
.more-button {
  display: block;
  margin: 20px auto 6px;
  min-width: 180px;
}
.preview-dialog {
  width: min(960px, calc(100% - 20px));
  border: none;
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.18);
}
.preview-dialog::backdrop { background: rgba(15, 23, 42, 0.45); }
.dialog-top {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 12px;
}
.preview-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
  margin-top: 12px;
}
.preview-image-wrap {
  background: #f8fafc;
  border-radius: 16px;
  display: grid;
  place-items: center;
  min-height: 360px;
}
.preview-image-wrap img {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
}
.preview-meta, .preview-original, .preview-tags {
  color: var(--muted);
  line-height: 1.7;
  margin: 0 0 12px;
}
.preview-actions {
  display: grid;
  gap: 10px;
}
.primary-action {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}
.btn-icon { margin-right: 4px; }
.toast {
  position: fixed;
  left: 50%;
  bottom: 18px;
  transform: translateX(-50%);
  background: rgba(15, 23, 42, 0.92);
  color: white;
  padding: 10px 14px;
  border-radius: 999px;
  z-index: 30;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
@media (max-width: 960px) {
  .main-layout { grid-template-columns: 1fr; }
  .controls { position: static; }
  .preview-body { grid-template-columns: 1fr; }
}
'''

app_js = r'''let allCards = [];
let filteredCards = [];
let visibleCount = 0;
let activePreviewId = null;
const PAGE_SIZE = 96;
const $ = (id) => document.getElementById(id);

function kanaToHira(str) {
  return String(str || "").replace(/[\u30a1-\u30f6]/g, ch => String.fromCharCode(ch.charCodeAt(0) - 0x60));
}

function normalizeText(str) {
  return kanaToHira(String(str || ""))
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[\s　・･、。,.，．（）()［\]【】「」『』\-_/／]+/g, "")
    .trim();
}

function tokenizeQuery(query) {
  return String(query || "")
    .trim()
    .split(/[\s　]+/)
    .map(normalizeText)
    .filter(Boolean);
}

function unique(arr) {
  return [...new Set(arr)].filter(Boolean);
}

function makeSearchTerms(card) {
  return unique([card.title, card.category, card.subcategory, card.code, ...(card.tags || [])]);
}

function makeSearchText(card) {
  return makeSearchTerms(card).map(normalizeText).join(" ");
}

function levenshtein(a, b) {
  if (a === b) return 0;
  if (!a.length || !b.length) return Math.max(a.length, b.length);
  const dp = Array.from({ length: a.length + 1 }, (_, i) => Array(b.length + 1).fill(0));
  for (let i = 0; i <= a.length; i++) dp[i][0] = i;
  for (let j = 0; j <= b.length; j++) dp[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost);
    }
  }
  return dp[a.length][b.length];
}

function scoreTokenAgainstCard(card, token) {
  const terms = card._searchTerms;
  const title = normalizeText(card.title);

  if (title === token) return 2000;
  if (terms.includes(token)) return 1800;
  if (title.startsWith(token)) return 1200;
  if (title.includes(token)) return 1000;
  if (card.searchText.includes(token)) return 800;

  let best = 0;
  for (const term of terms) {
    if (!term) continue;
    if (term.includes(token) || token.includes(term)) best = Math.max(best, 650);
    const limit = token.length <= 3 ? 1 : token.length <= 6 ? 2 : 3;
    const d = levenshtein(token, term);
    if (d <= limit) best = Math.max(best, 480 - d * 40);
  }
  return best;
}

function scoreCard(card, query) {
  const tokens = tokenizeQuery(query);
  if (!tokens.length) return 0;
  let total = 0;
  for (const token of tokens) {
    const s = scoreTokenAgainstCard(card, token);
    if (s <= 0) return 0;
    total += s;
  }
  return total;
}

function initFilters() {
  const categories = unique(allCards.map(c => c.category));
  $("categorySelect").innerHTML = `<option value="">すべての大カテゴリ</option>` + categories.map(c => `<option>${escapeHtml(c)}</option>`).join("");
  $("categoryButtons").innerHTML = [`<button class="chip active" data-cat="">全部</button>`, ...categories.map(c => `<button class="chip" data-cat="${escapeHtml(c)}">${escapeHtml(c)}</button>`)].join("");
  document.querySelectorAll(".chip").forEach(btn => {
    btn.addEventListener("click", () => {
      $("categorySelect").value = btn.dataset.cat;
      updateSubcategoryOptions();
      applySearch();
    });
  });
  updateSubcategoryOptions();
}

function updateSubcategoryOptions() {
  const cat = $("categorySelect").value;
  const subs = unique(allCards.filter(c => !cat || c.category === cat).map(c => c.subcategory));
  $("subcategorySelect").innerHTML = `<option value="">すべての小カテゴリ</option>` + subs.map(s => `<option>${escapeHtml(s)}</option>`).join("");
  document.querySelectorAll(".chip").forEach(btn => btn.classList.toggle("active", btn.dataset.cat === cat));
}

function applySearch() {
  const query = $("searchInput").value;
  const hasQuery = tokenizeQuery(query).length > 0;
  const cat = $("categorySelect").value;
  const sub = $("subcategorySelect").value;
  const sort = $("sortSelect").value;

  filteredCards = allCards
    .map(card => ({ ...card, score: hasQuery ? scoreCard(card, query) : 0 }))
    .filter(card => {
      const okQuery = !hasQuery || card.score > 0;
      const okCat = !cat || card.category === cat;
      const okSub = !sub || card.subcategory === sub;
      return okQuery && okCat && okSub;
    });

  if (sort === "score") {
    filteredCards.sort((a, b) => (b.score - a.score) || String(a.code).localeCompare(String(b.code), "ja"));
  } else if (sort === "title") {
    filteredCards.sort((a, b) => String(a.title).localeCompare(String(b.title), "ja"));
  } else {
    filteredCards.sort((a, b) => String(a.code).localeCompare(String(b.code), "ja"));
  }

  visibleCount = PAGE_SIZE;
  render();
}

function render() {
  const shown = filteredCards.slice(0, visibleCount);
  $("resultCount").textContent = `${filteredCards.length}件ヒット`;
  $("grid").innerHTML = shown.map(card => `
    <article class="card" tabindex="0" data-id="${card.id}">
      <div class="thumb-wrap">
        <img class="thumb" src="${card.image}" alt="${escapeHtml(card.title)}" loading="lazy">
      </div>
      <div>
        <div class="title">${escapeHtml(card.title)}</div>
        <div class="meta">${escapeHtml(card.subcategory)} / ${escapeHtml(card.code)}</div>
      </div>
      <div class="card-actions">
        <button class="icon-action" type="button" data-action="copy" data-id="${card.id}" title="画像をコピー">📋 コピー</button>
        <button class="icon-action" type="button" data-action="download" data-id="${card.id}" title="ダウンロード">⬇ 保存</button>
      </div>
    </article>
  `).join("");

  document.querySelectorAll(".card").forEach(el => {
    el.addEventListener("click", (e) => {
      if (e.target.closest(".icon-action")) return;
      openPreview(el.dataset.id);
    });
    el.addEventListener("keydown", (e) => { if (e.key === "Enter") openPreview(el.dataset.id); });
  });

  document.querySelectorAll(".icon-action").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const card = allCards.find(c => c.id === btn.dataset.id);
      if (!card) return;
      if (btn.dataset.action === "copy") await copyImage(card);
      if (btn.dataset.action === "download") downloadImage(card);
    });
  });

  $("moreButton").style.display = visibleCount < filteredCards.length ? "block" : "none";
}

function openPreview(id) {
  const card = allCards.find(c => c.id === id);
  if (!card) return;
  activePreviewId = id;
  $("previewImage").src = card.image;
  $("previewImage").alt = card.title;
  $("previewTitle").textContent = card.title;
  $("previewMeta").textContent = `${card.category} ＞ ${card.subcategory} / 番号：${card.code}`;
  $("previewOriginal").textContent = `元ファイル：${card.originalFile}`;
  $("previewTags").textContent = `検索ワード：${(card.tags || []).slice(0, 60).join("、")}`;
  $("previewDialog").showModal();
}

function makeDownloadName(card) {
  const ext = (card.image.split('.').pop() || 'png').toLowerCase();
  const title = String(card.title || 'droplet').replace(/[\\/:*?"<>|]/g, '_');
  return `${title}.${ext}`;
}

async function fetchImageBlob(card) {
  const res = await fetch(card.image);
  if (!res.ok) throw new Error('画像取得に失敗しました');
  return await res.blob();
}

async function copyImage(card) {
  try {
    const blob = await fetchImageBlob(card);
    if (!navigator.clipboard || !window.ClipboardItem) throw new Error('copy-unsupported');
    await navigator.clipboard.write([new ClipboardItem({ [blob.type || 'image/png']: blob })]);
    showToast('画像をコピーしたよ');
  } catch (err) {
    console.error(err);
    showToast('コピーできなかったので、プレビューから長押し保存してね');
    openPreview(card.id);
  }
}

function downloadImage(card) {
  const a = document.createElement('a');
  a.href = card.image;
  a.download = makeDownloadName(card);
  document.body.appendChild(a);
  a.click();
  a.remove();
  showToast('ダウンロードを開始したよ');
}

function showToast(message) {
  const el = $("toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => { el.hidden = true; }, 2200);
}

function escapeHtml(str) {
  return String(str || "").replace(/[&<>"']/g, s => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[s]));
}

async function start() {
  const res = await fetch('data/cards.json');
  allCards = await res.json();
  allCards = allCards.map(card => ({
    ...card,
    _searchTerms: makeSearchTerms(card).map(normalizeText),
    searchText: makeSearchText(card),
  }));
  filteredCards = [...allCards];
  $("totalCount").textContent = `${allCards.length}`;
  initFilters();
  applySearch();

  $("searchInput").addEventListener("input", applySearch);
  $("categorySelect").addEventListener("change", () => { updateSubcategoryOptions(); applySearch(); });
  $("subcategorySelect").addEventListener("change", applySearch);
  $("sortSelect").addEventListener("change", applySearch);
  $("clearButton").addEventListener("click", () => {
    $("searchInput").value = "";
    $("categorySelect").value = "";
    updateSubcategoryOptions();
    $("subcategorySelect").value = "";
    $("sortSelect").value = "score";
    applySearch();
    $("searchInput").focus();
  });
  $("moreButton").addEventListener("click", () => { visibleCount += PAGE_SIZE; render(); });
  $("closeDialog").addEventListener("click", () => $("previewDialog").close());
  $("previewCopy").addEventListener("click", async () => {
    const card = allCards.find(c => c.id === activePreviewId);
    if (card) await copyImage(card);
  });
  $("previewDownload").addEventListener("click", () => {
    const card = allCards.find(c => c.id === activePreviewId);
    if (card) downloadImage(card);
  });
  $("previewOpen").addEventListener("click", () => {
    const card = allCards.find(c => c.id === activePreviewId);
    if (card) window.open(card.image, '_blank');
  });
}

start().catch(err => {
  console.error(err);
  $("grid").innerHTML = '<p>データの読み込みに失敗しました。GitHub Pagesなどのサーバー上で開いてください。</p>';
});
'''

readme = f'''# ドロップレット検索サイト（改良版）

1406枚のドロップレット画像を検索できる静的サイトです。

## 主な改良点

- 1406枚を再確認して、`data/cards.json` と `data/cards.csv` を再生成
- タイトル・カテゴリ・小カテゴリだけでなく、**関連語・別名・読み方・表記ゆれ** を広めに付与
- ひらがな / カタカナ / 漢字 / 一部ローマ字のゆれに対応
- スペース区切りの複数語検索に対応
- 検索結果カードとプレビューの両方に **コピー** / **ダウンロード** ボタンを追加

## 使い方

1. このフォルダ一式を GitHub にアップロードする
2. GitHub Pages を有効にする
3. `index.html` を開く

## ファイル構成

- `index.html` … 画面本体
- `styles.css` … 見た目
- `app.js` … 検索処理・コピー/ダウンロード処理
- `data/cards.json` … 検索データ
- `data/cards.csv` … Excel でも編集しやすい一覧
- `assets/images/` … 画像1406枚

## メモ

- 画像コピーはブラウザの対応状況に左右されます。GitHub Pages の HTTPS 上での利用を前提にしています。
- Safari などで画像コピーがうまくいかない場合は、プレビューから長押し保存・共有がしやすいようにしてあります。
- 検索語はあとから `data/cards.csv` を編集して、さらに強化できます。
'''

for name, content in [('index.html', index_html), ('styles.css', styles_css), ('app.js', app_js), ('README.md', readme)]:
    with open(OUT_DIR / name, 'w', encoding='utf-8') as f:
        f.write(content)

# include builder script for transparency
shutil.copy('/mnt/data/build_droplet_site_v2.py', OUT_DIR / 'build_droplet_site_v2.py')

# zip it
zip_path = Path('/mnt/data/droplet_search_site_v2.zip')
if zip_path.exists():
    zip_path.unlink()
shutil.make_archive('/mnt/data/droplet_search_site_v2', 'zip', OUT_DIR)

print(f'Built {len(cards)} cards at {OUT_DIR}')
print('ZIP:', zip_path)
# quick sample
for c in cards[:10]:
    print(c['title'], '->', c['tags'][:12])
