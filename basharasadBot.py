
bot = Client("TOKEN")


from balethon import Client
from balethon.conditions import reply, regex, new_chat_members, group,private, equals
from balethon.conditions import private, successful_payment
from balethon.objects import LabeledPrice
from balethon.objects import ReplyKeyboard
import sqlite3
import json
import os
from datetime import datetime, timedelta
import asyncio
import random
import re

HACK_COST = 5000
HACK_SUCCESS_CHANCE = 70 

PROVIDER_TOKEN = ""


CEASEFIRE_VOTES = set()
CEASEFIRE_END_TIME = 0
CEASEFIRE_VOTE_LIMIT = 7
CEASEFIRE_DURATION = 6 * 60 * 60  


ELECTRON_WAR_DURATION = 24 * 60 * 60  


GAMBLE_QUEUE = []  
GAMBLE_MIN_AMOUNT = 100  

MISSILE_COOLDOWN = {}
MAX_MISSILES_PER_HOUR = 5

MINER_TYPES = {
    "CPU": {"price": 1000, "output_btc_per_hour": 0.00001},
    "GPU": {"price": 5000, "output_btc_per_hour": 0.00005},
    "ASIC": {"price": 20000, "output_btc_per_hour": 0.0002},
    "FPGA": {"price": 50000, "output_btc_per_hour": 0.0005},
    "Quantum": {"price": 500000, "output_btc_per_hour": 0.005}
}
MINER_INVENTORY_FILE = "miner_inventory.json"

def is_ceasefire_active():
    """بررسی فعال بودن آتش‌بس"""
    global CEASEFIRE_END_TIME
    if CEASEFIRE_END_TIME == 0:
        return False
    return datetime.now().timestamp() < CEASEFIRE_END_TIME

def add_ceasefire_vote(user_id):
    """افزودن رای برای آتش‌بس و مدیریت زمان"""
    global CEASEFIRE_VOTES, CEASEFIRE_END_TIME
    
    if is_ceasefire_active():
        return False, "آتش‌بس از قبل فعال است!"
    
    CEASEFIRE_VOTES.add(user_id)
    
    if len(CEASEFIRE_VOTES) >= CEASEFIRE_VOTE_LIMIT:

        CEASEFIRE_END_TIME = datetime.now().timestamp() + CEASEFIRE_DURATION
        return True, f"آتش‌بس با {len(CEASEFIRE_VOTES)} رای فعال شد!"
    else:
        return False, f"رای شما ثبت شد. ({len(CEASEFIRE_VOTES)}/{CEASEFIRE_VOTE_LIMIT})"

def is_electron_war_active(user_id):
    """بررسی فعال بودن جنگ الکترونیک برای یک کاربر خاص"""
    user = get_user(user_id)
    if not user:
        return False

    if user.get('electron_war_active', 0) != 1:
        return False
    
    end_time = user.get('electron_war_end', 0)
    current_time = datetime.now().timestamp()

    if end_time > 0 and current_time >= end_time:
        update_electron_war_status(user_id, 0, 0)
        return False
        
    return True

def update_electron_war_status(user_id, active: int, end_time: float = 0):
    """به‌روزرسانی وضعیت جنگ الکترونیک در دیتابیس"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE users SET electron_war_active = ?, electron_war_end = ? WHERE user_id = ?
        ''', (active, end_time, str(user_id)))
    except sqlite3.OperationalError:
        
        cursor.execute('''
            UPDATE users SET electron_war_active = ? WHERE user_id = ?
        ''', (active, str(user_id)))
    conn.commit()
    conn.close()

DADDY_USERS = [1208847974]
GOODLIST = {
    "جاوید شاه": 6, "مرگ بر جمهوری اسلامی": 1, "کیر تو جمهوری اسلامی": 1,
    "مرگ بر اخوند": 1, "مرگ بر آخوند": 1, "ک م خ": 1, "کص ننه خامنه ای": 1,
    "یا حسین": 1, "یا علی": 1, "یا عباس": 1, "کص ننه آخوند": 1, "کیر تو آخوند": 1,
    "آخوند مادر جنده": 1, "استخون های مرده هام تو کص و کون زنده های آخوند": 5,
    "یا مهاجری کبیر": 2
}
BADLIST = ["مرگ بر آمریکا", "سس خرسی", "جانم فدای رهبر", "کیر تو پهلوی", "چاپید شاه",
           "کص ننه پهلوی", "سیکیلی شاه", "کص مادر شاه"]
MISSILE_PRICES = {"فاتح": 2000, "قیام": 2500, "ذوالفقار": 3000, "شهاب": 3600, "قدر": 4000,
                  "عماد": 4400, "قاسم": 5000, "سجیل": 5500, "خیبرشکن": 6100, "خرمشهر": 7000,
                  "الخلیج": 7500, "فتاح": 8000, "آتش": 8600, "رستاخیز": 10000, "اتمیک": 50000, "هیدروژنیک": 200000}
MISSILE_DAMAGE = {"فاتح": 3000, "قیام": 4000, "ذوالفقار": 5000, "شهاب": 6000, "قدر": 8000,
                  "عماد": 9000, "قاسم": 10000, "سجیل": 11500, "خیبرشکن": 12000, "خرمشهر": 13000,
                  "الخلیج": 14000, "فتاح": 15000, "آتش": 16000, "رستاخیز": 17000, "اتمیک": 99999, "هیدروژنیک": 999999}
DEFENSE_PRICES = {"مجید": 1000, "مرصاد": 1300, "خرداد": 1500, "صیاد": 2000, "آرمان": 2500, "s300": 3000, "باور": 4000, "s400": 5000, "HQ9": 7000, "مهران": 8000, "s500": 10000, "تاد": 12500, "پاتریوت": 15000}
DEFENSE_CHANCE = {"مجید": 5, "مرصاد": 10, "خرداد": 15, "صیاد": 20, "آرمان": 30, "s300": 35, "باور": 40, "s400": 50, "HQ9": 60, "مهران": 65, "s500": 70, "تاد": 75, "پاتریوت": 85}
MAX_DEFENSE_USES = 1 
MAX_DEFENSE_COUNT = 1 


DB_FILE = "bashar.db"
INVENTORY_FILE = "missile_inventory.json"
DEFENSE_INVENTORY_FILE = "defense_inventory.json"

missile_inventory = {}
defense_inventory = {}
cooking_users = {}
miner_inventory = {} 
user_btc = {} 

def safe_load_json(filename):
    """بارگذاری امن JSON"""
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except:
        print(f"⚠️ فایل {filename} خراب - ساخت جدید")
        return {}

def safe_save_json(filename, data):
    """ذخیره امن JSON با فایل موقت"""
    try:
        temp_file = filename + ".tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, filename)
    except Exception as e:
        print(f"❌ خطای ذخیره {filename}: {e}")

def init_db():
    """راه‌اندازی دیتابیس"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY, username TEXT, first_name TEXT, ajr INTEGER DEFAULT 0,
            naft INTEGER DEFAULT 0, almas INTEGER DEFAULT 0, join_date TEXT,
            last_update TEXT, total_messages INTEGER DEFAULT 0, electron_war_active INTEGER DEFAULT 0,
            electron_war_end REAL DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            user_id TEXT PRIMARY KEY, username TEXT, first_name TEXT, ajr INTEGER, last_update TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ دیتابیس آماده!")

def get_db_connection():
    """اتصال به دیتابیس"""
    return sqlite3.connect(DB_FILE)

