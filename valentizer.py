import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import BadRequest

# Загружаем переменные окружения
load_dotenv()

# Конфигурация
TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID = -1002481390856  # Замените на ID вашей группы
BOT_USERNAME = "ValentizerBot"  # Укажите username бота
PORT = 10000  # Порт для вебхуков (используйте 10000 для Render)

# Участники (user_id, username)
participants_list = [
    (377737393, 'CHARONVl'),
    (397933331, 'm1role'),
    (367132365, 'prostoidinaxui'),
    (94837067, 'knopushka'),
    (349931272, 'polarzed'),
    (863951476, 'Kseniya_250'),
    (740464526, 'panikadanya'),
    (727143307, 'Ephochka'),
    (45375541, 'klinisch_fadian'),
    (680297697, 'silveromanv'),
    (287549169, 'Fidman7'),
    (184393120, 'iolera'),
    (46129871, 'hoiphuoc'),
    (614272146, 'john18_23doe'),
    (803689645, 'cr0mwell'),
    (635696972, 'pixellpot'),
    (476509129, 'mcaacm'),
    (907643796, 'elizabet_fridrih'),
    (838940255, 'tara_mani'),
    (845436821, 'Kromahi'),
    (359330387, 'disharapova'),
    (436784974, 'asmmadey'),
    (428677220, 'tread1ightly'),
    (1141520206, 'Wortex9670'),
    (497801276, 'mrSandman_R'),
    (922518145, 'Diva_Lilith'),
    (431918338, 'randomkvit'),
    (1349645511, 's1berian_m0use'),
    (457432385, 'hekkapoo'),
    (263442009, 'neShentseva'),
    (1278466384, 'alina22arefeva'),
    (942222874, 'artemkrauss')
]

valentines = {}

def get_participants():
    return participants_list

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Отправить валентинку", callback_data="send_valentine")],
        [InlineKeyboardButton("Посмотреть валентинки", callback_data="view_valentines")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Это бот для обмена валентинками. Ты можешь анонимно или открыто отправлять валентинки другим участникам.",
        reply_markup=reply_markup,
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "send_valentine":
        await show_participants(query, context)
    elif query.data == "view_valentines":
        await show_valentines(query, context)
    elif query.data.startswith("send_to_"):
        recipient_id = int(query.data.split("_")[2])
        context.user_data["recipient_id"] = recipient_id
        await ask_anonymity(query, context)
    elif query.data in ["anon_yes", "anon_no"]:
        await handle_anonymity_choice(query, context)
    elif query.data == "cancel":
        context.user_data.clear()
        await show_main_menu(query, context)

async def ask_anonymity(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Анонимно", callback_data="anon_yes")],
        [InlineKeyboardButton("Открыто", callback_data="anon_no")],
        [InlineKeyboardButton("Отмена", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Как отправить валентинку?",
        reply_markup=reply_markup,
    )

async def handle_anonymity_choice(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["anonymous"] = query.data == "anon_yes"
    if query.data == "anon_no":
        user = query.from_user
        sender_display = f"@{user.username}" if user.username else user.first_name
        context.user_data["sender_display"] = sender_display
    
    await query.edit_message_text(
        text="Пришли текст, фото, гифку или видео для валентинки:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отмена", callback_data="cancel")]]),
    )

