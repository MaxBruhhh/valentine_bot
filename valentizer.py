from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

# Предустановленный список участников (user_id, username)
participants_list = [
    (377737393, 'CHARONVl'),
    (397933331, 'm1role'),
    (367132365, 'prostoidinaxui'),
    (94837067, 'knopushka'),
    (349931272, 'polarzed')
]  # Замените на реальные данные
valentines = {}
GROUP_CHAT_ID = -1002481390856
BOT_USERNAME = 'ValentizerBot'  # Замените на username бота

def get_participants(): 
    return participants_list

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Отправить валентинку", callback_data='send_valentine')],
        [InlineKeyboardButton("Посмотреть валентинки", callback_data='view_valentines')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Привет! Это бот для обмена валентинками. Ты можешь анонимно или открыто отправлять валентинки другим участникам.',
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == 'send_valentine':
        await show_participants(query, context)

    elif query.data == 'view_valentines':
        await show_valentines(query, context)

    elif query.data.startswith('send_to_'):
        recipient_id = int(query.data.split('_')[2])
        context.user_data['recipient_id'] = recipient_id
        await ask_anonymity(query, context)

    elif query.data in ['anon_yes', 'anon_no']:
        context.user_data['anonymous'] = query.data == 'anon_yes'
        
        if query.data == 'anon_no':
            sender_display = f"@{user.username}" if user.username else user.first_name
            context.user_data['sender_display'] = sender_display
        
        await query.edit_message_text(
            text="Пришли текст, фото, гифку или видео для валентинки в следующем сообщении.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отмена", callback_data='cancel')]])
        )

    elif query.data == 'cancel':
        context.user_data.clear()
        await show_main_menu(query, context)

async def ask_anonymity(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Анонимно", callback_data='anon_yes')],
        [InlineKeyboardButton("Открыто", callback_data='anon_no')],
        [InlineKeyboardButton("Отмена", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Как отправить валентинку?",
        reply_markup=reply_markup
    )

async def show_main_menu(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Отправить валентинку", callback_data='send_valentine')],
        [InlineKeyboardButton("Посмотреть валентинки", callback_data='view_valentines')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('Что будем делать?', reply_markup=reply_markup)

async def show_participants(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    participants = get_participants()
    keyboard = [[InlineKeyboardButton(username, callback_data=f'send_to_{uid}')] for uid, username in participants]
    keyboard.append([InlineKeyboardButton("Отмена", callback_data='cancel')])
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
        content = val.get('caption') or val.get('content') or "Тебе прислали медиа без текста"
        
        if val["type"] == "text":
            await context.bot.send_message(user_id, text=f"{sender_info}\n\n{content}")
        elif val["type"] == "photo":
            await context.bot.send_photo(user_id, photo=val["file_id"], caption=f"{sender_info}\n\n{content}")
        elif val["type"] == "video":
            await context.bot.send_video(user_id, video=val["file_id"], caption=f"{sender_info}\n\n{content}")
        elif val["type"] == "animation":
            await context.bot.send_animation(user_id, animation=val["file_id"], caption=f"{sender_info}\n\n{content}")
    
    await show_main_menu(query, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Обработка ответов в группе
    if update.message.chat.id == GROUP_CHAT_ID and update.message.reply_to_message:
        bot_link = f"https://t.me/{BOT_USERNAME}"
        await update.message.reply_text(
            f"Если тоже хочешь отправить кому-то валентинку, заглядывай в бота: {bot_link}",
            reply_to_message_id=update.message.message_id
        )
        return

    user_data = context.user_data
    if 'recipient_id' not in user_data or 'anonymous' not in user_data:
        await update.message.reply_text("Сначала выбери получателя и тип отправки через меню бота!")
        return

    # Определение типа контента
    content = None
    content_type = 'text'
    
    if update.message.text:
        content = update.message.text
    elif update.message.photo:
        content = update.message.photo[-1]
        content_type = 'photo'
    elif update.message.video:
        content = update.message.video
        content_type = 'video'
    elif update.message.animation:
        content = update.message.animation
        content_type = 'animation'

    await send_valentine(update, context, content, content_type)
    context.user_data.clear()
    await show_main_menu(update, context)

async def send_valentine(update: Update, context: ContextTypes.DEFAULT_TYPE, content, content_type: str) -> None:
    user_data = context.user_data
    recipient_id = user_data['recipient_id']
    
    # Формирование сообщения
    sender_info = "💌 Анонимная валентинка" if user_data['anonymous'] else f"💌 Валентинка от {user_data.get('sender_display', 'Неизвестный')}"
    caption = update.message.caption if hasattr(update.message, 'caption') else None
    text_content = update.message.text or caption or "Тебе прислали медиа без текста"

    # Сохранение валентинки
    val_data = {
        "sender_info": sender_info,
        "type": content_type,
        "file_id": content.file_id if content_type != 'text' else None,
        "content": text_content if content_type == 'text' else None,
        "caption": text_content if content_type != 'text' else None
    }

    if recipient_id not in valentines:
        valentines[recipient_id] = []
    valentines[recipient_id].append(val_data)

    # Отправка получателю
    try:
        if content_type == 'text':
            await context.bot.send_message(recipient_id, f"{sender_info}\n\n{text_content}")
        elif content_type == 'photo':
            await context.bot.send_photo(recipient_id, photo=content.file_id, caption=f"{sender_info}\n\n{text_content}")
        elif content_type == 'video':
            await context.bot.send_video(recipient_id, video=content.file_id, caption=f"{sender_info}\n\n{text_content}")
        elif content_type == 'animation':
            await context.bot.send_animation(recipient_id, animation=content.file_id, caption=f"{sender_info}\n\n{text_content}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

    # Отправка в группу и добавление приглашения
    recipient_username = next((u for uid, u in participants_list if uid == recipient_id), "Неизвестный")
    bot_link = f"https://t.me/{BOT_USERNAME}"
    
    try:
        if content_type == 'text':
            sent_message = await context.bot.send_message(
                GROUP_CHAT_ID,
                f"💌 Для @{recipient_username}\n\n{text_content}"
            )
        else:
            if content_type == 'photo':
                send_method = context.bot.send_photo
            elif content_type == 'video':
                send_method = context.bot.send_video
            elif content_type == 'animation':
                send_method = context.bot.send_animation
            
            sent_message = await send_method(
                GROUP_CHAT_ID,
                content.file_id,
                caption=f"💌 Для @{recipient_username}\n\n{text_content}"
            )

        # Отправляем приглашение как ответ на валентинку
        await context.bot.send_message(
            GROUP_CHAT_ID,
            f"Если тоже хочешь отправить кому-то валентинку, заглядывай в бота: {bot_link}",
            reply_to_message_id=sent_message.message_id
        )

    except BadRequest as e:
        print(f"Ошибка отправки в группу: {e}")

    await update.message.reply_text("✅ Валентинка отправлена! Можешь отправить ещё или посмотреть свои")

def main():
    application = ApplicationBuilder().token('7630794114:AAFxBHG_dFoG8QNhq8dTfeKOrxnE7I9IMbs').build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.VIDEO | filters.ANIMATION,
        handle_message
    ))
    
    application.run_polling()

if __name__ == '__main__':
    main()
