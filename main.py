from pytubefix import YouTube
from pytubefix.cli import on_progress
import telebot
import os
import time
from requests.exceptions import ConnectionError, Timeout
import logging
import urllib
import json


# file logs
logging.basicConfig(filename='bot.log', level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TOKEN = ""
po_token = ""
user_id = ""
with open("token.json", "r") as file:
    data = json.load(file)
    TOKEN = data["TOKEN"]
    po_token = data["po_token"]
    user_id = data["user_id"]
bot = telebot.TeleBot(TOKEN)
count = 0

proxy = open("proxy.txt", "r")
proxy_server = proxy.readline().strip()
proxy.close()

proxy_handler = {}

if len(proxy_server) != 0:
    proxy_handler["http"] = f"{proxy_server}",
    proxy_handler["https"] = f"{proxy_server}"


@bot.message_handler(commands = ['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Отправь ссылку на видео, и я отправлю тебе mp3")

@bot.message_handler(content_types = ['text'])
def send_audio(message):   
    global count  
    count += 1
    time.sleep(2)

    user_id = message.chat.id
    path = os.path.dirname(os.path.abspath(__file__))
    
    if not os.path.exists(path + f"/storage/{user_id}"):
        os.mkdir(path + f"/storage/{user_id}")
        logging.info(f"Создаем папку {user_id}")
                     
    try:
        logging.info(f"Запускаем процесс получения видео для пользователя {user_id}")

        yt = YouTube(message.text, on_progress_callback=on_progress, proxies=proxy_handler)
        ttl = yt.title
        ys = yt.streams.get_audio_only()
        ys.download(mp3=True, filename=f"{count}", output_path=f"./storage/{user_id}")

        logging.info(f"Завершен процесс получения видео {ttl} для пользователя {user_id}")
    except urllib.error.URLError as e:
        logging.error(f"URLError for user {user_id}: {str(e)}")
        bot.send_message(message.chat.id, "Не удалось подключиться к YouTube. Проверьте ваше интернет-соединение или попробуйте позже.")
        return
    except Exception as e:
        logging.error(f"Unexpected error for user {user_id}: {str(e)}")
        bot.send_message(message.chat.id, "Произошла неожиданная ошибка. Пожалуйста, попробуйте позже.")
        return
    
    max_tries = 3
    retry_delay = 2
    bot.send_message(message.chat.id, f"Получение {ttl}")
    for attempt in range(max_tries):
        try:
            audio_path = f"./storage/{user_id}/{count}.mp3"
            audio = open(audio_path, "rb")

            logging.info(f"Попытка отправить пользователю {user_id} видео {ttl}, попытка {attempt}")
            bot.send_audio(message.chat.id, audio, title = f"{ttl}", timeout=60)
            audio.close()
            break
        except (ConnectionError, Timeout) as e:
            if attempt < max_tries - 1:
                logging.info(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay) 
            else:
                logging.info(f"Failed to send audio after {max_tries} attempts: {e}")
                bot.send_message(message.chat.id, "При отправке аудио возникла ошибка. Попробуйте снова.")
        finally:
            if os.path.exists(audio_path):
                logging.info(f"Deleting file {audio_path} from {user_id}")
                os.remove(audio_path)

bot.polling()
