import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

WAITING_REPLY = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Assalomu alaykum!\n\n"
        "Men <a href='https://t.me/intizomAi_bot'>IntizomAi</a> ning feedback botiman.\n\n"
        "Bu bot orqali siz:\n"
        "💬 Taklif yoki shikoyat yuborishingiz\n"
        "📢 Reklama bo'yicha murojaat qilishingiz\n"
        "❓ Istalgan savol yoki xabar yo'llashingiz mumkin\n\n"
        "Shunchaki xabaringizni yozing — men albatta ko'raman! ✍️"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if user.id == ADMIN_ID:
        await message.reply_text("⚙️ Siz adminsiz. Javob berish uchun 'Javob berish' tugmasini bosing.")
        return

    full_name = user.full_name
    user_id = user.id
    username = f"@{user.username}" if user.username else "username yo'q"

    admin_text = (
        f"📩 <b>Yangi xabar!</b>\n\n"
        f"👤 <b>Ism:</b> {full_name}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> {username}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ Javob berish", callback_data=f"reply_{user_id}")]
    ])

    try:
        # User ma'lumotlari + "Javob berish" tugmasi
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        # Xabarni copy — rasm+matn bitta, bold/italic/link formatlash saqlanadi
        await message.copy(chat_id=ADMIN_ID)

        await message.reply_text("✅ Xabaringiz yuborildi! Tez orada javob olasiz.")
    except Exception as e:
        logger.error(f"Xabar yuborishda xato: {e}")
        await message.reply_text("❌ Xabar yuborishda xato yuz berdi. Keyinroq urinib ko'ring.")


async def handle_reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    target_user_id = int(query.data.split("_")[1])
    WAITING_REPLY[ADMIN_ID] = target_user_id

    await query.message.reply_text(
        f"✍️ Javobingizni yozing (<code>{target_user_id}</code> ga yuboriladi):\n\n"
        f"Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML"
    )


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if user.id != ADMIN_ID:
        return await handle_user_message(update, context)

    if ADMIN_ID not in WAITING_REPLY:
        await message.reply_text("⚙️ Siz adminsiz. Javob berish uchun 'Javob berish' tugmasini bosing.")
        return

    target_id = WAITING_REPLY.pop(ADMIN_ID)

    try:
        await message.copy(chat_id=target_id)
        await message.reply_text(f"✅ Javob foydalanuvchiga ({target_id}) yuborildi!")
    except Exception as e:
        logger.error(f"Javob yuborishda xato: {e}")
        await message.reply_text("❌ Foydalanuvchiga xabar yuborib bo'lmadi. Ular botni bloklagandir.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID and ADMIN_ID in WAITING_REPLY:
        WAITING_REPLY.pop(ADMIN_ID)
        await update.message.reply_text("❌ Javob bekor qilindi.")
    else:
        await update.message.reply_text("Hech narsa bekor qilinmadi.")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(handle_reply_button, pattern=r"^reply_\d+$"))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_admin_reply
    ))
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.VOICE,
        handle_user_message
    ))
    logger.info("Bot ishga tushdi...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()