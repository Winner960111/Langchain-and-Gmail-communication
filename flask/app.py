from typing import Optional

from langchain.chains.openai_functions import (
    create_openai_fn_chain,
    create_openai_fn_runnable,
    create_structured_output_chain,
    create_structured_output_runnable,
)
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.document_loaders import PyPDFLoader
from langchain.pydantic_v1 import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from openai import OpenAI

from flask import Flask, render_template, request, url_for, jsonify
from flask_cors import CORS
import requests, os, sqlite3
import pickle

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from base64 import urlsafe_b64decode, urlsafe_b64encode

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type

import uuid, time, json
from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
CORS(app, origins='*')
openai_api_key = os.environ.get("OPENAI_API_KEY")

SCOPES = ['https://mail.google.com/']
our_email = 'harryporter319193@gmail.com'
job_titles = ['Healthcare Project Manager', 'Machinist', 'Maintenance Supervisor', 'Tampa Coverage Attorney', 'Senior Project Engineer']

msg_history = [{"role": "system", "content": "As a professional HR manager, your role is to ask screening questions to candidates. You should consider skills, industry experience and certifications of candidate. Your response should be limited up to 30 words."}]

twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
sms_phone_number = os.environ.get("SMS_NUMBER")


# twilio_client = Client(twilio_account_sid, twilio_auth_token)
openai_client = OpenAI(api_key=openai_api_key)

def phone_message(message, to_number, option):  # to_number have to include + at first
    
    if option == "sms":
        from_ = f'{sms_phone_number}'
        to = f'{to_number}'
    else:
        from_ = f'whatsapp:{twilio_phone_number}'
        to = f'whatsapp:{to_number}'
    
    # twilio_client.messages.create(
    #     from_=from_,
    #     body=message,
    #     to=to
    # )

screening_questions = ["Do you have experience as a Healthcare Project Manager with a proven track record of successfully managing projects, relevant industry knowledge, and any relevant certifications?", "Do you have at least 3 years of experience as a Machinist in the manufacturing industry, along with a certification in machining or a related field?", "Do you have at least 3 years of experience as a Maintenance Supervisor in the manufacturing industry, along with a certification in maintenance management or a related field?", "Do you have experience as a Coverage Attorney in Tampa, with a strong background in insurance law, knowledge of policy interpretation, and relevant certifications?", "Do you have a minimum of 5 years of experience as a Senior Project Engineer in the construction industry, along with a PMP certification?"]

def gmail_authenticate():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

service = gmail_authenticate()

def build_email(destination, obj, body, attachments=[]):
    message = MIMEText(body)
    message['to'] = destination
    message['from'] = our_email
    message['subject'] = obj
    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}

def send_email(destination, body):
    service.users().messages().send(userId="me", body=build_email(destination, "Message for Candidate", body)).execute()

def extract_info(filename):
    loader = PyPDFLoader(f"./uploads/{filename}")
    input = loader.load()[0].page_content
    runnable = create_structured_output_runnable(Person, llm, extract_prompt)
    res = runnable.invoke({"input": input})
    
    info = {}
    info["name"] = res.name
    info["email"] = res.email
    info["number"] = res.number
    
    return info

def email_init_message(destination, name, screen_question):
    init_msgs = f"Hello, {name}\n"
    
    init_msgs += screen_question
        
    send_email(destination, init_msgs)
    
def generate_screen_question(job_description):
    return screen_question_chain.run(job_description)

class Person(BaseModel):
    """Identifying information about a person."""

    name: str = Field(..., description="The person's name")
    email: str = Field(..., description="The person's email address")
    number: Optional[str] = Field(None, description="The person's phone number")

llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0, api_key=openai_api_key)

extract_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a world class algorithm for extracting information in structured formats.",
        ),
        (
            "human",
            "Use the given format to extract information from the following input: {input}",
        ),
        ("human", "Tip: Make sure to answer in the correct format"),
    ]
)

screen_question_template = """Please write screening question based on following job description. \n Job description : {job_description} \n Screening question should include job titles, skills and industry experience and certification. Screening question should be only one sentence and is limited to 30 words."""

screen_question_prompt = PromptTemplate(template=screen_question_template, input_variables=["job_description"])

