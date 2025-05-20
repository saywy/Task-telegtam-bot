from telethon.tl.custom import Button

def main_keyboard():
    """Главная клавиатура (inline)."""
    return [
        [Button.inline("Создать задание", 'create_task'),
         Button.inline("Посмотреть свои задания", 'view_tasks')],
        [Button.inline("Личный профиль", 'profile')],
        [Button.inline("Работа с профилями", 'profile_work')],  # Новая кнопка
        [Button.inline("ДЛЯ АДМИНИСТРАЦИИ", 'admin')]
    ]

def admin_keyboard():
    """Клавиатура администратора (inline)."""
    return [
        [Button.inline("Создать задание", 'admin_create_task')],
        [Button.inline("Посмотреть рейтинг пользователя", 'admin_view_user_rating')],
        [Button.inline("Посмотреть не выполненные задачи пользователя", 'admin_view_user_tasks')],
        [Button.inline("Обновить рейтинг", 'admin_update_rating')],
        [Button.inline("Понизить рейтинг пользователя", 'admin_lower_rating')],
        [Button.inline("В главное меню", 'main_menu')]
    ]

def task_navigation_keyboard(has_next, has_previous):
    """Клавиатура навигации по задачам (inline)."""
    buttons = []
    if has_previous:
        buttons.append(Button.inline("Назад", 'prev_page'))
    if has_next:
        buttons.append(Button.inline("Вперед", 'next_page'))
    buttons.append(Button.inline("В главное меню", 'main_menu'))
    return [buttons]

def task_actions_keyboard(task_id):
    """Клавиатура действий с задачей (inline)."""
    return [
        [Button.inline("ВЫПОЛНИЛ", f'complete_{task_id}'),
         Button.inline("В главное меню", 'main_menu')]
    ]

def confirmation_keyboard():
    """Клавиатура подтверждения (inline)."""
    return [
        [Button.inline("ДА", 'confirm'),
         Button.inline("НЕТ", 'cancel')]
    ]

def back_to_menu_keyboard():
    """Клавиатура с кнопкой "В главное меню"."""
    return [[Button.inline("В главное меню", 'main_menu')]]

def back_to_admin_keyboard():
    """Клавиатура с кнопкой "В админ меню"."""
    return [[Button.inline("В админ меню", 'back_to_admin_menu')]]

# Клавиатуры для работы с профилями
def profile_work_keyboard():
    """Клавиатура для работы с профилями."""
    return [
        [Button.inline("Выбрать букву", 'select_letter'),
         Button.inline("Создать новую букву", 'create_letter')],
        [Button.inline("Информация", 'profile_info')],
        [Button.inline("В главное меню", 'main_menu')]
    ]

def letter_selection_keyboard(letters, current_page=0, letters_per_page=5):
    """Клавиатура для выбора буквы профиля с пагинацией."""
    start_index = current_page * letters_per_page
    end_index = start_index + letters_per_page
    page_letters = letters[start_index:end_index]

    buttons = []
    for letter in page_letters:
        buttons.append([Button.inline(letter, f'letter_{letter}')])

    has_next = end_index < len(letters)
    has_previous = current_page > 0

    navigation_buttons = letter_navigation_keyboard(has_next, has_previous)
    for button_row in navigation_buttons:
        buttons.append(button_row)

    return buttons

def letter_navigation_keyboard(has_next, has_previous):
    """Клавиатура навигации по буквам профиля."""
    buttons = []
    if has_previous:
        buttons.append(Button.inline("Назад", 'prev_letter_page'))
    if has_next:
        buttons.append(Button.inline("Вперед", 'next_letter_page'))
    buttons.append(Button.inline("В меню профилей", 'profile_work_menu'))
    return [buttons]

def profile_actions_keyboard(letter):
    """Клавиатура действий для конкретного профиля."""
    return [
        [Button.inline("Сменить дату взятия заданий", f'change_date_bring_{letter}')],
        [Button.inline("Сменить дату ближайшего залива", f'change_date_fill_{letter}')],
        [Button.inline("Сменить дату выплаты", f'change_date_with_{letter}')],
        [Button.inline("Сменить статус", f'change_status_{letter}')],
        [Button.inline("В меню профилей", 'profile_work_menu')]
    ]

def profile_work_menu():
    return [[Button.inline("В меню профилей", 'profile_work_menu')]]