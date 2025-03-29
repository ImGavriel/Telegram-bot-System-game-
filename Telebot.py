import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import json
import time

TOKEN = "BOT API" 
bot = telebot.TeleBot(TOKEN)

# Database (Simulation)
users = {}

# Load & Save Data
def load_data():
    global users
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = {}

def save_data():
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎰 Daily Spin", callback_data="spin"),
    )
    markup.add(
        InlineKeyboardButton("📜 My Profile", callback_data="profile"),
        InlineKeyboardButton("Inventory", callback_data="inventory")
    )
   
    markup.add(
        InlineKeyboardButton("🏆 TOP members", callback_data="leaderboard"),
        
    )
    markup.add(
        InlineKeyboardButton("💰 Coins Store", callback_data="shop"),
        InlineKeyboardButton("💵 Withdraw Real Money ", callback_data="vip_menu"),
        
    )
    markup.add(
        InlineKeyboardButton("📜 Help ", callback_data="help"),
        InlineKeyboardButton("🎟️ VIP", callback_data="vip_menu")
        
        )
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    first_name = message.from_user.first_name  # קבלת שם המשתמש

    if user_id not in users:
        users[user_id] = {
            "points": 0,
            "real_money": 0,
            "vip": False,
            "level": 1,
            "referrals": 0,
            "inventory": []
        }
        save_data()
    
    bot.send_message(message.chat.id, 
        f"🎉Welcome Back, {first_name}🎉!\n",
     
        reply_markup=main_menu()
    )

###################################################################LEVEL SYSTEM
def add_xp(user_id, amount):
    # אם המשתמש לא קיים, נוסיף אותו עם ערכי ברירת מחדל
    if user_id not in users:
        users[user_id] = {
            "xp": 0,
            "level": 1,
            "xp_needed": 25,
            "points": 0,
            "real_money": 0,
            "total_xp": 0  # ערך חדש לסך כל ה-XP
        }
    
    # הבטחת שהמפתחות קיימים
    if "xp" not in users[user_id]:
        users[user_id]["xp"] = 0
    if "level" not in users[user_id]:
        users[user_id]["level"] = 1
    if "xp_needed" not in users[user_id]:
        users[user_id]["xp_needed"] = 25
    if "points" not in users[user_id]:
        users[user_id]["points"] = 0
    if "total_xp" not in users[user_id]:  # נוודא שהמפתח קיים
        users[user_id]["total_xp"] = 0

    # הוספת XP רגיל + שמירת הטוטאל
    users[user_id]["xp"] += amount
    users[user_id]["total_xp"] += amount  # שמירת כל ה-XP שהצטבר

    # בדיקת עליית רמה
    while users[user_id]["xp"] >= users[user_id]["xp_needed"]:
        users[user_id]["xp"] -= users[user_id]["xp_needed"]  # שמירת XP נוסף לרמה הבאה
        users[user_id]["level"] += 1
        users[user_id]["xp_needed"] = users[user_id]["level"] * 25  # נוסחה לרמה הבאה
        
        # בונוס בעליית רמה
        level_bonus = users[user_id]["level"] * 1  # בונוס מטבעות לפי הרמה
        users[user_id]["points"] += level_bonus

        bot.send_message(user_id, f"🎉 Congratulations! Level up to {users[user_id]['level']}!\n💰 You get {level_bonus} coins bonus :) Keep it up!")

    save_data()


###################################################################SPINS
@bot.callback_query_handler(func=lambda call: call.data == "spin")
def spin(call):
    user_id = str(call.message.chat.id)
    now = time.time()
    # בדיקה אם המשתמש כבר עשה ספין היום
   # בדיקה אם המשתמש כבר עשה ספין היום
    last_spin = users[user_id].get("last_spin", 0)
    time_since_last_spin = now - last_spin

    if time_since_last_spin < 3600:  # פחות מ-4 שעות
            time_left = int(3600 - time_since_last_spin)  # זמן שנותר בשניות
            hours = time_left // 3600
            minutes = (time_left % 3600) // 60
            bot.answer_callback_query(call.id, f"⏳ You already claimed your spin ! You can try again in {hours} hours and {minutes} minutes.", show_alert=True)
            return



    users[user_id]["last_spin"] = now
    save_data()

    # אפקט ספין
    animation_frames = ["🎰 |", "🎰 /", "🎰 -", "🎰 \\", "🎰 🎉"]
    for frame in animation_frames:
        bot.edit_message_text(frame, call.message.chat.id, call.message.message_id)
        time.sleep(0.5)

    # תוצאות רנדומליות
    spin_results = [
        {"text": "🎉 You won 200 coins!", "points": 200, "xp": 120},
   
    ]

    result = random.choice(spin_results)

    # הוספת XP ונקודות
    users[user_id]["points"] += result["points"]
    add_xp(user_id, result["xp"])
    save_data()

    # הודעה סופית
    final_message = (
        f"{result['text']} 🎰\n"
        f"✨You got XP: {result['xp']}\n"
        f"💰You got Coins: {result['points']}"
    )
    bot.edit_message_text(final_message, call.message.chat.id, call.message.message_id)
    


   ###################################################################PROFILE 
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user_id = str(call.message.chat.id)
    
    if user_id not in users:
        bot.answer_callback_query(call.id, "❌ NO PROFILE")
        return

    user_data = users[user_id]
    first_name = call.from_user.first_name  

    profile_text = (
    f"👤 *{first_name} Profile*\n"
    f"🆔 ID: {user_id}\n"
    f"✨ Level: {user_data['level']}\n"
    f"🎖️ XP: {user_data.get('xp', 0)}/{user_data.get('xp_needed', 100)} 🔹\n"
    f"💰 Coins: {user_data['points']}\n"
    f"👥 My invites: {user_data.get('referrals', 0)}\n"
    f"🎒 Inventory: {len(user_data['inventory'])}\n"
    f"🏆 VIP Status: {'✅ Yes' if user_data['vip'] else '❌ Not a VIP member'}\n"
    f"💵 Real Money: {user_data.get('real_money', 0)}$"
)
 

     # הוספת כפתור חזרה לתפריט הראשי
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="main_menu"))

    bot.edit_message_text(profile_text, call.message.chat.id, call.message.message_id, 
                          parse_mode="Markdown", reply_markup=keyboard)

