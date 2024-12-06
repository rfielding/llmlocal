#!/bin/env python3.12
import ollama
import chromadb
import psycopg
from psycopg.rows import dict_row

# prerequisite:
#   python3.12 venv to pip install -r requirements.txt
#   install ollama
#   ollama pull llama3.2 so that the model is available
#   ollama pull nomic-embed-text
#   sudo apt install postgresql postgresql-contrib
#   sudo systemctl start postgreql
#   sudo systemctl enable postgresql
#   sudo -u postgres psql
#
#  postgres=# create user llama with password 'llama' superuser;
#  CREATE ROLE
#  postgres=# grant all privileges on database postgres to llama;
#  GRANT
#
#  create database memory)agent;
#  grant all privileges on schema public to llama;
#  grant all privileges on database memory_agent to llama;
#  create table conversations (id serial primary key, timestamp timestamp not null default current_timestamp, prompt text not null, response text not null);

client = chromadb.Client()
system_prompt = (
        'You are an AI assistent that has memory of every conversation you have ever had with this user. '
        'On every prompt from the user, the system has checked for any relevant messages you have had with the user. '
        'If any embedded previous conversations are attached, use them for context to responding to the user, '
        'if the context is relevant and useful to responding. If the recalled conversations are irrelevant, '
        'disregard speaking about them and respond normally as an AI assistent. Do not talk about recalling conversations.'
        'Just use any useful data from the previous conversations and respond normally as an intelligent AI assistent.'
)

convo = [{'role': 'system', 'content': system_prompt}]
DB_PARAMS = {
        'dbname':  'memory_agent',
        'user':    'llama',
        'password':'llama',
        'host':    'localhost',
        'port':    '5432'
}

def connect_db():
    conn = psycopg.connect(**DB_PARAMS)
    return conn

def fetch_conversations():
    conn = connect_db()
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute('SELECT * from conversations')
        conversations = cursor.fetchall()
    conn.close()
    return conversations

def store_conversations(prompt, response):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute(
                'insert into conversations (timestamp, prompt, response) values (current_timestamp, %s, %s)',
                (prompt, response)
        )
        conn.commit()
    conn.close()

def stream_response(prompt):
    convo.append({'role':'user', 'content':prompt})
    response = ''
    stream = ollama.chat(model='llama3.2', messages=convo, stream=True)
    print('\nASSISTANT:')
    for chunk in stream:
        content = chunk['message']['content']
        response += content
        print(content, end='', flush=True)
    print('\n')
    store_conversations(prompt=prompt, response=response)
    convo.append({'role':'assistant', 'content':response})

def create_vector_db(conversations):
    vector_db_name = 'conversations'
    try:
        client.delete_collection(name=vector_db_name)
    except ValueError:
        pass

    vector_db = client.create_collection(name=vector_db_name)

    for c in conversations:
        serialized_convo = 'prompt: %s response: %s'%(c['prompt'],c['response'])
        response = ollama.embeddings(model='nomic-embed-text',prompt=serialized_convo)
        embedding = response['embedding']

        vector_db.add(
                ids=[str(c['id'])],
                embeddings=[embedding],
                documents=[serialized_convo]
        )


def retrieve_embeddings(prompt):
    response = ollama.embeddings(model='nomic-embed-text', prompt=prompt)
    prompt_embedding = response['embedding']

    vector_db = client.get_collection(name='conversations')
    results = vector_db.query(query_embeddings=[prompt_embedding], n_results=1)
    best_embedding = results['documents'][0][0]

    return best_embedding

def create_queries(prompt):
    query_msg = (
            'You are a first principle reasoning search query AI agent. '
            'Your list of search queries will be ran on an embedding database of all your conversations '
            'you have ever had with the user. With first principles create a Python list of euqeries to '
            'search the embeddings database for any data that would be necessary to have access to in '
            'order to correctly respond to the prompt. Your response must be a Python list with no syntax errors. '
            'Do not explain anything and do not ever generate anything but a perfect syntax Python list'
    )
    query_cocnvo = [
            {'role':'system', 'content': query_msg},
            {'role':'user', 'content': 'Write an email to my car insurance company and create a persuasive request for them to lower my rate.'},
            {'role': 'assistant', 'content': '["What is the users name?", "What is the users current auto insurance provider?"]'},
            {'role': 'user', 'content':prompt}
    ]

conversations = fetch_conversations()
create_vector_db(conversations=conversations)
while True:
    prompt = input('USER: \n')
    context = retrieve_embeddings(prompt=prompt)
    prompt = 'USER PROMPT: %s \nCONTEXT FROM EMBEDDINGS: %s'%(prompt,context)
    stream_response(prompt=prompt) 

