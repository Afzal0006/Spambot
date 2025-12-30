import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from pymongo import MongoClient
from datetime import datetime

# ================= CONFIG =================
BOT_TOKEN = "8083468954:AAFvcO-LVlUb3t2MfFD2HmCzRk9XuXhu_sw"
OWNER_ID = 6998916494
MONGO_URI = "mongodb+srv://Newdemodetabade:Newdemodetabade@cluster0.vp23uhz.mongodb.net/?appName=Cluster0"

START_PHOTO = "https://files.catbox.moe/bzzii0.jpg"
JOIN_URL = "https://t.me/MiniGamesUpdate"
PLAY_URL = "http://t.me/Fairytailmusicbot/CarGames"
TRENDING_URL = "https://t.me/Fairytailmusicbot/TrandingGame"

LOG_GROUP_ID = -1003067627921

# ===== LIVE SPAM CONFIG =====
LIVE_GROUP_ID = -1003067627921   # target group
LIVE_MESSAGE = "I'm live bs"
LIVE_DELAY = 5  # seconds ⚠️ risky

spam_task = None

# = DATABASE =
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]

users_col = db["users"]
stats_col = db["stats"]
admins_col = db["admins"]

# init stats
stats_col.update_one(
    {"_id": "bot"},
    {"$setOnInsert": {"starts": 0, "created_at": datetime.utcnow()}},
    upsert=True
)

# auto add OWNER as admin
admins_col.update_one(
    {"_id": OWNER_ID},
    {"$setOnInsert": {"role": "owner", "added_at": datetime.utcnow()}},
    upsert=True
)

# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    users_col.update_one(
        {"_id": user.id},
        {
            "$set": {
                "name": user.full_name,
                "username": user.username,
                "joined_at": datetime.utcnow()
            }
        },
        upsert=True
    )

    stats_col.update_one(
        {"_id": "bot"},
        {"$inc": {"starts": 1}},
        upsert=True
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥 Join", url=JOIN_URL),
            InlineKeyboardButton("🚗 Car games", url=PLAY_URL)
        ],
        [
            InlineKeyboardButton("📈 Trending Games", url=TRENDING_URL)
        ]
    ])

    await update.message.reply_photo(
        photo=START_PHOTO,
        caption=(
            "• Get ready for a world of quick games and endless fun 🕘\n\n"
            "• Play exciting mini-games, test your skills, and beat your own high scores 🏆\n\n"
            "• Every game is fast, fun, and a new challenge to conquer 🥇"
        ),
        reply_markup=keyboard
    )

    username = user.username if user.username else "unknown"

    await context.bot.send_message(
        chat_id=LOG_GROUP_ID,
        text=(
            "🚀 New User Started The Bot\n"
            f"🎗 Username : @{username}\n"
            f"👤 Name : {user.full_name}\n"
            f"🔗 Profile : <a href='tg://user?id={user.id}'>{user.full_name}</a>"
        ),
        parse_mode="HTML"
    )

# ================= /stats =================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_count = users_col.count_documents({})
    await update.message.reply_text(
        "📊 Bot Statistics\n\n"
        f"👥 Total Users: {users_count}"
    )

# ================= /broadcast =================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID and not admins_col.find_one({"_id": user_id}):
        return await update.message.reply_text("⛔ Only Owner or Admin!")

    users = list(users_col.find())
    target = update.message.reply_to_message

    if not target and not context.args:
        return await update.message.reply_text(
            "Reply to a message or use:\n/broadcast <text>"
        )

    ok, fail = 0, 0
    msg = " ".join(context.args) if context.args else None
    status = await update.message.reply_text("📢 Broadcasting...")

    for u in users:
        try:
            if target:
                await target.copy(chat_id=u["_id"])
            else:
                await context.bot.send_message(u["_id"], msg)
            ok += 1
        except:
            fail += 1

    await status.edit_text(
        f"📢 Broadcast Done\n\n✅ Sent: {ok}\n❌ Failed: {fail}"
    )

# ================= LIVE SPAM =================
async def live_spam_loop(context: ContextTypes.DEFAULT_TYPE):
    while True:
        try:
            await context.bot.send_message(
                chat_id=LIVE_GROUP_ID,
                text=LIVE_MESSAGE
            )
            await asyncio.sleep(LIVE_DELAY)
        except Exception as e:
            print("Spam error:", e)
            await asyncio.sleep(10)

async def startspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_task
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("⛔ Only owner allowed.")

    if spam_task:
        return await update.message.reply_text("⚠️ Spam already running.")

    spam_task = context.application.create_task(live_spam_loop(context))
    await update.message.reply_text("✅ Live spam started.")

async def stopspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_task
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("⛔ Only owner allowed.")

    if not spam_task:
        return await update.message.reply_text("⚠️ Spam not running.")

    spam_task.cancel()
    spam_task = None
    await update.message.reply_text("🛑 Live spam stopped.")

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("startspam", startspam))
    app.add_handler(CommandHandler("stopspam", stopspam))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
