from dead_simple_telegram import TelegramConfig


def test_from_dict_defaults():
    config = TelegramConfig.from_dict({"bot_token": "x", "chat_id": "y"})
    assert config.bot_token == "x"
    assert config.chat_id == "y"
    assert config.timeout == 10
