#!/usr/bin/env python3
"""


"""

import os

try:
    import requests
    from bs4 import BeautifulSoup
    _WEBREQ_AVAILABLE = True
except Exception:
    requests = None
    BeautifulSoup = None
    _WEBREQ_AVAILABLE = False
import re
from datetime import datetime
import time
import argparse
import sys
import ast
import json
import logging
import base64
import getpass
from typing import Optional
import difflib

try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.fernet import Fernet
    _CRYPTO_AVAILABLE = True
except Exception:
    _CRYPTO_AVAILABLE = False

try:
    # optional: load .env if python-dotenv installed
    from dotenv import load_dotenv
    _DOTENV_AVAILABLE = True
except Exception:
    _DOTENV_AVAILABLE = False

try:
    import openai
    _OPENAI_AVAILABLE = True
except Exception:
    openai = None
    _OPENAI_AVAILABLE = False

ASSISTANT_NAME = "뉴런"
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'NEURON_config.json')
HISTORY_PATH = os.path.join(os.path.dirname(__file__), 'NEURON_history.txt')
KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), 'NEURON_knowledge.json')
QUEUE_PATH = os.path.join(os.path.dirname(__file__), 'NEURON_learning_queue.jsonl')


def load_config():
    # Returns a dict with at least 'user_name' and optional 'openai_api_key'
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                if not isinstance(cfg, dict):
                    return {"user_name": ""}
                # ensure keys exist
                cfg.setdefault('user_name', '')
                return cfg
    except Exception:
        pass
    return {"user_name": ""}


def load_knowledge():
    try:
        if os.path.exists(KNOWLEDGE_PATH):
            with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception:
        logging.exception('Failed to load knowledge')
    return []


