import logging
import re
import os
import paramiko
from dotenv import load_dotenv
from pathlib import Path
import psycopg2
from psycopg2 import Error

from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler, CallbackContext

load_dotenv()

host = os.getenv('HOST')
port = os.getenv('PORT')
username = os.getenv('USER')
password = os.getenv('PASSWORD')
user_db = os.getenv('USER_DB')
password_db = os.getenv('PASSWORD_DB')
port_db = os.getenv('PORT_DB')
database_db = os.getenv('DATABASE')
host_db = os.getenv('HOST_DB')

# Подключаем логирование
logging.basicConfig(
    filename='tglog.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


def send_long_message(update: Update, context, message: str):
    splitted_text = []

    for part in range(0, len(message), 4000):
        splitted_text.append(message[part:part+4000])

    for part in splitted_text:
        update.message.reply_text(part)

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')

def helpCommand(update: Update, context):
    update.message.reply_text('Help!')

def findEmailAddressCommand(update: Update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text="Введите текст для поиска почтовых адресов: ")

    return 'find_email'

def findPhoneNumbersCommand(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text="Введите текст для поиска телефонных номеров: ")

    return 'find_phone_number'

def findEmailAddresses(update: Update, context):
    user_input = update.message.text
    
    emailAddressRegex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    emailAddressList = emailAddressRegex.findall(user_input)

    if not emailAddressList:
        update.message.reply_text('Почтовые адреса не найдены.')
        return ConversationHandler.END
    
    EmailAddress = []
    for email in emailAddressList:
        EmailAddress.append(''.join(email))

    update.message.reply_text('\n'.join(EmailAddress))
    update.message.reply_text('Хотите сохранить найденные почтовые адреса в базе данных? (Да/Нет)')
    context.user_data["emails"] = EmailAddress
    return "saveEmailsToDB" # Завершаем работу обработчика диалога

def saveEmailsToDB(update: Update, context):
    response = update.message.text.lower()
    if response == 'да':
        connection = None
        try: 
            connection = psycopg2.connect(user=user_db,
                                        password=password_db,
                                        host=host_db,
                                        port=port_db,
                                        database=database_db)
            cursor = connection.cursor()
            for emails in context.user_data.get("emails"):
                insert_query = 'INSERT INTO emails (email) VALUES (%s);'
                cursor.execute(insert_query, (emails,))
                connection.commit()
            update.message.reply_text("Почтовые адреса успешно сохранены в базе данных PostgreSQL")
        except (Exception, Error) as error:
            update.message.reply_text("Ошибка при работе с PostgreSQL %s", error)
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
        return ConversationHandler.END    
    elif response == 'нет':
        update.message.reply_text('Ок, почтовые адреса не будут сохранены')
        return ConversationHandler.END
    else:
        update.message.reply_text('Пожалуйста, ответьте "Да" или "Нет"')

def findPhoneNumbers (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов
    
    phoneNumRegex = re.compile(
        r"(\+7|8)(\d{10}|"
        r"\(\d{3}\)\d{7}|"
        r" \d{3} \d{3} \d{2} \d{2}|"
        r" \(\d{3}\) \d{3} \d{2} \d{2}|"
        r"-\d{3}-\d{3}-\d{2}-\d{2})"
    ) # формат 8 (000) 000-00-00, 80000000000, 8(000)0000000, 8 000 000 00 00, 8-000-000-00-00 (И с +7)

    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END# Завершаем выполнение функции
    
    phonesList = []  # Создаем пустой список для номеров телефонов
    for phone in phoneNumberList:
        phonesList.append(''.join(phone))
        
    update.message.reply_text('\n'.join(phonesList))  # Отправляем номера пользователю
    update.message.reply_text('Хотите сохранить найденные номера в базе данных? (Да/Нет)')
    context.user_data["phones_list"] = phonesList
    return "savePhoneNumbersToDB" # Завершаем работу обработчика диалога

def savePhoneNumbersToDB(update: Update, context):
    response = update.message.text.lower()
    if response == 'да':
        connection = None
        try: 
            connection = psycopg2.connect(user=user_db,
                                        password=password_db,
                                        host=host_db,
                                        port=port_db,
                                        database=database_db)
            cursor = connection.cursor()
            for phones in context.user_data.get("phones_list"):
                insert_query = 'INSERT INTO phone_numbers (phone_number) VALUES (%s);'
                cursor.execute(insert_query, (phones,))
                connection.commit()
            update.message.reply_text("Номера успешно сохранены в базе данных PostgreSQL")
        except (Exception, Error) as error:
            update.message.reply_text("Ошибка при работе с PostgreSQL %s", error)
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
        return ConversationHandler.END    
    elif response == 'нет':
        update.message.reply_text('Ок, номера не будут сохранены')
        return ConversationHandler.END
    else:
        update.message.reply_text('Пожалуйста, ответьте "Да" или "Нет"')

def checkPasswdCommand(update: Update, context):
    update.message.reply_text('Введите пароль, для проверки его на сложность: ')

    return 'verify_password'

def checkPasswdDifficult(update: Update, context):
    user_input = update.message.text
    
    passwordRegex = re.compile(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$')

    passwordinfo = passwordRegex.findall(user_input)

    if not passwordinfo:
        update.message.reply_text('Пароль простой.')
        return ConversationHandler.END
    elif passwordinfo:
        update.message.reply_text('Пароль сложный.')
        return ConversationHandler.END
    
def ssh_command(command, update, context):
    """Выполнение SSH команды и отправка результата в чат."""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=int(port), username=username, password=password)
        
        stdin, stdout, stderr = client.exec_command(command)
        result = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
        
        
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")
    finally:
        client.close()
    return result

# Добавляем обработчики для команд
def get_release(update, context):
    ssh_command("cat /etc/os-release", update, context)

def get_uname(update, context):
    ssh_command("uname -a", update, context)

def get_uptime(update, context):
    ssh_command("uptime", update, context)

def get_df(update, context):
    ssh_command("df -h", update, context)

def get_free(update, context):
    ssh_command("free -m", update, context)

def get_mpstat(update, context):
    ssh_command("mpstat", update, context)

def get_w(update, context):
    ssh_command("w", update, context)

def get_auths(update, context):
    ssh_command("last -n 10", update, context)

def get_critical(update, context):
    ssh_command("journalctl -p crit -n 5", update, context)

def get_ps(update, context):
    ssh_command("ps -a", update, context)

def get_ss(update, context):
    ssh_command("ss -tuln", update, context)

def get_apt_list(update, context):
    data = str
    if len(context.args) == 0:
        data = ssh_command("dpkg -l", update, context)
    else:
        package_name = "".join(context.args)
        data = ssh_command(f"dpkg -s {package_name}", update, context)

    send_long_message(update, context, data)

def get_services(update, context):
    data = ssh_command("systemctl --type=service", update, context)
    send_long_message(update, context, data)

def get_repl_logs(update, context):
    data = ssh_command('grep "replication" /var/log/postgresql/postgresql-16-main.log', update, context)
    send_long_message(update, context, data)

def get_emails(update, context):
    connection = None
    try: 
        connection = psycopg2.connect(user=user_db,
                                      password=password_db,
                                      host=host_db,
                                      port=port_db,
                                      database=database_db)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM emails;")
        logging.info("Команда выполнена успешно!")
        info = cursor.fetchall()
        for row in info:
            formatted_row = ". ".join(str(value) for value in row)
            update.message.reply_text(formatted_row)
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            print("Соединение с PostgresSql закрыто")
    

def get_phone_numbers(update, context):
    connection = None
    try: 
        connection = psycopg2.connect(user=user_db,
                                      password=password_db,
                                      host=host_db,
                                      port=port_db,
                                      database=database_db)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phone_numbers;")
        logging.info("Команда выполнена успешно!")
        data = cursor.fetchall()
        for row in data:
            formatted_row = ". ".join(str(value) for value in row)
            update.message.reply_text(formatted_row)
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            print("Соединение с PostgresSql закрыто")

def echo(update: Update, context):
    update.message.reply_text(update.message.text)

def main():
		# Создайте программу обновлений и передайте ей токен вашего бота
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher
    convHandlerFindPhoneNumber = ConversationHandler(
        entry_points = [CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states = {
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'savePhoneNumbersToDB': [MessageHandler(Filters.text & ~Filters.command, savePhoneNumbersToDB)]     
        },
        fallbacks=[]
    )

    convHandlerfindEmailAddresses = ConversationHandler(
        entry_points = [CommandHandler('find_email', findEmailAddressCommand)],
        states = {
            'find_email': [MessageHandler(Filters.text & ~Filters.command, findEmailAddresses)],
            'saveEmailsToDB': [MessageHandler(Filters.text & ~Filters.command, saveEmailsToDB)]
        },
        fallbacks=[]
    )

    convHandlerCheckPasswd = ConversationHandler(
        entry_points = [CommandHandler('verify_password', checkPasswdCommand)],
        states = {
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, checkPasswdDifficult)],
        },
        fallbacks=[]
    )


		# Регистрируем обработчик текстовых сообщений
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumber)
    dp.add_handler(convHandlerfindEmailAddresses)
    dp.add_handler(convHandlerCheckPasswd)
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_apt_list", get_apt_list))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo)) # Если сообщение не является командой по типу /start, то бот повторяет за пользователем
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    dp.add_handler(CommandHandler("get_emails", get_emails))

    	# Запускаем бота
    updater.start_polling()

		# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
