from unittest.mock import MagicMock, patch, mock_open
import sys

import os
from pathlib import Path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent

sys.path.insert(0, str(project_root))

from functions import bad_words, ban, is_banned, banned_users, user_warnings


def setup_method():
    banned_users.clear()
    user_warnings.clear()


def test_is_banned_false():
    user = MagicMock()
    user.id = 123

    assert not is_banned(user)


def test_is_banned_true():
    user = MagicMock()
    user.id = 123

    ban(user)

    assert is_banned(user)


def test_ban_user():
    user = MagicMock()
    user.id = 123
    user.first_name = "TestUser"

    with patch('functions.logging') as mock_logging, \
            patch('functions.datetime') as mock_datetime, \
            patch('builtins.open', mock_open()) as mock_file:

        mock_datetime.now.return_value = "2025-11-21 10:30:00"

        ban(user)

        assert user.id in banned_users

        mock_logging.info.assert_called_once_with("User TestUser (id: 123) is banned")

        mock_file.assert_called_once_with("banned_users.txt", "a", encoding="utf-8")
        mock_file().write.assert_called_once_with("123,TestUser,2025-11-21 10:30:00\n")


def test_no_bad_words():
    user = MagicMock()
    user.id = 123

    mock_content = "хей\nхей\n"

    with patch('builtins.open', mock_open(read_data=mock_content)):
        result = bad_words(user, "нормальное сообщение")

        assert result == ""
        assert user_warnings[123] == 0


def test_three_warnings():
    user = MagicMock()
    user.id = 123
    user_warnings[123] = 2

    mock_content = "блин\nблин\n"

    with patch('builtins.open', mock_open(read_data=mock_content)), \
            patch('functions.ban') as mock_ban:
        result = bad_words(user, "сообщение с блин")
        assert result == "banned"

        mock_ban.assert_called_once_with(user)

        assert user_warnings[123] == 3


