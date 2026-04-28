import threading
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

# ================== 🔴 EDIT HERE ==================
TOKEN = "8692523280:AAHS7nx1ZRrMafTkV5PWOkpysHliEsz-q4E"
ADMIN_ID = 5471364167
ZAPIER_WEBHOOK = "https://hooks.zapier.com/hooks/catch/XXXX"
# ==================================================

# ================== FLASK SERVER ==================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running ✅"

# ================== SIMPLE DATABASE ==================
users = {}
withdraw_requests = []

# ================== BUTTON MENU ==================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Wallet", callback_data='wallet')],
        [InlineKeyboardButton("📤 Send", callback_data='send')],
        [InlineKeyboardButton("🔗 Connect", callback_data='connect')],
        [InlineKeyboardButton("💸 Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("🌐 Language", callback_data='lang')],
        [InlineKeyboardButton("📢 Channel", url="https://t.me/YOUR_CHANNEL")],
        [InlineKeyboardButton("⚙️ Server", callback_data='server')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ================== COMMANDS ==================
def start(update: Update, context: CallbackContext):
    uid = update.message.from_user.id
    users[uid] = {"balance": 0}

    if uid == ADMIN_ID:
        update.message.reply_text("👑 Admin Panel\n/users\n/withdrawals", reply_markup=main_menu())
    else:
        update.message.reply_text("🚀 Start Earning", reply_markup=main_menu())

def wallet(update, context):
    uid = update.message.from_user.id
    bal = users.get(uid, {}).get("balance", 0)
    update.message.reply_text(f"💰 Balance: ${bal}")

def send(update, context):
    update.message.reply_text("📤 Send task coming soon")

def withdraw(update, context):
    update.message.reply_text("Enter amount:")
    context.user_data["withdraw"] = True

def connect(update, context):
    update.message.reply_text("📱 Send phone number (+91XXXXXXXXXX)")
    context.user_data["phone"] = True

def lang(update, context):
    update.message.reply_text("🌐 Language: English")

def channel(update, context):
    update.message.reply_text("📢 Join: https://t.me/YOUR_CHANNEL")

def server(update, context):
    msg = update.message.reply_text("⚙️ Connecting...")
    import time
    time.sleep(2)
    msg.edit_text("✅ Server Ready")

# ================== MESSAGE HANDLER ==================
def handle(update, context):
    uid = update.message.from_user.id
    text = update.message.text

    # PHONE INPUT
    if context.user_data.get("phone"):
        users[uid]["phone"] = text

        # 🔥 Zapier call
        try:
            requests.post(ZAPIER_WEBHOOK, json={"phone": text, "user": uid})
        except:
            pass

        update.message.reply_text("🔐 OTP sent (demo)")
        context.user_data["phone"] = False
        context.user_data["otp"] = True
        return

    # OTP INPUT (DEMO)
    if context.user_data.get("otp"):
        update.message.reply_text("✅ Verified (demo)")
        context.user_data["otp"] = False
        return

    # WITHDRAW
    if context.user_data.get("withdraw"):
        try:
            amount = float(text)
            withdraw_requests.append({"user": uid, "amount": amount})
            update.message.reply_text("✅ Withdraw request sent")
        except:
            update.message.reply_text("❌ Invalid amount")

        context.user_data["withdraw"] = False
        return

# ================== ADMIN ==================
def users_cmd(update, context):
    if update.message.from_user.id != ADMIN_ID:
        return
    update.message.reply_text(f"👥 Total users: {len(users)}")

def withdrawals(update, context):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not withdraw_requests:
        update.message.reply_text("No requests")
        return

    msg = "💸 Requests:\n"
    for i, w in enumerate(withdraw_requests):
        msg += f"{i} | {w['user']} | ₹{w['amount']}\n"

    update.message.reply_text(msg)

# ================== MAIN BOT ==================
def run_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("wallet", wallet))
    dp.add_handler(CommandHandler("send", send))
    dp.add_handler(CommandHandler("withdrawcash", withdraw))
    dp.add_handler(CommandHandler("connect", connect))
    dp.add_handler(CommandHandler("lang", lang))
    dp.add_handler(CommandHandler("channel", channel))
    dp.add_handler(CommandHandler("server", server))

    # ADMIN
    dp.add_handler(CommandHandler("users", users_cmd))
    dp.add_handler(CommandHandler("withdrawals", withdrawals))

    dp.add_handler(MessageHandler(Filters.text, handle))

    updater.start_polling()
    updater.idle()

# ================== RUN BOTH ==================
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
