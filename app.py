import os
import requests
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ConversationHandler, 
    filters, 
    ContextTypes
)

# ================= CONFIGURATION =================
# 👇 PASTE YOUR KEYS INSIDE THE QUOTES BELOW 👇
TOKEN = "PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE" 
UPTIME_API_KEY = "PASTE_YOUR_UPTIME_ROBOT_MAIN_API_KEY_HERE"

API_URL = "https://api.uptimerobot.com/v2/"

# Define states for the "Add Monitor" conversation
NAME, URL = range(2)
# =================================================

# --- PART 1: THE WEB SERVER (Required for Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive! The bot is running."

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- PART 2: UPTIME ROBOT LOGIC ---
def uptime_request(endpoint, payload={}):
    payload['api_key'] = UPTIME_API_KEY
    payload['format'] = 'json'
    try:
        response = requests.post(API_URL + endpoint, data=payload)
        data = response.json()
        if data.get('stat') == 'fail':
            print(f"API Error: {data.get('message')}")
            return None
        return data
    except Exception as e:
        print(f"Request failed: {e}")
        return None

# --- PART 3: TELEGRAM BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Updated Keyboard with "Delete Monitor"
    keyboard = [
        ["📊 Get Monitors", "📈 Account Stats"],
        ["➕ Add Monitor", "🗑️ Delete Monitor"],
        ["⏸️ Pause Monitor", "▶️ Resume Monitor"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)
    
    await update.message.reply_text(
        "👋 Welcome to your Uptime Robot Manager!\n\nUse the buttons below to control your monitors.",
        reply_markup=reply_markup
    )

# --- ADD MONITOR CONVERSATION ---
async def start_add_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆕 <b>Adding a New Monitor</b>\n\n"
        "First, please send me the <b>Friendly Name</b> for this monitor.\n"
        "(e.g., My Portfolio, Google, Backend API)\n\n"
        "<i>Type /cancel to stop.</i>",
        parse_mode='HTML'
    )
    return NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    context.user_data['new_monitor_name'] = user_input
    
    await update.message.reply_text(
        f"✅ Name set to: <b>{user_input}</b>\n\n"
        "Now, please send me the <b>URL</b> (Link) to monitor.\n"
        "(Make sure it starts with http:// or https://)",
        parse_mode='HTML'
    )
    return URL

async def receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url_input = update.message.text
    name = context.user_data['new_monitor_name']
    
    if not url_input.startswith("http"):
        await update.message.reply_text("⚠️ The URL must start with http:// or https://. Please try again.")
        return URL

    await update.message.reply_text("⏳ Creating monitor... please wait.")

    payload = {
        'friendly_name': name,
        'url': url_input,
        'type': 1 
    }
    
    res = uptime_request('newMonitor', payload)

    if res and res.get('stat') == 'ok':
        await update.message.reply_text(
            f"🎉 <b>Success!</b>\n\n"
            f"Monitor <b>{name}</b> has been added.\n"
            f"🔗 {url_input}",
            parse_mode='HTML'
        )
    else:
        error_msg = res.get('error', {}).get('message', 'Unknown error') if res else 'Connection failed'
        await update.message.reply_text(f"❌ Failed to create monitor.\nError: {error_msg}")

    return ConversationHandler.END

async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

# --- STANDARD HANDLERS ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📊 Get Monitors" or text == "/monitors":
        await get_monitors(update, context)
    elif text == "📈 Account Stats" or text == "/stats":
        await account_stats(update, context)
    elif text == "⏸️ Pause Monitor":
        await monitor_action_menu(update, context, 'pause')
    elif text == "▶️ Resume Monitor":
        await monitor_action_menu(update, context, 'resume')
    elif text == "🗑️ Delete Monitor":
        await monitor_action_menu(update, context, 'delete')

