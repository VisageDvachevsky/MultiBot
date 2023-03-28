import telebot
import vk_api
from telebot import types
from telebot.types import InputMediaPhoto
import youtube_dl
from time import sleep

import os
import requests
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

bot = telebot.TeleBot('')
# Авторизация в VK
vk_session = vk_api.VkApi(token='')

API_KEY = ''
SEARCH_ENGINE_ID = ''

# Задать опции для веб-драйвера Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Инициализировать веб-драйвер Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

start_from = ''

print('I am working')

groups_ids = ['-193591424','-217069685','-22751485',
    '-187783794','-201928587', '-57536014',
     '-190840422', '-159908458', '-97597836',
      '-194373124', '-49131654', '-206626877',
       '-186045777', '-190781961', '-92157416',
        '-193472341']

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f'hello, {message.from_user.username}\n \nКоманды: \n/f\n/feed\n\n/search <запрос>')

@bot.message_handler(commands=['feed', 'f', 'лента'])
def button_message(message):
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1=types.KeyboardButton("Новости")
    markup.add(item1)
    bot.send_message(message.chat.id,'Выберите что вам надо',reply_markup=markup)

@bot.message_handler(commands=['search'])
def handle_search(message):
    try:
        # Получить запрос пользователя
        query = message.text.split('/search ')[1]
        print(query)
        # Выполнить поиск в Google и получить первые 5 результатов
        service = build('customsearch', 'v1', developerKey=API_KEY)
        res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID, num=5).execute()
        urls = [result['link'] for result in res['items']]

        # Отправить скриншоты результатов пользователю
        for index, url in enumerate(urls):
            driver.get(url)
            file_path = f'screenshot-{index}.png'
            driver.save_screenshot(file_path)

            with open(file_path, 'rb') as f:
                bot.send_photo(message.chat.id, f)
            os.remove(file_path)
    except:
        previous_statement_search_text

@bot.message_handler(content_types='text')
def message_reply(message):
    if message.text=="Новости":
        global start_from
        vk = vk_session.get_api()
        news = vk.newsfeed.get(count=50, start_from=start_from)

        for feed in news['items']:
            if feed['type'] == 'post':
                for attach in feed['attachments']:
                    if attach['type'] == 'photo':
                        url = attach['photo']['sizes'][-1]['url']
                        if feed['text'] != "":
                            if len(feed['text']) > 200:
                                for x in range(0, len(feed['text']), 200):
                                    bot.send_photo(message.chat.id, url, caption=feed['text'][x:x+200])
                            else:
                                bot.send_photo(message.chat.id, url, caption=feed['text'])
                        else:
                            bot.send_photo(message.chat.id, url)

                    elif attach['type'] == 'wall_photo':
                        urls = []
                        for elem in attach['photos']['items']:
                            urls.append(elem['sizes'][-1]['url'])
                            media = [InputMediaPhoto(url) for url in urls]
                            if elem['text'] != "":
                                if len(elem['text']) > 200:
                                    for x in range(0, len(feed['text']), 200):
                                        bot.send_media_group(message.chat.id, media=media, caption=elem['text'][x:x+200])
                                else:
                                    bot.send_media_group(message.chat.id, media=media, caption=elem['text'])
                            else:
                                bot.send_media_group(message.chat.id, media=media)

                    # elif attach['type'] == 'video':
                    #     url = f"https://vk.com/{vk.groups.getById(group_id=attach['video']['owner_id']*-1)[0]['screen_name']}?z=video{attach['video']['owner_id']}_{attach['video']['id']}"
                    #     if feed['text'] != "":
                    #         ydl_opts 
                    #         = {}
                    #         with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    #             downloaded = ydl.download([url])

                    #         bot.send_video(message.chat.id, vid, caption=feed['text'])
                    #     else:
                    #         bot.send_video(message.chat.id, vid)
                    
                    else:
                        pass

                    sleep(0.5)

        start_from = news['next_from']



bot.polling(none_stop=True, interval=0)
