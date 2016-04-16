import urllib
from BeautifulSoup import *
import re
import requests

url = 'https://www.zhihu.com/question/36513074'
save_path = 'F:/temp/'
limit = 50
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
