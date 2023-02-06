from cleantext import clean
import cohere
import string
import numpy as np
from numpy.linalg import norm
from nltk.tokenize import SpaceTokenizer
import nltk
import os
from dotenv import load_dotenv
load_dotenv()

def coSkillEmbed(text):
    co = cohere.Client(os.getenv("COHERE_TOKEN"))
    response = co.embed(
        model='large',
        texts=[text])
    return response.embeddings
    
def cosine(A, B):
    return np.dot(A,B)/(norm(A)*norm(B))

def clean_my_text(resume):
    clean_text = ' '.join(resume.splitlines())
    clean_text = clean_text.replace('-', " ").replace("/"," ")
    clean_text = clean(clean_text.translate(str.maketrans('', '', string.punctuation)))
    stops = set(nltk.corpus.stopwords.words('english'))
    stops = stops.union({'eg', 'ie', 'etc', 'experience', 'experiences', 'experienced', 'experiencing', 'knowledge', 
    'ability', 'abilities', 'skill', 'skills', 'skilled', 'including', 'includes', 'included', 'include'
    'education', 'follow', 'following', 'follows', 'followed', 'make', 'made', 'makes', 'making', 'maker',
    'available', 'large', 'larger', 'largescale', 'client', 'clients', 'responsible', 'x', 'many', 'team', 'teams'})
    resume = [word for word in SpaceTokenizer().tokenize(resume) if word not in stops]
    resume = [word for word in resume if ")" not in word]
    resume = [word for word in resume if "(" not in word]
    return resume