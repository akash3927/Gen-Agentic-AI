import asyncio
import json
import pytest
from app.agent import DemoPlanner, run
from app.models import Decision, State
from app.tools import calculator, execute, public_url


@pytest.fixture
def anyio_backend():
    return "asyncio"


def state(**kwargs):
    return State(goal='Research Python',max_steps=10,token_budget=100000,**kwargs)


class Scripted:
    def __init__(self, actions):
        self.actions = iter(actions)
        self.seen = []
    async def decide(self, state):
        self.seen.append(state.model_dump())
        tool,args = next(self.actions)
        return Decision(action='tool' if tool else 'finish',summary='Next action',plan=[{'title':'Gather evidence','status':'in_progress'}],tool=tool,arguments_json=json.dumps(args),report='' if tool else 'Findings based on collected observations.'),10,20


@pytest.mark.anyio
async def test_loop_observation_state_and_completion():
    s=state()
    planner=Scripted([('calculator',{'expression':'2+3'}),(None,{})])
    await run(s,planner)
    assert s.status=='completed' and len(s.steps)==2
    assert planner.seen[1]['steps'][0]['observation']=={'value':5}
    assert s.plan and s.input_tokens==20 and s.output_tokens==40


@pytest.mark.anyio
async def test_max_steps():
    s=state();s.max_steps=1
    await run(s,Scripted([('calculator',{'expression':'1+1'})]))
    assert s.status=='stopped' and 'Maximum' in s.reason


@pytest.mark.anyio
async def test_failure_is_observed_and_recovered():
    s=state()
    await run(s,Scripted([('calculator',{'expression':'1/0'}),('calculator',{'expression':'4*5'}),(None,{})]))
    assert s.steps[0]['status']=='error' and s.steps[1]['observation']['value']==20
    assert s.status=='completed'


@pytest.mark.anyio
@pytest.mark.parametrize('approved',[True,False])
async def test_approval_pause_and_resume(tmp_path,monkeypatch,approved):
    monkeypatch.setenv('NOTES_DIR',str(tmp_path))
    s=state()
    planner=Scripted([('save_notes',{'content':'evidence'}),(None,{})])
    await run(s,planner)
    assert s.status=='awaiting_approval' and not list(tmp_path.iterdir())
    await run(s,planner,approved)
    assert s.status=='completed'
    assert bool(list(tmp_path.iterdir()))==approved
    assert s.notes==(['evidence'] if approved else [])


@pytest.mark.anyio
async def test_validation_before_approval():
    s=state()
    await run(s,Scripted([('save_notes',{'content':'x','path':'evil'}),(None,{})]))
    assert s.pending is None and s.steps[0]['status']=='error'


@pytest.mark.anyio
async def test_budget_prevents_model_call():
    s=state();s.token_budget=2000
    await run(s,Scripted([]))
    assert s.status=='stopped' and not s.steps


@pytest.mark.anyio
async def test_tool_timeout(monkeypatch):
    async def slow(*args):
        await asyncio.sleep(1)
    monkeypatch.setattr('app.tools.perform',slow)
    assert 'timed out' in (await execute('calculator',{'expression':'1'},state(),timeout=.001))['error']


@pytest.mark.anyio
async def test_transient_retry(monkeypatch):
    import httpx
    calls=[]
    async def flaky(*args):
        calls.append(1)
        if len(calls)==1: raise httpx.ConnectError('offline')
        return {'value':1}
    monkeypatch.setattr('app.tools.perform',flaky)
    assert await execute('calculator',{'expression':'1'},state())=={'value':1}
    assert len(calls)==2


@pytest.mark.parametrize('expression',['__import__("os")','2**100000','True+1','1e100'])
def test_calculator_rejects_unsafe_expressions(expression):
    with pytest.raises(ValueError): calculator(expression)


@pytest.mark.anyio
async def test_private_urls_blocked():
    for url in ['http://example.com','https://127.0.0.1','https://user:pass@example.com']:
        with pytest.raises(ValueError): await public_url(url)


@pytest.mark.anyio
async def test_demo_complete(tmp_path,monkeypatch):
    monkeypatch.setenv('NOTES_DIR',str(tmp_path))
    s=state(demo=True)
    p=DemoPlanner()
    await run(s,p)
    assert s.status=='awaiting_approval' and s.sources
    await run(s,p,False)
    assert s.status=='completed' and 'DEMO ONLY' in s.report


def test_api_demo_and_duplicate_approval():
    from fastapi.testclient import TestClient
    from app.main import app
    import time
    with TestClient(app) as client:
        response=client.post('/api/runs',json={'goal':'Research Python','demo':True})
        assert response.status_code==201
        run_id=response.json()['id']
        for _ in range(100):
            snapshot=client.get('/api/runs/'+run_id).json()
            if snapshot['status']=='awaiting_approval': break
            time.sleep(.01)
        assert snapshot['status']=='awaiting_approval'
        assert client.post('/api/runs/'+run_id+'/approval',json={'approved':False}).status_code==200
        assert client.post('/api/runs/'+run_id+'/approval',json={'approved':False}).status_code==409
        assert client.get('/api/runs/unknown').status_code==404


@pytest.mark.anyio
async def test_search_source_collection(monkeypatch):
    async def fake(name, args, state):
        return {'sources':[{'title':'Reference','url':'https://example.com','kind':'search_snippet'}]}
    monkeypatch.setattr('app.tools.perform',fake)
    s=state()
    await run(s,Scripted([('web_search',{'query':'Python'}),(None,{})]))
    assert s.sources[0]['url']=='https://example.com'
    assert 'https://example.com' in s.report


@pytest.mark.anyio
async def test_read_page_body_and_extraction(monkeypatch):
    import httpx
    from app import tools
    async def allow(url): pass
    monkeypatch.setattr(tools,'public_url',allow)
    transport=httpx.MockTransport(lambda request: httpx.Response(200,headers={'content-type':'text/html'},text='<html><script>ignore this</script><p>Evidence here</p></html>'))
    original=httpx.AsyncClient
    monkeypatch.setattr(tools.httpx,'AsyncClient',lambda **kwargs: original(transport=transport,**kwargs))
    result=await execute('read_page',{'url':'https://example.com'},state())
    assert 'Evidence here' in result['text'] and 'ignore this' not in result['text']
    assert result['sources'][0]['kind']=='read_page'


@pytest.mark.anyio
async def test_model_failure_stops():
    s=state()
    await run(s,Scripted([]))
    assert s.status=='failed' and 'Model failed' in s.reason
