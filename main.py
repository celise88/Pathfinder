from fastapi import FastAPI, Request, Form, File, Query, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import pandas as pd
import requests
from bs4 import BeautifulSoup
from cleantext import clean
from typing import List, Optional
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory='static'), name="static")
templates = Jinja2Templates(directory="templates/")

onet = pd.read_csv('static/ONET_JobTitles.csv')
coheredat = pd.read_csv('static/cohere_tSNE_dat.csv')
simdat = pd.read_csv('static/cohere_embeddings.csv')

### job information center ###
# get
@app.get("/")
def render_job_list(request: Request):
    joblist = onet['JobTitle']
    return templates.TemplateResponse('job_list.html', context={'request': request, 'joblist': joblist})

# post
@app.post("/")
def render_job_info(request: Request, jobtitle: str = Form(enum=[x for x in onet['JobTitle']])):
    
    def remove_new_line(value):
        return ''.join(value.splitlines())

    joblist = onet['JobTitle']

    if jobtitle: 
        onetCode = onet.loc[onet['JobTitle'] == jobtitle, 'onetCode']
        onetCode = onetCode.reindex().tolist()[0]
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}
        url = "https://www.onetonline.org/link/summary/" + onetCode
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobdescription = soup.p.get_text()
                
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
        return templates.TemplateResponse('job_list.html', context={
            'request': request, 
            'joblist': joblist, 
            'jobtitle': jobtitle, 
            'jobdescription': jobdescription, 
            'tasks': tasks})

### job neighborhoods ###
@app.get("/explore-job-neighborhoods/", response_class=HTMLResponse)
async def render_job_neighborhoods(request: Request):
    return templates.TemplateResponse('job_neighborhoods.html', context={'request': request})

### find my match ###
# get
@app.get("find_my_match.html", response_class=HTMLResponse)
async def render_matches(request: Request):
    pass

# post
@app.post("find_my_match.html", response_class=HTMLResponse)
async def render_matches(request: Request, resume: str = File(...)):
    pass