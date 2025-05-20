# bot.py

import logging
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.users import GetFullUserRequest
from datetime import datetime
import asyncio

import database as db
import keyboards as kb
import config
import utils

# Настройка логирования
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)

# Данные для подключения к Telegram API
api_id = config.API_ID
api_hash = config.API_HASH

# Создаем клиент Telethon
client = TelegramClient('session_name', api_id, api_hash)

# Состояния для обработки создания задачи
user_states = {}
CREATE_TASK_STATE_NAME = 1
CREATE_TASK_STATE_DESCRIPTION = 2
CREATE_TASK_STATE_DATE = 3
CREATE_TASK_STATE_COST = 4
CREATE_TASK_STATE_USER_ID = 5
ADMIN_STATE_LOWER_RATING_USER_ID = 6
ADMIN_STATE_LOWER_RATING_VALUE = 7

# Состояния для работы с профилями
CREATE_LETTER_STATE_INPUT = 10
CHANGE_DATE_BRING_STATE = 11
CHANGE_DATE_FILL_STATE = 12
CHANGE_DATE_WITH_STATE = 13
CHANGE_STATUS_STATE = 14
REMINDER_DATE_TIME_STATE = 15

# Пагинация задач
TASKS_PER_PAGE = 5
task_pages = {}

# Пагинация букв профиля
LETTERS_PER_PAGE = 5
letter_pages = {}

# ID пользователя, которому отправляем уведомление
NOTIFICATION_USER_ID = 7008792859


# Обработчик команды /start
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    user = await client.get_entity(user_id)
    username = user.username if user.username else 'NONE'
    db.add_user(user_id, username)
    await event.respond('Привет! Используйте меню для управления задачами.', buttons=kb.main_keyboard())


# Обработчик нажатия на кнопку "Создать задание"
@client.on(events.CallbackQuery(pattern='create_task'))
async def create_task(event):
    user_id = event.sender_id
    user_states[user_id] = {'state': CREATE_TASK_STATE_NAME, 'task_data': {}, 'creating_for': 'self'}
    await event.edit('Введите название задания:', buttons=kb.back_to_menu_keyboard())


# Обработчик для кнопки "ДЛЯ АДМИНИСТРАЦИИ"
@client.on(events.CallbackQuery(pattern='admin'))
async def admin_panel(event):
    user_id = event.sender_id
    user = db.get_user(user_id)
    if user and user[3] >= 1:  # Проверяем ранг пользователя (индекс 3 в кортеже user)
        try:
            await event.edit('Панель администратора', buttons=kb.admin_keyboard())
        except Exception as e:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
    else:
        await event.respond('У вас нет прав администратора.', buttons=kb.main_keyboard())


# Обработчики кнопок администратора
@client.on(events.CallbackQuery(pattern='admin_create_task'))
async def admin_create_task(event):
    user_id = event.sender_id
    user_states[user_id] = {'state': CREATE_TASK_STATE_USER_ID, 'task_data': {}, 'creating_for': 'other'}
    await event.edit('Введите ID пользователя, для которого нужно создать задание:',
                     buttons=kb.back_to_admin_keyboard())


@client.on(events.CallbackQuery(pattern='admin_view_user_rating'))
async def admin_view_user_rating(event):
    user_id = event.sender_id
    user_states[user_id] = {'state': 'ADMIN_VIEW_USER_RATING', 'task_data': {}}  # Инициализация task_data
    await event.edit('Введите ID пользователя, чей рейтинг вы хотите посмотреть:', buttons=kb.back_to_admin_keyboard())


@client.on(events.CallbackQuery(pattern='admin_view_user_tasks'))
async def admin_view_user_tasks(event):
    user_id = event.sender_id
    user_states[user_id] = {'state': 'ADMIN_VIEW_USER_TASKS', 'task_data': {}}  # Инициализация task_data
    await event.edit('Введите ID пользователя, чьи невыполненные задачи вы хотите посмотреть:',
                     buttons=kb.back_to_admin_keyboard())


@client.on(events.CallbackQuery(pattern='admin_update_rating'))
async def admin_update_rating(event):
    user_id = event.sender_id
    user_states[user_id] = {'state': 'CONFIRM_UPDATE_RATING', 'task_data': {}}  # Инициализация task_data
    await event.edit('Точно ли вы хотите обновить рейтинг всех пользователей на 100?',
                     buttons=kb.confirmation_keyboard())


