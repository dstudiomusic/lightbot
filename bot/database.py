import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from config import PINECONE_API_KEY, PINECONE_ENV, OPENAI_API_KEY

load_dotenv()


class Database:
    def __init__(self):
        self.pc = Pinecone(
            api_key=os.environ.get("PINECONE_API_KEY")
        )
        self.index = self.pc.Index('lighting-assistant')
        self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        self.text_splitter = CharacterTextSplitter(
            chunk_size=1000, chunk_overlap=0)

    def add_directory(self, directory_path):
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                    chunks = self.text_splitter.split_text(text)
                    for chunk in chunks:
                        self.add_text(chunk, {'source': file_path})

    def add_text(self, text, metadata=None):
        response = self.embeddings.embed_query(text)
        self.index.upsert([(str(hash(text)), response, metadata)])

    def search(self, query, top_k=5):
        response = self.embeddings.embed_query(query)
        results = self.index.query(vector=response, top_k=top_k)
        return results
