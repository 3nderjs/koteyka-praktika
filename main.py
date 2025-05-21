from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import errors
import re
from datetime import datetime
import bcrypt
import json

app = Flask(__name__)
app.secret_key = 'koteika_secret_2023'

db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'pet_hotel',
    'port': 3306,
    'raise_on_warnings': True,
    'use_pure': True
}


def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except errors.InterfaceError as e:
        app.logger.error(f"Failed to connect to MySQL: {e}")
        raise RuntimeError(f"Cannot connect to MySQL server: {e}")
    except errors.DatabaseError as e:
        app.logger.error(f"Database error: {e}")
        raise RuntimeError(f"Database error: {e}")
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        raise RuntimeError(f"Unexpected error: {e}")


# Validation functions
def validate_name(name):
    return bool(re.match(r'^[А-Яа-я\s\-\.]+$', name))


def validate_pet_name(name):
    return bool(re.match(r'^[А-Яа-яA-Za-z\s\-]+$', name))


def validate_phone(phone):
    return bool(re.match(r'^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$', phone))


def validate_email(email):
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))


def validate_date(date_str):
    try:
        day, month, year = map(int, date_str.split(':'))
        datetime(year, month, day)
        return True
    except ValueError:
        return False


# Main page
@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM hotel_info WHERE id = 1")
        hotel = cursor.fetchone()

        if hotel and hotel['social_links']:
            hotel['social_links'] = json.loads(hotel['social_links'])
        else:
            hotel['social_links'] = {}

        cursor.execute("SELECT * FROM rooms WHERE is_featured = TRUE ORDER BY price ASC")
        featured_rooms = cursor.fetchall()

        cursor.execute("SELECT * FROM reviews ORDER BY RAND() LIMIT 5")
        reviews = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('index.html', hotel=hotel, featured_rooms=featured_rooms, reviews=reviews)
    except RuntimeError as e:
        flash(f"Ошибка подключения к базе данных: {e}", "error")
        return render_template('error.html', errors=[str(e)])


# Room catalog
@app.route('/catalog', methods=['GET'])
def catalog():
    try:
        sort = request.args.get('sort', 'price_asc')
        filters = {
            'min_price': request.args.get('filters[min_price]', ''),
            'max_price': request.args.get('filters[max_price]', '')
        }

        where = []
        params = []
        if filters['min_price']:
            where.append("price >= %s")
            params.append(float(filters['min_price']))
        if filters['max_price']:
            where.append("price <= %s")
            params.append(float(filters['max_price']))

        where_clause = " AND ".join(where) if where else ""
        sort_clause = {
            'price_desc': "ORDER BY price DESC",
            'name_asc': "ORDER BY name ASC",
            'price_asc': "ORDER BY price ASC"
        }.get(sort, "ORDER BY price ASC")

        query = f"SELECT * FROM rooms {'WHERE ' + where_clause if where_clause else ''} {sort_clause}"

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        rooms = cursor.fetchall()

        cursor.execute("SELECT * FROM rooms")
        all_rooms = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('catalog.html', rooms=rooms, sort=sort, filters=filters, all_rooms=all_rooms)
    except RuntimeError as e:
        flash(f"Ошибка подключения к базе данных: {e}", "error")
        return render_template('error.html', errors=[str(e)])


# Booking
@app.route('/book', methods=['POST'])
def book():
    data = request.form
    errors = []

    if not data.get('guest_name') or not validate_name(data['guest_name']):
        errors.append("Некорректное имя гостя.")
    if not data.get('pet_name') or not validate_pet_name(data['pet_name']):
        errors.append("Некорректное имя питомца.")
    if not data.get('phone') or not validate_phone(data['phone']):
        errors.append("Некорректный номер телефона.")
    if not data.get('email') or not validate_email(data['email']):
        errors.append("Некорректный email.")
    if not data.get('check_in') or not validate_date(data['check_in']):
        errors.append("Некорректная дата заезда.")
    if not data.get('check_out') or not validate_date(data['check_out']):
        errors.append("Некорректная дата выезда.")

    try:
        check_in = datetime.strptime(data['check_in'], '%d:%m:%Y')
        check_out = datetime.strptime(data['check_out'], '%d:%m:%Y')
        today = datetime.now()

        if check_in.date() < today.date():
            errors.append("Дата заезда не может быть раньше текущей даты.")
        if check_out <= check_in:
            errors.append("Дата выезда должна быть позже даты заезда.")
    except ValueError:
        errors.append("Ошибка в формате дат.")

    if not errors:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM bookings WHERE room_id = %s AND status = 'approved' AND (
                    (check_in <= %s AND check_out >= %s) OR
                    (check_in <= %s AND check_out >= %s) OR
                    (check_in >= %s AND check_out <= %s)
                )
            """, (
                data['room_id'],
                check_out.strftime('%Y-%m-%d'), check_in.strftime('%Y-%m-%d'),
                check_in.strftime('%Y-%m-%d'), check_in.strftime('%Y-%m-%d'),
                check_in.strftime('%Y-%m-%d'), check_out.strftime('%Y-%m-%d')
            ))
            if cursor.fetchone():
                errors.append("Выбранный период уже забронирован.")
            cursor.close()
            conn.close()
        except RuntimeError as e:
            errors.append(f"Ошибка базы данных: {e}")

    if not errors:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bookings (room_id, guest_name, pet_name, phone, email, check_in, check_out)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                data['room_id'], data['guest_name'], data['pet_name'], data['phone'], data['email'],
                check_in.strftime('%Y-%m-%d'), check_out.strftime('%Y-%m-%d')
            ))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Заявка успешно отправлена!", "success")
            return redirect(url_for('index'))
        except RuntimeError as e:
            errors.append(f"Ошибка базы данных: {e}")

    return render_template('error.html', errors=errors)


# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
            admin = cursor.fetchone()
            cursor.close()
            conn.close()

            if admin and bcrypt.checkpw(password.encode('utf-8'), admin['password'].encode('utf-8')):
                session['admin'] = admin['id']
                return redirect(url_for('admin_index'))
            flash("Неверный логин или пароль.", "error")
        except RuntimeError as e:
            flash(f"Ошибка подключения к базе данных: {e}", "error")

    return render_template('admin/login.html')


# Admin panel
@app.route('/admin')
def admin_index():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    try:
        room_id = request.args.get('room_id', '')
        where = "WHERE b.room_id = %s" if room_id else ""
        params = [room_id] if room_id else []

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = f"""
            SELECT b.*, r.name as room_name
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            {where}
            ORDER BY b.created_at DESC
        """
        cursor.execute(query, params)
        bookings = cursor.fetchall()

        cursor.execute("SELECT * FROM rooms")
        rooms = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('admin/index.html', bookings=bookings, rooms=rooms, room_id=room_id)
    except RuntimeError as e:
        flash(f"Ошибка подключения к базе данных: {e}", "error")
        return render_template('error.html', errors=[str(e)])


# Admin actions
@app.route('/admin/action', methods=['POST'])
def admin_action():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    booking_id = request.form.get('booking_id')
    action = request.form.get('action')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if action == 'approve':
            cursor.execute("UPDATE bookings SET status = 'approved' WHERE id = %s", (booking_id,))
        elif action == 'delete':
            cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin_index'))
    except RuntimeError as e:
        flash(f"Ошибка подключения к базе данных: {e}", "error")
        return render_template('error.html', errors=[str(e)])


# Admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    app.run(debug=True)