import os
from flask import Flask, render_template, request

global total_sum
total_sum = 0
import math
import PyPDF2
import os

from io import StringIO
import pandas as pd
from collections import Counter
import en_core_web_sm
nlp = en_core_web_sm.load()
from spacy.matcher import PhraseMatcher

app = Flask(__name__)


def pdfextract(file):
    fileReader = PyPDF2.PdfFileReader(open(file,'rb'))
    countpage = fileReader.getNumPages()
    count = 0
    text = []
    while count < countpage:    
        pageObj = fileReader.getPage(count)
        count +=1
        t = pageObj.extractText()
       # print (t)
        text.append(t)
    return text

def create_profile(file, target_job_title):
    # converting the resume pdf into text
    text = pdfextract(file) 
    text = str(text)
    text = text.replace("\\n", "")
    text = text.lower()
    
    #below is the csv where we have all the keywords
    if target_job_title == 'DS':
        keyword_dict = pd.read_csv('data_science_keywords.csv')
    elif target_job_title == 'WD':
        keyword_dict = pd.read_csv('web_developer_keywords.csv')
    elif target_job_title == 'ISA':
        keyword_dict = pd.read_csv('information_security_analyst.csv')
    elif target_job_title == 'SE':
        keyword_dict = pd.read_csv('software_engineer_keywords.csv')
    elif target_job_title == 'AI':
        keyword_dict = pd.read_csv('ai_ml_keywords.csv')
        
    
    keyword_total = list(keyword_dict.count())
    total_sum = 0
    for i in keyword_total:
        total_sum = total_sum + i
        
    keyword_dict_col_names = list(keyword_dict.columns)
    
   
    matcher = PhraseMatcher(nlp.vocab)
    
    for col in keyword_dict_col_names: 
        matcher.add(col, None, *[nlp(text) for text in keyword_dict[col].dropna(axis = 0)])
    
    doc = nlp(text)
    
    d = []  
    matches = matcher(doc)
    for match_id, start, end in matches:
        rule_id = nlp.vocab.strings[match_id]  # get the unicode ID, i.e. 'COLOR'
        span = doc[start : end]  # get the matched slice of the doc
        d.append((rule_id, span.text))  
    keywords = "\n".join(f'{i[0]} {i[1]} ({j})' for i,j in Counter(d).items())
    
    ## convertimg string of keywords to dataframe
    df = pd.read_csv(StringIO(keywords),names = ['Keywords_List'])
    df1 = pd.DataFrame(df.Keywords_List.str.split(' ',1).tolist(),columns = ['Subject','Keyword'])
    df2 = pd.DataFrame(df1.Keyword.str.split('(',1).tolist(),columns = ['Keyword', 'Count'])
    df3 = pd.concat([df1['Subject'],df2['Keyword'], df2['Count']], axis =1) 
    df3['Count'] = df3['Count'].apply(lambda x: x.rstrip(")"))
    
    base = os.path.basename(file)
    filename = os.path.splitext(base)[0]
       
    name = filename.split('_')
    name2 = name[0]
    name2 = name2.lower()
    ## converting str to dataframe
    name3 = pd.read_csv(StringIO(name2),names = ['Candidate Name'])
    
    dataf = pd.concat([name3['Candidate Name'], df3['Subject'], df3['Keyword'], df3['Count']], axis = 1)
    dataf['Candidate Name'].fillna(dataf['Candidate Name'].iloc[0], inplace = True)
   # print(dataf)
    return(dataf,total_sum, )
    




#--------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=['POST'])
def upload():
    
    
    print('eer  0', request.form)
    dropdown_selection = str(request.form)
    dropdown_selection = dropdown_selection.split()
    dropdown_selection = dropdown_selection[1]
    
    if 'XMEN' in dropdown_selection:
        return ('Your are not an X men. You can never be.')
    
 
        
    
    target = 'images/'
    print('tt' , target)

    if not os.path.isdir(target):
        os.mkdir(target)

    for file in request.files.getlist("file"):
        print(file)
        filename = file.filename
        destination = "/".join([target, filename])
        print('des',destination)
        file.save(destination)
        
        
        
        
    mypath = os. getcwd()
    onlyfiles = [os.path.join(mypath, f) for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
    
    
    
    
    
    final_database=pd.DataFrame()
    i = 0 
    while i < 1:
        file = destination
        if 'WD' in dropdown_selection:
            dat, total_sum = create_profile(file,'WD')
            selection = 'Web Developer'
        if 'DS' in dropdown_selection:
            dat, total_sum = create_profile(file,'DS')
            selection = 'Data Scientist'
            
        if 'ISA' in dropdown_selection:
            dat, total_sum = create_profile(file,'ISA')
            selection = 'Information Security Analyst'
            
        if 'SE' in dropdown_selection:
            dat, total_sum = create_profile(file,'SE')
            selection = 'Software Engineer'
            
        if 'AI' in dropdown_selection:
            dat, total_sum = create_profile(file,'AI')
            selection = 'AI and ML Engineer'
        final_database = final_database.append(dat)
        i +=1
        
        

    #=========================================
    
    final_database2 = final_database['Keyword'].groupby([final_database['Candidate Name'], final_database['Subject']]).count().unstack()
    final_database2.reset_index(inplace = True)
    final_database2.fillna(0,inplace=True)
    print(dat)
    
    
    final_database_col = list(final_database2.columns)
    final_database_col.pop(0)
    sum = 0
    for i in final_database_col:
        sum = sum + final_database2[i]
        
    sum = int(sum)
    resume_score = (sum/total_sum) * 100 
    resume_score = math.floor(resume_score)
        
        
   
    return render_template('result.html',result = resume_score, selection =selection )

if __name__ == "__main__":
    app.run()
    
    
    