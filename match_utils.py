from docx import Document
import pandas as pd
import numpy as np
from numpy.linalg import norm
import plotly_express as px
from scrape_onet import get_onet_code
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_community.llms.ollama import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from sentence_transformers import SentenceTransformer

# LOAD DATA AND EMBEDDINGS:
simdat = pd.read_csv('static/embeddings/onet_embeddings_st5.csv')
tsne_dat = pd.read_csv('static/st5_tSNE_dat.csv')
parser = CommaSeparatedListOutputParser()

# LOAD MODELS:
model = Ollama(model="mistral")
embedding_model = SentenceTransformer('sentence-transformers/sentence-t5-base', device='cpu')

# UTILITY FUNCTIONS:
def remove_new_line(value):
        return ''.join(value.splitlines())

async def neighborhoods(jobtitle=None):
    def format_title(logo, title, subtitle, title_font_size = 28, subtitle_font_size=14):
        logo = f'<a href="/" target="_self">{logo}</a>'
        subtitle = f'<span style="font-size: {subtitle_font_size}px;">{subtitle}</span>'
        title = f'<span style="font-size: {title_font_size}px;">{title}</span>'
        return f'{logo}{title}<br>{subtitle}'
    fig = px.scatter(tsne_dat, x = 'longitude', y = 'latitude', color = 'Category', hover_data = ['Category', 'Title'], 
        title=format_title("Pathfinder", "     Job Neighborhoods: Explore the Map!", ""))
    fig['layout'].update(height=1000, width=1500, font=dict(family='Courier New, monospace', color='black'))
    fig.write_html('templates/job_neighborhoods.html')

def get_resume(resume):
    path = f"static/{resume.filename}"
    with open(path, 'wb') as buffer:
        buffer.write(resume.file.read())
    file = Document(path)
    text = []
    for para in file.paragraphs:
        text.append(para.text)
    resume = "\n".join(text)
    return resume

def skill_extractor(resume):
     system_prompt_template = SystemMessagePromptTemplate.from_template("""
     ### [INST] 
     Instruction: You are an expert job analyst tasked with identifying both technical and soft skills in resumes.
     You always respond in the following format: 'skill1, skill2, skill3, ...' and never provide an explanation or justification for your response. 
     For example, given the following statement in a resume: 'significant experience in python and familiarity with machine learning packages, such as sklearn, torch, and tensorflow' 
     you respond: 'python, sklearn, torch, tensorflow'. 
     [/INST]
     """)
     
     human_prompt_template = HumanMessagePromptTemplate.from_template("""
     ### QUESTION:
     What skills are in the following resume?: 
     {resume}
     """)

     prompt = ChatPromptTemplate.from_messages([system_prompt_template, human_prompt_template])
     llm_chain = LLMChain(llm=model, prompt=prompt)

     result = llm_chain.invoke({"resume": resume})
     result = remove_new_line(result['text'])
     return parser.parse(result)

def skillEmbed(skills):
    embeddings = embedding_model.encode(skills)
    return embeddings

async def sim_result_loop(skilltext):
    if type(skilltext) == str:
        skills = skilltext
    if type(skilltext) == dict:
        skills = [key for key, value in skilltext.items() if value == "Skill"]
        skills = str(skills).replace("'", "").replace(",", "")
    if type(skilltext) == list: 
        skills = ', '.join(skilltext)
    embeds = skillEmbed(skills)
    
    def cosine(A, B):
        return np.dot(A,B)/(norm(A)*norm(B))
    
    def format_sim(sim):
        return "{:0.2f}".format(sim)
    
    simResults = []
    [simResults.append(cosine(np.array(embeds), np.array(simdat.iloc[i,1:]))) for i in range(len(simdat))]
    simResults = pd.DataFrame(simResults)
    simResults['JobTitle'] = simdat['Title']
    simResults = simResults.iloc[:,[1,0]]
    simResults.columns = ['JobTitle', 'Similarity']
    simResults = simResults.sort_values(by = "Similarity", ascending = False)
    simResults = simResults.iloc[:13,:]
    simResults = simResults.iloc[1:,:]
    simResults.reset_index(drop=True, inplace=True)
    if simResults['Similarity'].min() < 0.5:
        simResults['Similarity'] = simResults['Similarity'] + (0.5 - simResults['Similarity'].min())
        if simResults['Similarity'].max() > 1.0:
            simResults['Similarity'] = simResults['Similarity'] - (simResults['Similarity'].max() - 1.0)
    for x in range(len(simResults)):
        simResults.iloc[x,1] = format_sim(simResults.iloc[x,1])
    return simResults, embeds

def get_links(simResults):
    links = []
    titles = simResults["JobTitle"]
    [links.append("https://www.onetonline.org/link/summary/" + get_onet_code(title)) for title in titles]
    return links

def sim_result_loop_jobFinder(skills):
    embeds = skillEmbed(skills)
    def cosine(A, B):
        return np.dot(A,B)/(norm(A)*norm(B))
    def format_sim(sim):
        return "{:0.2f}".format(sim)
    jobdat = pd.read_csv('static/jd_embeddings.csv')
    jobembeds = jobdat.iloc[:,5:].dropna()
    simResults = []
    [simResults.append(cosine(np.array(embeds), np.array(jobembeds.iloc[i,:]))) for i in range(len(jobembeds))]
    simResults = pd.DataFrame(simResults)
    simResults['job_id'] = jobdat['id']
    simResults['emp_email'] = jobdat['email']
    simResults = simResults.iloc[:,[1,2,0]]
    simResults.columns = ['job_id', 'employer_email', 'similarity']
    simResults = simResults.sort_values(by = "similarity", ascending = False)
    simResults.reset_index(drop=True, inplace=True)
    for x in range(len(simResults)):
        simResults.iloc[x,2] = format_sim(simResults.iloc[x,2])
    return simResults

def sim_result_loop_candFinder(skills):
    embeds = skillEmbed(skills)
    def cosine(A, B):
        return np.dot(A,B)/(norm(A)*norm(B))
    def format_sim(sim):
        return "{:0.2f}".format(sim)
    canddat = pd.read_csv('static/res_embeddings.csv')
    candembeds = canddat.iloc[:,5:].dropna()
    simResults = []
    [simResults.append(cosine(np.array(embeds), np.array(candembeds.iloc[i,:]))) for i in range(len(candembeds))]
    simResults = pd.DataFrame(simResults)
    simResults['cand_id'] = canddat['id']
    simResults['cand_email'] = canddat['email']
    simResults = simResults.iloc[:,[1,2,0]]
    simResults.columns = ['candidate_id', 'candidate_email', 'similarity']
    simResults = simResults.sort_values(by = "similarity", ascending = False)
    simResults.reset_index(drop=True, inplace=True)
    for x in range(len(simResults)):
        simResults.iloc[x,2] = format_sim(simResults.iloc[x,2])
    return simResults