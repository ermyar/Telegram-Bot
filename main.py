import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ErrorEvent
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import db
import dv_sys
import constants
from user import User

token = db.get_token()

bot = Bot(token, parse_mode=ParseMode.HTML)
dp = Dispatcher()


class RegStates(StatesGroup):
    default_state = State()
    get_name = State()
    get_age = State()
    get_description = State()
    get_photo = State()


@dp.error()
async def errors_handler(event: ErrorEvent):
    await bot.send_message(constants.admin_group, f'Ошибка при обработке запроса {event.update}\n\n{event.exception}')


@dp.message(Command('del'))
async def del_user(message: Message, state: FSMContext):
    await state.clear()
    if message.chat.id != constants.admin_group:
        return
    data = message.text.split()
    if len(data) != 2:
        return message.answer('Неверный формат: \n'
                              '/del id')
    if not data[1].isdigit():
        return message.answer('Неверный формат: \n'
                              '/del id')
    user_id = int(data[1])
    await db.delete_user(user_id)
    await message.answer('Анкета успешно удалена')
    try:
        await bot.send_message(user_id, constants.del_text)
    except TelegramAPIError:
        pass


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext):
    if message.from_user.username is None:
        return message.answer(constants.no_username_text)
    user = await db.get_user(message.from_user.id)
    if user is None:
        await state.set_state(RegStates.get_name)
        return await message.answer(constants.start_reg_text)
    await main_menu(message)


@dp.message(StateFilter(RegStates.get_name))
async def get_name(message: Message, state: FSMContext):
    await delete_messages(message)
    if len(message.text) > 15:
        return await message.answer('Имя слишком длинное. Попробуй ещё раз')
    await state.update_data({'name': message.text})
    await state.set_state(RegStates.default_state)
    await message.answer('Кто ты?', reply_markup=constants.sex_kb.as_markup())


@dp.message(StateFilter(RegStates.get_age))
async def get_age(message: Message, state: FSMContext):
    await delete_messages(message)
    state_data = await state.get_data()
    if 'name' not in state_data.keys():
        await state.set_state(RegStates.get_name)
        return await message.answer(constants.start_reg_text)
    if not message.text.isdigit():
        return await message.answer('Пожалуйста, введи только цифру')
    await state.update_data({'age': int(message.text)})
    await state.set_state(RegStates.default_state)
    await message.answer('Где ты живёшь?', reply_markup=constants.place_kb.as_markup())


@dp.message(StateFilter(RegStates.get_description))
async def get_description(message: Message, state: FSMContext):
    await delete_messages(message)
    state_data = await state.get_data()
    if 'name' not in state_data.keys():
        await state.set_state(RegStates.get_name)
        return await message.answer(constants.start_reg_text)
    await state.update_data({'description': message.text})
    await state.set_state(RegStates.get_photo)
    await message.answer(constants.photo_text)


@dp.message(F.photo, StateFilter(RegStates.get_photo))
async def get_photo(message: Message, state: FSMContext):
    await delete_messages(message)
    state_data = await state.get_data()
    if 'name' not in state_data.keys():
        await state.set_state(RegStates.get_name)
        return await message.answer(constants.start_reg_text)
    photo = message.photo[-1].file_id
    await state.update_data({'photo': photo})
    await state.set_state(RegStates.default_state)
    state_data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username
    name = state_data['name']
    age = state_data['age']
    place = state_data['place']
    sex = state_data['sex']
    searching_for = state_data['search']
    description = state_data['description']
    user = User(user_id, username, name, age, photo, description, place, sex, searching_for)
    await db.save_user(user)
    text = await dv_sys.get_profile(user_id)
    await message.answer_photo(photo, caption=text)
    await message.answer('Так выглядит твой профиль. Теперь можно приступать к поиску',
                         reply_markup=constants.reg_end_kb.as_markup())

 
@dp.callback_query(StateFilter(RegStates))
async def reg_callback(call: CallbackQuery, state: FSMContext):
    data = call.data
    message = call.message
    state_data = await state.get_data()
    if 'name' not in state_data.keys():
        await state.set_state(RegStates.get_name)
        return await message.answer(constants.start_reg_text)

    if data in ('sex_1', 'sex_2'):
        sex = int(data.removeprefix('sex_'))
        await state.update_data({'sex': sex})
        await message.edit_text('Кого ты хочешь найти?',
                                reply_markup=constants.search_for_kb.as_markup())

    elif data in ('search_1', 'search_2', 'search_3'):
        search = int(data.removeprefix('search_'))
        await state.update_data({'search': search})
        await state.set_state(RegStates.get_age)
        await message.edit_text('Сколько тебе лет?')

    elif data.startswith('living_'):
        place = int(data.removeprefix('living_'))
        await state.update_data({'place': place})
        await state.set_state(RegStates.get_description)
        await message.edit_text('Расскажи о себе. Чем увлекаешься, что ищешь?')

    elif data == 'again':
        await delete_messages(call.message)
        await db.delete_user(call.from_user.id)
        await state.set_state(RegStates.get_name)
        await message.answer('Как тебя зовут?')

    elif data == 'search':
        await state.clear()
        await delete_messages(message)
        await search_profile(call.from_user.id, message)


