"""
ollama_client.py
─────────────────────────────────────────────────────────────────
Ollama local LLM client for IMDTools AI features.

Setup:
  1. Install Ollama: https://ollama.com
  2. Pull model:     ollama pull llama3.1
  3. Start Ollama:   ollama serve  (or it auto-starts)
  4. This client connects to: http://localhost:11434

Models recommended:
  llama3.1       → 8B params, 4.7GB, good quality
  mistral        → 7B params, 4.1GB, slightly faster
  llama3.1:70b   → 70B params, 40GB (needs 32GB RAM)
"""

import requests
import json

OLLAMA_URL   = 'http://localhost:11434'
DEFAULT_MODEL = 'llama3.1:latest'


def is_ollama_running() -> bool:
    """Check if Ollama service is running."""
    try:
        r = requests.get(f'{OLLAMA_URL}/api/tags', timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def get_available_models() -> list:
    """Return list of locally available models."""
    try:
        r = requests.get(f'{OLLAMA_URL}/api/tags', timeout=3)
        if r.status_code == 200:
            models = r.json().get('models', [])
            return [m['name'] for m in models]
    except Exception:
        pass
    return []


def generate(prompt: str,
             system: str = None,
             model: str  = DEFAULT_MODEL,
             stream: bool = False) -> str:
    """
    Generate text from Ollama.

    Parameters:
        prompt  : user message
        system  : system context (basin knowledge)
        model   : ollama model name
        stream  : if True, returns generator for streaming

    Returns:
        Full response text (stream=False)
        Generator of text chunks (stream=True)
    """
    payload = {
        'model':  model,
        'prompt': prompt,
        'stream': stream,
        'options': {
            'temperature': 0.3,    # Lower = more factual
            'top_p':       0.9,
            'num_predict': 1024,   # Max tokens to generate
        }
    }
    if system:
        payload['system'] = system

    if stream:
        return _stream_generate(payload)
    else:
        return _sync_generate(payload)


def _sync_generate(payload: dict) -> str:
    """Non-streaming generation."""
    try:
        r = requests.post(
            f'{OLLAMA_URL}/api/generate',
            json=payload,
            timeout=120
        )
        if r.status_code == 200:
            return r.json().get('response', '')
        else:
            return f'Error: Ollama returned status {r.status_code}'
    except requests.exceptions.ConnectionError:
        return ('Error: Ollama is not running. '
                'Please start Ollama with: ollama serve')
    except Exception as e:
        return f'Error: {str(e)}'


def _stream_generate(payload: dict):
    """
    Streaming generation — yields text chunks.
    Use with Flask Response(stream_with_context(...))
    """
    try:
        with requests.post(
            f'{OLLAMA_URL}/api/generate',
            json=payload,
            stream=True,
            timeout=120
        ) as r:
            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get('response', '')
                    if token:
                        yield token
                    if chunk.get('done', False):
                        break
    except requests.exceptions.ConnectionError:
        yield ('⚠️ Ollama is not running. '
               'Please install and start Ollama: https://ollama.com')
    except Exception as e:
        yield f'⚠️ Error: {str(e)}'