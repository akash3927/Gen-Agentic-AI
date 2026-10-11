import json
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from .engine import SupportEngine
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
app=FastAPI(title='Northstar Customer Support')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://127.0.0.1:5173'],allow_methods=['GET','POST'],allow_headers=['Content-Type'])
engine=None
def get_engine():
    global engine
    if engine is None: engine=SupportEngine(persist=str(Path(__file__).resolve().parents[1]/'data'/'chroma'))
    return engine
class ChatRequest(BaseModel):
    message: str=Field(min_length=1,max_length=4000)
    @field_validator('message')
    @classmethod
    def nonblank(cls, value):
        if not value.strip(): raise ValueError('Message must not be blank')
        return value.strip()
class Confirmation(BaseModel):
    token: str
    approved: bool
@app.get('/api/health')
def health(): return {'status':'ok','mode':'openai' if os.getenv('OPENAI_API_KEY') else 'demo'}
@app.post('/api/conversations')
def create(): return {'id':get_engine().new_session()}
@app.get('/api/conversations/{sid}')
def history(sid:str):
    try: return {'messages':get_engine().session(sid)}
    except ValueError as exc: raise HTTPException(404,str(exc))
@app.post('/api/conversations/{sid}/chat')
def chat(sid:str,body:ChatRequest):
    try: get_engine().session(sid)
    except ValueError as exc: raise HTTPException(404,str(exc))
    async def events():
        try:
            async for event in get_engine().chat(sid,body.message.strip()):
                yield json.dumps(event)+'\n'
        except Exception as exc:
            yield json.dumps({'type':'error','message':str(exc) if isinstance(exc,ValueError) else 'The assistant is unavailable. Check backend configuration and try again.'})+'\n'
    return StreamingResponse(events(),media_type='application/x-ndjson')
@app.post('/api/conversations/{sid}/confirm')
def confirm(sid:str,body:Confirmation):
    try: return {'message':get_engine().confirm(sid,body.token,body.approved)}
    except ValueError as exc: raise HTTPException(400,str(exc))
