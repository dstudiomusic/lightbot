# database.py
import os
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from config import PINECONE_API_KEY, PINECONE_ENV, OPENAI_API_KEY

class Database:
   def __init__(self):
       pc = Pinecone(api_key=PINECONE_API_KEY)
       
       if 'lighting-assistant' not in pc.list_indexes().names():
           pc.create_index(
               name='lighting-assistant',
               dimension=1536,
               metric='cosine',
               spec=ServerlessSpec(
                   cloud='aws',
                   region='us-west-2'
               )
           )
       
       self.index = pc.Index('lighting-assistant')
       self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
       self.text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

   def add_directory(self, directory_path):
       if os.path.exists(directory_path):
           for filename in os.listdir(directory_path):
               file_path = os.path.join(directory_path, filename)
               if os.path.isfile(file_path):
                   try:
                       with open(file_path, 'r', encoding='utf-8') as file:
                           text = file.read()
                           chunks = self.text_splitter.split_text(text)
                           for chunk in chunks:
                               self.add_text(chunk, {'text': chunk, 'source': file_path})
                   except Exception as e:
                       print(f"Error processing {file_path}: {e}")

   def add_text(self, text, metadata=None):
       vector = self.embeddings.embed_query(text)
       self.index.upsert(vectors=[(str(hash(text)), vector, metadata)])

   def search(self, query, top_k=5):
       vector = self.embeddings.embed_query(query)
       return self.index.query(vector=vector, top_k=top_k, include_metadata=True)