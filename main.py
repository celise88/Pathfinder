# Author: Caitlin Blackmore
# Project: Pathfinder
# Project Description: This is a web application designed to facilitate job-mobility. 
# It uses NLP to help job seekers find jobs that match their skills and interests.
# Date: 2023-02-03
# File Description: This is the main file, containing the FastAPI app and all the endpoints.
# License: MIT License

# IMPORTS
from fastapi import FastAPI, Request, Form, File, UploadFile, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import pandas as pd
from scrape_onet import get_onet_code, get_onet_description, get_onet_tasks
from match_utils import neighborhoods, get_resume, skillNER, sim_result_loop, get_links
import time

# APP SETUP
app = FastAPI()
app.mount("/static", StaticFiles(directory='static'), name="static")
templates = Jinja2Templates(directory="templates/")

# LOAD DATA
onet = pd.read_csv('static/ONET_JobTitles.csv')

### JOB INFORMATION CENTER ###
# GET
@app.get("/")
def get_job(request: Request):
    joblist = onet['JobTitle']
    return templates.TemplateResponse('job_list.html', context={'request': request, 'joblist': joblist})

# POST
@app.post("/")
def post_job(request: Request, bt: BackgroundTasks, jobtitle: str = Form(enum=[x for x in onet['JobTitle']])):
    joblist = onet['JobTitle']
    if jobtitle: 
        onetCode = get_onet_code(jobtitle)
        jobdescription = get_onet_description(onetCode)
        tasks = get_onet_tasks(onetCode)
        bt.add_task(neighborhoods, jobtitle)
        return templates.TemplateResponse('job_list.html', context={
            'request': request, 
            'joblist': joblist, 
            'jobtitle': jobtitle, 
            'jobdescription': jobdescription, 
            'tasks': tasks})

### JOB NEIGHBORHOODS ###
@app.get("/explore-job-neighborhoods/", response_class=HTMLResponse)
async def get_job_neighborhoods(request: Request):
    return templates.TemplateResponse('job_neighborhoods.html', context={'request': request})

### FIND-MY-MATCH ###
# GET
@app.get("/find-my-match/", response_class=HTMLResponse)
def get_matches(request: Request):
    return templates.TemplateResponse('find_my_match.html', context={'request': request})

# POST
@app.post('/find-my-match/', response_class=HTMLResponse)
async def post_matches(request: Request, resume: UploadFile = File(...)):
    t = time.time()
    resume = get_resume(resume)
    skills = await skillNER(resume)
    simResults = await sim_result_loop(resume)
    links = get_links(simResults)
    print(time.time() - t)
    return templates.TemplateResponse('find_my_match.html', context={'request': request, 'resume': resume, 'skills': skills, 'simResults': simResults, 'links': links})

@app.get("/find-match/", response_class=HTMLResponse)
def find_match(request: Request):
    return templates.TemplateResponse('find_match.html', context={'request': request})

@app.get("/find-my-hire/", response_class=HTMLResponse)
def get_hires(request: Request):
    return templates.TemplateResponse('candidate_matcher.html', context={'request': request})

# POST
@app.post('/find-my-hire/', response_class=HTMLResponse)
async def post_matches(request: Request, jobdesc: UploadFile = File(...)):
    t = time.time()
    jobdesc = get_resume(jobdesc)
    skills = await skillNER(jobdesc)
    simResults = await sim_result_loop(jobdesc)
    links = get_links(simResults)
    print(time.time() - t)
    return templates.TemplateResponse('candidate_matcher.html', context={'request': request, 'jobdesc': jobdesc, 'skills': skills, 'simResults': simResults, 'links': links})

@app.get("/find-hire/", response_class=HTMLResponse)
def find_hire(request: Request):
    return templates.TemplateResponse('find_hire.html', context={'request': request})