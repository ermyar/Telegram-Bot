from aiogram.utils.keyboard import InlineKeyboardBuilder

admin_group = -4028842519

profile_template = '''{}, {}, {} - {}'''

places = [0, "Кампус", "Своя квартира"]

no_username_text = ('Привет! Чтобы бот работал,'
                    ' у тебя должен быть @username.'
                    ' Добавь его и возвращайся скорее!')

start_reg_text = ('Привет! Это бот для знакомств Физтеха.'
                  ' Давай начнём! как мне к тебе обращаться?')

photo_text = 'Теперь отправь своё фото. Пока максимум 1, но скоро можно будет больше!'

profile_text = '''Вот твоя анкета:

{}

🔄 - Заполнить анкету заново'
❌ - Удалить анкету'''

ans_like_text = ('Отлично! Надеюсь, вы хорошо проведёте время.'
                 ' Начинайте общаться 👉 '
                 '<a href="https://t.me/{}">{}</a>')

mutual_like_text = ('Есть взаимная симпатия! '
                    'Начинайте общаться 👉 '
                    '<a href="https://t.me/{}">{}</a>')

main_menu_text = '''Привет. Выбери действие по кнопке под сообщением'''

report_text = """Новая жалоба на пользователя

{}

<code>/del {}</code> - удалить анкету пользователя"""

del_text = ('Ваша анкета была удалена за нарушение правил пользования ботом.'
            ' Вы можете заполнить её заново, но на этот раз не нарушайте правила!')

main_menu_kb = InlineKeyboardBuilder()
main_menu_kb.button(text='👤 Мой профиль', callback_data='my_profile')
main_menu_kb.button(text='🔎 Поиск', callback_data='search')

sex_kb = InlineKeyboardBuilder()
sex_kb.button(text='Парень', callback_data='sex_1')
sex_kb.button(text='Девушка', callback_data='sex_2')

place_kb = InlineKeyboardBuilder()
place_kb.button(text='Кампус', callback_data='living_1')
place_kb.button(text='Своя квартира', callback_data='living_4')
place_kb.adjust(1, 1)

reg_end_kb = InlineKeyboardBuilder()
reg_end_kb.button(text='Заполнить заново', callback_data='again')
reg_end_kb.button(text='Поиск', callback_data='search')

search_for_kb = InlineKeyboardBuilder()
search_for_kb.button(text='Парня', callback_data='search_1')
search_for_kb.button(text='Девушку', callback_data='search_2')
search_for_kb.button(text='Не важно', callback_data='search_3')
search_for_kb.adjust(2, 1)

profile_kb = InlineKeyboardBuilder()
profile_kb.button(text='🔄', callback_data='again')
profile_kb.button(text='❌', callback_data='delete_profile')
profile_kb.button(text='Назад', callback_data='sleep')
profile_kb.adjust(2, 1)

delete_profile_kb = InlineKeyboardBuilder()
delete_profile_kb.button(text='Создать анкету', callback_data='again')

watch_likes_kb = InlineKeyboardBuilder()
watch_likes_kb.button(text='Посмотреть', callback_data='search')


def ans_kb(from_user: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text='❤️', callback_data=f'ans_like_{from_user}')
    kb.button(text='💔', callback_data=f'ans_skip_{from_user}')
    kb.button(text='😴', callback_data=f'sleep')
    kb.button(text='⚠️', callback_data=f'ans_report_{from_user}')
    kb.adjust(4)
    return kb


def react_kb(profile_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text='❤️', callback_data=f'like_{profile_id}')
    kb.button(text='💔', callback_data=f'skip_{profile_id}')
    kb.button(text='😴', callback_data=f'sleep')
    kb.button(text='⚠️', callback_data=f'report_{profile_id}')
    kb.adjust(4)
    return kb
