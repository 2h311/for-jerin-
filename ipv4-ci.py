from itertools import cycle
import logging
import threading
import time

import requests
from selenium import webdriver
from selenium.common.exceptions import JavascriptException
from fake_useragent import UserAgent

class TwoCaptcha(object):
	inputurl = 'https://2captcha.com/in.php'
	resulturl = 'http://2captcha.com/res.php'

	def __init__(self, api_key='', googlekey=''):
		'''
		https://2captcha.com/in.php?key=1abc234de56fab7c89012d34e56fa7b8&method=userrecaptcha&googlekey=6Le-wvkSVVABCPBMRTvw0Q4Muexq1bi0DJwx_mJ-&pageurl=http://mysite.com/page/with/recaptcha

		'''
		self.googlekey = googlekey
		self.api_key = api_key

	def solve(self, browser):
		pageurl = browser.current_url
		logging.info(f'Attempting to solve captcha on page: {pageurl}')
		token = self.initial(pageurl)
		# do the thingy on the page 
		browser.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML="{token}";')

	def initial(self, pageurl=''):
		data = {'key': self.api_key, 
				'method': 'userrecaptcha', 
				'googlekey': self.googlekey,
				'pageurl': pageurl
				}
		r = requests.post(self.inputurl, data=data, timeout=60)
		if r and r.status_code == requests.codes.ok:
			logging.debug('Captcha Request OK')
			if '|' in r.text:
				id_ = r.text.split('|')[-1]
				return self.wait_on_result(id_)
		
	def wait_on_result(self, id_):
		while True:
			logging.info('Waiting for captcha result.. ')
			logging.debug('Sleeping for 15 seconds')
			time.sleep(15)
			r2 = requests.get(f'{self.resulturl}?key={self.api_key}&action=get&id={id_}', timeout=5)
			logging.debug(r2.text)
			if r2 and r2.status_code == requests.codes.ok:
				if 'OK' in r2.text:
					captcha = r2.text.split('|')[-1]
					logging.info('Captcha solved !')
					return captcha


def make_driver_settings(proxy=None):
	opts = webdriver.ChromeOptions()
	chrome_prefs = {}
	opts.experimental_options["prefs"] = chrome_prefs
	chrome_prefs["profile.default_content_settings"] = {"images" : 2}
	chrome_prefs["profile.managed_default_content_settings"] = {"images" : 2}
	opts.add_argument(f"user-agent={user_agent_randomizer.random}")

	if proxy:
		opts.add_argument('--proxy-server=socks5://%s' % proxy)

	driver = webdriver.Chrome(executable_path='./chromedriver.exe', options=opts)
	driver.implicitly_wait(5)
	return driver

def vote(proxy):
	driver = ''
	try:
		driver = make_driver_settings(proxy)
		driver.get(URL)

		googlekey = driver.find_element_by_css_selector(".g-recaptcha").get_attribute('data-sitekey')
		solver = TwoCaptcha(API_KEY, googlekey)
		solver.solve(driver)

		vote = driver.find_element_by_css_selector('input[value="Voter"]')
		driver.execute_script("arguments[0].click();", vote)

		alert = driver.switch_to.alert
		text = alert.text
		if text == "Succès. Vote enregistré.":
			print("Upvote Done.")
		else:
			print(text)
		alert.accept()
		time.sleep(1)
		driver.quit()
	except Exception:
		if driver:
			driver.quit()
		
def main(proxy_list):
	def wrapper():
		try:
			start = time.time()
			for proxy in proxy_list:
				vote(proxy)	
			end = time.time()
			diff = end - start
			if diff < 3600:
				time.sleep(3600 - diff)
		except Exception as err:
			print(f"An Error Occured: {err}")
	
	while True:
		wrapper()

def create_proxy_pool():
	'''
	create a proxy pool
	'''
	with open('./shared.txt', 'r') as proxies:
		proxies = [proxy.strip() for proxy in proxies.readlines()]
	return proxies

def spawn_threads():
	'''
	this functions spawns worker threads
	'''
	threads = list()
	proxy_amount_for_each_thread = 10
	for amount in range(0, len(PROXIES_LIST), proxy_amount_for_each_thread):
		proxy_list = PROXIES_LIST[amount:amount+proxy_amount_for_each_thread]
		thread = threading.Thread(target=main, args=(proxy_list,))
		thread.start()
		threads.append(thread)

	for thread in threads:
		thread.join()

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	user_agent_randomizer = UserAgent(fallback='Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2')
	API_KEY = "70ce26d858b55dd33f3be14787203220"
	URL = 'https://ci.miss20.org/candidats/myriane/'
	PROXIES_LIST = create_proxy_pool()
	logging.disable()
	spawn_threads()