@client.on(events.CallbackQuery(pattern='admin_lower_rating'))
async def admin_lower_rating(event):
    user_id = event.sender_id
    user_states[user_id] = {'state': 'ADMIN_STATE_LOWER_RATING_USER_ID', 'task_data': {}}
    await event.edit('Введите ID пользователя, чей рейтинг вы хотите понизить:', buttons=kb.back_to_admin_keyboard())


# Обработчик для ввода ID пользователя для создания задания администратором и просмотра задач
@client.on(events.NewMessage)
async def handle_admin_input(event):
    user_id = event.sender_id
    if user_id in user_states:
        state = user_states[user_id]['state']
        task_data = user_states[user_id].get('task_data', {})

        if state == CREATE_TASK_STATE_USER_ID:
            try:
                task_data['target_user_id'] = int(event.text)
                user_states[user_id]['state'] = CREATE_TASK_STATE_NAME
                await event.respond('Введите название задания:', buttons=kb.back_to_admin_keyboard())
            except ValueError:
                await event.respond('Некорректный ID пользователя. Введите целое число.')

        elif state == CREATE_TASK_STATE_NAME:
            task_data['name'] = event.text
            user_states[user_id]['state'] = CREATE_TASK_STATE_DESCRIPTION
            await event.respond('Введите описание задания:', buttons=kb.back_to_admin_keyboard())

        elif state == CREATE_TASK_STATE_DESCRIPTION:
            task_data['description'] = event.text
            user_states[user_id]['state'] = CREATE_TASK_STATE_DATE
            await event.respond('Введите дату выполнения задания (например, 2024-12-31):',
                                buttons=kb.back_to_admin_keyboard())

        elif state == CREATE_TASK_STATE_DATE:
            task_data['date'] = event.text
            user_states[user_id]['state'] = CREATE_TASK_STATE_COST
            await event.respond('Введите рейтинг важности (целое число):')

        elif state == CREATE_TASK_STATE_COST:
            try:
                task_data['cost'] = int(event.text)
                # Создаем задачу, используя target_user_id, если задача создается администратором
                target_user_id = task_data.get('target_user_id',
                                               user_id)  # Если 'target_user_id' нет, используем user_id
                db.create_task(target_user_id, task_data['name'], task_data['description'], task_data['date'],
                               task_data['cost'])

                # Отправляем уведомление пользователю, для которого создана задача
                if 'target_user_id' in task_data:
                    try:
                        await client.send_message(target_user_id, "У вас новое задание!")
                        task_id = db.get_last_task_id()
                        await event.respond(f'Задание {task_id}, для человека {target_user_id} успешно создано!',
                                            buttons=kb.admin_keyboard())
                    except Exception as e:
                        await event.respond(
                            f'Задание успешно создано, но не удалось отправить уведомление пользователю. Ошибка: {e}',
                            buttons=kb.admin_keyboard())
                else:
                    await event.respond('Задание успешно создано!', buttons=kb.main_keyboard())

                del user_states[user_id]  # Сбрасываем состояние
            except ValueError:
                await event.respond('Некорректный рейтинг. Введите целое число.')

        elif state == 'ADMIN_VIEW_USER_TASKS':
            try:
                target_user_id = int(event.text)
                tasks = db.get_tasks(target_user_id, status=0,
                                     sort_by_cost=True)  # Получаем невыполненные задачи пользователя
                if tasks:
                    # Сохраняем message_id и target_user_id в task_pages
                    result = await display_tasks_page(event, user_id, tasks, target_user_id)
                    if result:
                        task_pages[user_id] = {'tasks': tasks, 'current_page': 0, 'target_user_id': target_user_id,
                                               'message_id': result.id}
                    else:
                        await event.respond("Не удалось отобразить задачи.", buttons=kb.back_to_admin_keyboard())
                else:
                    await event.respond('У пользователя нет невыполненных задач.', buttons=kb.back_to_admin_keyboard())
                del user_states[user_id]
            except ValueError:
                await event.respond('Некорректный ID пользователя. Введите целое число.')
            except KeyError:
                print("KeyError occurred. The 'task_data' key might be missing.")
            except Exception as e:
                logging.error(f"Ошибка при просмотре задач пользователя: {e}")
                await event.respond(f"Произошла ошибка: {e}", buttons=kb.back_to_admin_keyboard())

        elif state == 'ADMIN_VIEW_USER_RATING':
            try:
                target_user_id = int(event.text)
                user = db.get_user(target_user_id)
                if user:
                    rating = user[2]
                    await event.respond(f"Рейтинг пользователя {target_user_id}: {rating}",
                                        buttons=kb.back_to_admin_keyboard())
                else:
                    await event.respond('Пользователь не найден.', buttons=kb.back_to_admin_keyboard())
                del user_states[user_id]
            except ValueError:
                await event.respond('Некорректный ID пользователя. Введите целое число.')
            except KeyError:
                print("KeyError occurred. The 'task_data' key might be missing.")

        elif state == 'ADMIN_STATE_LOWER_RATING_USER_ID':
            try:
                task_data['target_user_id'] = int(event.text)
                user_states[user_id]['state'] = 'ADMIN_STATE_LOWER_RATING_VALUE'
                await event.respond('Введите число, на которое нужно понизить рейтинг:',
                                    buttons=kb.back_to_admin_keyboard())
            except ValueError:
                await event.respond('Некорректный ID пользователя. Введите целое число.')

        elif state == 'ADMIN_STATE_LOWER_RATING_VALUE':
            try:
                rating_decrease = int(event.text)
                target_user_id = task_data.get('target_user_id')
                if not target_user_id:
                    await event.respond('Произошла ошибка: не найден ID пользователя.',
                                        buttons=kb.back_to_admin_keyboard())
                    return

                user = db.get_user(target_user_id)
                if not user:
                    await event.respond('Пользователь не найден.', buttons=kb.back_to_admin_keyboard())
                    return

                current_rating = user[2]  # Текущий рейтинг пользователя
                new_rating = max(0, current_rating - rating_decrease)  # Уменьшаем рейтинг, но не ниже 0
                db.update_user_rating(target_user_id, new_rating)

                await event.respond(
                    f'Рейтинг пользователя {target_user_id} успешно понижен на {rating_decrease}. Новый рейтинг: {new_rating}',
                    buttons=kb.admin_keyboard())
                del user_states[user_id]

            except ValueError:
                await event.respond('Некорректное число. Введите целое число.')
            except Exception as e:
                logging.error(f"Ошибка при понижении рейтинга пользователя: {e}")
                await event.respond(f"Произошла ошибка: {e}", buttons=kb.back_to_admin_keyboard())

        # Обработчики состояний для работы с профилями
        elif state == CREATE_LETTER_STATE_INPUT:
            letter = event.text
            if db.create_profile_letter(letter):
                await event.respond(f'Все отлично, новая буква "{letter}" создана!', buttons=kb.main_keyboard())
            else:
                await event.respond('Эта буква уже существует. Пожалуйста, введите другую букву:',
                                    buttons=kb.back_to_menu_keyboard())
            del user_states[user_id]

        elif state == CHANGE_DATE_BRING_STATE:
            letter = task_data['letter']
            new_date = event.text
            if db.update_profile_field(letter, 'date_bring', new_date):
                await event.respond(f'Дата взятия заданий для буквы "{letter}" успешно изменена!',
                                    buttons=kb.main_keyboard())
            else:
                await event.respond('Ошибка при изменении даты.', buttons=kb.back_to_menu_keyboard())
            del user_states[user_id]

        elif state == CHANGE_DATE_FILL_STATE:
            letter = task_data['letter']
            new_date = event.text
            if db.update_profile_field(letter, 'date_fill', new_date):
                await event.respond(f'Дата ближайшего залива для буквы "{letter}" успешно изменена!',
                                    buttons=kb.main_keyboard())
            else:
                await event.respond('Ошибка при изменении даты.', buttons=kb.back_to_menu_keyboard())
            del user_states[user_id]

        elif state == CHANGE_DATE_WITH_STATE:
            letter = task_data['letter']
            new_date = event.text
            if db.update_profile_field(letter, 'date_with', new_date):
                await event.respond(f'Дата выплаты для буквы "{letter}" успешно изменена!', buttons=kb.main_keyboard())
            else:
                await event.respond('Ошибка при изменении даты.', buttons=kb.back_to_menu_keyboard())
            del user_states[user_id]

        elif state == CHANGE_STATUS_STATE:
            letter = task_data['letter']
            new_status = event.text
            if db.update_profile_field(letter, 'status', new_status):
                await event.respond(f'Статус для буквы "{letter}" успешно изменен!', buttons=kb.main_keyboard())
            else:
                await event.respond('Ошибка при изменении статуса.', buttons=kb.back_to_menu_keyboard())
            del user_states[user_id]

        elif state == REMINDER_DATE_TIME_STATE:
            letter = task_data['letter']
            reminder_time_str = event.text
            try:
                reminder_time = datetime.strptime(reminder_time_str, '%Y-%m-%d %H:%M')
                now = datetime.now()
                if reminder_time <= now:
                    await event.respond("Указанное время уже прошло. Пожалуйста, введите будущее время.",
                                        buttons=kb.back_to_menu_keyboard())
                    return

                delay = (reminder_time - now).total_seconds()
                asyncio.sleep(delay)  # Отправляем напоминание всем пользователям с рангом > 0
                users = db.get_all_users()
                for user_id, rang in users:
                    if rang > 0:
                        try:
                            await client.send_message(user_id, f"Напоминание по букве: {letter}")
                        except Exception as e:
                            logging.error(f"Не удалось отправить напоминание пользователю {user_id}: {e}")
                await event.respond(f'Напоминание для буквы "{letter}" будет отправлено {reminder_time_str}!',
                                    buttons=kb.main_keyboard())
            except ValueError:
                await event.respond('Некорректный формат даты и времени. Используйте формат ГГГГ-ММ-ДД ЧЧ:ММ.',
                                    buttons=kb.back_to_menu_keyboard())
            del user_states[user_id]