def save_knowledge(items):
    try:
        with open(KNOWLEDGE_PATH, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        logging.exception('Failed to save knowledge')


def teach_pair(question: str, answer: str):
    items = load_knowledge()
    items.append({'q': question.strip(), 'a': answer.strip()})
    save_knowledge(items)


def find_knowledge(prompt: str, threshold: float = 0.6):
    prompt = prompt.strip().lower()
    items = load_knowledge()
    best = None
    best_score = 0.0
    for it in items:
        q = it.get('q','').lower()
        if not q:
            continue
        score = difflib.SequenceMatcher(None, prompt, q).ratio()
        if score > best_score:
            best_score = score
            best = it
    if best and best_score >= threshold:
        return best['a']
    return None


def _load_learning_queue():
    items = []
    try:
        if os.path.exists(QUEUE_PATH):
            with open(QUEUE_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        items.append(json.loads(line))
                    except Exception:
                        items.append({'prompt': line})
    except Exception:
        logging.exception('Failed to read learning queue')
    return items


def _save_learning_queue(items):
    try:
        with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + '\n')
    except Exception:
        logging.exception('Failed to write learning queue')


def queue_for_learning(prompt: str):
    prompt = prompt.strip()
    if not prompt:
        return False
    # don't queue if knowledge already has similar
    if find_knowledge(prompt):
        return False
    items = _load_learning_queue()
    # avoid duplicates
    for it in items:
        if it.get('prompt','') == prompt:
            return False
    items.append({'prompt': prompt, 'when': datetime.now().isoformat()})
    _save_learning_queue(items)
    return True


def process_learning_queue(max_items: int = 5, dry_run: bool = False) -> int:
    """Process queued prompts: generate answers via OpenAI and save to knowledge.

    Returns number of items processed (saved). If dry_run True, does not save, only returns count.
    """
    items = _load_learning_queue()
    if not items:
        return 0
    cfg = load_config()
    limit = int(cfg.get('auto_learn_max_per_run', max_items))
    processed = 0
    remaining = []
    for it in items:
        if processed >= limit:
            remaining.append(it)
            continue
        prompt = it.get('prompt')
        if not prompt:
            continue
        try:
            # ask OpenAI for a concise answer
            answer_prompt = f"뜝럥졾뜝럥 슣돳쎌맄쎈즵뜝룞삕슣돢뙴삕뜝룞삕 쎈뇲쎄땀뺣돍삕쎌쓨뜝럥뉐뜝럥쐿뜝럥쎈닱섃뫁렰뜝럥깓싲쨪삕:\n{prompt}\n뜝럥:\n"
            ans = call_openai(answer_prompt)
            if ans:
                if not dry_run:
                    teach_pair(prompt, ans)
                processed += 1
            else:
                remaining.append(it)
        except Exception:
            remaining.append(it)

    # write back remaining
    _save_learning_queue(remaining)
    return processed


def _derive_key(password: str, salt: bytes) -> bytes:
    # derive a urlsafe base64 key for Fernet
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_api_key(key_str: str, password: str) -> str:
    if not _CRYPTO_AVAILABLE:
    salt = os.urandom(16)
    k = _derive_key(password, salt)
    f = Fernet(k)
    token = f.encrypt(key_str.encode())
    # store salt + token, both base64
    payload = base64.urlsafe_b64encode(salt).decode() + '::' + token.decode()
    return payload


def decrypt_api_key(payload: str, password: str) -> str:
    if not _CRYPTO_AVAILABLE:
    try:
        salt_b64, token = payload.split('::', 1)
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        k = _derive_key(password, salt)
        f = Fernet(k)
        return f.decrypt(token.encode()).decode()
    except Exception:
        raise


def save_config(cfg: dict):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        logging.exception('Failed to save config')


def append_history(role: str, text: str):
    try:
        now = datetime.now().isoformat()
        with open(HISTORY_PATH, 'a', encoding='utf-8') as f:
            f.write(f"[{now}] [{role}] {text}\n")
    except Exception:
        pass


def call_openai(prompt):
    # priority: env var -> config file -> .env
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        cfg = load_config()
        key = cfg.get('openai_api_key') or cfg.get('api_key')
    if not key and _DOTENV_AVAILABLE:
        # attempt to load .env and retry
        try:
            load_dotenv()
            key = os.getenv("OPENAI_API_KEY")
        except Exception:
            pass
    if not key:
    if not _OPENAI_AVAILABLE:
    # Prefer new openai v1+ client if available, otherwise fall back to older API
    messages = [{"role": "user", "content": prompt}]
    start = time.time()
    # New client: openai.OpenAI()
    if hasattr(openai, 'OpenAI'):
        try:
            client = openai.OpenAI(api_key=key)
            # try chat completions endpoint
            resp = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, max_tokens=512)
            elapsed = time.time() - start
            logging.info('OpenAI (v1+) call success (%.3fs)', elapsed)
            # try to extract content from various shapes
            try:
                # expected: resp.choices[0].message.content
                content = resp.choices[0].message.content
            except Exception:
                try:
                    # maybe mapping-like
                    content = resp.choices[0].message['content']
                except Exception:
                    try:
                        # responses API fallbacks
                        content = getattr(resp.choices[0], 'text', '')
                    except Exception:
                        content = str(resp)
            return content.strip() if isinstance(content, str) else str(content)
        except Exception as e:
            # if authentication error (invalid key), disable auto_learn to avoid repeated charges
            msg = str(e)
            try:
                if 'invalid_api_key' in msg or 'Incorrect API key' in msg or 'AuthenticationError' in repr(e):
                    cfg = load_config()
                    cfg['openai_api_key_valid'] = False
                    # disable autonomous processing to be safe
                    cfg['auto_learn'] = False
                    save_config(cfg)
                    logging.warning('Invalid OpenAI API key detected; auto_learn disabled in config')
            except Exception:
                logging.exception('Failed to disable auto_learn after auth error')
            raise
    else:
        # older client
        try:
            openai.api_key = key
            resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, max_tokens=512)
            elapsed = time.time() - start
            logging.info('OpenAI (legacy) call success (%.3fs)', elapsed)
            try:
                content = resp.choices[0].message.content.strip()
            except Exception:
                content = getattr(resp.choices[0], 'text', '') or str(resp)
            return content
        except Exception as e:
            msg = str(e)
            try:
                if 'invalid_api_key' in msg or 'Incorrect API key' in msg or 'AuthenticationError' in repr(e):
                    cfg = load_config()
                    cfg['openai_api_key_valid'] = False
                    cfg['auto_learn'] = False
                    save_config(cfg)
                    logging.warning('Invalid OpenAI API key detected; auto_learn disabled in config')
            except Exception:
                logging.exception('Failed to disable auto_learn after auth error')
            raise


