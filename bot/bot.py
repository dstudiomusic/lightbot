import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN, OPENAI_API_KEY
from database import Database
import openai

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class LightingBot:
    def __init__(self):
        self.database = Database()
        db = Database()
        db.add_directory('docs/')
        db.add_directory('chats/')
        db.add_directory('transcripts/')
        self.application = Application.builder().token(TELEGRAM_TOKEN).build()
        openai.api_key = OPENAI_API_KEY
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.application.add_handler(
            CommandHandler("start", self.start_command))
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await update.message.reply_text(
            "Привет! Я ваш ассистент по световому оборудованию. Чем могу помочь?"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            # Поиск релевантной информации в базе знаний
            search_results = self.database.search(update.message.text)

            # Формируем контекст для GPT
            messages = [
                {"role": "system", "content": "Вы - эксперт по световому оборудованию."},
                {"role": "user", "content": update.message.text}
            ]

            # Получаем ответ от GPT
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            await update.message.reply_text(response.choices[0].message.content)

        except Exception as e:
            logging.error(f"Error in handle_message: {str(e)}")
            await update.message.reply_text(
                "Извините, произошла ошибка. Попробуйте позже."
            )

    def run(self):
        """Запуск бота"""
        self.application.run_polling()


if __name__ == '__main__':
    bot = LightingBot()
    bot.run()
