import re
import sys
import json
import requests
import operator
from tqdm import tqdm
from bs4 import BeautifulSoup
from plotly.graph_objs import *
from plotly.offline import init_notebook_mode, plot

from colorama import init
init()

def isNumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

minThreshold = 3.0
maxThreshold = 10000.0
tagLimit = 100
achievRestrict = False

playerId = raw_input("Your steam id: ")
minThresholdInput = raw_input("Minimum hours (default 3): ")
maxThresholdInput = raw_input("Maximum hours (default 10000): ")
tagLimitInput = raw_input("Tag limit (default none): ")
achievRestrictInput = raw_input("Ignore games with no achievement unlocked? (Default NO)\nNote: This will not affect games that have no achievements.\n      This will take way longer time. (Y/N): ")

print("\nGenerating game list...")
if(isNumber(playerId)):
    url = "http://steamcommunity.com/profiles/" + playerId 
else:
    url = "http://steamcommunity.com/id/" + playerId

if isNumber(minThresholdInput):
    minThreshold = float(minThresholdInput)
if isNumber(maxThresholdInput):
    maxThreshold = float(maxThresholdInput)
if isNumber(tagLimitInput):
    tagLimit = float(tagLimitInput)
if achievRestrictInput == 'Y':
    achievRestrict = True


cookies = { 'birthtime': '283993201', 'mature_content': '1' }
page = requests.get(url + "/games/?tab=all" , cookies=cookies).text
want = json.loads(re.search(r"var rgGames = (.*);", page).group(1))

gameHourList = {}
nameDict = {}
whiteList = [242050]

t1 = tqdm(want)
for eachJson in t1:
    hasAchiev = True
    appID = eachJson['appid']
    gameName = eachJson['name'].encode('ascii', 'ignore')
    if achievRestrict:
        if eachJson['availStatLinks']['achievements']:
            achievUrl = url + "/stats/" + str(appID) + "/?tab=achievements"
            achievPage = requests.get(achievUrl, cookies=cookies).content
            achievSoup = BeautifulSoup(achievPage, 'html.parser')
            achievSummary = achievSoup.find("div", id="topSummaryAchievements")
            if achievSummary is not None:
                summaryText = achievSummary.get_text().strip()
                if summaryText.startswith('0') and not appID in whiteList:
                    print("\nThis game will be ignored because there is no achievement unlocked: " + gameName)
                    continue
    if 'hours_forever' in eachJson and float(eachJson['hours_forever'].replace(",", "")) > maxThreshold:
        print("\nThis game will be ignored because its number of hours exceed maximum threshold: " + gameName)
        continue
    if 'hours_forever' in eachJson and float(eachJson['hours_forever'].replace(",", "")) < minThreshold:
        print(gameName + " and other games with low hours will be ignored.")
        break
    gameHourList[appID] = float(eachJson['hours_forever'].replace(",", "")) if 'hours_forever' in eachJson else 0.0
    nameDict[appID] = gameName 

sumList = {}

print("There are " + str(len(gameHourList)) + " games to analyze in total.")

print("\nStarting the analysis...")
t = tqdm(gameHourList.items())
for appid, hour in t:
    gameUrl = "http://store.steampowered.com/app/" + str(appid)
    gamePage = requests.get(gameUrl, cookies=cookies).content
    soup = BeautifulSoup(gamePage, 'html.parser')
    t.set_description('Analyzing game %s' % nameDict[appid])
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
                    "size": 40
                },
                "showarrow": False,
                "text": playerId,
                "x": 0.5,
                "y": 0.5
            }
        ]
    }
fig = dict( data=data, layout=layout )
plot(fig, filename=playerId+".html")