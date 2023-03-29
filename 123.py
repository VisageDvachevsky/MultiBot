
"""
This bot has great functionality, mainly related to social network VK,
for example, reciving a news feed, but there are also functions outside VK, for example, search in sites
"""

import time
import os
import requests

import telebot
import urllib
from telebot import types
from telebot.types import InputMediaPhoto
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import vk_api

import config

bot = telebot.TeleBot(config.TgToken)
vk_session = vk_api.VkApi(token=config.VkToken)

# required variable
API_KEY = config.GoogleAPIKey
SEARCH_ENGINE_ID = config.EngineID
start_from = ''

# Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# google webdriver initialization
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                          options=chrome_options)


@bot.message_handler(commands=['start'])
def hello_msg(message):
    keyboard = ReplyKeyboardMarkup()
    button1 = KeyboardButton('Новости')
    button2 = KeyboardButton('Чат')
    keyboard.add(button1, button2)
    """
    { hello mail }

    :param      message:  User message
    :type       message:  { telebot.types.Message }
    """
    bot.reply_to(message,
                 f"hello, {message.from_user.username}.\n \nКоманды:\n/search <запрос>")

    bot.send_message(chat_id=message.chat.id,
                     text='Выберите кнопку:',
                     reply_markup=keyboard)

# search info in google


@bot.message_handler(commands=['search'])
def handle_search(message):
    """
    { finds sites for your requests }

    :param      message:  User message
    :type       message:  { telebot.types.Message }
    """
    try:
        # get user query
        query = message.text.split('/search ')[1]

        # get first five pages
        service = build('customsearch', 'v1', developerKey=API_KEY)
        res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID, num=5).execute()
        urls = [result['link'] for result in res['items']]

        # send screenshots
        for index, url in enumerate(urls):
            driver.get(url)
            file_path = f'screenshot-{index}.png'
            driver.save_screenshot(file_path)

            with open(file_path, 'rb') as f:
                bot.send_photo(message.chat.id, f)
            os.remove(file_path)
    except:
        pass

# commands handler


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.text == 'Новости':
        global start_from
        vkapp = vk_session.get_api()
        vk = vkapp.newsfeed.get(count=21, start_from=start_from)
        # parse vk-newsfeed
        for feed in vk['items']:
            time.sleep(0.5)
            # deafault post
            if feed['type'] == 'post':
                for attach in feed['attachments']:
                    if attach['type'] == 'photo':
                        url = attach['photo']['sizes'][-1]['url']
                        # checking for text in a post
                        if feed['text'] != "":
                            # error "message to long" handler
                            if len(feed['text']) > 200:
                                for x in range(0, len(feed['text']), 200):
                                    bot.send_photo(
                                        message.chat.id,
                                        url,
                                        caption=feed['text'][x:x+200])
                            else:
                                bot.send_photo(message.chat.id,
                                               url,
                                               caption=feed['text'])
                        else:
                            bot.send_photo(message.chat.id, url)

                    # set of photos
                    elif attach['type'] == 'wall_photo':
                        urls = []
                        for elem in attach['photos']['items']:
                            urls.append(elem['sizes'][-1]['url'])
                            media = [InputMediaPhoto(url) for url in urls]
                            # checking for text in a post
                            if elem['text'] != "":
                                # error "message to long" handler
                                if len(elem['text']) > 200:
                                    for x in range(0, len(feed['text']), 200):
                                        bot.send_media_group(
                                            message.chat.id,
                                            media=media,
                                            caption=elem['text'][x:x+200])

                                else:
                                    bot.send_media_group(
                                        message.chat.id,
                                        media=media,
                                        caption=elem['text'])

                            else:
                                bot.send_media_group(
                                    message.chat.id,
                                    media=media)
                    else:
                        pass
        # eliminate duplicates in feed
        start_from = vk['next_from']

    elif message.text == 'Чат':
        keyboard = ReplyKeyboardMarkup()

        getmsgBtn = KeyboardButton(
            'Получить последние сообщения')
        keyboard.add(getmsgBtn)
        sendmsgBtn = KeyboardButton('Переписка')
        keyboard.add(sendmsgBtn)

        bot.send_message(chat_id=message.chat.id,
                         text='Выберите кнопку:',
                         reply_markup=keyboard)

    elif message.text == 'Получить последние сообщения':
        vk = vk_session.get_api()
        # get chat id for bot
        chat_id = message.chat.id
        # getting a list of dialogs
        dialogs = vk.messages.getConversations(count=5)['items']
        # processing each dialogue
        for dialog in dialogs:
            if dialog['conversation']['peer']['type'] == 'user':
                peer_id = dialog['conversation']['peer']['id']
            else:
                peer_id = 2000000000 + dialog['conversation']['peer']['id']
            # get user info
            user_info = vk.users.get(user_ids=peer_id)
            if user_info:
                user_info = user_info[0]
                user_name = user_info['first_name']
                user_last = user_info['last_name']
            else:
                user_name = 'unknown'
                user_last = 'unknown'

            # get last five messages
            messages = vk.messages.getHistory(
                peer_id=peer_id, count=5)['items']

            """
            generating a message to send
            format First name Last name: text
            """
            for message in reversed(messages):
                sender_id = message['from_id']
                sender_info = vk.users.get(user_ids=sender_id)[0]
                sender_name = sender_info['first_name']
                sender_last = sender_info['last_name']

                text = message['text']

                message_dict = {
                    "sender_name": sender_name,
                    "sender_last": sender_last,
                    "text": text,
                }
                formatted_message = f"{sender_name} {sender_last}: {text}"

                # send message
                if text != "":
                    bot.send_message(chat_id, formatted_message)
                else:
                    pass
            # transition to a new dialogue
            bot.send_message(chat_id, '...')

        """
        test function. Get video from vk-newsfeed
        """

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


# start bot
bot.infinity_polling()
