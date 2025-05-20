# database.py

import sqlite3
from datetime import datetime

DATABASE_NAME = 'tasks.db'

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables():
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    rating INTEGER DEFAULT 100,
                    rang INTEGER DEFAULT 0,
                    doing_tasks INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_creator INTEGER,
                    name TEXT,
                    description TEXT,
                    date TEXT,
                    cost INTEGER,
                    status INTEGER DEFAULT 0
                )
            """)
            # Новая таблица для работы с профилями
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profile_work (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    letter TEXT UNIQUE,
                    status INTEGER DEFAULT 0,
                    date_create TEXT,
                    date_bring TEXT,
                    date_fill TEXT,
                    date_with TEXT
                )
            """)
            conn.commit()
            print("Таблицы успешно созданы или уже существуют.")
        except sqlite3.Error as e:
            print(f"Ошибка при создании таблиц: {e}")
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")

def add_user(user_id, username):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
                conn.commit()
                print(f"Пользователь с ID {user_id} добавлен.")
            else:
                print(f"Пользователь с ID {user_id} уже существует.")
        except sqlite3.Error as e:
            print(f"Ошибка при добавлении пользователя: {e}")
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")

def get_user(user_id):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
            user_data = cursor.fetchone()
            return user_data
        except sqlite3.Error as e:
            print(f"Ошибка при получении данных пользователя: {e}")
            return None
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")
        return None

def create_task(id_creator, name, description, date, cost):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (id_creator, name, description, date, cost)
                VALUES (?, ?, ?, ?, ?)
            """, (id_creator, name, description, date, cost))
            conn.commit()
            print("Задача успешно создана.")
        except sqlite3.Error as e:
            print(f"Ошибка при создании задачи: {e}")
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")

def get_tasks(user_id, status=0, sort_by_cost=False):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM tasks WHERE id_creator=? AND status=?"
            params = (user_id, status)
            if sort_by_cost:
                query += " ORDER BY cost DESC"
            cursor.execute(query, params)
            tasks = cursor.fetchall()
            return tasks
        except sqlite3.Error as e:
            print(f"Ошибка при получении задач: {e}")
            return []
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")
        return []

def update_task_status(task_id, status):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
            conn.commit()
            print(f"Статус задачи с ID {task_id} обновлен на {status}.")
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении статуса задачи: {e}")
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")

def get_task(task_id):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            task = cursor.fetchone()
            return task
        except sqlite3.Error as e:
            print(f"Ошибка при получении задачи: {e}")
            return None
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")
        return None

def get_task_counts(user_id):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE id_creator=? AND status=0", (user_id,))
            pending_tasks = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE id_creator=? AND status=1", (user_id,))
            completed_tasks = cursor.fetchone()[0]
            return pending_tasks, completed_tasks
        except sqlite3.Error as e:
            print(f"Ошибка при получении количества задач: {e}")
            return 0, 0
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")
        return 0, 0

def update_all_ratings(new_rating):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET rating=?", (new_rating,))
            conn.commit()
            print("Рейтинг всех пользователей успешно обновлен.")
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении рейтинга пользователей: {e}")
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")

def get_all_users():
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, rang FROM users")
            users = cursor.fetchall()
            return users
        except sqlite3.Error as e:
            print(f"Ошибка при получении списка пользователей: {e}")
            return []
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")
        return []

def get_last_task_id():
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM tasks")
            task_id = cursor.fetchone()[0]
            return task_id
        except sqlite3.Error as e:
            print(f"Ошибка при получении ID последней задачи: {e}")
            return None
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")
        return None

def update_user_rating(user_id, new_rating):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET rating=? WHERE id=?", (new_rating, user_id))
            conn.commit()
            print(f"Рейтинг пользователя с ID {user_id} успешно обновлен на {new_rating}.")
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении рейтинга пользователя: {e}")
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")

# Методы для работы с таблицей profile_work
def create_profile_letter(letter):
    """Создает новую букву профиля в таблице profile_work."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute("""
                INSERT INTO profile_work (letter, date_create)
                VALUES (?, ?)
            """, (letter, now))
            conn.commit()
            print(f"Буква профиля '{letter}' успешно создана.")
            return True
        except sqlite3.IntegrityError:
            print(f"Буква профиля '{letter}' уже существует.")
            return False
        except sqlite3.Error as e:
            print(f"Ошибка при создании буквы профиля: {e}")
            return False
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")
        return False

def get_all_profile_letters():
    """Получает список всех букв профиля из таблицы profile_work."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT letter FROM profile_work")
            letters = [row[0] for row in cursor.fetchall()]
            return letters
        except sqlite3.Error as e:
            print(f"Ошибка при получении букв профиля: {e}")
            return []
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")
        return []

def get_profile_by_letter(letter):
    """Получает информацию о профиле по букве."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profile_work WHERE letter=?", (letter,))
            profile = cursor.fetchone()
            return profile
        except sqlite3.Error as e:
            print(f"Ошибка при получении информации о профиле: {e}")
            return None
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")
        return None

def update_profile_field(letter, field, value):
    """Обновляет поле в таблице profile_work для указанной буквы."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            sql = f"UPDATE profile_work SET {field}=? WHERE letter=?"
            cursor.execute(sql, (value, letter))
            conn.commit()
            print(f"Поле '{field}' для буквы '{letter}' успешно обновлено.")
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении поля '{field}': {e}")
            return False
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")
        return False

def get_all_profile_data():
    """Получает все данные из таблицы profile_work."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profile_work")
            data = cursor.fetchall()
            return data
        except sqlite3.Error as e:
            print(f"Ошибка при получении данных из profile_work: {e}")
            return []
        finally:
            conn.close()
    else:
        print("Ошибка: Не удалось создать подключение к базе данных.")
        return []