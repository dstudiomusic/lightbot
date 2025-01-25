import logging, os, tempfile, base64, requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN, OPENAI_API_KEY
from database import Database
import speech_recognition as sr
from pydub import AudioSegment

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

temp_dir = os.path.join(os.getcwd(), 'temp')
if not os.path.exists(temp_dir):
   os.makedirs(temp_dir)

for folder in ['docs', 'chats', 'transcripts', 'generated_images', 'temp']:
   if not os.path.exists(folder):
       os.makedirs(folder)

ffmpeg_path = r"c:\Program Files\ffmpeg\bin\ffmpeg.exe"
AudioSegment.converter = ffmpeg_path

class LightingBot:
   def __init__(self):
       self.database = Database()
       self.application = Application.builder().token(TELEGRAM_TOKEN).build()
       self.user_roles = {}
       self.setup_handlers()

   def setup_handlers(self):
       self.application.add_handler(CommandHandler("start", self.start_command))
       self.application.add_handler(CommandHandler("role", self.set_role))
       self.application.add_handler(CommandHandler("help", self.help_command))
       self.application.add_handler(CommandHandler("generate", self.handle_generate))
       self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
       self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
       self.application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, self.handle_voice))

   async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
       await update.message.reply_text(
           "Привет! Я ваш ассистент по световому оборудованию.\n"
           "Используйте /role [novice/advanced/expert] для выбора уровня общения.\n"
           "Используйте /help для получения справки.\n"
           "Используйте /generate [описание] для генерации изображения."
       )

   async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
       help_text = (
           "Доступные команды:\n"
           "/start - Начать работу с ботом\n"
           "/role [level] - Установить уровень общения:\n"
           "  novice - начинающий\n"
           "  advanced - продвинутый\n"
           "  expert - эксперт\n"
           "/generate [описание] - Создать изображение\n"
           "/help - Показать эту справку"
       )
       await update.message.reply_text(help_text)

   async def set_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
       if not context.args:
           await update.message.reply_text("Укажите роль: novice, advanced или expert")
           return
       role = context.args[0].lower()
       if role not in ["novice", "advanced", "expert"]:
           await update.message.reply_text("Недопустимая роль. Используйте: novice, advanced или expert")
           return
       self.user_roles[update.effective_user.id] = role
       await update.message.reply_text(f"Установлена роль: {role}")

   async def handle_generate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
       try:
           if not context.args:
               await update.message.reply_text("Добавьте описание после команды /generate")
               return
           
           prompt = ' '.join(context.args)
           await update.message.reply_text("Генерирую изображение...")
           
           headers = {
               "Content-Type": "application/json",
               "Authorization": f"Bearer {OPENAI_API_KEY}"
           }
           
           payload = {
               "model": "dall-e-3",
               "prompt": prompt,
               "size": "1024x1024",
               "quality": "standard",
               "n": 1
           }
           
           response = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=payload)
           image_url = response.json()['data'][0]['url']
           
           image_content = requests.get(image_url).content
           image_path = f"generated_images/image_{update.message.message_id}.png"
           
           with open(image_path, 'wb') as f:
               f.write(image_content)
               
           with open(image_path, 'rb') as f:
               await update.message.reply_photo(f)
               
       except Exception as e:
           logging.error(f"Error in handle_generate: {str(e)}")
           await update.message.reply_text("Ошибка при генерации изображения")

   def get_role_prompt(self, role):
       prompts = {
           "novice": "Вы - помощник начинающего художника по свету. Используйте простые термины.",
           "advanced": "Вы - опытный художник по свету. Используйте профессиональную терминологию.",
           "expert": "Вы - эксперт по световому оборудованию. Используйте профессиональный сленг."
       }
       return prompts.get(role, prompts["novice"])

   async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
       try:
           voice = await update.message.voice.get_file()
           voice_path = os.path.join(temp_dir, f"voice_{update.message.message_id}.ogg")
           wav_path = os.path.join(temp_dir, f"voice_{update.message.message_id}.wav")
           
           await voice.download_to_drive(voice_path)
           
           audio = AudioSegment.from_file(voice_path)
           audio.export(wav_path, format='wav')
           
           r = sr.Recognizer()
           with sr.AudioFile(wav_path) as source:
               audio_data = r.record(source)
               text = r.recognize_google(audio_data, language='ru-RU')
           
           os.remove(voice_path)
           os.remove(wav_path)
           
           await update.message.reply_text(f"Распознанный текст: {text}")
           await self.handle_message(update, context, text)
           
       except Exception as e:
           logging.error(f"Error in handle_voice: {str(e)}")
           await update.message.reply_text("Ошибка при обработке голосового сообщения")

   async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
       try:
           photo = await update.message.photo[-1].get_file()
           photo_bytes = await photo.download_as_bytearray()
           
           headers = {
               "Content-Type": "application/json",
               "Authorization": f"Bearer {OPENAI_API_KEY}"
           }
           
           payload = {
               "model": "gpt-4-vision-preview",
               "messages": [
                   {
                       "role": "user",
                       "content": [
                           {"type": "text", "text": "Опишите световое оборудование на фото"},
                           {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(photo_bytes).decode()}"}}
                       ]
                   }
               ],
               "max_tokens": 300
           }
           
           response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
           response_json = response.json()
           
           await update.message.reply_text(response_json['choices'][0]['message']['content'])
           
       except Exception as e:
           logging.error(f"Error in handle_photo: {str(e)}")
           await update.message.reply_text("Ошибка при обработке изображения")

   async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, voice_text=None):
       try:
           user_id = update.effective_user.id
           role = self.user_roles.get(user_id, "novice")
           
           text = voice_text or update.message.text
           headers = {
               "Content-Type": "application/json",
               "Authorization": f"Bearer {OPENAI_API_KEY}"
           }
           
           payload = {
               "model": "gpt-3.5-turbo",
               "messages": [
                   {"role": "system", "content": self.get_role_prompt(role)},
                   {"role": "user", "content": text}
               ]
           }
           
           response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
           response_json = response.json()
           
           await update.message.reply_text(response_json['choices'][0]['message']['content'])
           
       except Exception as e:
           logging.error(f"Error in handle_message: {str(e)}")
           await update.message.reply_text("Ошибка при обработке запроса")

   def run(self):
       self.application.run_polling()

if __name__ == '__main__':
   bot = LightingBot()
   bot.run()