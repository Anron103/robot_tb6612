from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import os
import base64
import logging
import requests
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="Silero Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# server configuration
class Config:
    API_URL = os.getenv("CONVERSATION_API_URL", "http://192.168.0.1/ask")
    API_KEY = os.getenv("CONVERSATION_API_KEY", "keydsfg")
    API_TIMEOUT = 5
    CACHE_DIR = "audio_cache"

# request model for conversation endpoint
class ConversationRequest(BaseModel):
    user_text: str
    speaker: str = "baya"
    sample_rate: int = 48000

# response model for conversation endpoint
class ConversationResponse(BaseModel):
    audio_base64: str
    sample_rate: int
    user_text: str
    bot_response: str
    is_error: bool = False
    message: str

# global tts model variable
tts_model = None
# try to load model if none is found
def load_tts_model():
    global tts_model
    try:
        device = torch.device('cpu')
        torch.set_num_threads(4)
        local_file = 'model.pt'
        if not os.path.isfile(local_file):
            logger.info("downloading silero model...")
            torch.hub.download_url_to_file(
                'https://models.silero.ai/models/tts/ru/v4_ru.pt',
                local_file
            )
        tts_model = torch.package.PackageImporter(local_file).load_pickle(
            "tts_models", "model"
        )
        tts_model.to(device)
        logger.info("model loaded successfully")
        return True
    except Exception as e:
        logger.error(f"model load error: {e}")
        return False

def get_cache_path(text):
    if not os.path.exists(Config.CACHE_DIR):
        os.makedirs(Config.CACHE_DIR)
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    return os.path.join(Config.CACHE_DIR, f"{text_hash}.wav")

def get_cached_audio(text):
    path = get_cache_path(text)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return f.read()
    return None

def save_to_cache(text, data):
    path = get_cache_path(text)
    with open(path, 'wb') as f:
        f.write(data)

def generate_audio(text, speaker, sample_rate):
    # check cache first
    cached = get_cached_audio(text)
    if cached:
        return cached, True
    # generate new audio
    try:
        path = tts_model.save_wav(
            text=text,
            speaker=speaker,
            sample_rate=sample_rate
        )
        with open(path, 'rb') as f:
            data = f.read()
        os.remove(path)
        save_to_cache(text, data)
        return data, False
    except Exception as e:
        logger.error(f"tts generation error: {e}")
        return None, False

def call_external_api(text):
    try:
        resp = requests.get(
            Config.API_URL,
            params={'text': text, 'key': Config.API_KEY},
            timeout=Config.API_TIMEOUT
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get('response') or data.get('text')
        return None
    except Exception as e:
        logger.error(f"external api error: {e}")
        return None

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": tts_model is not None
    }

@app.post("/conversation", response_model=ConversationResponse)
async def conversation(req: ConversationRequest):
    if tts_model is None:
        raise HTTPException(503, "tts model not loaded")
    logger.info(f"processing: '{req.user_text[:30]}...'")
    # try to get response from external api
    api_response = call_external_api(req.user_text)
    is_error = False
    if api_response:
        bot_text = api_response
        logger.info("external api success")
    else:
        # api failed - echo user text as error
        bot_text = req.user_text
        is_error = True
        logger.warning("external api failed - echoing text")
    # generate audio for response text
    audio_data, cached = generate_audio(
        bot_text,
        req.speaker,
        req.sample_rate
    )
    if not audio_data:
        raise HTTPException(500, "tts generation failed")
    return ConversationResponse(
        audio_base64=base64.b64encode(audio_data).decode('utf-8'),
        sample_rate=req.sample_rate,
        user_text=req.user_text,
        bot_response=bot_text,
        is_error=is_error,
        message="error echo" if is_error else "success"
    )

if __name__ == "__main__":
    import uvicorn
    load_tts_model()
    uvicorn.run(app, host="0.0.0.0", port=8000)