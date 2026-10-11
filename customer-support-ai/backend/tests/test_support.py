import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.engine import SupportEngine, Route, OrderInput
from app import main
@pytest.fixture
def engine(tmp_path):
    return SupportEngine(persist=str(tmp_path),live=False)
def collect(engine,sid,q):
    async def run(): return [e async for e in engine.chat(sid,q)]
    return asyncio.run(run())
def test_routing_and_structured_output(engine):
    for q,route in [('Hi','normal'),('What is your refund policy?','rag'),('Where is order 12345?','tool'),('Refund order 67890','tool')]:
        result=asyncio.run(engine.router.ainvoke({'question':q,'history':''}))
        assert isinstance(result,Route) and result.route==route
    with pytest.raises(ValidationError): Route(route='unknown')
    with pytest.raises(ValidationError): OrderInput(order_id='x')
def test_lcel_retrieval_sources(engine):
    events=collect(engine,engine.new_session(),'What is your refund policy?')
    sources=next(e['sources'] for e in events if e['type']=='sources')
    assert any('30 days' in s['content'] for s in sources)
    answer=''.join(e['text'] for e in events if e['type']=='delta')
    assert '[1]' in answer and '30 days' in answer
    assert events[-1]['type']=='done'
def test_tools_history_and_followup(engine):
    sid=engine.new_session()
    collect(engine,sid,'Where is order 12345?')
    events=collect(engine,sid,'Cancel it')
    assert next(e for e in events if e['type']=='confirmation')['order_id']=='12345'
    assert len(engine.session(sid))==4
    result=engine.tools['ticket'].invoke({'description':'Damaged item'})
    assert result['ticket_id']=='T-0001'
    assert engine.tools['details'].invoke({'order_id':'12345'})['customer']=='Alex Morgan'
def test_confirmation_bound_replay_decline(engine):
    sid=engine.new_session();other=engine.new_session()
    token=next(e['token'] for e in collect(engine,sid,'Cancel order 12345') if e['type']=='confirmation')
    assert engine.orders['12345']['status']=='processing'
    with pytest.raises(ValueError): engine.confirm(other,token,True)
    engine.confirm(sid,token,False)
    assert engine.orders['12345']['status']=='processing'
    with pytest.raises(ValueError): engine.confirm(sid,token,True)
    token=next(e['token'] for e in collect(engine,sid,'Cancel order 12345') if e['type']=='confirmation')
    engine.confirm(sid,token,True)
    assert engine.orders['12345']['status']=='cancelled'
def test_refund_eligibility(engine):
    sid=engine.new_session()
    token=next(e['token'] for e in collect(engine,sid,'Refund order 12345') if e['type']=='confirmation')
    with pytest.raises(ValueError): engine.confirm(sid,token,True)
    token=next(e['token'] for e in collect(engine,sid,'Refund order 67890') if e['type']=='confirmation')
    engine.confirm(sid,token,True)
    assert engine.orders['67890']['status']=='refunded'
def test_api_stream_errors_and_validation(engine,monkeypatch):
    monkeypatch.setattr(main,'engine',engine)
    client=TestClient(main.app)
    sid=client.post('/api/conversations').json()['id']
    assert client.post(f'/api/conversations/{sid}/chat',json={'message':''}).status_code==422
    assert client.post('/api/conversations/missing/chat',json={'message':'hello'}).status_code==404
    response=client.post(f'/api/conversations/{sid}/chat',json={'message':'Where is order 11111?'})
    assert any(json.loads(line)['type']=='error' for line in response.text.splitlines())
    response=client.post(f'/api/conversations/{sid}/chat',json={'message':'Hi'})
    assert json.loads(response.text.splitlines()[-1])['type']=='done'

def test_expired_confirmation(engine):
    sid=engine.new_session()
    token=next(e['token'] for e in collect(engine,sid,'Cancel order 12345') if e['type']=='confirmation')
    engine.pending[token]['expires']=0
    with pytest.raises(ValueError,match='expired'): engine.confirm(sid,token,True)
    assert engine.orders['12345']['status']=='processing'
def test_parallel_conversation_rejected(engine):
    sid=engine.new_session();engine.busy.add(sid)
    with pytest.raises(ValueError,match='already running'): collect(engine,sid,'Hi')