def ensure_user(user_id, user=None):
    """اطمینان از وجود کاربر"""
    if get_user(user_id):
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    username = user.username if user and hasattr(user, 'username') else ''
    first_name = user.first_name if user and hasattr(user, 'first_name') else ''
    cursor.execute('''
        INSERT INTO users (user_id, username, first_name, join_date, last_update)
        VALUES (?, ?, ?, ?, ?)
    ''', (str(user_id), username, first_name, now, now))
    conn.commit()
    conn.close()
    global missile_inventory, defense_inventory, miner_inventory, user_btc
    uid_str = str(user_id)
    if uid_str not in missile_inventory:
        missile_inventory[uid_str] = {m: 0 for m in MISSILE_PRICES}
    if uid_str not in defense_inventory:
        defense_inventory[uid_str] = {d: {"count": 0, "uses_left": MAX_DEFENSE_USES} for d in DEFENSE_PRICES}
    if uid_str not in miner_inventory:
        miner_inventory[uid_str] = {m: 0 for m in MINER_TYPES}
    if uid_str not in user_btc:
        user_btc[uid_str] = 0.0
    safe_save_json(INVENTORY_FILE, missile_inventory)
    safe_save_json(DEFENSE_INVENTORY_FILE, defense_inventory)
    safe_save_json(MINER_INVENTORY_FILE, miner_inventory)

def get_user(user_id):
    """دریافت اطلاعات کاربر"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            'username': result[1] or '', 'first_name': result[2] or '',
            'ajr': result[3] or 0, 'naft': result[4] or 0,
            'almas': result[5] or 0, 'join_date': result[6] or 'نامشخص',
            'last_update': result[7] or 'هیچوقت', 'total_messages': result[8] or 0,
            'electron_war_active': result[9] or 0, 'electron_war_end': result[10] or 0
        }
    return None

def get_user_inventory(user_id):
    """دریافت موجودی موشک‌ها"""
    global missile_inventory
    uid_str = str(user_id)
    if uid_str not in missile_inventory:
        missile_inventory[uid_str] = {m: 0 for m in MISSILE_PRICES}
        safe_save_json(INVENTORY_FILE, missile_inventory)
    return missile_inventory[uid_str]

def get_user_defense(user_id):
    """دریافت پدافند کاربر با تعداد استفاده"""
    global defense_inventory
    uid_str = str(user_id)
    if uid_str not in defense_inventory:
        defense_inventory[uid_str] = {d: {"count": 0, "uses_left": MAX_DEFENSE_USES} for d in DEFENSE_PRICES}
        safe_save_json(DEFENSE_INVENTORY_FILE, defense_inventory)
    return defense_inventory[uid_str]

def get_user_miners(user_id):
    """دریافت ماینرهای کاربر"""
    global miner_inventory
    uid_str = str(user_id)
    if uid_str not in miner_inventory:
        miner_inventory[uid_str] = {m: 0 for m in MINER_TYPES}
        safe_save_json(MINER_INVENTORY_FILE, miner_inventory)
    return miner_inventory[uid_str]

def get_user_btc(user_id):
    """دریافت بیت‌کوین کاربر"""
    global user_btc
    uid_str = str(user_id)
    if uid_str not in user_btc:
        user_btc[uid_str] = 0.0
    return user_btc[uid_str]

def display_name(user):
    """نمایش نام کاربر"""
    if getattr(user, "username", None):
        return f"@{user.username}"
    return f"[{user.first_name or 'کاربر'}](tg://user?id={user.id})"

def get_display_name(user_id):
    """دریافت نام نمایشی"""
    user_data = get_user(user_id)
    if user_data and user_data['username']:
        return f"@{user_data['username']}"
    elif user_data and user_data['first_name']:
        return user_data['first_name']
    return f"کاربر {user_id}"

def sync_leaderboard(user_id):
    """همگام‌سازی لیدربورد"""
    user = get_user(user_id)
    if not user: return
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    display_ajr = 0 if is_electron_war_active(user_id) else user['ajr']
    cursor.execute('''
        INSERT OR REPLACE INTO leaderboard (user_id, username, first_name, ajr, last_update)
        VALUES (?, ?, ?, ?, ?)
    ''', (str(user_id), user['username'], user['first_name'], display_ajr, now))
    conn.commit()
    conn.close()

def update_ajr_safe(user_id, change):
    """به‌روزرسانی امن اجر"""
    ensure_user(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute('''
        UPDATE users SET ajr = MAX(0, ajr + ?), last_update = ?,
        total_messages = total_messages + 1 WHERE user_id = ?
    ''', (change, now, str(user_id)))
    conn.commit()
    conn.close()
    sync_leaderboard(user_id)

def update_almas_safe(user_id, change):
    """به‌روزرسانی امن الماس"""
    ensure_user(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute('UPDATE users SET almas = MAX(0, almas + ?), last_update = ? WHERE user_id = ?',
                  (change, now, str(user_id)))
    conn.commit()
    conn.close()

def convert_almas_to_ajr(user_id, amount):
    """تبدیل الماس به اجر"""
    user = get_user(user_id)
    if user['almas'] >= amount:
        update_almas_safe(user_id, -amount)
        ajr_gain = amount * 10000
        update_ajr_safe(user_id, ajr_gain)
        return True, ajr_gain
    return False, 0

def get_leaderboard(top=10):
    """دریافت لیدربورد"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, ajr FROM leaderboard ORDER BY ajr DESC LIMIT ?', (top,))
    result = cursor.fetchall()
    conn.close()
    return result

def get_rank(ajr):
    """دریافت رتبه"""
    if ajr >= 15000000: return "👑 شاهنشاه"
    elif ajr >= 5000000: return "⚜️ ولیعهد"
    elif ajr >= 100000: return "🎖️ سپهبد"
    elif ajr >= 10000: return "🪖 سرباز شاه"
    return "🔰 نوآموز"

async def delete_after_delay(message, seconds=30):
    """حذف پیام با تاخیر"""
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except: pass

def royal_text(title, body):
    """فرمت سلطنتی"""
    return f"👑 **{title}**\n━━━━━━━━━━━━━━━━\n{body}\n━━━━━━━━━━━━━━━━"

def check_missile_cooldown(user_id):
    """بررسی محدودیت شلیک (5 موشک در ساعت)"""
    global MISSILE_COOLDOWN
    now = datetime.now().timestamp()
    
    if user_id not in MISSILE_COOLDOWN:
        MISSILE_COOLDOWN[user_id] = []
    
    MISSILE_COOLDOWN[user_id] = [t for t in MISSILE_COOLDOWN[user_id] if now - t < 3600]
    
    if len(MISSILE_COOLDOWN[user_id]) >= MAX_MISSILES_PER_HOUR:
        return False
    return True

def record_missile_launch(user_id):
    """ثبت زمان شلیک برای محدودیت‌گذاری"""
    global MISSILE_COOLDOWN
    if user_id not in MISSILE_COOLDOWN:
        MISSILE_COOLDOWN[user_id] = []
    MISSILE_COOLDOWN[user_id].append(datetime.now().timestamp())

def update_miner_production():
    """به‌روزرسانی تولید بیت‌کوین بر اساس زمان واقعی"""
    global miner_inventory, user_btc
    
    current_time = datetime.now().timestamp()
    
    for uid_str, miners in miner_inventory.items():
        for miner_name, count in miners.items():
            if count > 0:
                miner_info = MINER_TYPES[miner_name]
                btc_per_hour = miner_info['output_btc_per_hour'] * count
                pass

