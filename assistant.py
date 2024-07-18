#!/bin/env python3.12
import ollama
import chromadb


# prerequisite:
#   python3.12 venv to pip install -r requirements.txt
#   install ollama
#   ollama pull llama3 so that the model is available
#   ollama pull nomic-embed-text

client = chromadb.Client()
message_history = [
    {
        'id': 1,
        'prompt': 'What is my name?',
        'response': 'Your name is Austion, known online as Ai Austin.'
    },
    {
        'id': 2,
        'prompt': 'What is the square root of 9876?',
        'response': '99.378'
    },
    {
        'id': 3,
        'prompt': 'What kind of dog to I have?',
        'response': 'Your dog Roxy is a pitbull'
    }
]

convo = []

def stream_response(prompt):
    convo.append({'role':'user', 'content':prompt})
    response = ''
    stream = ollama.chat(model='llama3', messages=convo, stream=True)
    print('\nASSISTANT:')
    for chunk in stream:
        content = chunk['message']['content']
        response += content
        print(content, end='', flush=True)
    print('\n')
    convo.append({'role':'assistant', 'content':response})

def create_vector_db(conversations):
    vector_db_name = 'conversations'
    try:
        client.delete_collection(name=vector_db_name)
    except ValueError:
        pass

    vector_db = client.create_collection(name=vector_db_name)

    for c in conversations:
        serialized_convo = f'prompt: {c['prompt']} response: {c['response']}'
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

create_vector_db(conversations=message_history)
while True:
    prompt = input('USER: \n')
    context = retrieve_embeddings(prompt=prompt)
    prompt = f'USER PROMPT: {prompt} \nCONTEXT FROM EMBEDDINGS: {context}'
    stream_response(prompt=prompt) 

