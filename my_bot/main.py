import asyncio
import io
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters.command import CommandStart
from aiogram.enums import ParseMode
from aiogram.utils import markdown
from aiogram.types import CallbackQuery
import random
from config_reader import settings
from init_db import initialize
from models.database import service
from recognize_speech import VOICE_INPUT_FILE, AssistantAI
from keyboards import (
    build_actions_kb
)
from yandex_meteo import get_weather
from utils.logger import get_logger

logger = get_logger("main")
bot: Bot = Bot(token=settings.BOT_TOKEN.get_secret_value())

router: Router = Router()
ai_assistant = AssistantAI()

last_letters = {}


@router.message(CommandStart())
async def handle_start(message: types.Message):
    url = "https://w7.pngwing.com/pngs/547/380/png-transparent-robot-waving-hand-bot-ai-robot-thumbnail.png"
    logger.info(f"Пользователь {message.from_user} подключиля к боту")
    await message.answer(
        text=f"{markdown.hide_link(url)}Hello, {markdown.hbold(message.from_user.full_name)}!",
        parse_mode=ParseMode.HTML,
        reply_markup=build_actions_kb(),
    )


@router.callback_query(F.data == 'help')
async def handle_help(call: CallbackQuery):
    logger.info(f"Пользователь {call.message.from_user} воспользовался помошью бота")
    user_data = call.from_user
    help_text = (
        f"Привет, {user_data.first_name}! 😊\n\n"
        "Этот бот умеет многое! Вот что он может для вас:\n\n"
        "1. <b>Текст из голосовых сообщений:</b> Просто отправьте голосовое сообщение, и бот автоматически преобразует его в текст.\n"
        "2. <b>Выдавать информацию о прогнозе погоды:</b> на сегодня и на завтра, для чего воспользуйтесь кнопкой снизу Погода.\n"
        "3. <b>Игра в городки:</b> Вы можете играть в игру в города с ботом! Просто начните игру, и бот будет называть города.\n"
        "4. <b>Прерывание игры:</b> Если вы захотите закончить игру в города, просто отправьте команду /finish.\n\n"
        "Чтобы начать, просто отправьте голосовое сообщение или начните игру в города, и наслаждайтесь общением с ботом!\n"
    )
    await call.message.answer(
        help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=build_actions_kb(),
    )


@router.callback_query(F.data == 'about')
async def about(callback: CallbackQuery):
    logger.info(f"Пользователь {callback.message.from_user} выбрал просмотр всплывающего сообщения о боте")
    await bot.answer_callback_query(
        callback.id,
        text='Привет! Я бот, который умеет преобразовать голосовое сообщение в текст, '
             'а еще я умею играть в городки.',
        show_alert=True
    )


@router.callback_query(F.data == 'voice')
async def voice_message_handler(callback_query: CallbackQuery):
    """"""
    await callback_query.message.reply("Пожалуйста, отправьте Ваше голосовое сообщение")


# Обработчик голосовых сообщений
@router.message(F.content_type == "voice")
async def voice_message_handler(message: types.Message, bot: Bot):
    """Handle voice input"""
    logger.info(f"Пользователь {message.from_user} отправил голосовое сообщение для преобразования в текст")
    voice_file = await bot.get_file(message.voice.file_id)
    processing_msg = await message.reply("Пожалуйста подождите, обрабатывается Ваше голосовое сообщение...")
    voice_ogg = io.BytesIO()
    await bot.download_file(voice_file.file_path, voice_ogg)
    with open(f"{str(message.from_user.id)}_{VOICE_INPUT_FILE}", "wb") as new_file:
        new_file.write(voice_ogg.getvalue())

    try:
        voice_response = ai_assistant.create_response_from_voice(message.from_user.id)
    except Exception as err:
        await message.reply("Извините, произошла ошибка при обращении к сервису распознавания речи.")
        return
    await processing_msg.delete()
    logger.info(f"Бот отправил пользователю {message.from_user} преобразованный в текст сообщение")

    await message.reply(voice_response)


