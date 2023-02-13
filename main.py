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
pd.set_option('display.max_colwidth', 100)
import time
from uuid import uuid1
from localStoragePy import localStoragePy
localStorage = localStoragePy('pathfinder', 'text')

from scrape_onet import get_onet_code, get_onet_description, get_onet_tasks
from match_utils import neighborhoods, get_resume, skillNER, sim_result_loop, get_links, coSkillEmbed
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
def post_register(request: Request, username: str = Form(...), password: str = Form(...), email: str = Form(...)):
    db = pd.read_csv('static/embeddings_db.csv')
    if username not in db['username'] and email not in db['email']:
        new_row = len(db.index)+1
        db.loc[new_row, 'id'] = uuid1()
        db.loc[new_row, 'username'] = username
        db.loc[new_row, 'password'] = Hash.bcrypt(password)
        db.loc[new_row, 'email'] = email
        db.to_csv('static/embeddings_db.csv', index=False)
        message = "You have registered successfully. Please log in to continue"
        return templates.TemplateResponse('register.html', context={'request': request, 'message': message})
    elif email in db['email']:
        message = "That email address has already been registered. Please try again."
        return templates.TemplateResponse('register.html', context={'request': request, 'message': message})
    elif username in db['username']:
        message = "That username has already been taken. Please select another."
        return templates.TemplateResponse('register.html', context={'request': request, 'message': message})

@app.post("/login/", response_class=HTMLResponse)
def post_login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = pd.read_csv('static/embeddings_db.csv')
    if username in list(db['username']):
        pw = db.loc[db['username'] == username,'password'].to_string()
        pw = pw.split(' ')[4]
        if Hash.verify(password, pw) == True:
            un = db.loc[db['username'] == username,'username'].to_string().split(' ')[4]
            localStorage.setItem('username', un)
            print(localStorage.getItem('username'))
            message = "You have been successfully logged in."
            return templates.TemplateResponse('login.html', context={'request': request, "message": message})
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
    
    resume = get_resume(resume)
    db = pd.read_csv('static/embeddings_db.csv')
    username = localStorage.getItem('username')
    if username == None: 
        return print("username was None")
    else:
        def add_data_to_db(resume, db, username):
            # pd.concat([df, pd.DataFrame(embeds)], axis=1)
            embeds = format(coSkillEmbed(resume)).replace('[[','').replace(']]','').split(',')
            db.iloc[db['username']== username,4:] = embeds
            db.to_csv('static/embeddings_db.csv')
        
        skills = await skillNER(resume)
        simResults = await sim_result_loop(resume)
        links = get_links(simResults[0])

        bt.add_task(add_data_to_db, resume, db, username)

        return templates.TemplateResponse('find_my_match.html', context={'request': request, 'resume': resume, 'skills': skills, 'simResults': simResults[0], 'links': links})

@app.get("/find-match/", response_class=HTMLResponse)
def find_match(request: Request):
    jobselection = str(request.url).split("=")[1].replace('HTTP/1.1', '').replace("-", " ")
    print(jobselection)
    return templates.TemplateResponse('find_match.html', context={'request': request, 'jobselection': jobselection})

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
    jobselection = str(request.url).split("=")[1].replace('HTTP/1.1', '').replace("-", " ")
    print(jobselection)
    return templates.TemplateResponse('find_hire.html', context={'request': request, 'jobselection': jobselection})