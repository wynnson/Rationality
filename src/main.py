import os 

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from agents.generator import generate_gemma


app = FastAPI()

load_dotenv()

@app.get("/")
def read_root():
    return ""


@app.get("/generate")
def send_request(query) -> str:
    try:
        api_key = os.getenv("GEMMA_KEY")
        client = genai.Client(api_key=api_key)
        generate_gemma(client, query)
    
    except:
        raise HTTPException(500, "Generation failed")