###################################################################main_menu
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def back_to_main_menu(call):
    """פונקציה שמחזירה את המשתמש לתפריט הראשי"""
    bot.edit_message_text("🏠 Main Menu - Choose an option:", 
                          call.message.chat.id, call.message.message_id, 
                          reply_markup=main_menu())

###################################################################leaderboard
@bot.callback_query_handler(func=lambda call: call.data == "leaderboard")

def show_leaderboard(call):
    # מיון משתמשים לפי נקודות (Coins) ולפי רמות (Level)
    sorted_by_coins = sorted(users.items(), key=lambda x: x[1].get("points", 0), reverse=True)
    sorted_by_level = sorted(users.items(), key=lambda x: (x[1].get("level", 0), x[1].get("xp", 0)), reverse=True)

    leaderboard_text = "🏆 *Leaderboard - Top Players*\n"

    # עשרת השחקנים המובילים לפי רמה
    top_10_level = sorted_by_level[:10]
    leaderboard_text += "\n🏅 *Top 10 Players by Level:*\n"
    for i, (uid, data) in enumerate(top_10_level, start=1):
        name = data.get("name") or bot.get_chat(uid).first_name  # שולף את השם מהמשתמש
        leaderboard_text += f"{i}. {name} (ID: {uid}) - Level {data.get('level', 0)} ({data.get('xp', 0)} XP)\n"

    # עשרת השחקנים המובילים לפי כמות המטבעות (Coins)
    top_10_coins = sorted_by_coins[:10]
    leaderboard_text += "\n💰 *Top 10 Players by Coins:*\n"
    for i, (uid, data) in enumerate(top_10_coins, start=1):
        name = data.get("name") or bot.get_chat(uid).first_name  # שולף את השם אם לא קיים
        leaderboard_text += f"{i}. {name} (ID: {uid}) - {data.get('points', 0)} Coins\n"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="main_menu"))

    # עריכת ההודעה עם לוח התוצאות וכפתור החזרה
    bot.edit_message_text(leaderboard_text, call.message.chat.id, call.message.message_id, 
                          parse_mode="Markdown", reply_markup=keyboard)
###################################################################inventory

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# הגדרת רשימת הפריטים עם שני מחירים (coins ו- real_money)
items = [
    ("😈 Demon Slayer", 955, 0.0955, "demon"),        # (שם, מחיר ב-coins, מחיר ב-real_money, מזהה)
    ("⚔️ Excalibur", 500, 0.0500, "excalibur"),
    ("🔨 Mjolnir", 600, 0.0600, "mjolnir"),
    ("⚰️ Death Scythe", 550, 0.550, "death"),
    ("🏹 Phoenix Bow", 480, 0.0480, "phoenix"),
    ("🔥 Hellfire Blade", 530, 0.0530, "hellfire"),
    ("❄️ Frostmourne", 570, 0.0570, "frostmourne"),
    ("🌑 Shadow Reaper", 560, 0.0560, "shadow"),
    ("⚡ Stormbringer", 590, 0.0590, "stormbringer"),
    ("🔮 Arcane Staff", 510, 0.0510, "arcane"),
]

# יצירת מילון מחירים מתוך הרשימה
item_prices = {item[3]: {"coins": item[1], "real_money": item[2]} for item in items}

