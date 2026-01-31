import os
import platform
from lazysdk import lazychromedriver

# browser_version = lazychromedriver.get_browser_version()
# print(browser_version)
# driver_url = lazychromedriver.find_driver_url()
# print(driver_url)
print(lazychromedriver.download_driver())

"""
chromedriver镜像地址：
https://repo.huaweicloud.com/chromedriver/
https://repo.huaweicloud.com/chromedriver/.index.json
"""