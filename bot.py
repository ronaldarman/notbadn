import os
import json
import time
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler
)
from telegram.ext import filters
from telegram.ext import ApplicationBuilder

# Load configuration
def load_config():
    if os.path.exists("admin.json"):
        with open("admin.json", 'r') as f:
            return json.load(f)
    raise Exception("admin.json configuration file not found")

CONFIG = load_config()

# Initialize data storage
def load_data():
    if os.path.exists("data.json"):
        with open("data.json", 'r') as f:
            return json.load(f)
    return {
        "users": {},
        "proxy_enabled": False,
        "proxies": [],
        "current_proxy_index": 0
    }

def save_data():
    with open("data.json", 'w') as f:
        json.dump(DATA, f, indent=2)

DATA = load_data()

# Load proxies
def load_proxies():
    if os.path.exists("proxy.txt"):
        with open("proxy.txt", 'r') as f:
            DATA['proxies'] = [line.strip() for line in f if line.strip()]
    else:
        DATA['proxies'] = []

load_proxies()

# GitHub Checker Core
def check_github_profile(username):
    """Check GitHub profile with proxy support"""
    config = {
        "api_url": f"https://api.github.com/users/{username}",
        "profile_url": f"https://github.com/{username}",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        },
        "timeout": 10
    }

    if DATA['proxy_enabled'] and DATA['proxies']:
        proxy = get_next_proxy()
        config["proxies"] = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }

    result = {
        "username": username,
        "exists": True,
        "is_suspended": False,
        "is_pro": False,
        "pro_source": None,
        "created_at": None,
        "public_repos": None,
        "error": None,
        "last_checked": datetime.now().isoformat()
    }

    try:
        # API Check
        api_response = requests.get(
            config["api_url"],
            headers=config["headers"],
            proxies=config.get("proxies"),
            timeout=config["timeout"]
        )
        time.sleep(CONFIG['check_cooldown'])

        if api_response.status_code == 404:
            result.update({
                "exists": False,
                "is_suspended": True
            })
            return result
            
        elif api_response.status_code != 200:
            result["error"] = f"API Error: {api_response.status_code}"
            return result

        profile_data = api_response.json()
        result.update({
            "created_at": profile_data.get("created_at"),
            "public_repos": profile_data.get("public_repos")
        })

        # Web Scraping Check
        web_response = requests.get(
            config["profile_url"],
            headers=config["headers"],
            proxies=config.get("proxies"),
            timeout=config["timeout"]
        )
        time.sleep(CONFIG['check_cooldown'])

        if web_response.status_code == 200:
            soup = BeautifulSoup(web_response.text, 'html.parser')
            
            # Check PRO badge
            highlights = soup.find("div", {"aria-label": "Highlights"})
            if highlights and "(PRO)" in highlights.get_text():
                result.update({
                    "is_pro": True,
                    "pro_source": "Highlights Section"
                })
            
            if not result["is_pro"]:
                for span in soup.find_all("span", class_=lambda x: bool(x) and "Label" in x):
                    if "Pro" in span.get_text(strip=True):
                        result.update({
                            "is_pro": True,
                            "pro_source": "Profile Badge"
                        })
                        break
                        
            if not result["is_pro"]:
                bio = soup.find("div", class_="p-note user-profile-bio mb-3 js-user-profile-bio f4")
                if bio and "student" in bio.get_text().lower():
                    result.update({
                        "is_pro": True,
                        "pro_source": "Bio Keyword"
                    })

    except requests.Timeout:
        result["error"] = "Request timeout"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
    
    return result

def get_next_proxy():
    if not DATA['proxies']:
        return None
    
    DATA['current_proxy_index'] = (DATA['current_proxy_index'] + 1) % len(DATA['proxies'])
    save_data()
    return DATA['proxies'][DATA['current_proxy_index']]

# Telegram Bot Handlers
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if str(user_id) not in DATA['users']:
        user_type = "admin" if user_id in CONFIG['admin_ids'] else "regular"
        DATA['users'][str(user_id)] = {
            "type": user_type,
            "checks_today": 0,
            "last_check_date": str(datetime.now().date()),
            "joined_date": str(datetime.now().date())
        }
        save_data()
    
    if update.message:
        await update.message.reply_text(
            "🛠 GitHub Profile Checker Bot\n\n"
            "Perintah yang tersedia:\n"
            "/check <username> - Cek profil GitHub\n"
            "/bulkcheck - Cek banyak username (kirim satu per satu, ketik /done ketika selesai)\n"
            "/mystats - Lihat statistik penggunaan\n\n"
            f"Limit harian: {CONFIG['limits']['regular_daily_limit']} checks (regular) / {CONFIG['limits']['premium_daily_limit']} checks (premium)"
        )