@router.callback_query(F.data == 'play')
async def play(call: CallbackQuery):
    """
    Выбрана игра с выбором игрока.
    """
    logger.info(f"Пользователь {call.message.from_user} начал игру с ботом")
    chat_id = call.message.chat.id
    await call.answer()
    await call.message.answer("Правила игры:")
    await call.message.answer(
        parse_mode=ParseMode.HTML,
        text=(
            "<b>Игра в города - это игра, в которой игрок называет город.</b>\n"
            "А второй игрок называет город начинающийся с последней буквы предыдущего названного города."
            "Первым игроком будет тот, кто выбран с помощью клавиатуры ниже."
            "Команда <b>/finish</b> завершает игру.\n"
            "<b>Приятной игры!</b>"
        ).strip()
    )
    cities_dict = await service.get_cities()
    litter = random.choice(list(cities_dict.keys()))
    if chat_id not in last_letters:
        last_letters[chat_id] = cities_dict
    last_letters[chat_id]["letter"] = litter
    await bot.send_message(
        chat_id,
        text='Начинаем игру! Пожалуйста, напишите город начинающий '
             'с буквы "<b>{}</b>"'.format(litter.upper()),
        parse_mode=ParseMode.HTML,
    )


@router.message()
async def echo(message: types.Message):
    chat_id = message.chat.id
    text = message.text.strip().lower()
    first_letter = text[0]
    if message.text != "/finish":
        if last_letters[chat_id]["letter"] == first_letter:

            chat_cities = last_letters[chat_id]
            last_letter = text[-1]
            cities_for_fist_letter = chat_cities.get(first_letter, [])

            if text in cities_for_fist_letter:  # Проверяем, есть ли введенный пользователем город в списке городов на первую букву
                cities_for_last_letter = chat_cities.get(last_letter,
                                                         [])  # Получаем список городов на последнюю букву предыдущего города
                if cities_for_last_letter:  # Проверяем, есть ли города на последнюю букву
                    bot_city = cities_for_last_letter[-1]  # Бот выбирает город на последнюю букву

                    if bot_city == text:  # Проверяем, был ли этот город уже назван ботом
                        await message.answer('Этот город уже был назван. Пажалуйста, попробуйте другой.')
                    else:
                        cities_for_fist_letter.remove(text)  # Удаляем выбранный пользователем город из списка
                        chat_cities[
                            first_letter] = cities_for_fist_letter  # Обновляем список городов на первую букву в chat_cities
                        cities_for_last_letter.remove(bot_city)  # Удаляем выбранный ботом город из списка
                        chat_cities[last_letter] = cities_for_last_letter
                        last_letters[chat_id]["letter"] = bot_city[-1]
                        await bot.send_message(
                            chat_id,
                            'Отлично. Мой город <b>"{}"</b>. Пожалуйста, напишите город на букву <b>"{}"</B>'.format(
                                bot_city.capitalize(), bot_city[-1].upper()),
                            parse_mode=ParseMode.HTML,
                        )
                else:
                    await message.answer(
                        'Я не знаю такого города на последнюю букву предыдущего города. Пожалуйста, попробуйте еще раз.'
                    )
            else:
                await message.answer(
                    'Я не знаю такого города или он уже был назван. Пожалуйста, попробуйте еще раз.'
                )


        else:
            await message.answer(
                text=f'Пожалуйста, введите город начинающийся с <b>{last_letters[chat_id]["letter"].upper()}</b>.',
                parse_mode=ParseMode.HTML,
            )
    else:
        if chat_id in last_letters:
            del last_letters[chat_id]  # Удалить список городов для данного чата
            await message.answer(
                'Игра завершена. Пожалуйста, начните новую игру.',
                reply_markup=build_actions_kb()
            )
        else:
            await message.answer('В данный момент нет активной игры.')


@router.callback_query(F.data == 'weather')
async def handle_weather(call: CallbackQuery):
    logger.info(f"Пользователь {call.message.from_user} запросил прогноз погоды")
    current_weather_message, tomorrow_weather_message = await get_weather()
    await call.message.answer(
        f"<b>Погода на сегодня</b>\n{current_weather_message}\n\n"
        f"<b>Погода на завтра</b>\n{tomorrow_weather_message}",
        parse_mode=ParseMode.HTML,
    )


async def main():
    await initialize()
    logger.info(f" Произведена инициализация базы")
    dp: Dispatcher = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logger.info(f" Бот запущен")
    asyncio.run(main())
