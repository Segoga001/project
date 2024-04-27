from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_actions_kb() -> InlineKeyboardMarkup:
    """
    Инлайн клавиатура для бота.
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Помощь',
        callback_data='help',
    )
    builder.button(
        text='Голос',
        callback_data='voice',
    )
    builder.button(
        text='Игра',
        callback_data='play',
    )

    builder.button(
        text='Погода',
        callback_data='weather'
    )


    builder.button(
        text='О боте',
        callback_data='about'
    )

    return builder.as_markup()
