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
				return func(*args, **kwargs)
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

@retry_request
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
		login_signal = True
	except (WebDriverException, TimeoutException):
		login_signal = False
	except Exception:
		login_signal = False

	return login_signal

def load_music(driver):
	driver.get("https://www.spotify.com/us/legal/end-user-agreement/plain/")
	WebDriverWait(driver, wait_time).until(EC.url_to_be("https://www.spotify.com/us/legal/end-user-agreement/plain/"))
	driver.get(play[0])

@retry_request
def press_play(driver):
	# wait for the playlist page to be visible, this is where the first play button and the tracks reside.
	# driver.find_element_by_css_selector('[data-testid*="playlist-page"]')
	
	WebDriverWait(driver, wait_time).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid*="tracklist-row"]')))
	playlist_page = WebDriverWait(driver, wait_time).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid*="playlist-page"]')))
	if playlist_page:
		playing = False
		play_button_elements = WebDriverWait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, "//button[@data-testid='play-button']")))
		# play_button_elements = playlist_page.find_elements_by_xpath("//button[@data-testid='play-button']")
		print("Play buttons Found")
		for num in range(5):
			for element in play_button_elements:
				if not playing:
					driver.execute_script("arguments[0].click();", element)
					print("Play button clicked.. Checking if playlist is playing.")
				sleep(random.randint(10, 12))
				if play_button_elements[0].get_attribute("title").lower() != "play" or play_button_elements[-1].get_attribute("title").lower() != "play":
					print("Playlist is Playing")
					playing = True
		return playing

def main(credentials):
	try:
		driver = create_driver()
		signal = login(credentials, driver)
		if signal:
			load_music(driver)
			# wait for the url to contain the playlist url
			# status = WebDriverWait(driver, wait_time).until(EC.url_contains(play[0]))
			status = press_play(driver)
			if status:
				music_is_playing()
	finally:
		close_browser(driver)


wait_time = 45
proxy_pool = create_proxy_pool()
playlist = fetch_playlist()
play = playlist[0]

# credentials = account.create_account()
# main(credentials)
