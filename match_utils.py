from cleantext import clean
import string
from nltk.tokenize import SpaceTokenizer
import nltk
import cohere
from cohere import CohereError
import os
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from docx import Document
import pandas as pd
import numpy as np
from numpy.linalg import norm
import ssl
from dotenv import load_dotenv
import concurrent.futures

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

# LOAD ENVIRONMENT VARIABLES
load_dotenv()

# LOAD COHERE EMBEDDINGS:
simdat = pd.read_csv('static/cohere_embeddings.csv')

# LOAD FINE-TUNED MODEL 
# (see https://huggingface.co/celise88/distilbert-base-uncased-finetuned-binary-classifier)
model = AutoModelForSequenceClassification.from_pretrained('static/model_shards', low_cpu_mem_usage=True)
tokenizer = AutoTokenizer.from_pretrained('static/tokenizer_shards', low_cpu_mem_usage=True)
classifier = pipeline('text-classification', model = model, tokenizer = tokenizer)

# UTILITY FUNCTIONS
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

def coSkillEmbed(text):
    try:
        co = cohere.Client(os.getenv("COHERE_TOKEN"))
        response = co.embed(
            model='large',
            texts=[text])
        return response.embeddings
    except CohereError as e:
        return e

async def get_simresults(resume):
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
    return simResults

async def skillNER(resume):
    def clean_my_text(text):
        clean_text = ' '.join(text.splitlines())
        clean_text = clean_text.replace('-', " ").replace("/"," ")
        clean_text = clean(clean_text.translate(str.maketrans('', '', string.punctuation)))
        return clean_text

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