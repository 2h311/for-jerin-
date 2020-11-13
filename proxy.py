import os
import zipfile

from selenium import webdriver

def get_chromedriver(use_proxy, host, port, user, password):
	manifest_json = """
	{
		"version": "1.0.0",
		"manifest_version": 2,
		"name": "Chrome Proxy",
		"permissions": [
			"proxy",
			"tabs",
			"unlimitedStorage",
			"storage",
			"<all_urls>",
			"webRequest",
			"webRequestBlocking"
		],
		"background": {
			"scripts": ["background.js"]
		},
		"minimum_chrome_version":"22.0.0"
	}
	"""

	background_js = """
	var config = {
			mode: "fixed_servers",
			rules: {
			singleProxy: {
				scheme: "http",
				host: "%s",
				port: parseInt(%s)
			},
			bypassList: ["localhost"]
			}
		};

	chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

	function callbackFn(details) {
		return {
			authCredentials: {
				username: "%s",
				password: "%s"
			}
		};
	}

	chrome.webRequest.onAuthRequired.addListener(
				callbackFn,
				{urls: ["<all_urls>"]},
				['blocking']
	);
	""" % (host, port, user, password)

	options = webdriver.ChromeOptions()
	
	binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
	if os.path.exists(binary_location):
		options.binary_location = binary_location
	
	options.add_experimental_option("useAutomationExtension", False)
	options.add_experimental_option("excludeSwitches", ["enable-automation"])
	options.add_argument("--start-maximized")
	options.add_argument('--disable-blink-features=AutomationControlled')
	chrome_prefs = {}
	options.experimental_options["prefs"] = chrome_prefs
	chrome_prefs["profile.default_content_settings"] = {"images" : 2}
	chrome_prefs["profile.managed_default_content_settings"] = {"images" : 2}
	
	if use_proxy:
		pluginfile = 'proxy_auth_plugin.zip'
		with zipfile.ZipFile(pluginfile, 'w') as zp:
			zp.writestr("manifest.json", manifest_json)
			zp.writestr("background.js", background_js)
		
		options.add_extension(pluginfile)

	driver = webdriver.Chrome(executable_path='./chromedriver.exe', options=options)
	return driver