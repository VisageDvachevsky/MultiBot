
"""
This bot has great functionality, mainly related to social network VK,
for example, reciving a news feed, but there are also functions outside VK, for example, search in sites
"""

import time
import os
import requests
import numpy as np


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
import cv2 
from PIL import ImageFont, ImageDraw, Image

import config

bot = telebot.TeleBot(config.TgToken)
vk_session = vk_api.VkApi(token=config.VkToken)

# required variable
API_KEY = config.GoogleAPIKey
SEARCH_ENGINE_ID = config.EngineID
start_from = ''
font_path = r"C:\Windows\Fonts\ARIALN.TTF"
font = ImageFont.truetype(font_path, 60)


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
    keyboard.add(button1)
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
            time.sleep(1)
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

# start bot
bot.infinity_polling()
