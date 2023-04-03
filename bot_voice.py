import asyncio
import logging
import os
import random
import string
import configparser
from io import BytesIO

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from aiogram.utils import executor

from change_voice import change_voice

# Чтение файла конфигурации
config = configparser.ConfigParser()
config.read('config.ini')

# Получение API_TOKEN из файла конфигурации
API_TOKEN = config.get('telegram', 'api_token')

logging.basicConfig(level=logging.INFO)


class VoiceBot:
    def __init__(self, api_token):
        self.bot = Bot(token=api_token)
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())
        self.dp.middleware.setup(LoggingMiddleware())

    @staticmethod
    def random_string(length):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    async def on_start(self, message: types.Message):
        keyboard = types.InlineKeyboardMarkup()
        orc_button = types.InlineKeyboardButton(text='Орк', callback_data='orc')
        elf_button = types.InlineKeyboardButton(text='Эльф', callback_data='elf')
        keyboard.add(orc_button, elf_button)

        await message.reply('Выберите голос для преобразования:\nОрк или Эльф', reply_markup=keyboard)

    async def on_callback_query(self, callback_query: types.CallbackQuery, state: FSMContext):
        voice_type = callback_query.data
        await state.update_data(voice_type=voice_type)
        await self.bot.answer_callback_query(callback_query.id)
        await self.bot.send_message(callback_query.from_user.id,
                                    f'Выбран голос {voice_type}. Отправьте голосовое сообщение.')

    async def on_voice_message(self, message: types.Message, state: FSMContext):
        user_data = await state.get_data()
        if not user_data:
            await message.reply('Пожалуйста, сначала выберите голос (Орк или Эльф) с помощью команды /start.')
            return

        voice_type = user_data['voice_type']
        voice = message.voice

        input_filename = f'input_voice_{self.random_string(8)}.wav'
        await voice.download(destination_file=input_filename)

        await asyncio.sleep(5)  # Задержка 5 секунд
        processing_message = await message.reply('Подождите, ваш файл обрабатывается...')

        output_filename = f'output_voice_{self.random_string(8)}.wav'
        change_voice(input_filename, output_filename, voice_type=voice_type)

        await self.bot.delete_message(message.chat.id, processing_message.message_id)
        os.remove(input_filename)

        with BytesIO() as file:
            # Чтение данных из файла output_filename
            with open(output_filename, 'rb') as output_file:
                audio_data = output_file.read()

            file.write(audio_data)
            file.seek(0)

            # Удаление предыдущей инлайн-кнопки
            if 'previous_message_id' in user_data:
                await self.bot.edit_message_reply_markup(chat_id=message.chat.id,
                                                         message_id=user_data['previous_message_id'], reply_markup=None)

            # Запоминаем ID текущего сообщения с инлайн-кнопкой
            keyboard = types.InlineKeyboardMarkup()
            menu_button = types.InlineKeyboardButton(text='Вернуться в меню выбора голоса',
                                                     callback_data='back_to_menu')
            keyboard.add(menu_button)
            sent_message = await message.reply_voice(file, reply_markup=keyboard)
            await state.update_data(previous_message_id=sent_message.message_id)

        os.remove(output_filename)
        await state.update_data(previous_message_id=sent_message.message_id)

    async def on_back_to_menu(self, callback_query: types.CallbackQuery):
        await self.on_start(callback_query.message)

    def run(self):
        self.dp.register_message_handler(self.on_start, commands=['start'])
        self.dp.register_callback_query_handler(self.on_callback_query, lambda c: c.data in ['orc', 'elf'])
        self.dp.register_message_handler(self.on_voice_message, content_types=[types.ContentType.VOICE])
        self.dp.register_callback_query_handler(self.on_back_to_menu, lambda c: c.data == 'back_to_menu')

        executor.start_polling(self.dp, skip_updates=True)

if __name__ == '__main__':
    voice_bot = VoiceBot(API_TOKEN)
    voice_bot.run()

