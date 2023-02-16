import requests
from bs4 import BeautifulSoup
from cleantext import clean
import pandas as pd
import numpy as np

onet = pd.read_csv('static/ONET_JobTitles.csv')
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}

def remove_new_line(value):
        return ''.join(value.splitlines())

def get_onet_code(jobtitle):
    onetCode = onet.loc[onet['JobTitle'] == jobtitle, 'onetCode']
    onetCode = onetCode.reindex().tolist()[0]
    return onetCode

def get_onet_description(onetCode):
    url = "https://www.onetonline.org/link/summary/" + onetCode
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobdescription = soup.p.get_text()
    return jobdescription

def get_onet_tasks(onetCode):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}
    url = "https://www.onetonline.org/link/result/" + onetCode + "?c=tk&n_tk=0&s_tk=IM&c_tk=0"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    tasks = str(soup.get_text('reportsubdesc')).replace("reportsubdesc", " ").replace("ImportanceCategoryTask ", "")
    tasks = clean(tasks)
    tasks = tasks.split('show all show top 10')[1]
    tasks = tasks.split('occupations related to multiple tasks')[0]
    tasks = remove_new_line(tasks).replace("related occupations", " ").replace("core", " - ").replace(" )importance category task", "").replace(" find ", "")
    tasks = tasks.split(". ")
    tasks = [''.join(map(lambda c: '' if c in '0123456789-' else c, task)) for task in tasks]
    return tasks

def get_job_postings(onetCode, state):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}
    url = "https://www.onetonline.org/link/localjobs/" + onetCode + "?st=" + state
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = str(soup.get_text("tbody")).split('PostedtbodyTitle and CompanytbodyLocation')[1].split('Sources:')[0].split("tbody")
    jobs = jobs[5:45]
    starts = np.linspace(start=0, stop=len(jobs)-4,num= 10)
    stops = np.linspace(start=3, stop=len(jobs)-1, num= 10)
    jobpostings = []
    for i in range(0,10):
        jobpostings.append(str([' '.join(jobs[int(starts[i]):int(stops[i])])]).replace("['", '').replace("']", ''))
    links = str(soup.find_all('a', href=True)).split("</small>")[1].split(', <a href="https://www.careeronestop.org/"')[0].split(' data-bs-toggle="modal" ')
    linklist = []
    for i in range(1, len(links)):
        links[i] = "https://www.onetonline.org" + str(links[i]).split(' role="button">')[0].replace("href=", "")
        linklist.append(links[i].replace('"', ''))
    return jobpostings, linklist