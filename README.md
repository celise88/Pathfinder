---
title: Pathfinder
emoji: 🗺️
colorFrom: blue
colorTo: green
sdk: docker
python_version: 3.10.9
app_port: 7860
models: celise88/distilbert-base-uncased-finetuned-binary-classifier
pinned: true
---

# Pathfinder
![logo](./static/PF.png)   

## Purpose: 
#### This is a FastAPI web application designed to allow job-seekers to learn more about various occupations and explore their future career path. See below for details and page descriptions. If you like the app, please star and/or fork and check back frequently for future releases. 

## To Access the App:
https://huggingface.co/spaces/celise88/Pathfinder

## To Clone the App and Run it Locally:
#### Note:
* You must have python3.10.9 installed.
* In addition, for the current release you must have a cohere.ai API key for the job-matching functionality to work (I plan to add an open-source option in a future release). Register for a free developer account here: https://dashboard.cohere.ai/welcome/register. 

#### In a terminal run the following commands:

```
pip3 install --user virtualenv
git clone https://github.com/celise88/ONET-Application.git
```

Once you have your API key, copy and paste it into the .env file in the ONET-Application folder. Make sure you save the file. Then proceed with the following commands in your terminal:

```
cd Pathfinder
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
uvicorn main:app
```

And navigate to http://localhost:8000/ in your browser

(Advanced: You can also use the Dockerfile in the repo to build an image and run a container. Note that the port in the Dockerfile is 7860.)

## Page Descriptions:

### Home Page:
#### Select a job title from the dropdown and click submit to get information about the selected job.

![Page1](./static/main/Page1.png)

### Job Neighborhoods Page:
#### Click on the "Explore Job Neighborhoods" link to see which job neighborhood(s) your job(s) of interest occupy. 

![Page2](./static/main/Page2.png)

### Job-Matcher Page:
#### Click on the "Find My Match" link to upload your resume, see your skillset, and get job recommendations. 

#### Resume Upload Functionality:
![Page3-Input](./static/main/Page3-Input.png)

#### Example Extracted Skills Ouput:
![Page3-Output](./static/main/Page3-output.png)

#### Job Matches for the Example Resume:
![Page3-Matches](./static/main/Page3-Matches.png)

#### *Please see the version history below for a description of the models and algorithms underlying the app functionality.  

## Version history:
 
* Initial commit - 2/3/2023 - Allows users to select a job title to learn more about and get a brief description of the selected job and the major tasks involved, which is dynamically scraped from https://onetonline.org. The job neighborhoods page was generated by using Co:here AI's LLM to embed ONET's task statements and subsequently performing dimension reduction using t-SNE to get a 2-D representation of job "clusters." The distance between jobs in the plot corresponds to how similar they are to one another - i.e., more similar jobs (according to the tasks involved in the job) will appear more closely "clustered" on the plot.

* Version 1.1.1 (current version) - 2/5/2023 - Added full functionality to the "find my match" page where users can upload a resume, curriculum vitae, cover letter, etc. to have their skills extracted from the text.  Neural text embeddings are then produced for the user's resume. Using a csv file containing the text embeddings for all ONET jobs, cosine similarity is calculated to determine how similar the user's resume is to each job description (the embedded ONET task statements) - this is the user's "match score."  
    * The classification model underlying the skills extractor is a custom distilbert-base-uncased binary classification model that was finetuned using a balanced dataset comprised of the emsi (now Lightcast) open skills database and a random sample of the dbpedia database. The model achieved an f1 score of 0.967 on the validation sample (accuracy of 0.967, loss of 0.096). It can be accessed via Hugging Face: https://huggingface.co/celise88/distilbert-base-uncased-finetuned-binary-classifier.
    * Cohere's LLM is used to get the neural text embeddings. (This is why a cohere API key is needed for the new functionality to work in this release; I plan to incorporate an open-source embedding model in a future release.)