def calculate_btc_to_sell(user_id):
    """محاسبه بیت‌کوین تولید شده تا الان برای فروش"""
    global miner_inventory, user_btc
    
    uid_str = str(user_id)
    miners = get_user_miners(user_id)
    current_btc = get_user_btc(user_id)
    
    if not any(miners.values()):
        return current_btc
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS miner_stats (
            user_id TEXT PRIMARY KEY,
            last_update_time REAL
        )
    ''')
    conn.commit()
    
    cursor.execute("SELECT last_update_time FROM miner_stats WHERE user_id = ?", (uid_str,))
    row = cursor.fetchone()
    
    now = datetime.now().timestamp()
    last_update = 0
    if row:
        last_update = row[0]
    else:
        last_update = now 

    diff_seconds = now - last_update
    diff_hours = diff_seconds / 3600
    
    total_btc_generated = 0
    for miner_name, count in miners.items():
        if count > 0:
            total_btc_generated += MINER_TYPES[miner_name]['output_btc_per_hour'] * count * diff_hours
            
    new_btc = current_btc + total_btc_generated
    
    cursor.execute('''
        INSERT OR REPLACE INTO miner_stats (user_id, last_update_time)
        VALUES (?, ?)
    ''', (uid_str, now))
    conn.commit()
    conn.close()
    user_btc[uid_str] = new_btc
    
    return new_btc

missile_inventory = safe_load_json(INVENTORY_FILE)
defense_inventory = safe_load_json(DEFENSE_INVENTORY_FILE)
miner_inventory = safe_load_json(MINER_INVENTORY_FILE)
init_db()


@bot.on_command(private)
async def start(*, message):
    ensure_user(message.author.id, message.author)
    sync_leaderboard(message.author.id)
    text = royal_text("درود بر شما",
        f"به **ربات شاهنشاهی بشار الاسد** خوش آمدید.\n\n"
        f"🔘 **منوی اصلی:**\n"
        f"➖➖➖➖➖➖➖➖➖\n"
        f"🔹 `/پروفایل` : مشاهده وضعیت شما\n"
        f"🔹 `/لیدربورد` : برترین‌های ایران\n"
        f"🔹 `/موشک‌ها` : لیست و خرید موشک\n"
        f"🔹 `/پدافند` : خرید سیستم‌های دفاعی\n"
        f"🔹 `/موجودی` : زرادخانه شخصی\n"
        f"🔹 `/الماس` : وضعیت الماس و پدافند\n"
        f"🔹 `/ماینر` : خرید و مدیریت ماینر بیت‌کوین\n"
        f"➖➖➖➖➖➖➖➖➖\n"
        f"💎 `تبدیل 1` : تبدیل الماس به اجر\n"
        f"✌️ `آتش بس` : رای برای صلح\n"
        f"💸 `هدیه` : انتقال الماس به دیگران\n"
        f"🎯 `شلیک ... [آیدی]` : شلیک از دور\n"
        f"📡 `جنگ الکترونیک` : مخفی کردن اجر\n"
        f"🎲 `قمار [مبلغ]` : شرط‌بندی با دیگران\n"
        f"🔥 `پخت کتلت` : کسب درآمد رندوم\n"
        f"🕷️ `هک کردن` : (ریپلای) دیدن دارایی\n"
        f"➖➖➖➖➖➖➖➖➖\n"
        f"💡 _برای خرید موشک یا پدافند، از منوی متنی استفاده کنید یا در PV دکمه‌ها را بزنید._")
    msg = await message.reply(text,ReplyKeyboard(
                ["📇 پروفایل","💰 زرادخانه"],
                ["🏆 لیدربورد"],
                ["🚀 موشک ها","🛡️ پدافند"],
                ["💎 الماس"],
                ["📡 جنگ الکترونیک","⛏️ ماینر"],
                ["🕊️ وضعیت آتش بس","✋ آتش بس"],
                ["🔙 بازگشت به منو"]
            )) 
            
            
    
@bot.on_command(group)
async def start(*, message):
    ensure_user(message.author.id, message.author)
    sync_leaderboard(message.author.id)
    text = royal_text("درود بر شما",
        f"به **ربات شاهنشاهی بشار الاسد** خوش آمدید.\n\n"
        f"🔘 **منوی اصلی:**\n"
        f"➖➖➖➖➖➖➖➖➖\n"
        f"🔹 `/پروفایل` : مشاهده وضعیت شما\n"
        f"🔹 `/لیدربورد` : برترین‌های ایران\n"
        f"🔹 `/موشک‌ها` : لیست و خرید موشک\n"
        f"🔹 `/پدافند` : خرید سیستم‌های دفاعی\n"
        f"🔹 `/موجودی` : زرادخانه شخصی\n"
        f"🔹 `/الماس` : وضعیت الماس و پدافند\n"
        f"🔹 `/ماینر` : خرید و مدیریت ماینر بیت‌کوین\n"
        f"➖➖➖➖➖➖➖➖➖\n"
        f"💎 `تبدیل 1` : تبدیل الماس به اجر\n"
        f"✌️ `آتش بس` : رای برای صلح\n"
        f"💸 `هدیه` : انتقال الماس به دیگران\n"
        f"🎯 `شلیک ... [آیدی]` : شلیک از دور\n"
        f"📡 `جنگ الکترونیک` : مخفی کردن اجر\n"
        f"🎲 `قمار [مبلغ]` : شرط‌بندی با دیگران\n"
        f"🔥 `پخت کتلت` : کسب درآمد رندوم\n"
        f"🕷️ `هک کردن` : (ریپلای) دیدن دارایی\n"
        f"➖➖➖➖➖➖➖➖➖\n"
        f"💡 _برای خرید موشک یا پدافند، از منوی متنی استفاده کنید یا در PV دکمه‌ها را بزنید._")
    msg = await message.reply(text)
    asyncio.create_task(delete_after_delay(message))
    asyncio.create_task(delete_after_delay(msg))

@bot.on_command(reply)
async def delete(*, message):
    try: await message.reply_to_message.delete()
    except: pass
    msg = await message.reply("🗑️ پاک شد.")
    asyncio.create_task(delete_after_delay(msg))
    
    
'''   
@bot.on_message(successful_payment)
async def show_payment(client, message):
    user = await client.get_chat(message.successful_payment.invoice_payload)
    amount = message.successful_payment.total_amount
    update_almas_safe(user.id, amount)
    await bot.send_message(1208847974,f"{user.full_name} paid {amount}")
    print(f"{user.full_name} paid {amount}")

@bot.on_message()
async def send_invoice(client, message):
    await client.send_invoice(
        chat_id=message.chat.id,
        title="خرید ۱۰ الماس",
        description="خرید ۱۰ الماس و حمایت از ربات",
        payload=str(message.author.id),
        provider_token=PROVIDER_TOKEN,
        prices=[LabeledPrice(label="خرید الماس", amount=100000)]
    )