@bot.callback_query_handler(func=lambda call: call.data == "inventory")
def show_inventory(call):
    user_id = str(call.message.chat.id)
    inventory = users.get(user_id, {}).get("inventory", [])

    if not inventory:
        bot.answer_callback_query(call.id, "🎒 Your inventory is empty!", show_alert=True)
        return

    # יצירת מילון עם ספירת הפריטים במלאי
    inventory_dict = {}
    for item in inventory:
        inventory_dict[item] = inventory_dict.get(item, 0) + 1

    # יצירת תפריט עם כפתורים
    keyboard = InlineKeyboardMarkup(row_width=2)
    for item, quantity in inventory_dict.items():
        prices = item_prices.get(item, {"coins": 10, "real_money": 1})  # ברירת מחדל למקרה שלא נמצא

        button_text = f"{item.replace('_', ' ').title()} (x{quantity})"
        sell_coin_button = InlineKeyboardButton(f"Sell for {prices['coins']/1.25} 💰", callback_data=f"sell_coin_{item}")
        sell_real_button = InlineKeyboardButton(f"Sell for {prices['real_money']} $💵", callback_data=f"sell_real_{item}")

        keyboard.add(InlineKeyboardButton(button_text, callback_data=f"item_{item}"))
        keyboard.add(sell_coin_button, sell_real_button)  # שני כפתורים למכירה

    keyboard.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="main_menu"))

    bot.send_message(call.message.chat.id, "🎒 *Your Inventory:*", reply_markup=keyboard, parse_mode="Markdown")
@bot.callback_query_handler(func=lambda call: call.data.startswith("sell_coin_") or call.data.startswith("sell_real_"))
def sell_item(call):
    user_id = str(call.message.chat.id)
    item = call.data.split("_", 2)[2]
    sell_type = call.data.split("_", 2)[1]  # "coin" או "real"

    # בדיקה אם הפריט קיים במלאי
    if item in users.get(user_id, {}).get("inventory", []):
        prices = item_prices.get(item, {"coins": 10, "real_money": 1})  # קבלת המחיר הרלוונטי
        amount = prices["coins"] if sell_type == "coin" else prices["real_money"]
        currency = "coins" if sell_type == "coin" else "real_money"

        # הסרת הפריט מהמלאי
        users[user_id]["inventory"].remove(item)
        users[user_id][currency] = users.get(user_id, {}).get(currency, 0) + amount

        # **שמירת הנתונים לקובץ JSON**
        save_data()

        bot.answer_callback_query(call.id, f"✅ You sold {item.replace('_', ' ').title()} for {amount}$ !", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ You don't have this item!", show_alert=True)



###################################################################  SHOP

@bot.callback_query_handler(func=lambda call: call.data == "shop")
def shop_menu(call):
    user_id = str(call.message.chat.id)
    
    # רשימת מוצרים (שם, מחיר, מזהה ייחודי)
    items = [
        ("😈 Demon Slayer", 955, "demon"),
        ("⚔️ Excalibur", 500, "excalibur"),
        ("🔨 Mjolnir", 600, "mjolnir"),
        ("⚰️ Death Scythe", 550, "death"),
        ("🏹 Phoenix Bow", 480, "phoenix"),
        ("🔥 Hellfire Blade", 530, "hellfire"),
        ("❄️ Frostmourne", 570, "frostmourne"),
        ("🌑 Shadow Reaper", 560, "shadow"),
        ("⚡ Stormbringer", 590, "stormbringer"),
        ("🔮 Arcane Staff", 510, "arcane"),
        
    ]

    # יצירת מקלדת עם כפתורי קנייה
    keyboard = InlineKeyboardMarkup()
    for name, price, item_id in items:
        keyboard.add(InlineKeyboardButton(f"{name} - {price}💰", callback_data=f"buy_{item_id}"))
    
    # הוספת כפתור חזרה לתפריט הראשי
    keyboard.add(InlineKeyboardButton("⬅ Back to Menu", callback_data="main_menu"))

    # שליחת הודעה עם תפריט החנות
    bot.send_message(user_id, "🛒 Welcome to the shop! Choose an item to buy:", reply_markup=keyboard)

   

###################################################################  BUY

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_item(call):
    user_id = str(call.message.chat.id)
    item_id = call.data.split("_")[1]  # קבלת המוצר שנבחר

    # רשימת מחירים
    prices = {
        "demon": 955,
        "excalibur": 500,
        "mjolnir": 600,
        "death": 550,
        "phoenix": 480,
        "hellfire": 530,
        "frostmourne": 570,
        "shadow": 560,
        "stormbringer": 590,
        "arcane": 510,
    }

    # בדיקה אם יש מספיק כסף
    if users[user_id]["points"] < prices[item_id]:
        bot.answer_callback_query(call.id, "❌ Not enough coins!", show_alert=True)
        return

    # הורדת כסף והוספת הפריט
    users[user_id]["points"] -= prices[item_id]
    users[user_id]["inventory"].append(item_id)
    save_data()  # שמירת הנתונים

    bot.answer_callback_query(call.id, "✅ Purchase successful!", show_alert=True)
    bot.send_message(user_id, f"🎉 You bought {item_id}! Check your inventory.")


############################################################sell


# Run Bot
load_data()
bot.polling(none_stop=True)