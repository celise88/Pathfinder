import requests
from bs4 import BeautifulSoup
from cleantext import clean
import pandas as pd
import numpy as np

onet = pd.read_csv('static/ONET_JobTitles.csv')
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}

def remove_new_line(value):
        return ''.join(value.splitlines())

def get_onet_code(jobtitle):
    onetCode = onet.loc[onet['JobTitle'] == jobtitle, 'onetCode']
    onetCode = onetCode.reindex().tolist()[0]
    return onetCode

def get_onet_description(onetCode):
    url = "https://www.onetonline.org/link/summary/" + onetCode
    response = requests.get(url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobdescription = soup.p.get_text()
    return jobdescription

def get_onet_tasks(onetCode):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}
    url = "https://www.onetonline.org/link/result/" + onetCode + "?c=tk&n_tk=0&s_tk=IM&c_tk=0"
    response = requests.get(url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    tasks = str(soup.get_text('reportsubdesc')).replace("reportsubdesc", " ").replace("ImportanceCategoryTask ", "")
    tasks = clean(tasks)
    if len(tasks.split('show all show top 10')) > 1:
        tasks = tasks.split('show all show top 10')[1]
        tasks = tasks.split('occupations related to multiple tasks')[0]
        tasks = remove_new_line(tasks).replace("related occupations", " ").replace("core", " - ").replace("supplemental", "").replace("not available", "").replace(" )importance category task", "").replace(" find ", "")
        tasks = tasks.split(". ")
        tasks = [''.join(map(lambda c: '' if c in '0123456789-' else c, task)) for task in tasks]
        return tasks
    else: 
        return pd.DataFrame([("We're sorry."), ("This occupation is currently undergoing updates."), ("Please try again later.")])

def get_onet_activities(onetCode):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}
    
    activities_url = "https://www.onetonline.org/link/result/" + onetCode + "?c=wa&n_wa=0&s_wa=IM&c_wa=0"

    response = requests.get(activities_url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    tasks = str(soup.get_text('reportsubdesc')).replace("reportsubdesc", " ").replace("ImportanceCategoryTask ", "")
    tasks = clean(tasks)
    if len(tasks.split('show all show top 10')) > 1:
        tasks = tasks.split('show all show top 10')[1]
        tasks = tasks.split('back to top')[0]
        tasks = remove_new_line(tasks).replace("related occupations", " ").replace("importance work activity", " ")
        tasks = tasks.split(". ")
        split_data = [item.split(" -- ")[0] for item in tasks]
        num_desc = []
        for i in range(len(tasks)):
            temp = [','.join(item) for item in split_data][i].split(',')
            num_desc.append([''.join([c for c in temp if c in '0123456789']), ''.join([c for c in temp if c not in '0123456789']).replace(' ) ', '')])
        df = pd.DataFrame(num_desc, columns = ['Importance', 'Activity'])
        df = df[df['Importance'] != '']
        activities = df
        return activities
    else: 
        return pd.DataFrame([("We're sorry."), ("This occupation is currently undergoing updates."), ("Please try again later.")])

    
def get_onet_context(onetCode):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}

    context_url = "https://www.onetonline.org/link/result/" + onetCode + "?c=cx&n_cx=0&c_cx=0&s_cx=n"

    response = requests.get(context_url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    tasks = str(soup.get_text('reportsubdesc')).replace("reportsubdesc", " ").replace("ImportanceCategoryTask ", "")
    tasks = clean(tasks)
    if len(tasks.split('show all show top 10')) > 1:
        tasks = tasks.split('show all show top 10')[1]
        tasks = tasks.split('back to top')[0]
        tasks = remove_new_line(tasks).replace("related occupations", " ").replace("importance work activity", " ")
        tasks = tasks.split("? ")
        split_data = [item.split(" -- ")[0] for item in tasks]
        num_desc = []
        for i in range(len(tasks)):
            temp = [','.join(item) for item in split_data][i].split(',')
            num_desc.append([''.join([c for c in temp if c in '0123456789']), ''.join([c for c in temp if c not in '0123456789']).replace(')context work context', '')])
        df2 = pd.DataFrame(num_desc, columns = ['Importance', 'Condition'])
        df2 = df2[df2['Importance'] != '']
        context = df2
        return context
    else: 
        return pd.DataFrame([("We're sorry."), ("This occupation is currently undergoing updates."), ("Please try again later.")])


def get_onet_skills(onetCode):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}

    skills_url = "https://www.onetonline.org/link/result/" + onetCode + "?c=sk&n_sk=0&s_sk=IM&c_sk=0"
    
    response = requests.get(skills_url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    tasks = str(soup.get_text('reportsubdesc')).replace("reportsubdesc", " ").replace("ImportanceCategoryTask ", "")
    tasks = clean(tasks)
    if len(tasks.split('show all show top 10')) > 1:
        tasks = tasks.split('show all show top 10')[1]
        tasks = tasks.split('back to top')[0]
        tasks = remove_new_line(tasks).replace("related occupations", " ").replace(")importance skill", " ")
        tasks = tasks.split(". ")
        split_data = [item.split(" -- ")[0] for item in tasks]
        num_desc = []
        for i in range(len(tasks)):
            temp = [','.join(item) for item in split_data][i].split(',')
            num_desc.append([''.join([c for c in temp if c in '0123456789']), ''.join([c for c in temp if c not in '0123456789']).replace(')context work context', '')])
        df3 = pd.DataFrame(num_desc, columns = ['Importance', 'Skill'])
        df3 = df3[df3['Importance'] != '']
        skills = df3
        return skills
    else: 
        return pd.DataFrame([("We're sorry."), ("This occupation is currently undergoing updates."), ("Please try again later.")])


def get_onet_knowledge(onetCode):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}

    knowledge_url = "https://www.onetonline.org/link/result/" + onetCode + "?c=kn&n_kn=0&s_kn=IM&c_kn=0"

    response = requests.get(knowledge_url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    tasks = str(soup.get_text('reportsubdesc')).replace("reportsubdesc", " ").replace("ImportanceCategoryTask ", "")
    tasks = clean(tasks)
    if len(tasks.split('show all show top 10')) > 1:
        tasks = tasks.split('show all show top 10')[1]
        tasks = tasks.split('back to top')[0]
        tasks = remove_new_line(tasks).replace("related occupations", " ").replace(")importance knowledge", " ")
        tasks = tasks.split(". ")
        split_data = [item.split(" -- ")[0] for item in tasks]
        num_desc = []
        for i in range(len(tasks)):
            temp = [','.join(item) for item in split_data][i].split(',')
            num_desc.append([''.join([c for c in temp if c in '0123456789']), ''.join([c for c in temp if c not in '0123456789']).replace(')context work context', '')])
        df4 = pd.DataFrame(num_desc, columns = ['Importance', 'Knowledge'])
        df4 = df4[df4['Importance'] != '']
        knowledge = df4
        return knowledge
    else: 
        return pd.DataFrame([("We're sorry."), ("This occupation is currently undergoing updates."), ("Please try again later.")])


def get_onet_abilities(onetCode):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}

    abilities_url = "https://www.onetonline.org/link/result/" + onetCode + "?c=ab&n_ab=0&s_ab=IM&c_ab=0"

    response = requests.get(abilities_url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    tasks = str(soup.get_text('reportsubdesc')).replace("reportsubdesc", " ").replace("ImportanceCategoryTask ", "")
    tasks = clean(tasks)
    if len(tasks.split('show all show top 10')) > 1:
        tasks = tasks.split('show all show top 10')[1]
        tasks = tasks.split('back to top')[0]
        tasks = remove_new_line(tasks).replace("related occupations", " ").replace(")importance ability", " ")
        tasks = tasks.split(". ")
        split_data = [item.split(" -- ")[0] for item in tasks]
        num_desc = []
        for i in range(len(tasks)):
            temp = [','.join(item) for item in split_data][i].split(',')
            num_desc.append([''.join([c for c in temp if c in '0123456789']), ''.join([c for c in temp if c not in '0123456789']).replace(')context work context', '')])
        df5 = pd.DataFrame(num_desc, columns = ['Importance', 'Ability'])
        df5 = df5[df5['Importance'] != '']
        abilities = df5
        return abilities
    else:
        return pd.DataFrame([("We're sorry."), ("This occupation is currently undergoing updates."), ("Please try again later.")])
        
    

def get_onet_interests(onetCode):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}

    interests_url = "https://www.onetonline.org/link/result/" + onetCode + "?c=in&c_in=0"

    response = requests.get(interests_url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    tasks = str(soup.get_text('reportsubdesc')).replace("reportsubdesc", " ").replace("ImportanceCategoryTask ", "")
    tasks = clean(tasks)
    tasks = tasks.split("occupational interest interest")[1]#.replace('bright outlook', '').replace('updated 2023', '')
    if len(tasks.split('back to top')) > 1:
        tasks = tasks.split('back to top')[0]
        tasks = remove_new_line(tasks).replace("related occupations", " ").replace(")importance interest", " ")
        tasks = tasks.split(". ")
        split_data = [item.split(" -- ")[0] for item in tasks]
        num_desc = []
        for i in range(len(tasks)):
            temp = [','.join(item) for item in split_data][i].split(',')
            num_desc.append([''.join([c for c in temp if c in '0123456789']), ''.join([c for c in temp if c not in '0123456789']).replace(')context work context', '')])
        df6 = pd.DataFrame(num_desc, columns = ['Importance', 'Interest'])
        df6 = df6[df6['Importance'] != '']
        interests = df6
        return interests
    else: 
        return pd.DataFrame([("We're sorry."), ("This occupation is currently undergoing updates."), ("Please try again later.")])


def get_onet_values(onetCode):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}

    values_url = "https://www.onetonline.org/link/result/" + onetCode + "?c=wv&c_wv=0"
    
    response = requests.get(values_url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    tasks = str(soup.get_text('reportsubdesc')).replace("reportsubdesc", " ").replace("ImportanceCategoryTask ", "")
    tasks = clean(tasks)
    tasks = tasks.split('extent work value')[1]
    tasks = tasks.split('back to top')[0]
    tasks = remove_new_line(tasks).replace("related occupations", " ").replace(")importance value", " ")
    tasks = tasks.split(". ")
    split_data = [item.split(" -- ")[0] for item in tasks]
    num_desc = []
    for i in range(len(tasks)):
        temp = [','.join(item) for item in split_data][i].split(',')
        num_desc.append([''.join([c for c in temp if c in '0123456789']), ''.join([c for c in temp if c not in '0123456789']).replace(')context work context', '')])
    df7 = pd.DataFrame(num_desc, columns = ['Importance', 'Value'])
    df7 = df7[df7['Importance'] != '']
    values = df7
    return values

def get_onet_styles(onetCode):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}

    style_url = "https://www.onetonline.org/link/result/" + onetCode + "?c=ws&n_ws=0&c_ws=0"

    response = requests.get(style_url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    tasks = str(soup.get_text('reportsubdesc')).replace("reportsubdesc", " ").replace("ImportanceCategoryTask ", "")
    tasks = clean(tasks)
    tasks = tasks.split('show all show top 10')[1]
    tasks = tasks.split('back to top')[0]
    tasks = remove_new_line(tasks).replace("related occupations", " ").replace(")importance work style", "").replace(")importance style", " ")
    tasks = tasks.split(". ")
    split_data = [item.split(" -- ")[0] for item in tasks]
    num_desc = []
    for i in range(len(tasks)):
        temp = [','.join(item) for item in split_data][i].split(',')
        num_desc.append([''.join([c for c in temp if c in '0123456789']), ''.join([c for c in temp if c not in '0123456789']).replace(')context work context', '')])
    df8 = pd.DataFrame(num_desc, columns = ['Importance', 'Style'])
    df8 = df8[df8['Importance'] != '']
    styles = df8
    return styles

def get_job_postings(onetCode, state):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'}
    url = "https://www.onetonline.org/link/localjobs/" + onetCode + "?st=" + state
    response = requests.get(url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = str(soup.get_text("tbody")).split('PostedtbodyTitle and CompanytbodyLocation')[1].split('Sources:')[0].split("tbody")
    jobs = jobs[5:45]
    starts = np.linspace(start=0, stop=len(jobs)-4,num= 10)
    stops = np.linspace(start=3, stop=len(jobs)-1, num= 10)
    jobpostings = []
    for i in range(0,10):
        jobpostings.append(str([' '.join(jobs[int(starts[i]):int(stops[i])])]).replace("['", '').replace("']", ''))
    links = str(soup.find_all('a', href=True)).split("</small>")[1].split(', <a href="https://www.careeronestop.org/"')[0].split(' data-bs-toggle="modal" ')
    linklist = []
    for i in range(1, len(links)):
        links[i] = "https://www.onetonline.org" + str(links[i]).split(' role="button">')[0].replace("href=", "")
        linklist.append(links[i].replace('"', ''))
    return jobpostings, linklist