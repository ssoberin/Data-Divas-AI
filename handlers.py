from functions import *


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Здравствуй, {update.effective_user.first_name}!\n\nЯ - Data_Divas_AI, телеграмм-бот с искусственным интеллектом"
        f"\nЧем могу помочь?")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я - Data_Divas_AI, бот с искусственным интеллектом, который может"
                                    "беседовать, генерировать текст или отвечать на вопросы ")

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Список доступных команд:\n\n"
        "/start - начать общение с ботом\n"
        "/about - получить информацию о боте\n"
        "/reset - очистить контекст общения\n"
        "/help - показать это сообщение\n\n"
        'Остались вопросы? Ты можешь написать администратору бота - <a href="https://t.me/ssoberin">@ssoberin</a>'
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'conversation_context' in context.user_data:
        context.user_data['conversation_context'] = []
    await update.message.reply_text("Контекст диалога сброшен")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message.text
    logger.info(f"Message from {user.id}: {user_message[:20]}...")

    if is_banned(user):
        await update.message.reply_text("Вы заблокированы и не можете отправлять сообщения.")
        logger.info(f"Banned user {user.id} tried to request a bot")
        return

    warning_text = bad_words(user, user_message)

    if warning_text == "banned":
        await update.message.reply_text("Вы получили 3 предупреждения и были заблокированы!")
        return
    elif warning_text:
        await update.message.reply_text(warning_text)
        return

    if len(user_message) > 2000:
        await update.message.reply_text("Сообщение слишком длинное. Максимум 2000 символов.")
        return

    processing_msg = await update.message.reply_text("⏳ Генерирую ответ...")

    try:
        user_context = get_user_context(context)
        ai_response = generate_response(user_message, user_context)

        try:
            await processing_msg.delete()
        except Exception as e:
            logger.warning(f"Could not delete processing message: {e}")

        if ai_response and not ai_response.startswith("Произошла ошибка"):
            update_user_context(context, user_message, ai_response)

            if len(ai_response) > 1500:
                logger.info(f"Response is laaarge, starting huge work...")
                parts = []
                for i in range(0, len(ai_response), 1500):
                    parts.append(ai_response[i:i + 1500])

                total_parts = len(parts)
                logger.info(f"Prepared {total_parts} parts for sending")

                for part in parts:
                    try:
                        await update.message.reply_text(part.strip())
                        logger.info(f"Successfully sent one of parts")
                    except Exception as e:
                        logger.error(f"Failed to send part {e}")
            else:
                await update.message.reply_text(ai_response)
        else:
            await update.message.reply_text("Не удалось получить ответ от AI. Попробуйте позже.")
            logger.error(f"AI response error: {ai_response}")

    except Exception as e:
        logger.error(f"Error in handling message: {e}")
        await processing_msg.delete()


def main():
    try:
        application = Application.builder().token(token).build()

        mes = MessageHandler(filters.TEXT, handle_message)
        c1 = CommandHandler("start", start)
        c2 = CommandHandler("reset", reset)
        c3 = CommandHandler("about", about)
        c4 = CommandHandler("help", help_handler)
        application.add_handler(c1)
        application.add_handler(c2)
        application.add_handler(c3)
        application.add_handler(c4)
        application.add_handler(mes)

        logger.info("Bot is working...")
        application.run_polling()

    except Exception as e:
        logger.critical(f"Critical error during bot startup: {e}")
        bot = Bot(token=token)
        admin = admin_id
        bot.send_message(admin, f"CRITICAL: Bot failed to start: {e}",parse_mode="HTML")



if __name__ == "__main__":
    main()