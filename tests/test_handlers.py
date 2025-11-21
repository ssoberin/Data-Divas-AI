import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import Update, Message, User
import sys
sys.path.insert(0, r'C:\\Users\\Honor\\PycharmProjects3Data_Divas_AI')
from handlers import start, about, help_handler, reset, handle_message

pytestmark = pytest.mark.asyncio # все тесты здесь - асинхронные


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.effective_user = MagicMock(spec=User)
    update.effective_user.first_name = "test_user"
    return update


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.user_data = {}
    return context


async def test_start_command(mock_update, mock_context):
    await start(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()

    actual_text = mock_update.message.reply_text.call_args[0][0]
    expected_text = (
        f"Здравствуй, test_user!\n\n"
        f"Я - Data_Divas_AI, телеграмм-бот с искусственным интеллектом\n"
        f"Чем могу помочь?"
    )

    assert actual_text == expected_text


async def test_about_command(mock_update, mock_context):
    await about(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()

    actual_text = mock_update.message.reply_text.call_args[0][0]
    expected_text = (
        "Я - Data_Divas_AI, бот с искусственным интеллектом, который может"
        "беседовать, генерировать текст или отвечать на вопросы "
    )

    assert actual_text == expected_text


async def test_help_handler(mock_update, mock_context):
    await help_handler(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()

    call_args = mock_update.message.reply_text.call_args
    actual_text = call_args[0][0]
    parse_mode = call_args[1].get('parse_mode')

    expected_text = (
        "Список доступных команд:\n\n"
        "/start - начать общение с ботом\n"
        "/about - получить информацию о боте\n"
        "/reset - очистить контекст общения\n"
        "/help - показать это сообщение\n\n"
        'Остались вопросы? Ты можешь написать администратору бота - <a href="https://t.me/ssoberin">@ssoberin</a>'
    )

    assert actual_text == expected_text
    assert parse_mode == "HTML"


async def test_reset_with_context(mock_update, mock_context):
    mock_context.user_data['conversation_context'] = [
        {"role": "user", "content": "Привет, как дела?"},
        {"role": "assistant", "content": "Привет! У меня всё отлично!"},
        {"role": "user", "content": "Что ты умеешь?"},
        {"role": "assistant", "content": "Я могу отвечать на вопросы..."}
    ]

    await reset(mock_update, mock_context)
    assert mock_context.user_data['conversation_context'] == []

    mock_update.message.reply_text.assert_called_once_with("Контекст диалога сброшен")


async def test_reset_command_without_context(mock_update, mock_context):
    mock_context.user_data = {}

    await reset(mock_update, mock_context)
    assert 'conversation_context' not in mock_context.user_data

    mock_update.message.reply_text.assert_called_once_with("Контекст диалога сброшен")


async def test_handle_message(mock_update, mock_context):
    mock_update.message.text = "короткое сообщение с блин"
    print("starting test_handle_message")

    with patch('functions.is_banned', return_value=False) as mock_banned, \
            patch('functions.bad_words', return_value="") as mock_bad_words, \
            patch('functions.get_user_context', return_value=[]) as mock_get_context, \
            patch('functions.generate_response', return_value="Тестовый ответ") as mock_generate, \
            patch('functions.update_user_context') as mock_update_context, \
            patch('functions.logger'):
        mock_processing = AsyncMock()
        mock_processing.delete = AsyncMock()
        mock_update.message.reply_text.return_value = mock_processing

        await handle_message(mock_update, mock_context)

        print(f"is_banned called: {mock_banned.called}")
        print(f"bad_words called: {mock_bad_words.called}")
        print(f"get_user_context called: {mock_get_context.called}")
        print(f"generate_response called: {mock_generate.called}")
        print(f"update_user_context called: {mock_update_context.called}")

        calls = mock_update.message.reply_text.call_args_list
        print(f"reply_text called {len(calls)} раз:")
        for i, call in enumerate(calls):
            print(f"  {i + 1}. {call[0][0]}")