@dp.callback_query()
async def callback(call: CallbackQuery, state: FSMContext):
    data = call.data
    message = call.message

    user = await db.get_user(call.from_user.id)
    if user is None:
        await state.set_state(RegStates.get_name)
        return await message.answer(constants.start_reg_text)

    if data == 'my_profile':
        await message.delete()
        text = await dv_sys.get_profile(call.from_user.id)
        photo = await db.get_photo(call.from_user.id)
        await message.answer_photo(photo, caption=constants.profile_text.format(text),
                                   reply_markup=constants.profile_kb.as_markup())

    elif data == 'again':
        await message.delete()
        await db.delete_user(call.from_user.id)
        await state.set_state(RegStates.get_name)
        await message.answer('Как тебя зовут?')

    elif data == 'delete_profile':
        await message.delete()
        await db.delete_user(call.from_user.id)
        await message.answer('Надеюсь, ты нашёл то, что искал.'
                             ' Возвращайся, если станет скучно',
                             reply_markup=constants.delete_profile_kb.as_markup())

    elif data == 'search':
        await message.delete()
        has_like = await check_likes(call.from_user.id, call.message)
        if has_like:
            return
        await search_profile(call.from_user.id, message)

    elif data == 'sleep':
        await message.delete()
        await main_menu(message)

    elif data.startswith('like_'):
        await message.delete()
        to_id = int(data.removeprefix('like_'))
        await db.add_like(call.from_user.id, to_id)
        await db.add_watched(call.from_user.id, to_id)
        try:
            await bot.send_message(to_id, 'Кому-то понравилась твоя анкета!',
                                   reply_markup=constants.watch_likes_kb.as_markup())
        except TelegramAPIError:
            pass
        has_like = await check_likes(call.from_user.id, call.message)
        if has_like:
            return
        await search_profile(call.from_user.id, message)

    elif data.startswith('skip_'):
        await message.delete()
        to_id = int(data.removeprefix('skip_'))
        await db.add_watched(call.from_user.id, to_id)
        has_like = await check_likes(call.from_user.id, call.message)
        if has_like:
            return
        await search_profile(call.from_user.id, message)

    elif data.startswith('report_'):
        await message.delete()
        to_id = int(data.removeprefix('report_'))
        await db.add_watched(call.from_user.id, to_id)
        text = await dv_sys.get_profile(to_id)
        photo = await db.get_photo(to_id)
        await bot.send_photo(constants.admin_group, photo, caption=constants.report_text.format(text, to_id, to_id))
        has_like = await check_likes(call.from_user.id, call.message)
        if has_like:
            return
        await search_profile(call.from_user.id, message)

    elif data.startswith('ans_'):
        act, from_id = data.removeprefix('ans_').split('_')
        from_id = int(from_id)
        await db.del_like(from_id, call.from_user.id)
        await message.delete()
        await db.add_watched(call.from_user.id, from_id)
        if act == 'like':
            from_user = await db.get_user(from_id)
            to_user = await db.get_user(call.from_user.id)
            await message.answer(constants.ans_like_text.format(from_user[1], from_user[2]),
                                 disable_web_page_preview=True)
            try:
                await bot.send_message(from_id, constants.mutual_like_text.format(to_user[1], to_user[2]),
                                       disable_web_page_preview=True)
            except TelegramAPIError:
                pass
        elif act == 'report':
            text = await dv_sys.get_profile(from_id)
            photo = await db.get_photo(from_id)
            await bot.send_photo(constants.admin_group, photo, constants.report_text.format(text, from_id, from_id))
        has_like = await check_likes(call.from_user.id, call.message)
        if has_like:
            return
        await search_profile(call.from_user.id, message)


async def main_menu(message: Message):
    await message.answer(constants.main_menu_text,
                         reply_markup=constants.main_menu_kb.as_markup())


async def check_likes(user_id: int, message: Message):
    from_user = await db.get_like(user_id)
    if from_user is None:
        return 0
    from_user = from_user[0]
    text = await dv_sys.get_profile(from_user)
    photo = await db.get_photo(from_user)
    await message.answer_photo(photo, caption='<b>Кто-то тобой заинтересовался!!</b>\n\n' + text,
                               reply_markup=constants.ans_kb(from_user).as_markup())
    return 1


async def search_profile(user_id: int, message: Message):
    user = User(*(await db.get_user(user_id))[:-1])
    profile_id = await dv_sys.find_random_profile(user)
    if profile_id == -1:
        kb = InlineKeyboardBuilder()
        kb.button(text='Главное меню', callback_data=f'sleep')
        return await message.answer('Больше не осталось анкет. Приходи завтра', reply_markup=kb.as_markup())
    text = await dv_sys.get_profile(profile_id)
    photo = await db.get_photo(profile_id)
    await message.answer_photo(photo,
                               caption=text,
                               reply_markup=constants.react_kb(profile_id).as_markup())


async def delete_messages(message: Message):
    try:
        await message.delete()
    except TelegramAPIError:
        pass
    try:
        await bot.delete_message(message.chat.id, message.message_id-1)
    except TelegramAPIError:
        pass


async def new_day():
    await db.clear_watched()


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(new_day, 'cron', hour=4, minute=0)
    scheduler.start()
    await db.start_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    asyncio.run(main())
