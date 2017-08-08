import spotipy
import random
import re
import telegram
import schedule
import threading
import time
import pickle
import config
import os.path
from spotipy.oauth2 import SpotifyClientCredentials
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# YOUTUBE API #
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

DEVELOPER_KEY = config.credentials['google_dev']
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
VIDEO = 'https://www.youtube.com/watch?v='

def youtube_search(title):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  # Call the search.list method to retrieve results matching the specified
  # query term.
  print('asking youtube', title)
  search_response = youtube.search().list(
    q=title,
    part="id,snippet",
    maxResults=1,
    type='video',
  ).execute()

  id = search_response['items'][0]['id']['videoId']
  return VIDEO+id


#######################################	

audio_format = ('.mp3', '.wav')
music = 'musicList.txt'
black_list = ('(Video	)')

client_credentials_manager= SpotifyClientCredentials()
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

if os.path.isfile('users.pkl'):
	USERS = pickle.load(open('users.pkl','rb+'))
else:
	USERS = set([])


with open(music, 'r') as file:
	songs = file.read().splitlines()


def clear_title(song):
	song = song.replace('_', ' ')
	m = re.match('([^A-Z,a-z,0-9]+)(.*)\.', song)
	return m.group(2).lower()


def random_song(songs, num_songs):
	drawed = 0
	selected = []
	total = len(songs)
	while drawed < num_songs:
		n = random.randint(0, total-1)
		song = songs[n]
		if song.endswith(audio_format):
			drawed += 1
			selected.append(clear_title(song))
	return selected


def ask_spotify(song_list, spotify):
	for song in song_list:
		print(song)
		results = spotify.search(q=song, type='track')
		try:
			s = results['tracks']['items'][0]['external_urls']['spotify']
			print(s)
		except IndexError:
			try:
				s = youtube_search(song)
				print(s)
			except (HttpError, e):
				print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

			# s = 'Bobby salva le canzoni con nomi di merda, sta roba qua "{:s}" non esiste su Spotify'.format(song)
	return s

def start(bot, update):
	user = update.message['chat']['id']
	USERS.add(user)
	bot.send_message(chat_id=update.message.chat_id, text='Bishop is the answer!')
	print(USERS)
	pickle.dump(USERS, open('users.pkl','wb+'))


def stop(bot, update):
	user = update.message['chat']['id']
	USERS.remove(user)
	print(USERS)
	pickle.dump(USERS, open('users.pkl','wb+'))



def bobby(bot, update):
	song = ask_spotify(random_song(songs, 1), spotify)
	bot.send_message(chat_id=update.message.chat_id, text=song)


def test(bot, update):
	print('alive')


def stupid_job(bot):
	song = 'It\'s Bobby time!\n'
	song += ask_spotify(random_song(songs, 1), spotify)
	for user in USERS:
		bot.send_message(chat_id=user, text=song)


def daily_song(bot):
	schedule.every().day.at('11:00').do(stupid_job, bot)
	while True:
	    schedule.run_pending()
	    time.sleep(1)

def help(bot, update):
	help_msg = 'Supported commands:\n/bobby to get a daily song\n/help to see this message\n' + \
				'/start to subscribe to the automatic daily song\n/stop to unsubscribe'
	bot.send_message(chat_id=update.message.chat_id, text=help_msg)

def unknown(bot, update):
	msg = 'Unsupported command, try /help for more information'
	bot.send_message(chat_id=update.message.chat_id, text=msg)

	


def main():
	print(USERS)
	bot = telegram.Bot(config.credentials['telegram_bot'])
	updater = Updater(config.credentials['telegram_bot'])

	updater.dispatcher.add_handler(CommandHandler('start', start))
	updater.dispatcher.add_handler(CommandHandler('stop', stop))
	updater.dispatcher.add_handler(CommandHandler('bobby', bobby))
	updater.dispatcher.add_handler(CommandHandler('test', test))
	updater.dispatcher.add_handler(CommandHandler('help', help))
	unknown_handler = MessageHandler(Filters.command, unknown)
	updater.dispatcher.add_handler(unknown_handler)
	
	t = threading.Thread(target=daily_song, args=(bot,), daemon=True)
	t.start()
	updater.start_polling()
	updater.idle()


if __name__=='__main__':
	main()