def check_user_limit(user_id):
    user_id = str(user_id)
    if user_id not in DATA['users']:
        return False
    
    user = DATA['users'][user_id]
    
    # Reset daily counter if it's a new day
    if user['last_check_date'] != str(datetime.now().date()):
        user['checks_today'] = 0
        user['last_check_date'] = str(datetime.now().date())
        save_data()
    
    # Check if user has exceeded limit
    if user['type'] == 'regular' and user['checks_today'] >= CONFIG['limits']['regular_daily_limit']:
        return False
    if user['type'] == 'premium' and user['checks_today'] >= CONFIG['limits']['premium_daily_limit']:
        return False
    
    return True

def increment_user_counter(user_id):
    user_id = str(user_id)
    if user_id in DATA['users']:
        DATA['users'][user_id]['checks_today'] += 1
        save_data()

async def check_handler(update: Update, context: CallbackContext):
    if update.effective_user is None or update.effective_user.id is None:
        if update.message:
            await update.message.reply_text("❌ Tidak dapat mengambil ID pengguna.")
        return
    user_id = update.effective_user.id

    if not check_user_limit(user_id):
        user_type = DATA['users'].get(str(user_id), {}).get("type", "regular")
        limit = CONFIG['limits']['regular_daily_limit'] if user_type == "regular" else CONFIG['limits']['premium_daily_limit']
        if update.message:
            await update.message.reply_text(
                f"❌ Limit harian tercapai ({limit} checks/hari)."
            )
        return

    if not context.args:
        if update.message:
            await update.message.reply_text("Format: /check <github_username>")
        return

    username = " ".join(context.args)
    result = check_github_profile(username)
    increment_user_counter(user_id)

    response = format_single_result(result)
    if update.message is not None:
        await update.message.reply_text(response, parse_mode="Markdown")

async def bulk_check_start(update: Update, context: CallbackContext):
    if update.effective_user is None or update.effective_user.id is None:
        if update.message:
            await update.message.reply_text("❌ Tidak dapat mengambil ID pengguna.")
        return
    if update.effective_user is None or update.effective_user.id is None:
        if update.message:
            await update.message.reply_text("❌ Tidak dapat mengambil ID pengguna.")
        return
    user_id = update.effective_user.id
    user_type = DATA['users'].get(str(user_id), {}).get("type", "regular")
    
    if user_type != "premium" and user_type != "admin":
        if update.message:
            await update.message.reply_text("❌ Fitur bulk check hanya untuk user premium!")
        return

    if context.user_data is None:
        context.user_data = {}

    context.user_data['bulk_check'] = {
        'usernames': [],
        'results': []
    }
    
    if update.message:
        await update.message.reply_text(
            "📝 Mode bulk check aktif. Kirim username GitHub satu per satu.\n"
            "Ketika selesai, ketik /done untuk melihat hasil.\n"
            "Ketik /cancel untuk membatalkan."
        )

async def bulk_check_add(update: Update, context: CallbackContext):
    if context.user_data is None or 'bulk_check' not in context.user_data:
        return

    if update.message is None or update.message.text is None:
        return

    # Ambil semua username, pisahkan per baris, hapus spasi kosong
    lines = [u.strip() for u in update.message.text.splitlines() if u.strip()]
    if not lines:
        return

    # Tambahkan semua username ke daftar bulk_check
    context.user_data['bulk_check']['usernames'].extend(lines)
    await update.message.reply_text(
        f"✅ Menambahkan {len(lines)} username ke daftar check. Kirim username lain atau /done jika selesai."
    )

async def bulk_check_process(update: Update, context: CallbackContext):
    if context.user_data is None or 'bulk_check' not in context.user_data:
        return
    
    usernames = context.user_data['bulk_check']['usernames']
    if not usernames:
        if update.message:
            await update.message.reply_text("❌ Tidak ada username yang dimasukkan.")
        return
    
    if update.message:
        await update.message.reply_text(f"🔍 Memproses {len(usernames)} username...")

    for username in usernames:
        if update.effective_user is None or update.effective_user.id is None or not check_user_limit(update.effective_user.id):
            result = {
                "username": username,
                "exists": False,
                "is_pro": False,
                "pro_source": None,
                "created_at": None,
                "public_repos": None,
                "error": "Daily limit reached",
                "last_checked": datetime.now().isoformat()
            }
        else:
            result = check_github_profile(username)
            increment_user_counter(update.effective_user.id)
        response = format_single_result(result)
        if update.message:
            await update.message.reply_text(response, parse_mode="Markdown")
        time.sleep(CONFIG['check_cooldown'])

    del context.user_data['bulk_check']

    # Tambahkan pesan selesai di sini
    if update.message:
        await update.message.reply_text("✅ Semua username sudah dicek.")

async def bulk_check_cancel(update: Update, context: CallbackContext):
    if context.user_data is not None and 'bulk_check' in context.user_data:
        del context.user_data['bulk_check']
    if update.message is not None:
        await update.message.reply_text("❌ Bulk check dibatalkan.")

