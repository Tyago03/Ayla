from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from ayla_v2.main import create_app
from ayla_v2.speech import LocalSpeech, MAX_AUDIO_BYTES
from ayla_v2.errors import AppError
from ayla_v2.schemas import Comando

class Speech:
    calls=[]
    def status(self): return {'disponivel':True,'modo':'simulado','limite_segundos':60}
    def transcribe(self,raw):
        self.calls.append(raw)
        return 'Adicione café na lista mercado.'

@pytest.fixture
def fixture(tmp_path):
    voice=Speech();voice.calls=[]
    def parse(_): raise AssertionError('Ditado não pode invocar o modelo de comandos')
    app=create_app(tmp_path/'test.db',parse,speech=voice)
    with TestClient(app,base_url='http://127.0.0.1') as client:
        yield client,voice

def test_transcription_does_not_send_command(fixture):
    c,voice=fixture
    result=c.post('/api/voz/transcrever',content=b'test-audio',headers={'Content-Type':'audio/webm'})
    assert result.status_code==200 and result.json()['enviado'] is False
    assert voice.calls==[b'test-audio']
    assert c.get('/api/listas').json()=={'listas':[]}

def test_status(fixture):
    assert fixture[0].get('/api/voz/status').json()['disponivel']

@pytest.mark.parametrize('media',['application/json','text/plain','image/png'])
def test_invalid_audio_type(fixture,media):
    assert fixture[0].post('/api/voz/transcrever',content=b'x',headers={'Content-Type':media}).status_code==415

def test_audio_limits(fixture):
    c,voice=fixture
    response=c.post('/api/voz/transcrever',content=b'x'*(MAX_AUDIO_BYTES+1),headers={'Content-Type':'audio/webm'})
    assert response.status_code==413 and voice.calls==[]

def test_audio_stream_limit(fixture):
    c,voice=fixture
    response=c.post('/api/voz/transcrever',content=iter([b'x'*(MAX_AUDIO_BYTES),b'x']),headers={'Content-Type':'audio/webm'})
    assert response.status_code==413 and voice.calls==[]

def test_audio_foreign_origin(fixture):
    c,voice=fixture
    assert c.post('/api/voz/transcrever',content=b'x',headers={'Content-Type':'audio/webm','Origin':'https://elsewhere.test'}).status_code==403
    assert not voice.calls

def test_audio_compressed_refused(fixture):
    assert fixture[0].post('/api/voz/transcrever',content=b'x',headers={'Content-Type':'audio/webm','Content-Encoding':'gzip'}).status_code==415

def test_no_install_runtime_download(tmp_path):
    speech=LocalSpeech(tmp_path/'missing')
    assert speech.status()['disponivel'] is False
    with pytest.raises(AppError,match='não instalado'):
        speech.transcribe(b'test')
    assert not (tmp_path/'missing').exists()

@pytest.mark.parametrize('raw',[b'',b'x'*(MAX_AUDIO_BYTES+1)])
def test_empty_or_big_rejected_before_load(tmp_path,raw):
    with pytest.raises(AppError): LocalSpeech(tmp_path/'missing').transcribe(raw)

def test_voice_resources_exist(fixture):
    c,_=fixture
    assert c.get('/static/voice.js').status_code==200
    html=c.get('/').text
    for element in ('id="microphone"','id="voice-select"','id="voice-consent"','id="dictation-mode"','id="speech-player"'):
        assert element in html
    assert 'microphone=(self)' in c.get('/').headers['Permissions-Policy']
