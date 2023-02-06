# Author: Caitlin Blackmore
# Project: Pathfinder
# Project Description: This is a web application designed to facilitate job-mobility. 
# It uses NLP to help job seekers find jobs that match their skills and interests.
# Date: 2023-02-03
# File Description: This is the main file, containing the FastAPI app and all the endpoints.
# License: MIT License

# IMPORTS
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import pandas as pd
import requests
from bs4 import BeautifulSoup
from cleantext import clean
from docx import Document
import os
import ssl
import cohere
from cohere import CohereError
import string
import numpy as np
from numpy.linalg import norm
from nltk.tokenize import SpaceTokenizer
import nltk
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from dotenv import load_dotenv

# LOAD ENVIRONMENT VARIABLES
load_dotenv()

# SSL CERTIFICATE FIX
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# DOWNLOAD NLTK DATA IF NOT ALREADY DOWNLOADED
if os.path.isdir('nltk_data')==False:
    nltk.download('stopwords', quiet=True)

# APP SETUP
app = FastAPI()
app.mount("/static", StaticFiles(directory='static'), name="static")
templates = Jinja2Templates(directory="templates/")

# LOAD DATA
onet = pd.read_csv('static/ONET_JobTitles.csv')
simdat = pd.read_csv('static/cohere_embeddings.csv')

# LOAD FINE-TUNED MODEL 
# (see https://huggingface.co/celise88/distilbert-base-uncased-finetuned-binary-classifier)
model = AutoModelForSequenceClassification.from_pretrained('static/model_shards', low_cpu_mem_usage=True)
tokenizer = AutoTokenizer.from_pretrained('static/tokenizer_shards', low_cpu_mem_usage=True)
classifier = pipeline('text-classification', model = model, tokenizer = tokenizer)

# UTILITY FUNCTIONS
def clean_my_text(text):
    clean_text = ' '.join(text.splitlines())
    clean_text = clean_text.replace('-', " ").replace("/"," ")
    clean_text = clean(clean_text.translate(str.maketrans('', '', string.punctuation)))
    return clean_text

def remove_new_line(value):
        return ''.join(value.splitlines())

def coSkillEmbed(text):
    try:
        co = cohere.Client(os.getenv("COHERE_TOKEN"))
        response = co.embed(
            model='large',
            texts=[text])
        return response.embeddings
    except CohereError as e:
        return e

def skillNER(resume):
    resume = clean_my_text(resume)
    stops = set(nltk.corpus.stopwords.words('english'))
    stops = stops.union({'eg', 'ie', 'etc', 'experience', 'experiences', 'experienced', 'experiencing', 'knowledge', 
    'ability', 'abilities', 'skill', 'skills', 'skilled', 'including', 'includes', 'included', 'include'
    'education', 'follow', 'following', 'follows', 'followed', 'make', 'made', 'makes', 'making', 'maker',
    'available', 'large', 'larger', 'largescale', 'client', 'clients', 'responsible', 'x', 'many', 'team', 'teams'})
    resume = [word for word in SpaceTokenizer().tokenize(resume) if word not in stops]
    resume = [word for word in resume if ")" not in word]
    resume = [word for word in resume if "(" not in word]
            
    labels = []
    for i in range(len(resume)):
        classification = classifier(resume[i])[0]['label']
        if classification == 'LABEL_1':
            labels.append("Skill")
        else:
            labels.append("Not Skill")
        labels_dict = dict(zip(resume, labels))
    return labels_dict

def cosine(A, B):
    return np.dot(A,B)/(norm(A)*norm(B))

### JOB INFORMATION CENTER ###
# GET
@app.get("/")
def render_job_list(request: Request):
    joblist = onet['JobTitle']
    return templates.TemplateResponse('job_list.html', context={'request': request, 'joblist': joblist})

# POST
@app.post("/")
def render_job_info(request: Request, jobtitle: str = Form(enum=[x for x in onet['JobTitle']])):
    joblist = onet['JobTitle']
    if jobtitle: 
        # SCRAPE ONET TO GET JOB DESCRIPTION, TASKS, ETC.
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

### JOB NEIGHBORHOODS ###
@app.get("/explore-job-neighborhoods/", response_class=HTMLResponse)
def render_job_neighborhoods(request: Request):
    return templates.TemplateResponse('job_neighborhoods.html', context={'request': request})

### FIND-MY-MATCH ###
# GET
@app.get("/find-my-match/", response_class=HTMLResponse)
def match_page(request: Request):
    return templates.TemplateResponse('find_my_match.html', context={'request': request})

# POST
@app.post('/find-my-match/', response_class=HTMLResponse)
async def get_resume(request: Request, resume: UploadFile = File(...)):
    
    # READ AND PERFORM BASIC CLEANING ON RESUME
    path = f"static/{resume.filename}"
    with open(path, 'wb') as buffer:
        buffer.write(resume.file.read())
    file = Document(path)
    text = []
    for para in file.paragraphs:
        text.append(para.text)
    resume = "\n".join(text)

    # GET RESUME EMBEDDINGS AND JOB SIMILARITY SCORES
    embeds = coSkillEmbed(resume)
    simResults = []
    for i in range(len(simdat)):
        simResults.append(cosine(np.array(embeds), np.array(simdat.iloc[i,1:])))
    simResults = pd.DataFrame(simResults)
    simResults['JobTitle'] = simdat['Title']
    simResults = simResults.iloc[:,[1,0]]
    simResults.columns = ['JobTitle', 'Similarity']
    simResults = simResults.sort_values(by = "Similarity", ascending = False)
    simResults = simResults.iloc[:13,:]
    simResults = simResults.iloc[1:,:]
    simResults.reset_index(drop=True, inplace=True)
    for x in range(len(simResults)):
        simResults.iloc[x,1] = "{:0.2f}".format(simResults.iloc[x,1])
        
    # EXTRACT SKILLS FROM RESUME 
    skills = skillNER(resume)

    return templates.TemplateResponse('find_my_match.html', context={'request': request, 'resume': resume, 'skills': skills, 'simResults': simResults})