async def my_stats(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in DATA['users']:
        if update.message is not None:
            await update.message.reply_text("Anda belum terdaftar. Gunakan /start untuk memulai.")
        return
    
    user = DATA['users'][user_id]
    checks_today = user['checks_today']
    user_type = user['type']
    
    if user['last_check_date'] != str(datetime.now().date()):
        checks_today = 0
    
    limit = CONFIG['limits']['premium_daily_limit'] if user_type == "premium" else CONFIG['limits']['regular_daily_limit']
    
    message = (
        f"📊 Statistik Anda:\n"
        f"• Tipe: {user_type.upper()}\n"
        f"• Checks hari ini: {checks_today}/{limit}\n"
        f"• Bergabung pada: {user['joined_date']}\n\n"
    )
    
    if user_type == "regular":
        message += "Upgrade ke premium untuk limit checks lebih tinggi!"
    
    await update.message.reply_text(message)

# Admin Commands
async def admin_toggle_proxy(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in CONFIG['admin_ids']:
        await update.message.reply_text("❌ Hanya admin yang bisa menggunakan perintah ini")
        return
    
    DATA['proxy_enabled'] = not DATA['proxy_enabled']
    save_data()
    status = "AKTIF" if DATA['proxy_enabled'] else "NON-AKTIF"
    if update.message is not None:
        await update.message.reply_text(f"🔄 Status proxy: {status}")

async def admin_reload_proxies(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in CONFIG['admin_ids']:
        await update.message.reply_text("❌ Hanya admin yang bisa menggunakan perintah ini")
        return
    
    load_proxies()
    await update.message.reply_text(f"✅ Memuat ulang {len(DATA['proxies'])} proxy")

async def admin_add_premium(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in CONFIG['admin_ids']:
        await update.message.reply_text("❌ Hanya admin yang bisa menggunakan perintah ini")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /addpremium <user_id>")
        return

    target_id = context.args[0]
    if target_id not in DATA['users']:
        await update.message.reply_text("User belum pernah menggunakan bot.")
        return

    DATA['users'][target_id]['type'] = "premium"
    save_data()
    await update.message.reply_text(f"✅ User {target_id} sekarang menjadi premium.")

# Formatting Functions
def format_single_result(result):
    status = "❌ TIDAK ADA/SUSPEND" if not result['exists'] else "✅ AKTIF"
    pro_status = '✅ YA' if result['is_pro'] else '❌ TIDAK'
    pro_source = f" ({result['pro_source']})" if result['is_pro'] else ''
    
    created_at = "Tidak diketahui"
    if result['created_at']:
        try:
            created_at = datetime.strptime(result['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d %B %Y')
        except:
            created_at = result['created_at']
    
    error_msg = f"\n⚠️ Error: {result['error']}" if result['error'] else ''
    
    return (
        f"🔍 HASIL PENGECEKAN: @{result['username']}\n"
        f"====================\n"
        f"• Status: {status}\n"
        f"• Badge PRO: {pro_status}{pro_source}\n"
        f"• Dibuat pada: {created_at}\n"
        f"• Repo Publik: {result['public_repos'] or '0'}\n"
        f"• Terakhir diperiksa: {datetime.fromisoformat(result['last_checked']).strftime('%Y-%m-%d %H:%M:%S')}"
        f"{error_msg}"
    )

def format_bulk_results(results):
    success = [r for r in results if r.get('exists') and not r.get('error')]
    suspended = [r for r in results if not r.get('exists')]
    errors = [r for r in results if r.get('error')]
    pro_users = [r for r in success if r.get('is_pro')]
    
    summary = (
        f"📊 HASIL BULK CHECK ({len(results)} username)\n"
        f"====================\n"
        f"• ✅ Aktif: {len(success)}\n"
        f"• ❌ Suspended: {len(suspended)}\n"
        f"• ⚠️ Error: {len(errors)}\n"
        f"• 🎖 PRO Users: {len(pro_users)}\n\n"
    )
    
    details = []
    for result in results:
        status = "SUSPEND" if not result['exists'] else "AKTIF"
        pro = " (PRO)" if result.get('is_pro') else ""
        error = f" [ERROR: {result['error']}]" if result.get('error') else ""
        details.append(f"@{result['username']}: {status}{pro}{error}")
    
    return summary + "Detail:\n" + "\n".join(details)

def main():
    # Create data file if not exists
    if not os.path.exists("data.json"):
        save_data()

    # Initialize bot using ApplicationBuilder
    application = ApplicationBuilder().token(CONFIG['bot_token']).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check_handler))
    application.add_handler(CommandHandler("bulkcheck", bulk_check_start))
    application.add_handler(CommandHandler("done", bulk_check_process))
    application.add_handler(CommandHandler("cancel", bulk_check_cancel))
    application.add_handler(CommandHandler("mystats", my_stats))
    application.add_handler(CommandHandler("proxy", admin_toggle_proxy))
    application.add_handler(CommandHandler("reloadproxies", admin_reload_proxies))
    application.add_handler(CommandHandler("addpremium", admin_add_premium))

    # Add handler for bulk check usernames
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        bulk_check_add
    ))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()