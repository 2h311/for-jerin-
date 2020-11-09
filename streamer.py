import csv
import functools
import random
import re
from itertools import cycle
import threading
from time import sleep

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import account
import proxy

def retry_request(func, retry_times=3):
	'''
	decorator - for retrying a failed request
	'''
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		for num in range(1, retry_times+1):
			print(f"Running {func.__name__}. Try {num}")
			try:
				status = func(*args, **kwargs)
				if status:
					return
			except Exception as exp:
				print(f"An error occured: {exp}")			
	return wrapper

def fetch_playlist():
	'''
	open the playlist file and read them in
	'''
	playlist = list()
	with open('playlist.csv', 'r') as fp:
		reader = csv.reader(fp)
		for content in reader:
			playlist.append(content)
	return playlist

def create_proxy_pool():
	'''
	create a proxy pool
	'''
	with open('./shared.txt', 'r') as proxies:
		proxies = [proxy.strip() for proxy in proxies.readlines()]
		return cycle(proxies)

def close_browser(driver):
	# print("Closing browser")
	driver.quit()

def create_driver():
	try:
		ip = next(proxy_pool)
		driver = proxy.get_chromedriver(True, *ip.split(":"))
		driver.implicitly_wait(wait_time)
		return driver
	except Exception as err:
		print(f"An Error Occured: {err}")
			
def like_track(driver):
	# like music | save to library
	try:
		like_music_element = WebDriverWait(driver, wait_time*3).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button[title='Save to Your Library']")))
		driver.execute_script("arguments[0].click();", like_music_element)
	except Exception as exp:
		print(f"An Error occured: {exp}")

def music_is_playing():
	print("Music is playing...")
	sleep(random.randint(1670, 1870))

def login(credentials, driver):
	# each worker can stream from the playlist
	# driver = create_driver()
	try:
		driver.get('https://accounts.spotify.com/en/login')
		# login to the created account

		WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.ID, 'login-username')))
		# input the email
		username = driver.find_element_by_xpath('//*[@id="login-username"]')
		username.clear()
		username.send_keys(credentials['email'])
		# input the password	
		password = driver.find_element_by_xpath('//*[@id="login-password"]')
		password.clear()
		password.send_keys(credentials['password'])
		driver.find_element_by_xpath('//*[@id="login-button"]').click()

		# wait until this account overview button appears
		WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.user-details.ng-binding')))
		# returns True if the status page is displayed, which is a good sign of proper login
		login_signal = WebDriverWait(driver, wait_time).until(EC.url_to_be('https://accounts.spotify.com/en/status'))
	except (WebDriverException, TimeoutException):
		login_signal = False
	except Exception:
		login_signal = False
	finally:
		return login_signal

def load_music(driver):
	driver.get(play[0])

def press_play(driver):
	# wait for the playlist page to be visible, this is where the first play button and the tracks reside.
	playlist_page = WebDriverWait(driver, wait_time).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid*="playlist-page"]')))
	if playlist_page:
		# driver.find_element_by_css_selector('[data-testid*="playlist-page"]')
		play_button_elements = playlist_page.find_elements_by_xpath("//button[@data-testid='play-button']")
		print("Play buttons Found")
		# for element in play_button_elements:
		driver.execute_script("arguments[0].click();", play_button_elements[-1])
		print("Play button clicked.. Checking if playlist is playing.")
		for num in range(5):
			sleep(random.randint(5, 12))
			if play_button_elements[0].get_attribute("title").lower() != "play" or play_button_elements[-1].get_attribute("title").lower() != "play":
				print("Playlist is Playing")
				playlist_status = True

def main(credentials):
	driver = create_driver()
	signal = login(credentials, driver)
	if signal:
		load_music(driver)
		# wait for the url to contain the playlist url
		status = WebDriverWait(driver, wait_time).until(EC.url_contains(play[0]))
		press_play(driver)
		music_is_playing()
		close_browser(driver)

wait_time = 45
proxy_pool = create_proxy_pool()
playlist = fetch_playlist()
play = playlist[0]

# main()