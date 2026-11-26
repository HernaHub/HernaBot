import asyncio
import os
import ssl
from dotenv import load_dotenv
from darkob import Bot, Keyboard, Button
from database.db import db
from aiohttp import web
from pyngrok import ngrok

ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
# 🔴 توکن ngrok خودت را اینجا قرار بده:
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")

bot = Bot(token=BOT_TOKEN)

# ------------------ دستور /start ------------------
@bot.on_command("start")
async def start(bot, event):
    user_id = event.author_id
    first_name = getattr(event, "author_title", "کاربر")

    try:
        async with db.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (id, first_name) 
                VALUES ($1, $2) 
                ON CONFLICT (id) DO NOTHING
            ''', user_id, first_name)
    except Exception as e:
        print(f"Database insert error: {e}")

    keyboard = Keyboard().row(
        Button("👤 پروفایل من", id="profile"),
        Button("💰 موجودی سکه", id="coins")
    ).row(
        Button("🛒 فروشگاه", id="shop"),
        Button("🎮 بازی‌ها", id="games")
    ).row(
        Button("📜 قوانین", id="rules"),
        Button("📊 آمار من", id="stats")
    )

    await event.reply(
        "سلام! 👋\n"
        "به **هرنا بات** خوش آمدید!\n\n"
        "من یک ربات مدیریتی و سرگرمی هستم.\n"
        "برای شروع، از منوی زیر انتخاب کن:",
        inline_keypad=keyboard
    )

# ------------------ مدیریت کلیک روی دکمه‌ها ------------------
@bot.on_callback()
async def handle_buttons(bot, event):
    button_id = event.button_id
    user_id = event.author_id
    chat_id = event.chat_id

    if button_id == "profile":
        try:
            async with db.pool.acquire() as conn:
                user_data = await conn.fetchrow(
                    'SELECT coins, vip_expire_at FROM users WHERE id = $1', user_id
                )
            
            if user_data:
                coins = user_data['coins']
                vip = user_data['vip_expire_at']
                vip_status = f"✅ فعال (تا {vip.strftime('%Y-%m-%d')})" if vip else "❌ غیرفعال"
                
                profile_text = (
                    f"👤 **پروفایل شما**\n\n"
                    f"🆔 آیدی شما: `{user_id}`\n"
                    f"💰 موجودی سکه: **{coins}** سکه\n"
                    f"👑 وضعیت VIP: {vip_status}\n"
                )
                await bot.send_message(chat_id=chat_id, text=profile_text)
            else:
                await bot.send_message(chat_id=chat_id, text="اطلاعات شما یافت نشد. لطفاً دوباره /start بزنید.")
        except Exception as e:
            print(f"Profile fetch error: {e}")
            await bot.send_message(chat_id=chat_id, text="خطایی در دریافت اطلاعات رخ داد.")

    elif button_id == "coins":
        await bot.send_message(chat_id=chat_id, text="💰 سیستم کیف پول هنوز فعال نشده است. به زودی!")

# ------------------ هندلر دریافت Webhook ------------------
async def webhook_handler(request):
    try:
        data = await request.json()
        # ارسال دیتای دریافتی از روبیکا به کتابخانه darkob
        await bot.process_update(data) 
        return web.Response(text="OK")
    except Exception as e:
        print(f"Webhook error: {e}")
        return web.Response(status=500)

# ------------------ اجرای ربات ------------------
async def main():
    print("🚀 Starting Herna Bot in Webhook mode...")
    await db.connect()
    
    # 1. راه اندازی ngrok برای گرفتن لینک عمومی
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    public_url = ngrok.connect(8080).public_url
    print(f"🌐 Public Webhook URL: {public_url}")
    
    # 2. دادن آدرس به روبیکا
    await bot.set_webhook(url=f"{public_url}/webhook")
    print("✅ Webhook set successfully!")
    
    # 3. راه اندازی وب سرور محلی برای دریافت سیگنال‌ها
    app = web.Application()
    app.router.add_post('/webhook', webhook_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    print("✅ Server is running. Waiting for updates...")
    await asyncio.Event().wait() # ربات را روشن نگه می‌دارد

if __name__ == "__main__":
    asyncio.run(main())