def get_response(prompt: str) -> str:
    """Central entrypoint: try OpenAI (if configured) else fallback.

    This function also appends to history and returns the assistant text.
    """
    # prefer runtime env variable presence OR saved key
    out = None
    try:
        # 1) Local knowledge base lookup
        k = find_knowledge(prompt)
        if k:
            out = k
            return out


        # (moved helper functions to top-level)

        # 2) Try OpenAI if configured
        if _OPENAI_AVAILABLE and (os.getenv('OPENAI_API_KEY') or load_config().get('openai_api_key')):
            try:
                out = call_openai(prompt)
            except Exception as e:
                out = fallback_response(prompt)
        else:
            out = fallback_response(prompt)
        return out
    finally:
        # always append history even if something raised earlier
        try:
            append_history('You', prompt)
            # ensure out is a string
            append_history(ASSISTANT_NAME, out if isinstance(out, str) else str(out))
        except Exception:


def check_openai_key() -> tuple[bool, str]:
    """Check for an OpenAI API key in environment or config. Returns (present, source)."""
    key = os.getenv('OPENAI_API_KEY')
    if key:
        return True, 'env'
    cfg = load_config()
    if cfg.get('openai_api_key'):
        return True, 'config'
    if cfg.get('openai_api_key_encrypted'):
        return True, 'config_encrypted'
    # attempt .env if available
    if _DOTENV_AVAILABLE:
        try:
            load_dotenv()
            if os.getenv('OPENAI_API_KEY'):
                return True, '.env'
        except Exception:
            pass
    return False, ''


def learn_from_url(url: str, max_pairs: int = 5) -> int:
    """Fetch URL, extract main text, ask OpenAI to generate Q/A pairs, store them via teach_pair.

    Returns the number of Q/A pairs saved.
    Requires requests and BeautifulSoup installed and OpenAI configured.
    """
    if not _WEBREQ_AVAILABLE:
    ok, src = check_openai_key()
    if not ok or not _OPENAI_AVAILABLE:

    # fetch page
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:

    # extract text
    try:
        doc = BeautifulSoup(resp.text, 'html.parser')
        # remove scripts/styles
        for s in doc(['script', 'style', 'noscript']):
            s.decompose()
        text = ' '.join(p.get_text(separator=' ', strip=True) for p in doc.find_all(['p', 'li', 'h1', 'h2', 'h3']))
        if not text or len(text) < 100:
            # fallback to body text
            body = doc.body
            text = body.get_text(separator=' ', strip=True) if body else doc.get_text(separator=' ', strip=True)
    except Exception as e:

    if not text:

    # prepare a prompt for generating Q/A pairs
    prompt = (
        + text[:20000]
    )

    try:
        out = call_openai(prompt)
    except Exception as e:

    # attempt to parse JSON from response
    items = []
    try:
        # try to find first JSON array in the response
        start = out.find('[')
        end = out.rfind(']')
        if start != -1 and end != -1 and end > start:
            jsonstr = out[start:end+1]
            items = json.loads(jsonstr)
    except Exception:
        items = []

    # fallback: try line-parsing q: a:
    if not isinstance(items, list) or not items:
        items = []
        for line in out.splitlines():
            if ':' in line:
                q,a = line.split(':',1)
                items.append({'q': q.strip(), 'a': a.strip()})
            if len(items) >= max_pairs:
                break

    saved = 0
    for it in items[:max_pairs]:
        q = it.get('q') if isinstance(it, dict) else None
        a = it.get('a') if isinstance(it, dict) else None
        if q and a:
            teach_pair(q, a)
            saved += 1

    return saved