async def show_main_menu(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Отправить валентинку", callback_data="send_valentine")],
        [InlineKeyboardButton("Посмотреть валентинки", callback_data="view_valentines")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Что будем делать?", reply_markup=reply_markup)

async def show_participants(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    participants = get_participants()
    keyboard = [
        [InlineKeyboardButton(username, callback_data=f"send_to_{uid}")]
        for uid, username in participants
    ]
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Кому отправим валентинку?", reply_markup=reply_markup)

async def show_valentines(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = query.from_user.id
    user_valentines = valentines.get(user_id, [])
    
    if not user_valentines:
        await query.edit_message_text(text="Пока валентинок нет 😢")
        await show_main_menu(query, context)
        return

    await query.edit_message_text(text="📩 Твои валентинки:")
    
    for val in user_valentines:
        sender_info = val["sender_info"]
        content = val.get("caption") or val.get("content") or "Тебе прислали медиа без текста"
        
        try:
            if val["type"] == "text":
                await context.bot.send_message(user_id, text=f"{sender_info}\n\n{content}")
            elif val["type"] == "photo":
                await context.bot.send_photo(user_id, photo=val["file_id"], caption=f"{sender_info}\n\n{content}")
            elif val["type"] == "video":
                await context.bot.send_video(user_id, video=val["file_id"], caption=f"{sender_info}\n\n{content}")
            elif val["type"] == "animation":
                await context.bot.send_animation(user_id, animation=val["file_id"], caption=f"{sender_info}\n\n{content}")
        except BadRequest as e:
            print(f"Ошибка отправки валентинки: {e}")
    
    await show_main_menu(query, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat.id == GROUP_CHAT_ID:
        if update.message.reply_to_message:
            bot_link = f"https://t.me/{BOT_USERNAME}"
            await update.message.reply_text(
                f"Если тоже хочешь отправить валентинку — загляни в бота: {bot_link}",
                reply_to_message_id=update.message.message_id,
            )
        return

    user_data = context.user_data
    if "recipient_id" not in user_data or "anonymous" not in user_data:
        await update.message.reply_text("Сначала выбери получателя через меню бота!")
        return

    content_type, content = detect_content_type(update)
    if content_type:
        await send_valentine(update, context, content, content_type)
        context.user_data.clear()
        await show_main_menu(update, context)
    else:
        await update.message.reply_text("Неподдерживаемый тип сообщения. Отправь текст, фото, видео или GIF.")

def detect_content_type(update: Update):
    if update.message.text:
        return "text", update.message.text
    elif update.message.photo:
        return "photo", update.message.photo[-1]
    elif update.message.video:
        return "video", update.message.video
    elif update.message.animation:
        return "animation", update.message.animation
    return None, None

async def send_valentine(update: Update, context: ContextTypes.DEFAULT_TYPE, content, content_type: str) -> None:
    user_data = context.user_data
    recipient_id = user_data["recipient_id"]
    
    # Формируем сообщение
    sender_info = "💌 Анонимная валентинка" if user_data["anonymous"] else f"💌 Валентинка от {user_data.get('sender_display', 'Неизвестный')}"
    text_content = get_message_text(update, content_type)

    # Сохраняем валентинку
    save_valentine(recipient_id, content_type, content, sender_info, text_content)

    # Отправляем получателю
    await send_to_recipient(context, recipient_id, content_type, content, sender_info, text_content)

    # Публикуем в группе
    await publish_to_group(context, recipient_id, content_type, content, text_content)

    await update.message.reply_text("✅ Валентинка отправлена! Можешь отправить ещё")

def get_message_text(update: Update, content_type: str) -> str:
    if content_type == "text":
        return update.message.text
    return update.message.caption or "Тебе прислали медиа без текста"

def save_valentine(recipient_id, content_type, content, sender_info, text_content):
    val_data = {
        "sender_info": sender_info,
        "type": content_type,
        "file_id": content.file_id if content_type != "text" else None,
        "content": text_content if content_type == "text" else None,
        "caption": text_content if content_type != "text" else None,
    }
    if recipient_id not in valentines:
        valentines[recipient_id] = []
    valentines[recipient_id].append(val_data)

async def send_to_recipient(context, recipient_id, content_type, content, sender_info, text_content):
    try:
        if content_type == "text":
            await context.bot.send_message(recipient_id, f"{sender_info}\n\n{text_content}")
        else:
            method = {
                "photo": context.bot.send_photo,
                "video": context.bot.send_video,
                "animation": context.bot.send_animation,
            }[content_type]
            await method(
                recipient_id,
                content.file_id,
                caption=f"{sender_info}\n\n{text_content}",
            )
    except Exception as e:
        print(f"Ошибка отправки получателю: {e}")

async def publish_to_group(context, recipient_id, content_type, content, text_content):
    recipient_username = next((u for uid, u in participants_list if uid == recipient_id), "Неизвестный")
    bot_link = f"https://t.me/{BOT_USERNAME}"
    
    try:
        if content_type == "text":
            sent_message = await context.bot.send_message(
                GROUP_CHAT_ID,
                f"💌 Для @{recipient_username}\n\n{text_content}",
            )
        else:
            method = {
                "photo": context.bot.send_photo,
                "video": context.bot.send_video,
                "animation": context.bot.send_animation,
            }[content_type]
            sent_message = await method(
                GROUP_CHAT_ID,
                content.file_id,
                caption=f"💌 Для @{recipient_username}\n\n{text_content}",
            )

        await context.bot.send_message(
            GROUP_CHAT_ID,
            f"Хочешь тоже отправить валентинку? Переходи в бота: {bot_link}",
            reply_to_message_id=sent_message.message_id,
        )
    except BadRequest as e:
        print(f"Ошибка публикации в группе: {e}")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.VIDEO | filters.ANIMATION,
        handle_message,
    ))

    # Настройка вебхуков для Render
    application.run_webhook(
        listen="0.0.0.0",
        port=1000,
        webhook_url=f"https://{BOT_USERNAME}.onrender.com/{TOKEN}",
        url_path=TOKEN,
    )

if __name__ == "__main__":
    main()
