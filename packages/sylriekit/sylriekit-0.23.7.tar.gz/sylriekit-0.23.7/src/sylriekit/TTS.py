import time
import array
import threading
import uuid
from enum import Enum

import requests
import miniaudio


class _TTS_Provider(Enum):
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"
    CAMBAI = "cambai"


class _TTS_ElevenLabsModels(Enum):
    ELEVEN_MULTILINGUAL_V2 = "eleven_multilingual_v2"
    ELEVEN_TURBO_V2 = "eleven_turbo_v2"
    ELEVEN_MONOLINGUAL_V1 = "eleven_monolingual_v1"
    ELEVEN_MULTILINGUAL_V3 = "eleven_multilingual_v3"


class _TTS_OpenAIModels(Enum):
    GPT_4O_MINI_TTS = "gpt-4o-mini-tts"
    TTS_1 = "tts-1"
    TTS_1_HD = "tts-1-hd"


class _TTS_CambAIModels(Enum):
    MARS_FLASH = "mars-flash"
    MARS_PRO = "mars-pro"
    MARS_INSTRUCT = "mars-instruct"


class _TTS_OpenAIVoices(Enum):
    ALLOY = "alloy"
    ASH = "ash"
    BALLAD = "ballad"
    CORAL = "coral"
    ECHO = "echo"
    FABLE = "fable"
    NOVA = "nova"
    ONYX = "onyx"
    SAGE = "sage"
    SHIMMER = "shimmer"
    VERSE = "verse"
    MARIN = "marin"
    CEDAR = "cedar"


class _TTS_Voice:
    def __init__(self, voice_id: str, provider, model, voice_setting, optional_data: dict = None):
        self.id = voice_id
        self.provider = provider
        self.model = model
        self.voice_setting = voice_setting
        self.optional_data = optional_data or {}


class _TTS_Audio:
    def __init__(self, audio_id: str, voice: _TTS_Voice, thread: threading.Thread, stop_event: threading.Event):
        self.id = audio_id
        self.voice = voice
        self.thread = thread
        self.stop_event = stop_event


class _TTS_Queue:
    def __init__(self, queue_id: str):
        self.id = queue_id
        self.items = []
        self.thread = None
        self.stop_event = threading.Event()
        self.current_audio_stop = None
        self.lock = threading.Lock()