screen_question_chain = LLMChain(prompt=screen_question_prompt, llm=llm)


def email_mark_as_read(id):
    service.users().messages().batchModify(userId='me', body={'ids': [ id ],'removeLabelIds': ['UNREAD']}).execute()

def read_email():
    file = open("current_candidate.txt", "r")
    from_email = file.readlines()[0]
    
    results = service.users().messages().list(userId='me', q=f"from:{from_email}").execute()
    messages = results.get('messages', [])
    
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        
        if 'UNREAD' in msg['labelIds']:
            msg_history.append({"role": "user", "content": msg['snippet']})
            
            completion = openai_client.chat.completions.create(
                model="gpt-4",
                messages=msg_history
            )
            
            response = completion.choices[0].message.content
            
            send_email(from_email, response)
            msg_history.append({"role": "assistant", "content": response})
            
            email_mark_as_read(message['id'])
            
    time.sleep(20)
    
    read_email()

@app.route('/message', methods=['POST'])
def message():
    incoming_msg = request.values.get('Body', '').lower()
    
    from_address = request.values.get('From')
            
@app.route('/resume_upload', methods=['GET', 'POST'])
def resume_upload():
    if request.method == 'POST':

        resume = request.files['resume']
        filename = resume.filename
        
        filename = str(uuid.uuid4()) + f".{filename.split('.')[-1]}"
        resume.save(os.path.join(f"./uploads/{filename}"))
        
        info = extract_info(filename)
        
        email_init_message(info['email'], info['name'])
        
        file = open("current_candidate.txt", "w")
        file.write(info['email'])
        file.close()
        
        read_email()
        
        return jsonify(info)

def insert_resume_db(resume_data):
    conn = sqlite3.connect('mydb.sqlite')
    cur = conn.cursor()
    
    first_name = resume_data['first_name']
    # middle_name = resume_data['middle_name']
    last_name = resume_data['last_name']
    email = resume_data['email']
    mobile = resume_data['mobile']
    status = resume_data['status']
    filename = resume_data['filename']
    
    cur.execute('SELECT * FROM resume WHERE filename = ?', (filename,))
    
    row = cur.fetchone()
    if not row:
        try:
            cur.execute('INSERT INTO resume (first_name, last_name, email, mobile, status, filename) VALUES (?, ?, ?, ?, ?, ?, ?)', (first_name, last_name, email, mobile, status, filename))
            conn.commit()
        except:
            print("Bad")
        cur.close()
        conn.close()
        
        print("Record is created.")
    else:
        print("Record already exist.")
    
@app.route('/screen_start', methods=['POST'])
def screen_start():
    if request.method == 'POST':
        res = request.json
        print(res)
        job_id = res['job_description_title']
        email = res['candidates'][0]['email']
        number = res['candidates'][0]['phone']
        first_name = res['candidates'][0]['first_name']
        last_name = res['candidates'][0]['last_name']
        
        # if res['middle_name']:
        #     name = f"{first_name} {res['middle_name']} {last_name}"
        # else:
        name = f"{first_name} {last_name}"
        
        with open(f'../job_description/{job_id}.json') as file:
            job_description = json.load(file)['job_description']
        
        screen_question = generate_screen_question(job_description)
        
        # send initial message
        email_init_message(email, name=name, screen_question=screen_question)
        
        if not '+' in number:
            number = '+' + number
        
        # phone_message(f"Hi, {name}\n{screen_question}", number, 'sms')
        # phone_message(f"Hi, {name}\n{screen_question}", number, 'wa')
        # end
        
        resume_data = {}
        resume_data['first_name'] = first_name
        resume_data['last_name'] = last_name
        resume_data['email'] = email
        resume_data['mobile'] = number
        resume_data['status'] = 'active'
        
        # if res['middle_name']:
        #     resume_data['middle_name'] = ''
            
        # resume_data['filename'] = f"{first_name} {resume_data['middle_name']} {last_name}_{number}"
        resume_data['filename'] = f"{first_name} {last_name}_{number}"
        
        insert_resume_db(resume_data)
        
        return "Good"
        
if __name__ == '__main__':
    app.run(debug=True)