'''


@bot.on_message()
async def main_handler(*, message):
    if not message.text: return
    if re.match(r'هدیه\s+(\d+)', message.text.strip(), re.IGNORECASE) and message.reply_to_message:
        amount_match = re.match(r'هدیه\s+(\d+)', message.text.strip(), re.IGNORECASE)
        if amount_match:
            amount = int(amount_match.group(1))
            sender_id = message.author.id
            target_id = message.reply_to_message.author.id
            if sender_id == target_id:
                await message.reply("❌ نمی‌تونی به خودت هدیه بدی!")
                asyncio.create_task(delete_after_delay(message))
                return
            sender = get_user(sender_id)
            if sender['almas'] >= amount:
                update_almas_safe(sender_id, -amount)
                update_almas_safe(target_id, amount)
                await message.reply(f"✅ **{amount}** الماس به {get_display_name(target_id)} هدیه داده شد! 💎")
            else:
                await message.reply("❌ الماس کافی نداری!")
            asyncio.create_task(delete_after_delay(message))
            return
        
    uid = message.author.id
    text = message.text.strip()
    ensure_user(uid, message.author)
    
    if text == "جنگ الکترونیک" or text == "📡 جنگ الکترونیک":
        user = get_user(uid)
        if is_electron_war_active(uid):
            await message.reply("⚠️ شما قبلاً جنگ الکترونیک را فعال کرده‌اید!")
            asyncio.create_task(delete_after_delay(message))
            return
        if user['ajr'] >= 10000:
            update_ajr_safe(uid, -10000)
            end_timestamp = datetime.now().timestamp() + ELECTRON_WAR_DURATION
            update_electron_war_status(uid, 1, end_timestamp)
            sync_leaderboard(uid)
            hours = 24
            msg = await message.reply(
                f"📡 **جنگ الکترونیک فعال شد!**\n"
                f"⏰ **{hours} ساعت** اجر شما مخفی می‌شود!\n"
                f"🛡️ دیگران نمی‌توانند اجر شما را ببینند.\n"
                f"⚠️ اما همچنان آسیب‌پذیر هستید و موشک می‌خورید!"
            )
            asyncio.create_task(delete_after_delay(msg))
        else:
            await message.reply("❌ اجر کافی نیست! (۱۰,۰۰۰ اجر لازم است)")
        asyncio.create_task(delete_after_delay(message))
        return

    gamble_match = re.match(r'^قمار\s+(\d+)$', text, re.IGNORECASE)
    if gamble_match:
        amount = int(gamble_match.group(1))
        if amount < GAMBLE_MIN_AMOUNT:
            await message.reply(f"❌ حداقل مبلغ شرط‌بندی **{GAMBLE_MIN_AMOUNT}** اجر است.")
            asyncio.create_task(delete_after_delay(message))
            return
        user = get_user(uid)
        if user['ajr'] < amount:
            await message.reply(f"❌ اجر کافی نداری! نیاز داری: `{amount:,}` | داری: `{user['ajr']:,}`")
            asyncio.create_task(delete_after_delay(message))
            return
        if len(GAMBLE_QUEUE) > 0:
            player1 = GAMBLE_QUEUE.pop(0)
            if player1['user_id'] == uid:
                await message.reply("❌ شما قبلاً در صف قمار هستید! منتظر حریف بمانید یا `لغو قمار` بزنید.")
                asyncio.create_task(delete_after_delay(message))
                return
            player1_id = player1['user_id']
            player1_amount = player1['amount']
            update_ajr_safe(player1_id, -player1_amount)
            update_ajr_safe(uid, -amount)
            total_pot = player1_amount + amount
            chance_p1 = player1_amount / total_pot
            chance_p2 = amount / total_pot
            winner_ajr = random.random()
            if winner_ajr < chance_p1:
                winner_id = player1_id
                loser_id = uid
                winner_name = get_display_name(player1_id)
                loser_name = get_display_name(uid)
            else:
                winner_id = uid
                loser_id = player1_id
                winner_name = get_display_name(uid)
                loser_name = get_display_name(player1_id)
            update_ajr_safe(winner_id, total_pot)
            result_msg = (
                f"🎲 **نتیجه قمار**\n"
                f"👤 بازیکن ۱: {winner_name if winner_id == player1_id else loser_name} (شرط: {player1_amount:,})\n"
                f"👤 بازیکن ۲: {loser_name if winner_id == uid else winner_name} (شرط: {amount:,})\n"
                f"🏆 **برنده: {winner_name}**\n"
                f"💰 **جایزه: {total_pot:,} اجر**"
            )
            await asyncio.sleep(5)
            await message.reply(result_msg)
            try:
                await bot.send_message(loser_id, f"😢 **تو در قمار باختی!**\nجایزه به {winner_name} رسید.")
            except:
                pass
            asyncio.create_task(delete_after_delay(message))
        else:

            if any(p['user_id'] == uid for p in GAMBLE_QUEUE):
                await message.reply("❌ شما قبلاً در صف قمار هستید!")
                asyncio.create_task(delete_after_delay(message))
            else:
                GAMBLE_QUEUE.append({
                    'user_id': uid,
                    'amount': amount,
                    'chat_id': message.chat.id
                })
                await message.reply(
                    f"⏳ **در صف انتظار قمار هستی!**\n"
                    f"💰 مبلغ شرط: **{amount:,}** اجر\n"
                    f"📝 منتظر حریف بمان یا `لغو قمار` بزن."
                )
                asyncio.create_task(delete_after_delay(message))
        return

    if text == "لغو قمار":
        if uid in [p['user_id'] for p in GAMBLE_QUEUE]:
            GAMBLE_QUEUE[:] = [p for p in GAMBLE_QUEUE if p['user_id'] != uid]
            await message.reply("✅ درخواست قمار لغو شد.")
        else:
            await message.reply("❌ شما در صف قمار نیستی!")
        asyncio.create_task(delete_after_delay(message))
        return

    if text == "آتش بس" or text == "✋ آتش بس":
        activated, status = add_ceasefire_vote(uid)
        msg = await message.reply(f"✌️ **{status}**")
        if "فعال شد" in status:
            try:
                await bot.send_message(message.chat.id,
                    f"🌍 **آتش‌بس جهانی فعال شد!** 🌍\n"
                    f"⏰ **6 ساعت** صلح!\n"
                    f"🕐 زمان پایان: **{datetime.fromtimestamp(CEASEFIRE_END_TIME).strftime('%H:%M')}**"
                )
            except: pass
        asyncio.create_task(delete_after_delay(msg))
        asyncio.create_task(delete_after_delay(message))
        return
    if text == "بازگشت به منو" or text == "🔙 بازگشت به منو":
        text1 = royal_text("درود بر شما",
            f"به **ربات شاهنشاهی بشار الاسد** خوش آمدید.\n\n"
            f"🔘 **منوی اصلی:**\n"
            f"➖➖➖➖➖➖➖➖➖\n"
            f"🔹 `/پروفایل` : مشاهده وضعیت شما\n"
            f"🔹 `/لیدربورد` : برترین‌های ایران\n"
            f"🔹 `/موشک‌ها` : لیست و خرید موشک\n"
            f"🔹 `/پدافند` : خرید سیستم‌های دفاعی\n"
            f"🔹 `/موجودی` : زرادخانه شخصی\n"
            f"🔹 `/الماس` : وضعیت الماس و پدافند\n"
            f"🔹 `/ماینر` : خرید و مدیریت ماینر بیت‌کوین\n"
            f"➖➖➖➖➖➖➖➖➖\n"
            f"💎 `تبدیل 1` : تبدیل الماس به اجر\n"
            f"✌️ `آتش بس` : رای برای صلح\n"
            f"💸 `هدیه` : انتقال الماس به دیگران\n"
            f"🎯 `شلیک ... [آیدی]` : شلیک از دور\n"
            f"📡 `جنگ الکترونیک` : مخفی کردن اجر\n"
            f"🎲 `قمار [مبلغ]` : شرط‌بندی با دیگران\n"
            f"🔥 `پخت کتلت` : کسب درآمد رندوم\n"
            f"🕷️ `هک کردن` : (ریپلای) دیدن دارایی\n"
            f"➖➖➖➖➖➖➖➖➖\n"
            f"💡 _برای خرید موشک یا پدافند، از منوی متنی استفاده کنید یا در PV دکمه‌ها را بزنید._")
        msg = await message.reply(text1,ReplyKeyboard(
                ["📇 پروفایل","💰 زرادخانه"],
                ["🏆 لیدربورد"],
                ["🚀 موشک ها","🛡️ پدافند"],
                ["💎 الماس"],
                ["📡 جنگ الکترونیک","⛏️ ماینر"],
                ["🕊️ وضعیت آتش بس","✋ آتش بس"],
                ["🔙 بازگشت به منو"]
            )) 
    if text == "وضعیت آتش بس" or text == "🕊️ وضعیت آتش بس":
        if is_ceasefire_active():
            remaining = int(CEASEFIRE_END_TIME - datetime.now().timestamp())
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            msg = await message.reply(
                f"🕐 **آتش‌بس فعال** 🕐\n"
                f"⏰ **{hours:02d}:{minutes:02d}** باقی‌مانده\n"
                f"📊 `{len(CEASEFIRE_VOTES)}/{CEASEFIRE_VOTE_LIMIT}` رای"
            )
        else:
            msg = await message.reply(
                f"✅ **آتش‌بس غیرفعال**\n"
                f"📊 `{len(CEASEFIRE_VOTES)}/{CEASEFIRE_VOTE_LIMIT}` رای جمع شده"
            )
        asyncio.create_task(delete_after_delay(msg, 45))
        asyncio.create_task(delete_after_delay(message))
        return

    if is_ceasefire_active() and re.search(r'(خرید|شلیک)\s+\w+', text, re.IGNORECASE):
        remaining = int(CEASEFIRE_END_TIME - datetime.now().timestamp())
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        msg = await message.reply(
            f"🕐 **آتش‌بس فعال** 🕐\n"
            f"⏰ **{hours:02d}:{minutes:02d}** باقی‌مانده\n"
            f"⚠️ تا پایان آتش‌بس نمی‌تونید موشک بزنید!"
        )
        asyncio.create_task(delete_after_delay(msg))
        asyncio.create_task(delete_after_delay(message))
        return
    
    
    almasi = re.search(r'(almas)\s+(\d+)\s+(\d+)', text, re.IGNORECASE)
    if almasi:
        action, idkarbar, almas1 = almasi.groups()
        try:
            update_almas_safe(idkarbar, almas1)
            await message.reply("pass")
        except:
            await message.reply("error")
        return
            
        
        

    missile_distant_match = re.search(r'(شلیک)\s+(\w+)\s+(\d+)', text, re.IGNORECASE)
    if missile_distant_match:
        action, missile, target_id_str = missile_distant_match.groups()
        target_uid = int(target_id_str)
        if missile in MISSILE_PRICES:
            user = get_user(uid)
            inventory = get_user_inventory(uid)
            
            
            if not check_missile_cooldown(uid):
                await message.reply("❌ شما به حداکثر 5 شلیک در ساعت رسیده‌اید! لطفاً صبر کنید.")
                asyncio.create_task(delete_after_delay(message))
                return

            if target_uid == uid:
                await message.reply("❌ نمی‌تونی به خودت شلیک کنی!")
                asyncio.create_task(delete_after_delay(message))
                return
            if inventory.get(missile, 0) > 0 and user['ajr'] >= 10:
                inventory[missile] -= 1
                safe_save_json(INVENTORY_FILE, missile_inventory)
                update_ajr_safe(uid, -10)
                record_missile_launch(uid)
                
                attacker_name = message.author.first_name or "ناشناس"
                msg1 = await message.reply("🚀 موشک پرتاب شد...")
                await asyncio.sleep(30)
                target_defense = get_user_defense(target_uid)
                best_defense_name = None
                total_defense_power = 0
                for d_name in sorted(DEFENSE_CHANCE.keys(), key=lambda k: DEFENSE_CHANCE[k], reverse=True):
                    d_data = target_defense.get(d_name, {"count": 0, "uses_left": 0})
                    if d_data["count"] > 0 and d_data["uses_left"] > 0:
                        best_defense_name = d_name
                        total_defense_power = DEFENSE_CHANCE[d_name]
                        break
                defense_success = False
                if total_defense_power > 0:
                    defense_success = random.randint(1, 100) <= total_defense_power
                if defense_success and best_defense_name:
                    target_defense[best_defense_name]["uses_left"] -= 1
                    if target_defense[best_defense_name]["uses_left"] <= 0:
                        target_defense[best_defense_name]["count"] = 0
                        print(f"پدافند {best_defense_name} از موجودی {target_uid} حذف شد.")
                    safe_save_json(DEFENSE_INVENTORY_FILE, defense_inventory)
                    try:
                        await bot.send_message(target_uid,
                            f"🛡️ **پدافند شما فعال شد!**\n"
                            f"🚀 موشک **{missile}** از {attacker_name} رهگیری شد!\n"
                            f"🛡️ سیستم: **{best_defense_name}**\n"
                            f"📊 قدرت دفاع: {total_defense_power}%"
                        )
                    except: pass
                    await message.reply("❌ موشک توسط پدافند رهگیری شد!")
                else:
                    
                    damage = MISSILE_DAMAGE[missile]
                    target_user_data = get_user(target_uid)
                    if target_user_data:
                        update_ajr_safe(target_uid, -damage)
                        loot = min(int(damage * (2/3)), target_user_data["ajr"])
                        update_ajr_safe(uid, loot)
                        try:
                            await bot.send_message(target_uid,
                                f"💥 **حمله موشکی!**\n"
                                f"🚀 **{missile}** از {attacker_name} اصابت کرد!\n"
                                f"💀 **{damage:,}**⚜️ خسارت!\n"
                                f"📊 باقی‌مانده: `{target_user_data['ajr']:,}`⚜️"
                            )
                        except: pass
                        await message.reply(f"✅ **{loot:,}**⚜️ غنیمت از `{get_display_name(target_uid)}`!")
                        await message.reply(f"💥 **{missile}** اصابت!\n💀 **{damage:,}** خسارت!")
                asyncio.create_task(delete_after_delay(msg1))
                asyncio.create_task(delete_after_delay(message))
            else:
                reason = "موشک نداری" if inventory.get(missile, 0) == 0 else "نمیشه به خودت! یا اجر کم"
                await message.reply(f"❌ {reason}")
                asyncio.create_task(delete_after_delay(message))
            return


    missile_match = re.search(r'(خرید|شلیک)\s+(\w+)', text, re.IGNORECASE)
    if missile_match:
        action, missile = missile_match.groups()
        if missile in MISSILE_PRICES:
            user = get_user(uid)
            inventory = get_user_inventory(uid)
            
            if action == "شلیک" and not check_missile_cooldown(uid):
                await message.reply("❌ شما به حداکثر 5 شلیک در ساعت رسیده‌اید! لطفاً صبر کنید.")
                asyncio.create_task(delete_after_delay(message))
                return

            if action == "خرید":
                price = MISSILE_PRICES[missile]
                if user['ajr'] >= price:
                    if inventory[missile] >= 1:
                        w = await message.reply("❌ زرادخانه پر است! (حداکثر 1)")
                        asyncio.create_task(delete_after_delay(w))
                    else:
                        update_ajr_safe(uid, -price)
                        inventory[missile] += 1
                        safe_save_json(INVENTORY_FILE, missile_inventory)
                        msg = await message.reply(
                            f"✅ **{missile}** خریداری شد! 💰-{price}⚜️ | موجودی: `{inventory[missile]}`"
                        )
                        asyncio.create_task(delete_after_delay(msg))
                    asyncio.create_task(delete_after_delay(message))
                else:
                    msg = await message.reply(f"❌ اجر کافی نیست! `{price:,}`⚜️ نیازه")
                    asyncio.create_task(delete_after_delay(msg))
                    asyncio.create_task(delete_after_delay(message))
                return
            if action == "شلیک" and message.reply_to_message:
                target_uid = message.reply_to_message.author.id
                if target_uid != uid and inventory[missile] > 0 and user['ajr'] >= 10:
                    inventory[missile] -= 1
                    safe_save_json(INVENTORY_FILE, missile_inventory)
                    update_ajr_safe(uid, -10)
                    record_missile_launch(uid)
                    attacker_name = message.author.first_name or "ناشناس"
                    msg1 = await message.reply("🚀 موشک پرتاب شد...")
                    await asyncio.sleep(30)
                    target_defense = get_user_defense(target_uid)
                    best_defense_name = None
                    total_defense_power = 0
                    for d_name in sorted(DEFENSE_CHANCE.keys(), key=lambda k: DEFENSE_CHANCE[k], reverse=True):
                        d_data = target_defense.get(d_name, {"count": 0, "uses_left": 0})
                        if d_data["count"] > 0 and d_data["uses_left"] > 0:
                            best_defense_name = d_name
                            total_defense_power = DEFENSE_CHANCE[d_name]
                            break
                    defense_success = False
                    if total_defense_power > 0:
                        defense_success = random.randint(1, 100) <= total_defense_power
                    if defense_success and best_defense_name:
                        target_defense[best_defense_name]["uses_left"] -= 1
                        if target_defense[best_defense_name]["uses_left"] <= 0:
                            target_defense[best_defense_name]["count"] = 0
                        safe_save_json(DEFENSE_INVENTORY_FILE, defense_inventory)
                        try:
                            await bot.send_message(target_uid,
                                f"🛡️ **پدافند شما فعال شد!**\n"
                                f"🚀 موشک **{missile}** از {attacker_name} رهگیری شد!\n"
                                f"🛡️ سیستم: **{best_defense_name}**\n"
                                f"📊 قدرت دفاع: {total_defense_power}%"
                            )
                        except: pass
                        await message.reply("❌ موشک توسط پدافند رهگیری شد!")
                    else:
                        damage = MISSILE_DAMAGE[missile]
                        target_user_data = get_user(target_uid)
                        if target_user_data:
                            update_ajr_safe(target_uid, -damage)
                            loot = min(int(damage * (2/3)), target_user_data["ajr"])
                            update_ajr_safe(uid, loot)
                            try:
                                await bot.send_message(target_uid,
                                    f"💥 **حمله موشکی!**\n"
                                    f"🚀 **{missile}** از {attacker_name} اصابت کرد!\n"
                                    f"💀 **{damage:,}**⚜️ خسارت!\n"
                                    f"📊 باقی‌مانده: `{target_user_data['ajr']:,}`⚜️"
                                )
                            except: pass
                            await message.reply(f"✅ **{loot:,}**⚜️ غنیمت از `{get_display_name(target_uid)}`!")
                            await message.reply(f"💥 **{missile}** اصابت!\n💀 **{damage:,}** خسارت!")
                    asyncio.create_task(delete_after_delay(msg1))
                    asyncio.create_task(delete_after_delay(message))
                else:
                    reason = "موشک نداری" if inventory[missile] == 0 else "نمیشه به خودت! یا اجر کم"
                    msg = await message.reply(f"❌ {reason}")
                    asyncio.create_task(delete_after_delay(msg))
                    asyncio.create_task(delete_after_delay(message))
                return

    if uid in DADDY_USERS and message.reply_to_message:
        amount_match = re.match(r'([\+\-])(\d+)(الماس|اجر)', text, re.IGNORECASE)
        if amount_match:
            sign, num, type_ = amount_match.groups()
            amount = int(sign + num)
            target_uid = message.reply_to_message.author.id
            if type_.lower() == 'الماس':
                update_almas_safe(target_uid, amount)
                stats = get_user(target_uid)
                msg = await message.reply(f"💎 **{amount} الماس** | `{stats['almas']}`💎")
            else:
                update_ajr_safe(target_uid, amount)
                stats = get_user(target_uid)
                msg = await message.reply(f"👑 **{amount}** | `{stats['ajr']:,}`⚜️")
            asyncio.create_task(delete_after_delay(msg))
            asyncio.create_task(delete_after_delay(message))
            return

    if text == "پروفایل" or text == "📇 پروفایل":
        stats = get_user(uid)
        rank = get_rank(stats['ajr'])
        body = (f"👤 **{message.author.first_name}**\n"
                f"🏷️ {display_name(message.author)}\n"
                f"🔥 `{stats['ajr']:,}`⚜️\n"
                f"💎 `{stats['almas']}` الماس\n"
                f"⚜️ {rank}")
        if is_electron_war_active(uid):
            body += "\n\n📡 **جنگ الکترونیک فعال است!** (اجر شما مخفی است)"
        msg = await message.reply(royal_text("پروفایل", body))
        asyncio.create_task(delete_after_delay(msg))
        asyncio.create_task(delete_after_delay(message))
        return

    if text == "الماس" or text == "💎 الماس":
        user = get_user(uid)
        defense = get_user_defense(uid)

        txt = f"💎 **الماس شما**: `{user['almas']}`\n \n   برای خرید الماس از دکمه (حمایت از ما) استفاده کنید و به جای اسم ای دی عددی خود راقرار دهید! آي دی عددی شما{uid}\n\n🛡️ پدافند شما**:\n"
        for d, data in defense.items():
            if data["count"] > 0:
                txt += f"**{d}**: `{data['count']}` (باقی: {data['uses_left']}/{MAX_DEFENSE_USES} | ش.{DEFENSE_CHANCE[d]}%)\n"
        if not any(data["count"] > 0 for data in defense.values()):
            txt += "❌ هیچ پدافندی ندارید\n"
        txt += f"\n📝 `تبدیل 1` (1الماس=10000اجر)"
        msg = await message.reply(txt,ReplyKeyboard(
                ["تبدیل 1"],
                ["تبدیل 5"],
                ["تبدیل 10"],
                ["🔙 بازگشت به منو"]
            ))
        asyncio.create_task(delete_after_delay(msg, 60))
        asyncio.create_task(delete_after_delay(message))
        return

    if text == "موجودی" or text == "زرادخانه" or text == "💰 زرادخانه":
        inventory = get_user_inventory(uid)
        user = get_user(uid)
        txt = "📦 **موجودی موشک‌ها** 📦\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for m in MISSILE_PRICES:
            txt += f"**{m}**: `{inventory.get(m, 0)}`\n"
        txt += f"\n💰 اجرات: `{user['ajr']:,}`⚜️"
        msg = await message.reply(txt)
        asyncio.create_task(delete_after_delay(msg, 90))
        asyncio.create_task(delete_after_delay(message))
        return

    if re.match(r'تبدیل\s+(\d+)', text, re.IGNORECASE):
        amount = int(re.match(r'تبدیل\s+(\d+)', text, re.IGNORECASE).group(1))
        success, ajr_gain = convert_almas_to_ajr(uid, amount)
        if success:
            msg = await message.reply(f"✅ **{amount} الماس** → {ajr_gain:,}⚜️ تبدیل شد!")
        else:
            msg = await message.reply(f"❌ الماس کافی نیست! `{amount}` نیازه")
        asyncio.create_task(delete_after_delay(msg))
        asyncio.create_task(delete_after_delay(message))
        return

    if text in ["لیدربورد", "لیدربرد"] or text == "🏆 لیدربورد":
        top = get_leaderboard(10)
        lb_text = "🏆 **لیدربورد شاهنشاهی** 🏆\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (user_id_str, ajr) in enumerate(top, 1):
            name = get_display_name(int(user_id_str))
            medal = "🥇🥈🥉"[i-1] if i <= 3 else f"{i}."
            lb_text += f"{medal} **{name}**: `{ajr:,}`⚜️\n"
        if not top: lb_text += "❌ هنوز کسی نیست!"
        msg = await message.reply(lb_text)
        asyncio.create_task(delete_after_delay(msg))
        asyncio.create_task(delete_after_delay(message))
        return

    if text in ["موشک‌ها", "موشک ها"] or text == "🚀 موشک ها":
        txt = "🚀 **موشک‌های ایرانی** 🚀\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for m, p in MISSILE_PRICES.items():
            d = MISSILE_DAMAGE[m]
            txt += f"**{m}**: `{p:,}`⚜️ → `{d:,}`⚜️ خسارت\n"
        txt += f"\n📝 `خرید فاتح` | `شلیک رستاخیز` (ریپلای)\n💡 **{len(MISSILE_PRICES)} موشک**\n🎯 `شلیک رستاخیز 12345678` (شلیک از دور)"
        msg = await message.reply(txt,ReplyKeyboard(
                ["خرید فاتح","خرید قیام"],
                ["خرید آتش","خرید رستاخیز"],
                ["🔙 بازگشت به منو"]
            ))
        asyncio.create_task(delete_after_delay(msg, 40))
        asyncio.create_task(delete_after_delay(message))
        return

    if text == "پدافند" or text == "🛡️ پدافند":
        txt = "🛡️ **سیستم‌های پدافندی** 🛡️\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for d, p in DEFENSE_PRICES.items():
            chance = DEFENSE_CHANCE[d]
            txt += f"**{d}**: `{p:,}`⚜️ (شانس: {chance}% | 3بار استفاده)\n"
        txt += f"\n📝 `خرید پدافند1` | **حداکثر 1 عدد از هر نوع**"
        msg = await message.reply(txt)
        asyncio.create_task(delete_after_delay(msg, 50))
        asyncio.create_task(delete_after_delay(message))
        return


    defense_buy_match = re.search(r'خرید\s+(پدافند|دفاع)\s+(\w+)', text, re.IGNORECASE)
    if defense_buy_match:
        action_type, defense_name = defense_buy_match.groups()
        if defense_name in DEFENSE_PRICES:
            user = get_user(uid)
            defense_data = get_user_defense(uid)
            price = DEFENSE_PRICES[defense_name]
            if user['ajr'] >= price:
                if defense_data[defense_name]["count"] >= MAX_DEFENSE_COUNT:
                    msg = await message.reply(f"❌ **{defense_name}** قبلاً خریداری شده!\n(حداکثر {MAX_DEFENSE_COUNT})")
                else:
                    update_ajr_safe(uid, -price)
                    defense_data[defense_name]["count"] += 1
                    defense_data[defense_name]["uses_left"] = MAX_DEFENSE_USES
                    safe_save_json(DEFENSE_INVENTORY_FILE, defense_inventory)
                    msg = await message.reply(
                        f"🛡️ **پدافند {defense_name}** خریداری شد! ✅\n"
                        f"💰 **-{price:,}**⚜️\n"
                        f"🎯 شانس رهگیری: **{DEFENSE_CHANCE[defense_name]}%**\n"
                        f"🔄 **{MAX_DEFENSE_USES}** بار استفاده\n"
                        f"📊 **تعداد: 1**"
                    )
            else:
                msg = await message.reply(f"❌ **اجر کافی نیست!**\n`{price:,}⚜️` نیازه")
            asyncio.create_task(delete_after_delay(msg))
            asyncio.create_task(delete_after_delay(message))
            return


    if text == "ماینر" or text == "⛏️ ماینر":
        txt = "⛏️ **سیستم ماین بیت‌کوین** ⛏️\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        txt += "📊 **لیست ماینرهای موجود:**\n"
        for m_name, info in MINER_TYPES.items():
            txt += f"**{m_name}**: قیمت `{info['price']:,}`⚜️ | تولید `{info['output_btc_per_hour']}` BTC/ساعت\n"
        
        my_miners = get_user_miners(uid)
        txt += "\n📦 **ماینرهای شما:**\n"
        has_miner = False
        for m_name, count in my_miners.items():
            if count > 0:
                txt += f"**{m_name}**: {count} عدد\n"
                has_miner = True
        if not has_miner:
            txt += "❌ شما ماینری ندارید.\n"
        
        current_btc = calculate_btc_to_sell(uid)
        txt += f"\n💰 **بیت‌کوین استخراج شده:** `{current_btc:.8f}` BTC\n"
        txt += f"💎 **الماس:** `{get_user(uid)['almas']}`\n"
        txt += f"\n📝 **دستورات:**\n"
        txt += f"`خرید ماینر [نام]` (مثال: خرید ماینر ASIC)\n"
        txt += f"`فروش بیت‌کوین [تعداد]` (مثال: فروش بیت‌کوین 0.0001)\n"
        txt += f"`وضعیت ماینر` (برای به‌روزرسانی تولید)"
        
        msg = await message.reply(txt)
        asyncio.create_task(delete_after_delay(msg, 60))
        asyncio.create_task(delete_after_delay(message))
        return

    buy_miner_match = re.search(r'خرید\s+ماینر\s+(\w+)', text, re.IGNORECASE)
    if buy_miner_match:
        miner_name = buy_miner_match.group(1)
        if miner_name in MINER_TYPES:
            user = get_user(uid)
            price = MINER_TYPES[miner_name]['price']
            
            if user['ajr'] >= price:       
                my_miners = get_user_miners(uid)
                if my_miners[miner_name] >= 3:    
                    w = await message.reply(f"⚠️ موجودی ماینر پر است!")
                    asyncio.create_task(delete_after_delay(w))
                else:                              
                    update_ajr_safe(uid, -price)
                    my_miners[miner_name] += 1
                    safe_save_json(MINER_INVENTORY_FILE, miner_inventory)
                    msg = await message.reply(
                        f"⛏️ **ماینر {miner_name}** خریداری شد! ✅\n"
                        f"💰 **-{price:,}**⚜️\n"
                        f"⚡ قدرت تولید: **{MINER_TYPES[miner_name]['output_btc_per_hour']}** BTC/ساعت\n"
                        f"📦 **تعداد کل {miner_name}:** {my_miners[miner_name]}"
                    )
                    asyncio.create_task(delete_after_delay(msg))
                    asyncio.create_task(delete_after_delay(message))
            else:                                 
                msg = await message.reply(f"❌ **اجر کافی نیست!**\n`{price:,}⚜️` نیازه")
                asyncio.create_task(delete_after_delay(msg))
                asyncio.create_task(delete_after_delay(message))
            return
        
        return
    
    sell_btc_match = re.search(r'فروش\s+بیت کوین\s+([\d.]+)', text, re.IGNORECASE)
    if sell_btc_match:
        amount_to_sell = float(sell_btc_match.group(1))
        current_btc = calculate_btc_to_sell(uid)
        
        if current_btc >= amount_to_sell:
            BTC_PRICE_IN_AJR = 1000000
            ajr_gain = int(amount_to_sell * BTC_PRICE_IN_AJR)
            new_btc_amount = current_btc - amount_to_sell
            user_btc[str(uid)] = new_btc_amount
            
            update_ajr_safe(uid, ajr_gain)
            
            msg = await message.reply(
                f"💰 **فروش بیت‌کوین موفق!**\n"
                f"📤 فروختی: `{amount_to_sell}` BTC\n"
                f"💎 دریافتی: **{ajr_gain:,}** اجر\n"
                f"📊 باقی‌مانده BTC: `{new_btc_amount:.8f}`"
            )
            asyncio.create_task(delete_after_delay(msg))
        else:
            msg = await message.reply(f"❌ **بیت‌کوین کافی نداری!**\nدارای: `{current_btc:.8f}` BTC")
            asyncio.create_task(delete_after_delay(msg))
        asyncio.create_task(delete_after_delay(message))
        return

    if text == "پخت کتلت":
        is_in_group = False
        if hasattr(message, 'chat') and hasattr(message.chat, 'type'):
            if message.chat.type in ['group', 'supergroup']:
                is_in_group = True
        
        
        if not is_in_group:
            await message.reply("⛔ این دستور فقط در گروه‌ها فعال است!")
            asyncio.create_task(delete_after_delay(message))
            return

        if uid in cooking_users:
            msg = await message.reply("⛔ در حال پخت هستی! صبر کن 😄")
            asyncio.create_task(delete_after_delay(msg))
        else:
            cooking_users[uid] = True
            msg1 = await message.reply("🍳 پخت کتلت شروع شد...")
            await asyncio.sleep(random.randint(600, 1200))
            if uid not in cooking_users: return
            if random.choice([0, 1, 0, 0, 0]) == 1:
                msg10 = await message.reply("🔥 کتلت سوخت!!")
                cooking_users.pop(uid, None)
            else:
                update_ajr_safe(uid, 7500)
                msg2 = await message.reply("✅ **+7500*⚜️ کتلت به حزب‌اللهی‌ها فروخته شد!")
                cooking_users.pop(uid, None)
                asyncio.create_task(delete_after_delay(msg1))
                asyncio.create_task(delete_after_delay(msg2))
                if 'msg10' in locals():
                    asyncio.create_task(delete_after_delay(msg10))
        asyncio.create_task(delete_after_delay(message))
        return

    if text == "هک کردن" and message.reply_to_message:
        target_uid = message.reply_to_message.author.id
        if target_uid == uid:
            msg10 = await message.reply("❌ نمی‌تونی خودت رو هک کنی!")
            asyncio.create_task(delete_after_delay(message))
            asyncio.create_task(delete_after_delay(msg10))
            return
        user = get_user(uid)
        if user['ajr'] < HACK_COST:
            msg11 = await message.reply(f"❌ اجر کافی نیست! `{HACK_COST:,}`⚜️ نیازه")
            asyncio.create_task(delete_after_delay(message))
            asyncio.create_task(delete_after_delay(msg11))
            return
        update_ajr_safe(uid, -HACK_COST)
        msg14 = await message.reply("هک کردن استارت خورد!")
        asyncio.create_task(delete_after_delay(msg14))
        success = random.randint(1, 5) in [1,2,3]
        await asyncio.sleep(30)
        if success:
            target_user = get_user(target_uid)
            target_inventory = get_user_inventory(target_uid)
            target_defense = get_user_defense(target_uid)
            target_missiles = {k: v for k, v in target_inventory.items() if v > 0}
            target_defenses = {k: v for k, v in target_defense.items() if v['count'] > 0}
            report = f"🎯 **گزارش هک موفق**\n\n"
            report += f"👤 هدف: {get_display_name(target_uid)}\n"
            report += f"💰 اجر: {target_user['ajr']:,}⚜️\n"
            report += f"💎 الماس: {target_user['almas']}\n"
            report += f"📦 موشک‌ها: {len(target_missiles)}\n"
            report += f"🛡️ پدافندها: {len(target_defenses)}\n"
            msg1 = await message.reply("گزارش هک تو پیوی ارسال شد حتما ربات را استارت کرده باشید!")
            asyncio.create_task(delete_after_delay(message))
            asyncio.create_task(delete_after_delay(msg1))
            try:
                await bot.send_message(uid, f"📊 **جزئیات هک**\n{report}")
            except:
                pass
        else:
            msg1 = await message.reply("❌ **هک ناموفق!** تلاش شما لو رفت!")
            asyncio.create_task(delete_after_delay(message))
            asyncio.create_task(delete_after_delay(msg1))

    if text == "حذف کتلت" and uid in DADDY_USERS:
        cooking_users.clear()
        msg = await message.reply("⛔ لیست کتلت‌ها خالی شد 😄")
        asyncio.create_task(delete_after_delay(msg))
        asyncio.create_task(delete_after_delay(message))
        return

    if uid in DADDY_USERS:
        if text.startswith("حذف جنگ الکترونیک") or text.startswith("دیلیت جنگ الکترونیک") or text.startswith("حذف جنگ") or text == "zfwar":
            parts = text.split()
            if len(parts) > 2:
                try:
                    target_id = int(parts[2])
                    update_electron_war_status(target_id, 0, 0)
                    sync_leaderboard(target_id)
                    await message.reply(f"✅ جنگ الکترونیک کاربر {get_display_name(target_id)} حذف شد.")
                except ValueError:
                    await message.reply("❌ آیدی عددی وارد کنید.")
            elif len(parts) == 2:
                if message.reply_to_message:
                    target_id = message.reply_to_message.author.id
                    update_electron_war_status(target_id, 0, 0)
                    sync_leaderboard(target_id)
                    await message.reply(f"✅ جنگ الکترونیک کاربر {get_display_name(target_id)} حذف شد.")
                else:
                    await message.reply("❌ آیدی کاربر را مشخص کنید یا ریپلای بزنید.")
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("UPDATE users SET electron_war_active = 0, electron_war_end = 0")
                except sqlite3.OperationalError:
                    cursor.execute("UPDATE users SET electron_war_active = 0")
                conn.commit()
                conn.close()
                await message.reply("✅ جنگ الکترونیک برای **همه کاربران** حذف شد.")
            asyncio.create_task(delete_after_delay(message))
            return

    for word, reward in GOODLIST.items():
        if text == word:
            update_ajr_safe(uid, reward)
            stats = get_user(uid)
            emoji = "🟩⬜🟨⬜🟥" if word == "جاوید شاه" else "✅"
            msg = await message.reply(f"{emoji} **+{reward}** | `{stats['ajr']:,}`⚜️")
            asyncio.create_task(delete_after_delay(msg))
            asyncio.create_task(delete_after_delay(message))
            return

    for bad in BADLIST:
        if text == bad:
            update_ajr_safe(uid, -10000)
            msg = await message.reply("❌ریدی بدبخت حزب اللهی **-10000**⚜️")
            asyncio.create_task(delete_after_delay(msg))
            asyncio.create_task(delete_after_delay(message))
            return

print("pass")
bot.run()




