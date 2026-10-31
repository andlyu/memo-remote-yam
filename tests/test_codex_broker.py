import json
from pathlib import Path
import socket
import sys
import threading
import pytest
from agp_remote_yam.codex_broker import execute,receive,send,validate


def value():
    return dict(op='coding',protocol='agp-codex-remote-v1',prompt='offline fixture',
                executor_url='ws://127.0.0.1:32123',executor_token='a'*43)


def test_broker_rejects_endpoint_and_cli_overrides():
    assert validate(value())['prompt']=='offline fixture'
    for changes in [dict(executor_url='ws://example.com:32123'),dict(executor_url='ws://127.0.0.1:99999'),
                    dict(binary='/bin/sh'),dict(model='other'),dict(executor_token='short')]:
        with pytest.raises(ValueError):validate(value()|changes)


@pytest.mark.parametrize('prepared', [False, True])
def test_native_environment_handshake_and_result(tmp_path, prepared):
    home=tmp_path/'home';(home/'workspace').mkdir(parents=True)
    binary=tmp_path/'codex-fixture'
    binary.write_text('#!'+sys.executable+'\n'+'''
import json,sys
assert 'features.shell_tool=true' in sys.argv
assert 'features.unified_exec=true' in sys.argv
assert 'mcp_servers={}' in sys.argv
assert 'model_reasoning_effort="low"' in sys.argv
assert 'shell_environment_policy.inherit="none"' in sys.argv
assert any(v.startswith('shell_environment_policy.set=') and 'HOME="/tmp"' in v and '/opt/python/bin' in v for v in sys.argv)
def emit(value):print(json.dumps(value),flush=True)
warming=0
for line in sys.stdin:
 v=json.loads(line)
 if 'id' not in v:continue
 i=v['id'];p=v.get('params',{})
 if i==5:
  assert v['method']=='environment/info'
  warming+=1
  if warming==1:
   emit(dict(id=i,error=dict(code=-32603,message='executor starting')));continue
  emit(dict(id=i,result=dict(cwd='file:///work',shell=dict(name='sh',path='/bin/sh'))));continue
 if i==2:
  assert v['method']=='environment/add' and p['execServerUrl']=='ws://127.0.0.1:32123'
  assert p['authBearerToken']=='a'*43
 if i==3:
  assert p['environments'][0]['cwd']=='/work' and p['ephemeral']
  assert p['model']=='gpt-6-astra'
 emit(dict(id=i,result={'thread':{'id':'fixture'}} if i==3 else {}))
 if i==4:
  assert warming==2
  assert p['outputSchema']['properties']['status']['enum']==['continue','done','give_up']
  result=dict(status='done',summary='Offline fixture complete',evidence=[])
  emit(dict(method='item/completed',params=dict(item=dict(type='agentMessage',text=json.dumps(result)))))
  emit(dict(method='turn/completed',params=dict(turn=dict(status='completed'))))
''')
    binary.chmod(0o700)
    left,right=socket.socketpair();failures=[]
    def run():
        try:
            request=value()
            if prepared: request=dict(op='prepare',protocol='agp-codex-remote-v2',executor_url=request['executor_url'],executor_token=request['executor_token'])
            execute(left,request,binary=str(binary),home=home,timeout=5)
        except Exception as exc:failures.append(exc)
    thread=threading.Thread(target=run);thread.start();right.settimeout(6)
    try:
        event=receive(right)
        while event.get('event', {}).get('type') == 'agp.profile': event=receive(right)
        if prepared:
            assert event==dict(prepared=True)
            send(right,dict(prompt='offline fixture'))
            event=receive(right)
        assert event['event']['item']['type']=='agent_message'
        assert receive(right)['result']['status']=='done'
        thread.join(5);assert not thread.is_alive() and not failures
        assert not list((home/'workspace').iterdir())
    finally:left.close();right.close()


def test_broker_images_cannot_reference_a_host_path_or_network_url():
    import base64
    from agp_remote_yam.mock import preview
    valid='data:image/jpeg;base64,'+base64.b64encode(preview()).decode()
    assert validate(value()|dict(images=[valid]))['images']==[valid]
    for images in [['file:///home/login'], ['https://example.com/image.jpg'], [valid]*5,
                   ['data:image/jpeg;base64,not-base64'], ['data:image/jpeg;base64,YQ==']]:
        with pytest.raises(ValueError): validate(value()|dict(images=images))