async def get_monitors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    data = uptime_request('getMonitors')
    
    if not data or not data.get('monitors'):
        await update.message.reply_text("❌ Failed to fetch monitors.")
        return

    monitors = data['monitors']
    if not monitors:
        await update.message.reply_text("You have no monitors configured.")
        return

    msg = "<b>📡 Your Monitors:</b>\n\n"
    for m in monitors:
        status_icon = "✅" if m['status'] == 2 else ("⏸️" if m['status'] == 0 else "🔴")
        status_text = "Up" if m['status'] == 2 else ("Paused" if m['status'] == 0 else "Down")
        msg += f"{status_icon} <b>{m['friendly_name']}</b>\n🔗 {m['url']}\nStatus: {status_text}\n\n"

    await update.message.reply_text(msg, parse_mode='HTML')

async def account_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    data = uptime_request('getAccountDetails')
    if not data or 'account' not in data:
        await update.message.reply_text("❌ Failed to fetch stats.")
        return
    acc = data['account']
    msg = (f"<b>👤 Account Stats</b>\n\n"
           f"📧 Email: {acc.get('email')}\n"
           f"🆙 Up Monitors: {acc.get('up_monitors')}\n"
           f"🔻 Down Monitors: {acc.get('down_monitors')}\n"
           f"⏸️ Paused Monitors: {acc.get('paused_monitors')}")
    await update.message.reply_text(msg, parse_mode='HTML')

async def monitor_action_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, action):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    data = uptime_request('getMonitors')
    if not data: return
    
    monitors_list = data.get('monitors', [])
    
    # Filter logic: 
    # If action is 'pause', show only Running (2).
    # If action is 'resume', show only Paused (0).
    # If action is 'delete', show ALL monitors.
    
    if action == 'pause':
        filtered = [m for m in monitors_list if m['status'] == 2]
    elif action == 'resume':
        filtered = [m for m in monitors_list if m['status'] == 0]
    else: # delete
        filtered = monitors_list

    if not filtered:
        await update.message.reply_text(f"No monitors available to {action}.")
        return

    warning_text = "⚠️ <b>Warning:</b> Deleting is permanent!" if action == 'delete' else ""
    
    keyboard = []
    for m in filtered:
        # Callback data format: action|id
        keyboard.append([InlineKeyboardButton(f"{m['friendly_name']}", callback_data=f"{action}|{m['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Select a monitor to <b>{action.upper()}</b>:\n{warning_text}", 
        reply_markup=reply_markup, 
        parse_mode='HTML'
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, monitor_id = query.data.split('|')
    
    if action == 'delete':
        res = uptime_request('deleteMonitor', {'id': monitor_id})
        success_msg = "🗑️ Monitor successfully deleted!"
        fail_msg = "❌ Failed to delete monitor."
    else:
        # Pause or Resume
        new_status = 0 if action == 'pause' else 1
        res = uptime_request('editMonitor', {'id': monitor_id, 'status': new_status})
        success_msg = f"✅ Monitor successfully {action}d!"
        fail_msg = f"❌ Failed to {action} monitor."

    if res and res.get('stat') == 'ok':
        await query.edit_message_text(success_msg)
    else:
        await query.edit_message_text(fail_msg)

# --- PART 4: MAIN EXECUTION ---
if __name__ == "__main__":
    keep_alive()
    print("🤖 Bot is starting...")
    
    if "PASTE" in TOKEN or "PASTE" in UPTIME_API_KEY:
        print("❌ ERROR: You forgot to paste your API keys in bot.py!")
    else:
        application = Application.builder().token(TOKEN).build()

        # Conversation Handler for Adding Monitor
        add_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^➕ Add Monitor$"), start_add_monitor)],
            states={
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
                URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_url)],
            },
            fallbacks=[CommandHandler("cancel", cancel_add)]
        )

        application.add_handler(CommandHandler("start", start))
        application.add_handler(add_conv_handler) 
        application.add_handler(CommandHandler("monitors", get_monitors))
        application.add_handler(CommandHandler("stats", account_stats))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_click))

        application.run_polling()
