from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from openai import OpenAI, APITimeoutError
from settings import token, api_key, admin_id
import logging
from telegram import Bot
from datetime import datetime


client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=api_key
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def generate_response(prompt: str, user_context: list):
    try:
        messages = user_context
        messages.append({"role": "user", "content": prompt})
        engine = "qwen/qwen3-235b-a22b-2507"
        completion = client.chat.completions.create(
            model=engine,
            messages=messages,
            max_tokens=3000,
            temperature=0.7,
            timeout=2
        )
        response = completion.choices[0].message.content
        logger.info(f"AI answer is generated: {response[:50]}...")
        return response
    except APITimeoutError:
        logger.info(f"Request timed out! The user is notified to repeat the request.")
        return "Ответ от AI занял много времени. Попробуй ввести свой запрос еще раз"

def update_user_context(context: ContextTypes.DEFAULT_TYPE, user_message: str, ai_response: str):
    try:
        if 'conversation_context' not in context.user_data:
            context.user_data['conversation_context'] = []
        conversation = context.user_data['conversation_context']
        conversation.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_response}
        ])
        if len(conversation) > 6:
            context.user_data['conversation_context'] = conversation[-6:]
    except Exception as e:
        logger.error(f"Error in updating user context: {e}")

def get_user_context(context: ContextTypes.DEFAULT_TYPE):
    try:
        return context.user_data.get('conversation_context', [])
    except Exception as e:
        logger.error(f"Error in getting user context: {e}")
        return []

banned_users = set()
user_warnings = {}

def bad_words(user, message):
    user_id = user.id
    if user_id not in user_warnings:
        user_warnings[user_id] = 0

    bad_words_found = []

    with open("words.txt", "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and stripped.lower() in message.lower():
                bad_words_found.append(stripped)

    if bad_words_found:
        user_warnings[user_id] += 1
        warnings = user_warnings[user_id]

        if warnings >= 3:
            ban(user)
            return "banned"
        else:
            return (f"Не говори при мне нецензурные слова! "
                    f"\n\nДаю тебе предупреждение {warnings}/3. "
                    f"При 3 предупреждениях - бан!")

    return ""

def ban(user):
    user_id = user.id
    banned_users.add(user_id)

    logging.info(f"User {user.first_name} (id: {user_id}) is banned")

    with open("banned_users.txt", "a", encoding="utf-8") as f:
        f.write(f"{user_id},{user.first_name},{datetime.now()}\n")

def is_banned(user):
    return user.id in banned_users