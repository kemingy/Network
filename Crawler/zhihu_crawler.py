import urllib
from BeautifulSoup import *
import re
import requests

url = raw_input('Please input the url: ')
save_path = 'F:/temp/'
limit = int(raw_input('limit: '))
i = 0
html = urllib.urlopen(url).read()
soup = BeautifulSoup(html)
imgs = soup('img')
for img in imgs:
    if i >= limit:
        break
    img = img.get('src')
    if img and re.search(r'^https://pic.*?_b\..*[gf]$', img):
        fw = open(save_path + img[img.rfind('/')+1:], 'wb')
        fw.write(requests.get(img).content)
        fw.close()
        i += 1
