import os
import requests
import json
import time
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# ==================== CONFIGURATION ====================
API_BASE = "https://anishexploits.site/api/api.php?key=exploits&num="
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8372266918:AAGMkYzH0QvmxGJVrrTXvF8nzT7KXjj1O40')
PORT = int(os.environ.get('PORT', 8080))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Termux) Gecko/117.0 Firefox/117.0",
    "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
    "Referer": "https://oliver-exploits.vercel.app/",
    "Connection": "keep-alive"
}

# ==================== SIMPLE WEB SERVER ====================
class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running. Powered by Render.")
    
    def log_message(self, format, *args):
        pass

def run_web_server():
    """Run a simple web server to keep Render alive"""
    server = HTTPServer(('0.0.0.0', PORT), WebHandler)
    print(f"✅ Web server started on port {PORT}")
    server.serve_forever()

# ==================== BOT FUNCTIONS ====================
def start(update: Update, context: CallbackContext):
    welcome_text = "👋 *WELCOME TO OLIVER EXPLOITS*\n\n"
    
    keyboard = [[KeyboardButton("📞 ENTER NUMBER")]]  
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)  
    
    update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    
    if text == "📞 ENTER NUMBER":
        update.message.reply_text("📤 *Send Your 10-digit Number Without +91:*", parse_mode='Markdown')  
    else:  
        process_number(update, context)

def process_number(update: Update, context: CallbackContext):
    number = update.message.text.strip()
    
    if not number.isdigit() or len(number) != 10:  
        update.message.reply_text("❌ *INVALID INPUT*\nPlease send 10-digit number only.", parse_mode='Markdown')  
        return  
    
    processing_msg = update.message.reply_text("🔍 *Scanning Database...*", parse_mode='Markdown')  
    time.sleep(2)  
    
    result = search_number_api(number)  
    
    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_msg.message_id)  
    
    update.message.reply_text(result, parse_mode='Markdown')

def search_number_api(number):
    url = f"{API_BASE}{number}"
    
    try:  
        response = requests.get(url, headers=HEADERS, timeout=30)
        
        if response.status_code != 200:  
            return f"🛡️ OLIVER EXPLOITS CYBERSECURITY INFORMATION 🛡️\n\n" \
                   f"🎯 TARGET: {number}\n\n" \
                   f"❌ DATABASE ERROR\n\n" \
                   f"Server connection failed.\n\n" \
                   f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                   f"🔐 END OF REPORT"
        
        try:
            data = response.json()
        except:
            return f"🛡️ OLIVER EXPLOITS CYBERSECURITY INFORMATION 🛡️\n\n" \
                   f"🎯 TARGET: {number}\n\n" \
                   f"❌ DATA ERROR\n\n" \
                   f"Invalid response format.\n\n" \
                   f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                   f"🔐 END OF REPORT"
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        user_data, record_count = extract_user_data(data)
        
        if user_data:
            return format_cybersecurity_report(user_data, number, record_count, current_time)
        else:
            return f"🛡️ OLIVER EXPLOITS CYBERSECURITY INFORMATION 🛡️\n\n" \
                   f"🎯 TARGET: {number}\n\n" \
                   f"⚠️ NO INFORMATION FOUND\n\n" \
                   f"Number not found in database.\n\n" \
                   f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                   f"🔐 END OF REPORT"
        
    except requests.exceptions.Timeout:
        return f"🛡️ OLIVER EXPLOITS CYBERSECURITY INFORMATION 🛡️\n\n" \
               f"🎯 TARGET: {number}\n\n" \
               f"⏱️ TIMEOUT ERROR\n\n" \
               f"Request timed out.\n\n" \
               f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
               f"🔐 END OF REPORT"
    except requests.exceptions.ConnectionError:
        return f"🛡️ OLIVER EXPLOITS CYBERSECURITY INFORMATION 🛡️\n\n" \
               f"🎯 TARGET: {number}\n\n" \
               f"🌐 CONNECTION ERROR\n\n" \
               f"Network connection failed.\n\n" \
               f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
               f"🔐 END OF REPORT"
    except Exception as e:  
        return f"🛡️ OLIVER EXPLOITS CYBERSECURITY INFORMATION 🛡️\n\n" \
               f"🎯 TARGET: {number}\n\n" \
               f"❌ SYSTEM ERROR\n\n" \
               f"Unknown error occurred.\n\n" \
               f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
               f"🔐 END OF REPORT"

def extract_user_data(data):
    """Extract user data from different API formats"""
    user_data = None
    record_count = 1
    
    if isinstance(data, dict) and data.get('success') and data.get('result'):
        results = data.get('result', [])
        if results:
            user_data = results[0]
            record_count = len(results)
    elif isinstance(data, dict) and (data.get('mobile') or data.get('name')):
        user_data = data
    elif isinstance(data, list) and len(data) > 0:
        user_data = data[0]
        record_count = len(data)
    elif isinstance(data, dict) and data.get('status') == 'success':
        user_data = data.get('data', {})
    
    return user_data, record_count

def format_cybersecurity_report(user_data, number, record_count, current_time):
    """Format the cybersecurity report"""
    
    phone = user_data.get('mobile', number)
    alt = user_data.get('alt_mobile')
    aadhar = user_data.get('id_number', user_data.get('aadhar'))
    name = user_data.get('name', 'None')
    father = user_data.get('father_name', 'None')
    address = user_data.get('address', '')
    circle = user_data.get('circle', '')
    
    if address:
        address = address.replace('!', ' ').replace('|', ' ').replace('NA', '').replace('l\'', '').replace('Ii', '')
        address = ' '.join(address.split())
    
    actual_circle = 'Unknown'
    if circle:
        parts = circle.split()
        if len(parts) >= 2:
            actual_circle = parts[0]
        else:
            actual_circle = circle
    
    network = 'Unknown'
    circle_upper = circle.upper()
    if 'JIO' in circle_upper:
        network = 'JIO'
    elif 'VODAFONE' in circle_upper:
        network = 'VODAFONE'
    elif 'AIRTEL' in circle_upper:
        network = 'AIRTEL'
    elif 'BSNL' in circle_upper:
        network = 'BSNL'
    elif circle:
        operators = ['JIO', 'VODAFONE', 'AIRTEL', 'BSNL', 'IDEA', 'AIRCEL']
        for operator in operators:
            if operator in circle_upper:
                network = operator
                break
    
    report = "🛡️ OLIVER EXPLOITS CYBERSECURITY INFORMATION 🛡️\n\n"
    report += f"🎯 TARGET: {number}\n\n"
    
    if name and name != 'None':
        report += f"👤 Name: {name}\n"
    if father and father != 'None':
        report += f"👨‍👦 Father: {father}\n"
    if address:
        report += f"📍 Address: {address[:80] + '...' if len(address) > 80 else address}\n"
    if aadhar:
        report += f"🆔 Aadhar: {aadhar}\n"
    if alt:
        report += f"📱 Alt Mobile: {alt}\n"
    
    report += f"🌐 Network: {network}\n"
    report += f"📡 Circle: {actual_circle}\n"
    report += f"⏰ Time: {current_time}\n\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    report += "🔐 END OF REPORT"
    
    return report

# ==================== MAIN FUNCTION ====================
def main():
    """Main function"""
    print("\n" + "="*50)
    print("🛡️ OLIVER EXPLOITS NUMBER SCANNER")
    print("="*50)
    
    # Start web server in a thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Start the bot
    try:
        updater = Updater(BOT_TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        print("\n✅ Bot initialized successfully!")
        print("🔍 Waiting for scan requests...\n")
        
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == "__main__":
    main()
