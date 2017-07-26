import re
import sys
import json
import requests
import operator
from tqdm import tqdm
from bs4 import BeautifulSoup
from plotly.graph_objs import *
from plotly.offline import init_notebook_mode, plot


def isNumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

hourThreshold = 5.0
tagLimit = 100

if(len(sys.argv) > 1):
    playerId = str(sys.argv[1])
    if(isNumber(sys.argv[1])):
        url = "http://steamcommunity.com/profiles/" + playerId + "/games/?tab=all"
    else:
        url = "http://steamcommunity.com/id/" + playerId + "/games/?tab=all"
if(len(sys.argv) > 2 and isNumber(sys.argv[2])):
    hourThreshold = float(sys.argv[2])
if(len(sys.argv) > 3 and isNumber(sys.argv[3])):
    tagLimit = float(sys.argv[2])


cookies = { 'birthtime': '283993201', 'mature_content': '1' }
page = requests.get(url, cookies=cookies).text
want = json.loads(re.search(r"var rgGames = (.*);", page).group(1))

gameHourList = {}
for i in range (0, len (want)):
    if 'hours_forever' in want[i] and float(want[i]['hours_forever'].replace(",", "")) < hourThreshold:
        break
    gameHourList[want[i]['appid']] = float(want[i]['hours_forever'].replace(",", "")) if 'hours_forever' in want[i] else 0.0

sumList = {}

t = tqdm(gameHourList.items())
for appid, hour in t:
    gameUrl = "http://store.steampowered.com/app/" + str(appid)
    gamePage = requests.get(gameUrl, cookies=cookies).content
    soup = BeautifulSoup(gamePage, 'html.parser')
    gameName = soup.find("div", class_="apphub_AppName").get_text().encode('ascii', 'ignore')
    t.set_description('Analyzing game %s' % gameName)
    tags = soup.find_all("a", class_="app_tag")
    count = 1
    for tag in tags:
        tag = tag.get_text().strip()
        if tag in sumList:
            sumList[tag] += hour
        else:
            sumList[tag] = hour
        count+=1
        if(count>tagLimit):
            break

# sortedSumList = sorted(sumList.items(), key=operator.itemgetter(1), reverse=True)
sortedSumList = sumList.items()

keys = []
values = []
for element in sortedSumList:
    keys.append(element[0])
    values.append(element[1])


trace = Pie(labels=keys, values=values,
               hoverinfo='label+percent', textinfo='value', 
               textfont=dict(size=20), hole=0.4)
data=[trace]
layout = {
        "title":"",
        "annotations": [
            {
                "font": {
                    "size": 20
                },
                "showarrow": False,
                "text": "Hours on Tags",
                "x": 0.5,
                "y": 0.5
            }
        ]
    }
fig = dict( data=data, layout=layout )
plot(fig, filename=playerId+".html")