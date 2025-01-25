from telethon import TelegramClient, sync
import os


def export_telegram_chat(api_id, api_hash, chat_name, output_dir):
    """
    Экспортирует историю чата из Telegram и сохраняет в файл.

    Args:
        api_id (str): ID API Telegram.
        api_hash (str): Хэш API Telegram.
        chat_name (str): Название чата для экспорта.
        output_dir (str): Путь к директории для сохранения файла.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    client = TelegramClient('session_name', api_id, api_hash)
    client.start()

    chat = client.get_entity(chat_name)
    messages = client.get_messages(chat, limit=None)

    filename = os.path.join(output_dir, f"{chat_name.replace(' ', '_')}.txt")
    with open(filename, 'w', encoding='utf-8') as f:
        for message in messages:
            f.write(
                f"{message.date} - {message.sender.first_name}: {message.text}\n")

    client.disconnect()


# Пример использования
export_telegram_chat(
    api_id='your_api_id',
    api_hash='your_api_hash',
    chat_name='lighting_equipment_chat',
    output_dir='chats/'
)
