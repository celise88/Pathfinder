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
import cohere
import string
import numpy as np
from numpy.linalg import norm
from nltk.tokenize import SpaceTokenizer
import nltk
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory='static'), name="static")
templates = Jinja2Templates(directory="templates/")

onet = pd.read_csv('static/ONET_JobTitles.csv')
simdat = pd.read_csv('static/cohere_embeddings.csv')
coheredat = pd.read_csv("static/cohere_tSNE_dat.csv")

model = AutoModelForSequenceClassification.from_pretrained('static/model_shards', low_cpu_mem_usage=True)
tokenizer = AutoTokenizer.from_pretrained('static/tokenizer_shards', low_cpu_mem_usage=True)
classifier = pipeline('text-classification', model = model, tokenizer = tokenizer)

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
    def format_title(logo, title, subtitle, title_font_size = 28, subtitle_font_size=14):
        logo = f'<a href="/" target="_self">{logo}</a>'
        subtitle = f'<span style="font-size: {subtitle_font_size}px;">{subtitle}</span>'
        title = f'<span style="font-size: {title_font_size}px;">{title}</span>'
        return f'{logo}{title}<br>{subtitle}'
    
    fig = px.scatter(coheredat, x = 'longitude', y = 'latitude', color = 'Category', hover_data = ['Category', 'Title'], 
        title=format_title("Pathfinder", "     Job Neighborhoods: Explore the Map!", "(Generated using Co-here AI's LLM & ONET's Task Statements)"))
    fig['layout'].update(height=1000, width=1500, font=dict(family='Courier New, monospace', color='black'))
    fig.write_html('templates/job_neighborhoods.html')

    return templates.TemplateResponse('job_neighborhoods.html', context={'request': request})

### find my match ###
# get
@app.get("/find-my-match", response_class=HTMLResponse)
async def match_page(request: Request):
    return templates.TemplateResponse('find_my_match.html', context={'request': request})

# post
@app.post('/find-my-match', response_class=HTMLResponse)
def get_resume(request: Request, resume: UploadFile = File(...)):
    path = f"static/{resume.filename}"
    with open(path, 'wb') as buffer:
        buffer.write(resume.file.read())
    file = Document(path)
    text = []
    for para in file.paragraphs:
        text.append(para.text)
    resume = "\n".join(text)

    def clean_my_text(text):
        clean_text = ' '.join(text.splitlines())
        clean_text = clean_text.replace('-', " ").replace("/"," ")
        clean_text = clean(clean_text.translate(str.maketrans('', '', string.punctuation)))
        return clean_text

    def coSkillEmbed(text):
        co = cohere.Client(os.getenv("COHERE_TOKEN"))
        response = co.embed(
            model='large',
            texts=[text])
        return response.embeddings
    
    def cosine(A, B):
        return np.dot(A,B)/(norm(A)*norm(B))

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
    
    skills=skillNER(resume)

    return templates.TemplateResponse('find_my_match.html', context={'request': request, 'resume': resume, 'skills': skills, 'simResults': simResults})