# Обработчик подтверждения обновления рейтинга
@client.on(events.CallbackQuery(pattern='confirm'))
async def confirm_action(event):
    user_id = event.sender_id
    if user_id in user_states:
        state = user_states[user_id]['state']
        if state == 'CONFIRM_UPDATE_RATING':
            # Обновляем рейтинг всех пользователей
            db.update_all_ratings(100)
            # Отправляем уведомления всем пользователям
            all_users = db.get_all_users()
            for user in all_users:
                try:
                    await client.send_message(user[0], "Ваш рейтинг обновлен на 100.")
                except Exception as e:
                    logging.error(f"Не удалось отправить уведомление пользователю {user[0]}: {e}")

            await event.respond('Процесс завершен.', buttons=kb.admin_keyboard())
            del user_states[user_id]
        elif user_states[user_id]['state'] == 'CONFIRM_COMPLETION':
            task_id = user_states[user_id]['task_id']
            db.update_task_status(task_id, 1)

            # Отправляем уведомления пользователям с рангом > 0
            task = db.get_task(task_id)
            if task:
                task_name = task[2]  # Название задачи
                users = db.get_all_users()
                for user_id, rang in users:
                    if rang > 0:
                        try:
                            await client.send_message(user_id,
                                                      f"Пользователь {event.sender_id} выполнил задание: {task_name}")
                        except Exception as e:
                            logging.error(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

            # Отправляем уведомление пользователю с ID 7008792859
            try:
                await client.send_message(NOTIFICATION_USER_ID,
                                          f"Пользователь {event.sender_id} выполнил задание {task_id}.")
            except Exception as e:
                logging.error(f"Не удалось отправить уведомление пользователю {NOTIFICATION_USER_ID}: {e}")

            await event.edit('Задача выполнена!', buttons=kb.main_keyboard())
            del user_states[user_id]
        else:
            await event.respond('Произошла ошибка. Попробуйте выполнить задачу еще раз.')
    else:
        await event.respond('Произошла ошибка. Попробуйте выполнить задачу еще раз.')


# Обработчик отказа от обновления рейтинга
@client.on(events.CallbackQuery(pattern='cancel'))
async def cancel_action(event):
    user_id = event.sender_id
    if user_id in user_states:
        state = user_states[user_id]['state']
        if state == 'CONFIRM_UPDATE_RATING':
            await event.edit('Действие отменено.', buttons=kb.admin_keyboard())
            del user_states[user_id]
        elif user_states[user_id]['state'] == 'CONFIRM_COMPLETION':
            del user_states[user_id]
            await event.edit('Действие отменено.', buttons=kb.main_keyboard())
        else:
            await event.respond('Произошла ошибка. Попробуйте выполнить задачу еще раз.')
    else:
        await event.respond('Произошла ошибка. Попробуйте выполнить задачу еще раз.')


# Обработчик нажатия на кнопку "Посмотреть свои задания"
@client.on(events.CallbackQuery(pattern='view_tasks'))
async def view_tasks(event):
    user_id = event.sender_id
    tasks = db.get_tasks(user_id, sort_by_cost=True)
    if not tasks:
        await event.edit('Поздравляем, у вас нет рабочих задач!', buttons=kb.main_keyboard())
    else:
        # Сохраняем message_id и user_id в task_pages
        result = await display_tasks_page(event, user_id, tasks, user_id)
        if result:
            task_pages[user_id] = {'tasks': tasks, 'current_page': 0, 'target_user_id': user_id,
                                   'message_id': result.id}
        else:
            await event.respond("Не удалось отобразить задачи.", buttons=kb.main_keyboard())


async def display_tasks_page(event, user_id, tasks, target_user_id):
    """Отображает страницу задач с пагинацией."""
    try:
        current_page = 0  # Начальная страница
        start_index = current_page * TASKS_PER_PAGE
        end_index = start_index + TASKS_PER_PAGE
        page_tasks = tasks[start_index:end_index]

        if not page_tasks:
            return await event.respond('Нет задач на этой странице.', buttons=kb.main_keyboard())

        buttons = []
        for task in page_tasks:
            buttons.append([Button.inline(task[2], f'task_{task[0]}')])  # task[0] - ID задачи, task[2] - имя задачи

        has_next = end_index < len(tasks)
        has_previous = current_page > 0

        navigation_buttons = kb.task_navigation_keyboard(has_next, has_previous)
        for button_row in navigation_buttons:
            buttons.append(button_row)

        return await event.respond('Вот Ваши рабочие задачи:', buttons=buttons)

    except Exception as e:
        logging.error(f"Ошибка при отображении страницы задач: {e}")
        await event.respond(f"Произошла ошибка: {e}", buttons=kb.main_keyboard())
        return None


# Обработчики для навигации по задачам
@client.on(events.CallbackQuery(pattern='next_page'))
async def next_page(event):
    user_id = event.sender_id
    if user_id in task_pages:
        page_data = task_pages[user_id]
        tasks = page_data['tasks']
        current_page = page_data['current_page']
        if (current_page + 1) * TASKS_PER_PAGE < len(tasks):
            task_pages[user_id]['current_page'] += 1
            message_id = page_data['message_id']
            target_user_id = page_data['target_user_id']
            await edit_tasks_page(event, user_id, tasks, page_data['current_page'], message_id, target_user_id)


@client.on(events.CallbackQuery(pattern='prev_page'))
async def prev_page(event):
    user_id = event.sender_id
    if user_id in task_pages:
        page_data = task_pages[user_id]
        tasks = page_data['tasks']
        current_page = page_data['current_page']
        if current_page > 0:
            task_pages[user_id]['current_page'] -= 1
            message_id = page_data['message_id']
            target_user_id = page_data['target_user_id']
            await edit_tasks_page(event, user_id, tasks, page_data['current_page'], message_id, target_user_id)


async def edit_tasks_page(event, user_id, tasks, current_page, message_id, target_user_id):
    """Редактирует существующее сообщение со списком задач."""
    try:
        start_index = current_page * TASKS_PER_PAGE
        end_index = start_index + TASKS_PER_PAGE
        page_tasks = tasks[start_index:end_index]

        if not page_tasks:
            return await event.edit('Нет задач на этой странице.', buttons=kb.main_keyboard())

        buttons = []
        for task in page_tasks:
            buttons.append([Button.inline(task[2], f'task_{task[0]}')])  # task[0] - ID задачи, task[2] - имя задачи

        has_next = end_index < len(tasks)
        has_previous = current_page > 0

        navigation_buttons = kb.task_navigation_keyboard(has_next, has_previous)
        for button_row in navigation_buttons:
            buttons.append(button_row)

        await client.edit_message(event.chat_id, message_id, 'Вот Ваши рабочие задачи:', buttons=buttons)

    except Exception as e:
        logging.error(f"Ошибка при редактировании страницы задач: {e}")
        await event.respond(f"Произошла ошибка: {e}", buttons=kb.main_keyboard())


# Обработчик нажатия на кнопку с названием задачи (inline button)
@client.on(events.CallbackQuery(pattern='task_'))
async def show_task_details(event):
    task_id = int(event.data.decode().split('_')[1])
    task = db.get_task(task_id)
    if task:
        message = utils.format_task(task)
        await event.edit(message, buttons=kb.task_actions_keyboard(task_id), parse_mode='html')
    else:
        await event.respond('Задача не найдена.')


# Обработчик нажатия на кнопку "ВЫПОЛНИЛ"
@client.on(events.CallbackQuery(pattern='complete_'))
async def confirm_task_completion(event):
    task_id = int(event.data.decode().split('_')[1])
    await event.edit('Вы точно выполнили поставленную задачу?', buttons=kb.confirmation_keyboard())
    user_states[event.sender_id] = {'state': 'CONFIRM_COMPLETION', 'task_id': task_id, 'task_data': {}}


# Обработчик нажатия на кнопку "Личный профиль"
@client.on(events.CallbackQuery(pattern='profile'))
async def show_profile(event):
    user_id = event.sender_id
    user_data = db.get_user(user_id)
    if user_data:
        pending_tasks, completed_tasks = db.get_task_counts(user_id)
        message = (
            f"<b>ID:</b> {user_data[0]}\n"
            f"<b>Рейтинг:</b> {user_data[2]}\n"
            f"<b>Невыполненные задачи:</b> {pending_tasks}\n"
            f"<b>Выполненные задачи:</b> {completed_tasks}"
        )
        await event.edit(message, parse_mode='html', buttons=kb.back_to_menu_keyboard())
    else:
        await event.respond('Профиль не найден. Используйте /start')


# Обработчики для работы с профилями
@client.on(events.CallbackQuery(pattern='profile_work'))
async def profile_work_menu(event):
    await event.edit('Работа с профилями', buttons=kb.profile_work_keyboard())


@client.on(events.CallbackQuery(pattern='create_letter'))
async def create_letter(event):
    user_id = event.sender_id
    user_states[user_id] = {'state': CREATE_LETTER_STATE_INPUT, 'task_data': {}}
    await event.edit('Введите букву для создания:', buttons=kb.back_to_menu_keyboard())


@client.on(events.CallbackQuery(pattern='select_letter'))
async def select_letter(event):
    user_id = event.sender_id
    letters = db.get_all_profile_letters()
    if letters:
        result = await display_letters_page(event, user_id, letters)
        if result:
            letter_pages[user_id] = {'letters': letters, 'current_page': 0, 'message_id': result.id}
        else:
            await event.respond("Не удалось отобразить буквы.", buttons=kb.profile_work_keyboard())
    else:
        await event.respond('Нет доступных букв. Создайте новую букву.', buttons=kb.profile_work_keyboard())


async def display_letters_page(event, user_id, letters):
    """Отображает страницу с буквами профиля."""
    try:
        current_page = 0  # Начальная страница
        start_index = current_page * LETTERS_PER_PAGE
        end_index = start_index + LETTERS_PER_PAGE
        page_letters = letters[start_index:end_index]

        if not page_letters:
            return await event.respond('Нет букв на этой странице.', buttons=kb.profile_work_keyboard())

        buttons = kb.letter_selection_keyboard(letters, current_page, LETTERS_PER_PAGE)

        return await event.respond('Вот все доступные буквы:', buttons=buttons)

    except Exception as e:
        logging.error(f"Ошибка при отображении страницы букв: {e}")
        await event.respond(f"Произошла ошибка: {e}", buttons=kb.profile_work_keyboard())
        return None


@client.on(events.CallbackQuery(pattern='next_letter_page'))
async def next_letter_page(event):
    user_id = event.sender_id
    if user_id in letter_pages:
        page_data = letter_pages[user_id]
        letters = page_data['letters']
        current_page = page_data['current_page']
        if (current_page + 1) * LETTERS_PER_PAGE < len(letters):
            letter_pages[user_id]['current_page'] += 1
            message_id = page_data['message_id']
            await edit_letters_page(event, user_id, letters, page_data['current_page'], message_id)


@client.on(events.CallbackQuery(pattern='prev_letter_page'))
async def prev_letter_page(event):
    user_id = event.sender_id
    if user_id in letter_pages:
        page_data = letter_pages[user_id]
        letters = page_data['letters']
        current_page = page_data['current_page']
        if current_page > 0:
            letter_pages[user_id]['current_page'] -= 1
            message_id = page_data['message_id']
            await edit_letters_page(event, user_id, letters, page_data['current_page'], message_id)


async def edit_letters_page(event, user_id, letters, current_page, message_id):
    """Редактирует существующее сообщение со списком букв."""
    try:
        start_index = current_page * LETTERS_PER_PAGE
        end_index = start_index + LETTERS_PER_PAGE
        page_letters = letters[start_index:end_index]

        if not page_letters:
            return await event.edit('Нет букв на этой странице.', buttons=kb.profile_work_keyboard())

        buttons = kb.letter_selection_keyboard(letters, current_page, LETTERS_PER_PAGE)

        await client.edit_message(event.chat_id, message_id, 'Вот все доступные буквы:', buttons=buttons)

    except Exception as e:
        logging.error(f"Ошибка при редактировании страницы букв: {e}")
        await event.respond(f"Произошла ошибка: {e}", buttons=kb.profile_work_keyboard())


@client.on(events.CallbackQuery(pattern='letter_'))
async def show_letter_details(event):
    letter = event.data.decode().split('_')[1]
    profile = db.get_profile_by_letter(letter)
    if profile:
        message = utils.format_profile(profile)
        await event.edit(message, buttons=kb.profile_actions_keyboard(letter), parse_mode='html')
    else:
        await event.respond('Профиль не найден.')


@client.on(events.CallbackQuery(pattern='change_date_bring_'))
async def change_date_bring(event):
    letter = event.data.decode().split('_')[3]
    user_id = event.sender_id
    user_states[user_id] = {'state': CHANGE_DATE_BRING_STATE, 'task_data': {'letter': letter}}
    await event.edit('Введите новую дату взятия заданий:', buttons=kb.profile_work_menu())


@client.on(events.CallbackQuery(pattern='change_date_fill_'))
async def change_date_fill(event):
    letter = event.data.decode().split('_')[3]
    user_id = event.sender_id
    user_states[user_id] = {'state': CHANGE_DATE_FILL_STATE, 'task_data': {'letter': letter}}
    await event.edit('Введите новую дату ближайшего залива:', buttons=kb.profile_work_menu())


@client.on(events.CallbackQuery(pattern='change_date_with_'))
async def change_date_with(event):
    letter = event.data.decode().split('_')[3]
    user_id = event.sender_id
    user_states[user_id] = {'state': CHANGE_DATE_WITH_STATE, 'task_data': {'letter': letter}}
    await event.edit('Введите новую дату выплаты:', buttons=kb.profile_work_menu())


@client.on(events.CallbackQuery(pattern='change_status_'))
async def change_status(event):
    letter = event.data.decode().split('_')[2]
    user_id = event.sender_id
    user_states[user_id] = {'state': CHANGE_STATUS_STATE, 'task_data': {'letter': letter}}
    await event.edit('Введите новый статус:', buttons=kb.profile_work_menu())


@client.on(events.CallbackQuery(pattern='remind_'))
async def remind_profile(event):
    letter = event.data.decode().split('_')[1]
    user_id = event.sender_id
    user_states[user_id] = {'state': REMINDER_DATE_TIME_STATE, 'task_data': {'letter': letter}}
    await event.edit('Введите дату и время напоминания в формате ГГГГ-ММ-ДД ЧЧ:ММ:', buttons=kb.profile_work_menu())


@client.on(events.CallbackQuery(pattern='profile_info'))
async def show_profile_info(event):
    data = db.get_all_profile_data()
    if data:
        message = utils.format_all_profiles(data)
        await event.respond(message, parse_mode='html', buttons=kb.back_to_menu_keyboard())
    else:
        await event.respond('Нет данных о профилях.', buttons=kb.back_to_menu_keyboard())


@client.on(events.CallbackQuery(pattern='profile_work_menu'))
async def back_to_profile_work_menu(event):
    await event.edit('Работа с профилями', buttons=kb.profile_work_keyboard())


# Обработчик нажатия на кнопку "В главное меню"
@client.on(events.CallbackQuery(pattern='main_menu'))
async def main_menu(event):
    await event.edit('Главное меню', buttons=kb.main_keyboard())


# Обработчик нажатия на кнопку "В админ меню"
@client.on(events.CallbackQuery(pattern='back_to_admin_menu'))
async def back_to_admin_menu(event):
    await event.edit('Панель администратора', buttons=kb.admin_keyboard())


# Запуск клиента
async def main():
    await client.start()
    print('Бот запущен!')
    await client.run_until_disconnected()


if __name__ == '__main__':
    db.create_tables()
    client.loop.run_until_complete(main())
