# Author: Caitlin Blackmore
# Project: Pathfinder
# Project Description: This is a web application designed to facilitate job-mobility. 
# It uses NLP to help job seekers find jobs that match their skills and interests.
# Date: 2023-02-03
# File Description: This is the main file, containing the FastAPI app and all the endpoints.
# License: MIT License

# IMPORTS
from fastapi import FastAPI, Request, Form, File, UploadFile, BackgroundTasks, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import pandas as pd
import time
from uuid import uuid1
from localStoragePy import localStoragePy
localStorage = localStoragePy('pathfinder', 'text')

from scrape_onet import get_onet_code, get_onet_description, get_onet_tasks
from match_utils import neighborhoods, get_resume, skillNER, sim_result_loop, get_links, coSkillEmbed, sim_result_loop_jobFinder, sim_result_loop_candFinder
from user_utils import Hash

# APP SETUP
app = FastAPI()
app.mount("/static", StaticFiles(directory='static'), name="static")
templates = Jinja2Templates(directory="templates/")

# LOAD DATA
onet = pd.read_csv('static/ONET_JobTitles.csv')

@app.get("/register/", response_class=HTMLResponse)
def get_register(request: Request):
    return templates.TemplateResponse('register.html', context={'request': request})

@app.get("/login/", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse('login.html', context={'request': request})

@app.post('/register/', response_class=HTMLResponse)
def post_register(request: Request, username: str = Form(...), password: str = Form(...), email: str = Form(...), account_type: str = Form(...)):
    if account_type == "candidate":
        db = pd.read_csv('static/res_embeddings.csv')
    else:
        db = pd.read_csv('static/jd_embeddings.csv')
    if username not in db['username'] and email not in db['email']:
        new_row = len(db.index)+1
        db.loc[new_row, 'id'] = uuid1()
        db.loc[new_row, 'username'] = username
        db.loc[new_row, 'password'] = Hash.bcrypt(password)
        db.loc[new_row, 'email'] = email
        db.loc[new_row, 'account_type'] = account_type
        message = "You have registered successfully. Please log in to continue"
        if account_type == "candidate":
            db.to_csv('static/res_embeddings.csv', index=False)
        else:
            db.to_csv('static/jd_embeddings.csv', index=False)
        return templates.TemplateResponse('register.html', context={'request': request, 'message': message})
    elif email in db['email']:
        message = "That email address has already been registered. Please try again."
        return templates.TemplateResponse('register.html', context={'request': request, 'message': message})
    elif username in db['username']:
        message = "That username has already been taken. Please select another."
        return templates.TemplateResponse('register.html', context={'request': request, 'message': message})

@app.post("/login/", response_class=HTMLResponse)
def post_login(request: Request, username: str = Form(...), password: str = Form(...)):
    
    pd.set_option('display.max_colwidth', 100)
    dbres = pd.read_csv('static/res_embeddings.csv')
    dbjd = pd.read_csv('static/jd_embeddings.csv')

    if username in list(dbres['username']):
        pw = dbres.loc[dbres['username'] == username,'password'].to_string()
        pw = pw.split(' ')[4]
        if Hash.verify(password, pw) == True:
            un = dbres.loc[dbres['username'] == username,'username'].to_string().split(' ')[4]
            localStorage.setItem('username', un)
            print(localStorage.getItem('username'))
            message = "You have been successfully logged in."
        else:
            message = "Username or password not found. Please try again."
    elif username in list(dbjd['username']):
        pw = dbjd.loc[dbjd['username'] == username,'password'].to_string()
        pw = pw.split(' ')[4]
        if Hash.verify(password, pw) == True:
            un = dbjd.loc[dbjd['username'] == username,'username'].to_string().split(' ')[4]
            localStorage.setItem('username', un)
            print(localStorage.getItem('username'))
            message = "You have been successfully logged in."
        else:
            message = "Username or password not found. Please try again."
    else:
        message = "Username or password not found. Please try again."
    return templates.TemplateResponse('login.html', context={'request': request, "message": message})

@app.get("/logout/", response_class=HTMLResponse)
def get_logout(request: Request):
    return templates.TemplateResponse('logout.html', context={'request': request})

@app.post("/logout/", response_class=HTMLResponse)
def post_logout(request: Request):
    localStorage.clear()
    print(localStorage.getItem('username'))
    message = "You have been successfully logged out."
    return templates.TemplateResponse('logout.html', context={'request': request, 'message': message})

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
async def post_matches(request: Request, bt: BackgroundTasks, resume: UploadFile = File(...)):
    
    username = localStorage.getItem('username')

    def add_data_to_db(resume):
        db = pd.read_csv('static/res_embeddings.csv')
        embeds = format(coSkillEmbed(resume)).replace('[[','').replace(']]','').split(',')
        db.iloc[db['username']== username,5:] = embeds
        db.to_csv('static/res_embeddings.csv', index=False)

    def get_jobs_from_db(resume):
        job_matches = sim_result_loop_jobFinder(resume)
        print(job_matches)

    resume = get_resume(resume)
    skills = await skillNER(resume)
    simResults = await sim_result_loop(resume)
    links = get_links(simResults[0])

    if username is not None:
        bt.add_task(add_data_to_db, resume)
        bt.add_task(get_jobs_from_db, resume)

    return templates.TemplateResponse('find_my_match.html', context={'request': request, 'resume': resume, 'skills': skills, 'simResults': simResults[0], 'links': links})

@app.get("/find-match/", response_class=HTMLResponse)
def find_match(request: Request):
    jobselection = str(request.url).split("=")[1].replace('HTTP/1.1', '').replace("-", " ").replace("%2C", "")
    print(jobselection)
    return templates.TemplateResponse('find_match.html', context={'request': request, 'jobselection': jobselection})

@app.get("/find-my-hire/", response_class=HTMLResponse)
def get_hires(request: Request):
    return templates.TemplateResponse('candidate_matcher.html', context={'request': request})

# POST
@app.post('/find-my-hire/', response_class=HTMLResponse)
async def post_matches(request: Request, bt: BackgroundTasks, jobdesc: UploadFile = File(...)):

    username = localStorage.getItem('username')

    def add_data_to_db(jobdesc):
        db = pd.read_csv('static/jd_embeddings.csv')
        embeds = format(coSkillEmbed(jobdesc)).replace('[[','').replace(']]','').split(',')
        db.iloc[db['username']== username,5:] = embeds
        db.to_csv('static/jd_embeddings.csv', index=False)
    
    def get_cand_from_db(jobdesc):
        cand_matches = sim_result_loop_candFinder(jobdesc)
        print(cand_matches)

    jobdesc = get_resume(jobdesc)
    skills = await skillNER(jobdesc)
    simResults = await sim_result_loop(jobdesc)
    links = get_links(simResults[0])

    if username is not None:
        bt.add_task(add_data_to_db, jobdesc)
        bt.add_task(get_cand_from_db, jobdesc)

    return templates.TemplateResponse('candidate_matcher.html', context={'request': request, 'jobdesc': jobdesc, 'skills': skills, 'simResults': simResults[0], 'links': links})

@app.get("/find-hire/", response_class=HTMLResponse)
def find_hire(request: Request):
    jobselection = str(request.url).split("=")[1].replace('HTTP/1.1', '').replace("-", " ").replace("%2C", "")
    print(jobselection)
    return templates.TemplateResponse('find_hire.html', context={'request': request, 'jobselection': jobselection})

@app.get("/find-job/", response_class=HTMLResponse)
def find_job(request: Request):
    pass