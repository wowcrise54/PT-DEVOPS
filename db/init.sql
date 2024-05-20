CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD 'qwerty12345';
SELECT pg_create_physical_replication_slot('replication_slot');

CREATE DATABASE tg_bot_db;
\c tg_bot_db

CREATE TABLE IF NOT EXISTS emails(
    id SERIAL PRIMARY KEY,
    email VARCHAR (50) NOT NULL
);

CREATE TABLE IF NOT EXISTS phone_numbers(
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR (30) NOT NULL
);
