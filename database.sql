CREATE DATABASE pet_hotel;
USE pet_hotel;

CREATE TABLE hotel_info (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    slogan VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    working_hours VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    social_links TEXT NOT NULL
);

CREATE TABLE rooms (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    is_featured BOOLEAN DEFAULT FALSE
);

CREATE TABLE bookings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    guest_name VARCHAR(100) NOT NULL,
    pet_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);

CREATE TABLE reviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admins (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

INSERT INTO hotel_info (name, city, slogan, address, working_hours, phone, email, social_links)
VALUES ('Котейка', 'Москва', 'Дом для ваших питомцев!', 'ул. Лесная, д. 5', '09:00-21:00', '+7(495)123-45-67', 'info@koteika.ru', '{"vk":"vk.com/koteika","tg":"t.me/koteika"}');

INSERT INTO rooms (name, description, price, is_featured) VALUES
('Стандарт', 'Уютный номер для одного питомца', 1500.00, TRUE),
('Комфорт', 'Просторный номер с игрушками', 2000.00, TRUE),
('Люкс', 'Номер с окном и лежанкой', 3000.00, FALSE),
('Эконом', 'Бюджетный вариант', 1000.00, FALSE),
('Семейный', 'Для нескольких питомцев', 3500.00, TRUE),
('VIP', 'Эксклюзивный номер', 5000.00, FALSE);

INSERT INTO reviews (content) VALUES
('Отличное место, мой кот был счастлив!'),
('Чисто, уютно, рекомендую!'),
('Персонал очень заботливый.'),
('Номер комфортный, но цена высоковата.'),
('Питомец вернулся довольным!');

INSERT INTO admins (username, password)
VALUES ('admin', '$2b$12$6X8j3z9Qz7kXz5Y8v6W8v.t6j4k9Qz8Y7v5Xz9Qz7kXz5Y8v6W8v');
-- Password is PROF2023 (hashed with bcrypt)