def safe_eval_math(expr):
    allowed_nodes = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
                     ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
                     ast.USub, ast.UAdd, ast.Load, ast.FloorDiv)

    node = ast.parse(expr, mode='eval')

    for n in ast.walk(node):
        if not isinstance(n, allowed_nodes):
    return eval(compile(node, '<string>', mode='eval'))


def fallback_response(prompt):
    cfg = load_config()
    user_name = cfg.get('user_name') or ''
    p = prompt.strip().lower()
        if user_name:
        if user_name:

        expr = re.sub(r"[쎈쨬쎈읈뜝-s:]*", "", prompt)
        expr = expr.replace('^', '**')
        try:
            val = safe_eval_math(expr)
        except Exception:

    # queue for potential autonomous learning
    try:
        cfg = load_config()
        if cfg.get('auto_learn', False):
            # when auto_learn_confirm is True, we queue but require manual processing
            queued = queue_for_learning(prompt)
            if cfg.get('auto_learn_confirm', True):
            # if no confirm, we still inform user that learning is scheduled
    except Exception:


def repl():
    cfg = load_config()
    user_name = cfg.get('user_name') or ''
    while True:
        try:
            prompt = input('You: ').strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not prompt:
            continue
        if prompt.startswith('/'):
            parts = prompt.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ''
            if cmd == '/setname' and arg:
                cfg['user_name'] = arg
                save_config(cfg)
                continue
            if cmd == '/name':
                if cfg.get('user_name'):
                else:
                continue
            if cmd == '/history':
                if os.path.exists(HISTORY_PATH):
                    with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                        print(f.read())
                else:
                continue
            if cmd == '/teach':
                # format: /teach 슣돳쎌맄쎈즵 => 뜝럥
                if arg and '=>' in arg:
                    q,a = arg.split('=>',1)
                    teach_pair(q.strip(), a.strip())
                else:
                    # interactive teach
                    q = input('슣돳쎌맄쎈즵뜝럡꼤뜝럩뜝럡꽠쎈빝뜝 ').strip()
                    if not q:
                        continue
                    a = input('뜝럥뜝럡꼤뜝럩뜝럡꽠쎈빝뜝 ').strip()
                    if not a:
                        continue
                    teach_pair(q, a)
                continue
            if cmd == '/autolearn':
                # usage: /autolearn on|off|status|process|clear
                sub = (arg or '').lower()
                cfg = load_config()
                if sub == 'on':
                    cfg['auto_learn'] = True
                    save_config(cfg)
                elif sub == 'off':
                    cfg['auto_learn'] = False
                    save_config(cfg)
                elif sub == 'status':
                    print(f"auto_learn={cfg.get('auto_learn', False)}, auto_learn_confirm={cfg.get('auto_learn_confirm', True)}")
                elif sub == 'process':
                    n = process_learning_queue()
                elif sub == 'clear':
                    _save_learning_queue([])
                else:
                continue
            if cmd == '/learn-url' and arg:
                try:
                    n = learn_from_url(arg)
                except Exception as e:
                continue
            if cmd == '/check-key':
                ok, src = check_openai_key()
                if ok:
                else:
                continue
            if cmd == '/clear':
                try:
                    open(HISTORY_PATH, 'w', encoding='utf-8').close()
                except Exception:
                continue
            if cmd == '/help':
                continue
            if cmd == '/teach':
                # format: /teach 슣돳쎌맄쎈즵 => 뜝럥
                if arg and '=>' in arg:
                    q,a = arg.split('=>',1)
                    teach_pair(q.strip(), a.strip())
                else:
                    # interactive teach
                    q = input('슣돳쎌맄쎈즵뜝럡꼤뜝럩뜝럡꽠쎈빝뜝 ').strip()
                    if not q:
                        continue
                    a = input('뜝럥뜝럡꼤뜝럩뜝럡꽠쎈빝뜝 ').strip()
                    if not a:
                        continue
                    teach_pair(q, a)
                continue
            break

        # Get response (will consult knowledge base first, then OpenAI/fallback)
        out = get_response(prompt)
        print(f'\n{ASSISTANT_NAME}:', out, '\n')


