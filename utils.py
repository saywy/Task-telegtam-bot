def format_task(task):
    """Форматирует задачу в удобочитаемый вид."""
    return (
        f"<b>{task[2]}</b>\n"  # name
        f"Описание: {task[3]}\n"  # description
        f"Рейтинг: {task[5]}\n"  # cost
        f"Срок выполнения: {task[4]}"  # date
    )

def format_profile(profile):
    """Форматирует информацию о профиле в удобочитаемый вид."""
    return (
        f"<b>Буква профиля:</b> {profile[1]}\n"
        f"<b>Дата создания:</b> {profile[3]}\n"
        f"<b>Дата взятия заданий:</b> {profile[4] if profile[4] else 'Не указана'}\n"
        f"<b>Дата ближайшего залива:</b> {profile[5] if profile[5] else 'Не указана'}\n"
        f"<b>Дата выплаты:</b> {profile[6] if profile[6] else 'Не указана'}\n\n"
        f"<b>Статус:</b> {profile[2]}"
    )

def format_all_profiles(data):
    """Форматирует все данные из таблицы profile_work для отображения."""
    message = "<b>Информация о профилях:</b>\n\n"
    for profile in data:
        message += (
            f"Буква: {profile[1]}, "
            f"Статус: {profile[2]}, "
            f"Дата создания: {profile[3]}, "
            f"Дата взятия: {profile[4] if profile[4] else 'Не указана'}, "
            f"Дата залива: {profile[5] if profile[5] else 'Не указана'}, "
            f"Дата выплаты: {profile[6] if profile[6] else 'Не указана'}\n"
        )
    return message