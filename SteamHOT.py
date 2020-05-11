import re
import sys
import json
import requests
import operator
from collections import defaultdict
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

# Gets and interprets input
playerId = input("Your steam id: ")
minThresholdInput = input("Minimum hours (default 3): ")
maxThresholdInput = input("Maximum hours (default 10000): ")
tagLimitInput = input("Tag limit (default none): ")
achievRestrictInput = input("Ignore games with no achievement unlocked? (Default NO)\nNote: This will not affect games that have no achievements.\n      This will take a lot longer time. (Y/N): ")

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
achievRestrict = achievRestrictInput == 'Y'

print("\nGenerating game list...")

cookies = { 'birthtime': '283993201', 'mature_content': '1' }
page = requests.get(url + "/games/?tab=all" , cookies=cookies).text
want = json.loads(re.search(r"var rgGames = (.*);", page).group(1))

gameHourList = {}
nameDict = {}
whiteList = []

# Shows progress bar #1
t1 = tqdm(want)
for eachJson in t1:
    hasAchiev = True
    appID = eachJson['appid']
    gameName = eachJson['name']
    if achievRestrict:
        # Excludes games with no achievements unlocked
        if eachJson['availStatLinks']['achievements']:
            achievUrl = url + "/stats/" + str(appID) + "/?tab=achievements"
            achievPage = requests.get(achievUrl, cookies=cookies).content
            achievSoup = BeautifulSoup(achievPage, 'html.parser')
            achievSummary = achievSoup.find("div", id="topSummaryAchievements")
            if achievSummary is not None:
                summaryText = achievSummary.get_text().strip()
                if summaryText.startswith('0') and not summaryText.startswith('0 of 0') and not appID in whiteList:
                    print("\nThis game will be ignored because there is no achievement unlocked: " + gameName)
                    continue
    # Gets number of hours
    hours = 0
    if 'hours_forever' in eachJson:
        hours = float(eachJson['hours_forever'].replace(",", ""))
        # Excludes games with number of hours > maximum threshold
        if hours > maxThreshold:
            print("\nThis game will be ignored because its number of hours exceed maximum threshold: " + gameName)
            continue
        # Excludes games with number of hours < minimum threshold. The list is already sorted, so we direclty break here.
        if hours < minThreshold:
            print("\n" + gameName + " and other games with low number of hours will be ignored.")
            break
    gameHourList[appID] = hours
    nameDict[appID] = gameName 

print("There are " + str(len(gameHourList)) + " games to analyze in total.\nStarting the analysis...")

sumDict = defaultdict(float)
# Shows progress bar #2
t2 = tqdm(gameHourList.items())
# Generates the tag->hours dict
for appid, hour in t2:
    gameUrl = "http://store.steampowered.com/app/" + str(appid)
    gamePage = requests.get(gameUrl, cookies=cookies).content
    soup = BeautifulSoup(gamePage, 'html.parser')
    t2.set_description('Analyzing game {}'.format(nameDict[appid]))
    tags = soup.find_all("a", class_="app_tag")
    count = 1
    for tag in tags:
        tag = tag.get_text().strip()
        sumDict[tag] += hour
        count+=1
        if(count>tagLimit):
            break

# Draws the pie
trace = Pie(labels=list(sumDict.keys()), values=list(sumDict.values()),
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
fig = dict(data=data, layout=layout)
plot(fig, filename=playerId+".html")