def run_test():
    samples = [
    ]
    for s in samples:
        print('\nYou:', s)
        if _OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            try:
                out = call_openai(s)
            except Exception as e:
                out = f"OpenAI 뜝럥욅춯옚삕: {e} fallback 뜝럥울옙\n" + fallback_response(s)
        else:
            out = fallback_response(s)
        print('Assistant:', out)
        time.sleep(0.2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--set-key', metavar='KEY', help='OPENAI API 뜝럥 뜝럥졾뜝럩젳뜝럡꽘뜝룞삕뜝 (쎈꽞뚯뼔) 뜝럥졾뜝럩젳 뜝럩뮝뜝럥럡뜝룞삕왿몾쑏뜝뜝럥맄뜝럥렡')
    parser.add_argument('--secure-set-key', metavar='KEY', help='API 뜝럥 쎈롥뜝룞삕먮뛼뒙뜝쎌녃뱄퐢깙뜝럡돭뜝럥깓쎈빝뜝 뜝럥졾뜝럩젳 뜝럩뮝뜝럥럡뜝룞삕왿몾쑏뜝뜝럥맄뜝럥렡 (쎈롥뜝룞삕먲옙 뜝럡꼤뜝럩쎄껀쎌뒜쎈쐮뜝럥녑뜝럥돲')
    parser.add_argument('--decrypt-config', action='store_true', help='쎈롥뜝룞삕먲옙쎄껀쎈폇쏉옙 뜝럥졾뜝럩젳 뜝럩뮝뜝럥럡API 뜝럥 쎌녃뱄퐢밧뜝럡돭쎈롥뜝띂눀뜝뜝럥돯뜝럥듿뜝럩뜝럥녑뜝럥돲)
    parser.add_argument('--test', action='store_true', help='뜝럡꽣쏙옙뼲삕 뜝룞삕뜝럥춯뺤삕 뜝럥욃뜝럡꼤뚯빢삕')
    args = parser.parse_args()
    if getattr(args, 'set_key', None):
        key = args.set_key
        cfg = load_config()
        cfg['openai_api_key'] = key
        save_config(cfg)
        # set for current session
        os.environ['OPENAI_API_KEY'] = key
        return

    if getattr(args, 'secure_set_key', None):
        key = args.secure_set_key
        if not _CRYPTO_AVAILABLE:
            return
        pwd = getpass.getpass('쎈롥뜝룞삕먮뜉삕륅옙뜝럡꼤뜝럩뜝럡꽠쎈빝뜝(쎌녃뱄퐢쏙옙뜝럥쐾: ')
        payload = encrypt_api_key(key, pwd)
        cfg = load_config()
        cfg['openai_api_key_encrypted'] = payload
        # remove plain key if present
        cfg.pop('openai_api_key', None)
        save_config(cfg)
        return

    if getattr(args, 'decrypt_config', False):
        cfg = load_config()
        payload = cfg.get('openai_api_key_encrypted')
        if not payload:
            return
        pwd = getpass.getpass('쎈롥뜝룞삕먮뜉삕륅옙뜝럡꼤뜝럩뜝럡꽠쎈빝뜝 ')
        try:
            key = decrypt_api_key(payload, pwd)
        except Exception:
        return

    if args.test:
        run_test()
        return
    # start autolearn service if enabled and auto processing allowed
    cfg = load_config()
    if cfg.get('auto_learn', False) and not cfg.get('auto_learn_confirm', True):
        # start a background thread to process the learning queue periodically
        def _autolearn_loop():
            import time as _t
            while True:
                try:
                    n = process_learning_queue()
                    if n:
                        logging.info('Autolearn processed %d items', n)
                except Exception:
                    logging.exception('Autolearn loop error')
                _t.sleep(int(cfg.get('auto_learn_interval', 60)))
        import threading as _thr
        t = _thr.Thread(target=_autolearn_loop, daemon=True)
        t.start()
    repl()


if __name__ == '__main__':
    main()