class TTS:
    ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
    OPENAI_BASE_URL = "https://api.openai.com/v1/audio/speech"
    CAMBAI_BASE_URL = "https://client.camb.ai/apis/tts-stream"

    CHUNK_SIZE = 1024
    DEFAULT_OUTPUT_FORMAT = "wav"
    AUDIO_PADDING_MS = 250
    QUEUE_OVERLAP_MS = 0

    ELEVENLABS_API_KEY = None
    OPENAI_API_KEY = None
    CAMBAI_API_KEY = None

    _VOICES = {}
    _AUDIOS = {}
    _QUEUES = {}
    _PLAYBACK_LOCK = threading.Lock()

    Providers = _TTS_Provider

    class Models:
        ElevenLabs = _TTS_ElevenLabsModels
        OpenAI = _TTS_OpenAIModels
        CambAI = _TTS_CambAIModels

    class Voices:
        OpenAI = _TTS_OpenAIVoices

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config.get("api_key", {})
        if "TTS" in config.keys():
            tool_config = config["TTS"]
            cls.ELEVENLABS_API_KEY = tool_config.get("ELEVENLABS_API_KEY", cls.ELEVENLABS_API_KEY)
            cls.OPENAI_API_KEY = tool_config.get("OPENAI_API_KEY", cls.OPENAI_API_KEY)
            cls.CAMBAI_API_KEY = tool_config.get("CAMBAI_API_KEY", cls.CAMBAI_API_KEY)
            cls.CHUNK_SIZE = tool_config.get("CHUNK_SIZE", cls.CHUNK_SIZE)
            cls.DEFAULT_OUTPUT_FORMAT = tool_config.get("DEFAULT_OUTPUT_FORMAT", cls.DEFAULT_OUTPUT_FORMAT)
            cls.AUDIO_PADDING_MS = tool_config.get("AUDIO_PADDING_MS", cls.AUDIO_PADDING_MS)
            cls.QUEUE_OVERLAP_MS = tool_config.get("QUEUE_OVERLAP_MS", cls.QUEUE_OVERLAP_MS)
        if "ELEVENLABS_API_KEY" in api_keys.keys():
            cls.ELEVENLABS_API_KEY = api_keys["ELEVENLABS_API_KEY"]
        if "OPENAI_API_KEY" in api_keys.keys():
            cls.OPENAI_API_KEY = api_keys["OPENAI_API_KEY"]
        if "CAMBAI_API_KEY" in api_keys.keys():
            cls.CAMBAI_API_KEY = api_keys["CAMBAI_API_KEY"]

    @classmethod
    def create_voice(cls, provider: _TTS_Provider, model, voice_id, optional_data: dict = None) -> str:
        internal_id = str(uuid.uuid4())
        model_value = model.value if isinstance(model, Enum) else model
        voice_value = voice_id.value if isinstance(voice_id, Enum) else voice_id
        voice = _TTS_Voice(internal_id, provider, model_value, voice_value, optional_data)
        cls._VOICES[internal_id] = voice
        return internal_id

    @classmethod
    def create_queue(cls) -> str:
        queue_id = str(uuid.uuid4())
        queue = _TTS_Queue(queue_id)
        cls._QUEUES[queue_id] = queue
        return queue_id

    @classmethod
    def play(cls, voice_id: str, text: str) -> str:
        voice = cls._get_voice(voice_id)
        cls._ensure_api_key(voice.provider)
        audio_data = cls._request_audio(voice, text)
        audio_id = str(uuid.uuid4())
        stop_event = threading.Event()
        thread = threading.Thread(
            target=cls._play_audio_bytes_sync,
            args=(audio_data, stop_event, audio_id),
            daemon=True
        )
        audio = _TTS_Audio(audio_id, voice, thread, stop_event)
        cls._AUDIOS[audio_id] = audio
        thread.start()
        return audio_id

    @classmethod
    def play_queued(cls, queue_id: str, voice_id: str, text: str) -> str:
        voice = cls._get_voice(voice_id)
        queue = cls._get_queue(queue_id)
        cls._ensure_api_key(voice.provider)
        audio_id = str(uuid.uuid4())
        with queue.lock:
            queue.items.append((audio_id, voice, text))
            if queue.thread is None or not queue.thread.is_alive():
                queue.stop_event.clear()
                queue.thread = threading.Thread(
                    target=cls._process_queue,
                    args=(queue_id,),
                    daemon=True
                )
                queue.thread.start()
        return audio_id

    @classmethod
    def save_to_file(cls, voice_id: str, text: str, path: str):
        voice = cls._get_voice(voice_id)
        cls._ensure_api_key(voice.provider)
        audio_data = cls._request_audio(voice, text)
        with open(path, "wb") as f:
            f.write(audio_data)

    @classmethod
    def play_file(cls, path: str) -> str:
        with open(path, "rb") as f:
            audio_data = f.read()
        audio_id = str(uuid.uuid4())
        stop_event = threading.Event()
        thread = threading.Thread(
            target=cls._play_audio_bytes_sync,
            args=(audio_data, stop_event, audio_id),
            daemon=True
        )
        audio = _TTS_Audio(audio_id, None, thread, stop_event)
        cls._AUDIOS[audio_id] = audio
        thread.start()
        return audio_id

    @classmethod
    def stop(cls, audio_id: str):
        if audio_id in cls._AUDIOS:
            audio = cls._AUDIOS[audio_id]
            audio.stop_event.set()

    @classmethod
    def stop_queue(cls, queue_id: str):
        if queue_id in cls._QUEUES:
            queue = cls._QUEUES[queue_id]
            queue.stop_event.set()
            with queue.lock:
                queue.items.clear()
                if queue.current_audio_stop is not None:
                    queue.current_audio_stop.set()

    @classmethod
    def stop_all(cls):
        for audio_id in list(cls._AUDIOS.keys()):
            cls.stop(audio_id)
        for queue_id in list(cls._QUEUES.keys()):
            cls.stop_queue(queue_id)

    @classmethod
    def is_playing(cls, audio_id: str) -> bool:
        if audio_id in cls._AUDIOS:
            audio = cls._AUDIOS[audio_id]
            return audio.thread.is_alive()
        return False

    @classmethod
    def is_queue_active(cls, queue_id: str) -> bool:
        if queue_id in cls._QUEUES:
            queue = cls._QUEUES[queue_id]
            return queue.thread is not None and queue.thread.is_alive()
        return False

    ### PRIVATE UTILITIES START
    @classmethod
    def _get_voice(cls, voice_id: str) -> _TTS_Voice:
        if voice_id not in cls._VOICES:
            raise ValueError(f"Voice ID '{voice_id}' not found. Use TTS.create_voice() first.")
        return cls._VOICES[voice_id]

    @classmethod
    def _get_queue(cls, queue_id: str) -> _TTS_Queue:
        if queue_id not in cls._QUEUES:
            raise ValueError(f"Queue ID '{queue_id}' not found. Use TTS.create_queue() first.")
        return cls._QUEUES[queue_id]

    @classmethod
    def _ensure_api_key(cls, provider: _TTS_Provider):
        if provider == _TTS_Provider.ELEVENLABS:
            if cls.ELEVENLABS_API_KEY is None:
                raise ValueError("ElevenLabs API Key is not set! Use load_config() or set TTS.ELEVENLABS_API_KEY")
        elif provider == _TTS_Provider.OPENAI:
            if cls.OPENAI_API_KEY is None:
                raise ValueError("OpenAI API Key is not set! Use load_config() or set TTS.OPENAI_API_KEY")
        elif provider == _TTS_Provider.CAMBAI:
            if cls.CAMBAI_API_KEY is None:
                raise ValueError("Camb.ai API Key is not set! Use load_config() or set TTS.CAMBAI_API_KEY")

    @classmethod
    def _request_audio(cls, voice: _TTS_Voice, text: str) -> bytes:
        if voice.provider == _TTS_Provider.ELEVENLABS:
            return cls._request_elevenlabs(voice, text)
        elif voice.provider == _TTS_Provider.OPENAI:
            return cls._request_openai(voice, text)
        elif voice.provider == _TTS_Provider.CAMBAI:
            return cls._request_cambai(voice, text)
        raise ValueError(f"Unknown provider: {voice.provider}")

    @classmethod
    def _request_elevenlabs(cls, voice: _TTS_Voice, text: str) -> bytes:
        url = f"{cls.ELEVENLABS_BASE_URL}/text-to-speech/{voice.voice_setting}/stream"
        headers = {
            "xi-api-key": cls.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        data = {
            "text": text,
            "model_id": voice.model,
            "voice_settings": {
                "stability": voice.optional_data.get("stability", 0.5),
                "similarity_boost": voice.optional_data.get("similarity_boost", 0.75)
            }
        }
        data.update({k: v for k, v in voice.optional_data.items() if k not in ["stability", "similarity_boost"]})
        response = requests.post(url, json=data, headers=headers, stream=True)
        if response.status_code != 200:
            raise ValueError(f"ElevenLabs API Error {response.status_code}: {response.text}")
        audio_data = b""
        for chunk in response.iter_content(chunk_size=cls.CHUNK_SIZE):
            if chunk:
                audio_data += chunk
        return audio_data

    @classmethod
    def _request_openai(cls, voice: _TTS_Voice, text: str) -> bytes:
        headers = {
            "Authorization": f"Bearer {cls.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": voice.model,
            "input": text,
            "voice": voice.voice_setting,
            "response_format": voice.optional_data.get("response_format", cls.DEFAULT_OUTPUT_FORMAT)
        }
        if "instructions" in voice.optional_data:
            data["instructions"] = voice.optional_data["instructions"]
        for key, value in voice.optional_data.items():
            if key not in ["response_format", "instructions"]:
                data[key] = value
        response = requests.post(cls.OPENAI_BASE_URL, headers=headers, json=data)
        if response.status_code != 200:
            raise ValueError(f"OpenAI API Error {response.status_code}: {response.text}")
        return response.content

    @classmethod
    def _request_cambai(cls, voice: _TTS_Voice, text: str) -> bytes:
        headers = {
            "x-api-key": cls.CAMBAI_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "voice_id": int(voice.voice_setting) if isinstance(voice.voice_setting, str) and voice.voice_setting.isdigit() else voice.voice_setting,
            "language": voice.optional_data.get("language", "en-us"),
            "speech_model": voice.model,
            "output_configuration": voice.optional_data.get("output_configuration", {
                "format": cls.DEFAULT_OUTPUT_FORMAT,
                "apply_enhancement": True
            })
        }
        if "user_instructions" in voice.optional_data:
            data["user_instructions"] = voice.optional_data["user_instructions"]
        if "enhance_named_entities_pronunciation" in voice.optional_data:
            data["enhance_named_entities_pronunciation"] = voice.optional_data["enhance_named_entities_pronunciation"]
        if "voice_settings" in voice.optional_data:
            data["voice_settings"] = voice.optional_data["voice_settings"]
        if "inference_options" in voice.optional_data:
            data["inference_options"] = voice.optional_data["inference_options"]
        response = requests.post(cls.CAMBAI_BASE_URL, headers=headers, json=data, stream=True)
        if response.status_code != 200:
            raise ValueError(f"Camb.ai API Error {response.status_code}: {response.text}")
        audio_data = b""
        for chunk in response.iter_content(chunk_size=cls.CHUNK_SIZE):
            if chunk:
                audio_data += chunk
        return audio_data

    @classmethod
    def _process_queue(cls, queue_id: str):
        queue = cls._QUEUES.get(queue_id)
        if queue is None:
            return
        while not queue.stop_event.is_set():
            item = None
            with queue.lock:
                if queue.items:
                    item = queue.items.pop(0)
            if item is None:
                break
            audio_id, voice, text = item
            try:
                audio_data = cls._request_audio(voice, text)
                stop_event = threading.Event()
                with queue.lock:
                    queue.current_audio_stop = stop_event
                audio = _TTS_Audio(audio_id, voice, None, stop_event)
                cls._AUDIOS[audio_id] = audio
                has_more = len(queue.items) > 0
                if cls.QUEUE_OVERLAP_MS > 0 and has_more:
                    thread = threading.Thread(
                        target=cls._play_audio_bytes_sync,
                        args=(audio_data, stop_event, audio_id),
                        daemon=True
                    )
                    thread.start()
                    duration = cls._get_audio_duration(audio_data)
                    overlap_wait = max(0, duration - (cls.QUEUE_OVERLAP_MS / 1000))
                    start_time = time.time()
                    while time.time() - start_time < overlap_wait:
                        if stop_event.is_set() or queue.stop_event.is_set():
                            break
                        time.sleep(0.05)
                else:
                    cls._play_audio_bytes_sync(audio_data, stop_event, audio_id)
                with queue.lock:
                    queue.current_audio_stop = None
            except Exception:
                pass
            if queue.stop_event.is_set():
                break

    @classmethod
    def _get_audio_duration(cls, audio_data: bytes) -> float:
        try:
            decoded = miniaudio.decode(audio_data, output_format=miniaudio.SampleFormat.SIGNED16)
            return len(decoded.samples) / (decoded.sample_rate * decoded.nchannels)
        except Exception:
            return 0.0

    @classmethod
    def _play_audio_bytes_sync(cls, audio_data: bytes, stop_event: threading.Event, audio_id: str):
        try:
            decoded = miniaudio.decode(audio_data, output_format=miniaudio.SampleFormat.SIGNED16)
            padding_samples = int(decoded.sample_rate * decoded.nchannels * cls.AUDIO_PADDING_MS / 1000)
            silence = array.array('h', [0] * padding_samples)
            samples = silence + array.array('h', decoded.samples)

            def sample_generator():
                position = 0
                required_frames = yield b""
                while position < len(samples) and not stop_event.is_set():
                    samples_needed = required_frames * decoded.nchannels
                    end = min(position + samples_needed, len(samples))
                    chunk = samples[position:end]
                    required_frames = yield chunk.tobytes()
                    position = end

            device = miniaudio.PlaybackDevice(
                output_format=miniaudio.SampleFormat.SIGNED16,
                nchannels=decoded.nchannels,
                sample_rate=decoded.sample_rate
            )
            generator = sample_generator()
            next(generator)
            device.start(generator)
            duration = len(samples) / (decoded.sample_rate * decoded.nchannels)
            start_time = time.time()
            while time.time() - start_time < duration + 0.2:
                if stop_event.is_set():
                    break
                time.sleep(0.05)
            device.close()
        except Exception:
            pass
        finally:
            if audio_id in cls._AUDIOS:
                del cls._AUDIOS[audio_id]
    ### PRIVATE UTILITIES END
