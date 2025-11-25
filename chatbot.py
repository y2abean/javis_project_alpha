#!/usr/bin/env python3
"""
ê°œì¸ ë¹„ì„œ '?ë¹„?? (ê°„ë‹¨??ChatGPT ?¤í???ì±—ë´‡)

ê¸°ëŠ¥ ?”ì•½:
- ê·œì¹™ ê¸°ë°˜ ?‘ë‹µ ë°?? íƒ??OpenAI ?µí•©
- ëª…ë ¹: `/setname ?´ë¦„`, `/name`, `/history`, `/clear`, `/help`, `exit`
- ?€???ˆìŠ¤? ë¦¬ ?€?? `NEURON_history.txt` (?€?„ìŠ¤?¬í”„ ?¬í•¨)
- ?¤ì • ?€?? `NEURON_config.json`

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

# ?Œì¼ ê²½ë¡œ / ê¸°ë³¸ê°?
ASSISTANT_NAME = "?ë¹„??
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
            answer_prompt = f"?¤ìŒ ì§ˆë¬¸???€??ì§§ê³  ì¹œì ˆ???œêµ­???µë????‘ì„±?´ì¤˜:\n{prompt}\n?µë?:\n"
            ans = call_openai(answer_prompt)
            if ans:
                if not dry_run:
                    teach_pair(prompt, ans)
                processed += 1
            else:
                remaining.append(it)
        except Exception:
            logging.exception('?™ìŠµ ì²˜ë¦¬ ì¤??¤ë¥˜')
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
        raise RuntimeError('cryptography ?¨í‚¤ì§€ê°€ ?„ìš”?©ë‹ˆ??')
    salt = os.urandom(16)
    k = _derive_key(password, salt)
    f = Fernet(k)
    token = f.encrypt(key_str.encode())
    # store salt + token, both base64
    payload = base64.urlsafe_b64encode(salt).decode() + '::' + token.decode()
    return payload


def decrypt_api_key(payload: str, password: str) -> str:
    if not _CRYPTO_AVAILABLE:
        raise RuntimeError('cryptography ?¨í‚¤ì§€ê°€ ?„ìš”?©ë‹ˆ??')
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
        raise RuntimeError("OPENAI_API_KEY ?˜ê²½ë³€?˜ê? ?¤ì •?˜ì–´ ?ˆì? ?ŠìŠµ?ˆë‹¤.")
    if not _OPENAI_AVAILABLE:
        raise RuntimeError("openai ?¨í‚¤ì§€ê°€ ?¤ì¹˜?˜ì–´ ?ˆì? ?ŠìŠµ?ˆë‹¤. `pip install openai`ë¥??¤í–‰?˜ì„¸??")
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
            logging.exception('OpenAI (v1+) API ?¸ì¶œ ?¤íŒ¨, ?œë„ ì¤‘ë‹¨')
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
            logging.exception('OpenAI API ?¸ì¶œ ?¤íŒ¨')
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
                logging.warning('OpenAI ?¸ì¶œ ?¤íŒ¨, fallback ?¬ìš©: %s', e)
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
            logging.exception('?ˆìŠ¤? ë¦¬ ?°ê¸° ?¤íŒ¨')


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
        raise RuntimeError('???”ì²­ ê¸°ëŠ¥???¬ìš©?˜ë ¤ë©?requests ë°?beautifulsoup4 ?¨í‚¤ì§€ê°€ ?„ìš”?©ë‹ˆ??')
    ok, src = check_openai_key()
    if not ok or not _OPENAI_AVAILABLE:
        raise RuntimeError('?¨ë¼???™ìŠµ?ëŠ” OpenAI API ?¤ì? openai ?¨í‚¤ì§€ê°€ ?„ìš”?©ë‹ˆ??')

    # fetch page
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f'URL??ê°€?¸ì˜¤??ì¤??¤ë¥˜: {e}')

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
        raise RuntimeError(f'HTML ?Œì‹± ì¤??¤ë¥˜: {e}')

    if not text:
        raise RuntimeError('ì¶”ì¶œ???ìŠ¤?¸ê? ?†ìŠµ?ˆë‹¤.')

    # prepare a prompt for generating Q/A pairs
    prompt = (
        f"?¤ìŒ ?ìŠ¤?¸ë? ?½ê³  ìµœë? {max_pairs}ê°œì˜ ê°„ë‹¨??ì§ˆë¬¸-?µë?(Q/A) ?ì„ ë§Œë“¤?´ì¤˜."
        " ê°?ì§ˆë¬¸?€ ?¬ìš©??ì§ˆë¬¸ ?•íƒœë¡? ê°??µë??€ ì§§ê³  ëª…í™•?˜ê²Œ ?‘ì„±?´ì¤˜."
        " ì¶œë ¥?€ JSON ë°°ì—´ ?•ì‹?¼ë¡œ [{\"q\":...,\"a\":...}, ...] ë§?ì¶œë ¥?´ì¤˜.\n\n"
        + text[:20000]
    )

    try:
        out = call_openai(prompt)
    except Exception as e:
        raise RuntimeError(f'OpenAI ?¸ì¶œ ?¤íŒ¨: {e}')

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
    # ê°„ë‹¨?˜ê³  ?ˆì „???˜ì‹ ?‰ê?: ASTë¡??ˆìš©???¸ë“œë§??ˆìš©
    allowed_nodes = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
                     ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
                     ast.USub, ast.UAdd, ast.Load, ast.FloorDiv)

    node = ast.parse(expr, mode='eval')

    for n in ast.walk(node):
        if not isinstance(n, allowed_nodes):
            raise ValueError("?ˆìš©?˜ì? ?ŠëŠ” ?°ì‚°?…ë‹ˆ??")
    return eval(compile(node, '<string>', mode='eval'))


def fallback_response(prompt):
    cfg = load_config()
    user_name = cfg.get('user_name') or ''
    p = prompt.strip().lower()
    if any(g in p for g in ["?ˆë…•", "?ˆë…•?˜ì„¸??, "?ã…‡"]):
        if user_name:
            return f"?ˆë…•?˜ì„¸?? {user_name}?? ë¬´ì—‡???„ì??œë¦´ê¹Œìš”?"
        return f"?ˆë…•?˜ì„¸?? ?€??{ASSISTANT_NAME}?…ë‹ˆ?? ë¬´ì—‡???„ì??œë¦´ê¹Œìš”?"
    if "?´ë¦„" in p:
        if user_name:
            return f"{user_name}?? ?€??ê°œì¸ ë¹„ì„œ {ASSISTANT_NAME}?…ë‹ˆ?? ?„ìš”?˜ì‹  ?‘ì—…???Œë ¤ì£¼ì„¸??"
        return f"?€??ê°œì¸ ë¹„ì„œ {ASSISTANT_NAME}?…ë‹ˆ?? ë¨¼ì? ?´ë¦„???Œë ¤ì£¼ì‹œë©???ì¹œê·¼?˜ê²Œ ë¶€ë¥¼ê²Œ?? (/setname ?´ë¦„)"
    if "?œê°„" in p or "ëª??? in p:
        return f"ì§€ê¸??œê°„?€ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ?…ë‹ˆ??"

    # ?˜í•™ ê³„ì‚° ?”ì²­ ê°ì?: ?«ì?€ ?°ì‚°ê¸°í˜¸ ?¬í•¨
    if re.search(r"[0-9]+\s*[-+*/%^]", p) or p.startswith("ê³„ì‚°"):
        # ?˜ì‹ë§?ì¶”ì¶œ?´ë³´ê¸?
        expr = re.sub(r"[ê°€-??s:]*", "", prompt)
        expr = expr.replace('^', '**')
        try:
            val = safe_eval_math(expr)
            return f"ê³„ì‚° ê²°ê³¼: {val}"
        except Exception:
            return "ì£„ì†¡?©ë‹ˆ?? ê³„ì‚°???´ì„?˜ì? ëª»í–ˆ?µë‹ˆ?? ?? 2+3*4"

    # ê¸°ë³¸ ?ì½” / ?ˆë‚´
    # queue for potential autonomous learning
    try:
        cfg = load_config()
        if cfg.get('auto_learn', False):
            # when auto_learn_confirm is True, we queue but require manual processing
            queued = queue_for_learning(prompt)
            if cfg.get('auto_learn_confirm', True):
                return f"?„ì§ ?™ìŠµ???œí•œ?ì…?ˆë‹¤. ?…ë ¥?˜ì‹  ?´ìš©: {prompt}\n(?™ìŠµ ?„ë³´ë¡??ì— ì¶”ê??˜ì—ˆ?µë‹ˆ??"
            # if no confirm, we still inform user that learning is scheduled
            return f"?„ì§ ?™ìŠµ???œí•œ?ì…?ˆë‹¤. ?…ë ¥?˜ì‹  ?´ìš©: {prompt}\n(?ë™ ?™ìŠµ???œì„±?”ë˜???ˆìŠµ?ˆë‹¤ ??ê³??™ìŠµ?©ë‹ˆ??"
    except Exception:
        logging.exception('queue_for_learning ?¤íŒ¨')
    return f"?„ì§ ?™ìŠµ???œí•œ?ì…?ˆë‹¤. ?…ë ¥?˜ì‹  ?´ìš©: {prompt}"


def repl():
    cfg = load_config()
    user_name = cfg.get('user_name') or ''
    print(f"{ASSISTANT_NAME}???¤ì‹  ê²ƒì„ ?˜ì˜?©ë‹ˆ?? ì¢…ë£Œ?˜ë ¤ë©?'exit' ?ëŠ” 'ì¢…ë£Œ'ë¥??…ë ¥?˜ì„¸??")
    print("?„ì?ë§? /help ë¥??…ë ¥?˜ì„¸??")
    while True:
        try:
            prompt = input('You: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nì¢…ë£Œ?©ë‹ˆ??')
            break
        if not prompt:
            continue
        # ëª…ë ¹??ì²˜ë¦¬
        if prompt.startswith('/'):
            parts = prompt.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ''
            if cmd == '/setname' and arg:
                cfg['user_name'] = arg
                save_config(cfg)
                print(f"{ASSISTANT_NAME}: ?Œê² ?µë‹ˆ?? ?´ì œ {arg}?˜ì´?¼ê³  ë¶€ë¥¼ê²Œ??")
                continue
            if cmd == '/name':
                if cfg.get('user_name'):
                    print(f"{ASSISTANT_NAME}: ?¬ìš©???´ë¦„?€ {cfg['user_name']} ?…ë‹ˆ??")
                else:
                    print(f"{ASSISTANT_NAME}: ?¬ìš©?ì˜ ?´ë¦„???¤ì •?˜ì–´ ?ˆì? ?ŠìŠµ?ˆë‹¤. '/setname ?´ë¦„' ?¼ë¡œ ?¤ì •?˜ì„¸??")
                continue
            if cmd == '/history':
                if os.path.exists(HISTORY_PATH):
                    with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                        print(f.read())
                else:
                    print(f"{ASSISTANT_NAME}: ?€??ê¸°ë¡???†ìŠµ?ˆë‹¤.")
                continue
            if cmd == '/teach':
                # format: /teach ì§ˆë¬¸ => ?µë?
                if arg and '=>' in arg:
                    q,a = arg.split('=>',1)
                    teach_pair(q.strip(), a.strip())
                    print(f"{ASSISTANT_NAME}: ?™ìŠµ ?„ë£Œ?ˆìŠµ?ˆë‹¤. ì§ˆë¬¸: '{q.strip()}' -> ?µë? ?€?¥ë¨")
                else:
                    # interactive teach
                    q = input('ì§ˆë¬¸???…ë ¥?˜ì„¸?? ').strip()
                    if not q:
                        print('ì·¨ì†Œ??')
                        continue
                    a = input('?µë????…ë ¥?˜ì„¸?? ').strip()
                    if not a:
                        print('ì·¨ì†Œ??')
                        continue
                    teach_pair(q, a)
                    print(f"{ASSISTANT_NAME}: ?™ìŠµ ?„ë£Œ?ˆìŠµ?ˆë‹¤. ì§ˆë¬¸: '{q}' -> ?µë? ?€?¥ë¨")
                continue
            if cmd == '/autolearn':
                # usage: /autolearn on|off|status|process|clear
                sub = (arg or '').lower()
                cfg = load_config()
                if sub == 'on':
                    cfg['auto_learn'] = True
                    save_config(cfg)
                    print('?ë™ ?™ìŠµ???œì„±?”ë˜?ˆìŠµ?ˆë‹¤.')
                elif sub == 'off':
                    cfg['auto_learn'] = False
                    save_config(cfg)
                    print('?ë™ ?™ìŠµ??ë¹„í™œ?±í™”?˜ì—ˆ?µë‹ˆ??')
                elif sub == 'status':
                    print(f"auto_learn={cfg.get('auto_learn', False)}, auto_learn_confirm={cfg.get('auto_learn_confirm', True)}")
                elif sub == 'process':
                    n = process_learning_queue()
                    print(f"ì²˜ë¦¬???™ìŠµ ??ª© ?? {n}")
                elif sub == 'clear':
                    _save_learning_queue([])
                    print('?™ìŠµ ?ë? ë¹„ì› ?µë‹ˆ??')
                else:
                    print("?¬ìš©ë²? /autolearn on|off|status|process|clear")
                continue
            if cmd == '/learn-url' and arg:
                try:
                    n = learn_from_url(arg)
                    print(f"{ASSISTANT_NAME}: ?¨ë¼???™ìŠµ ?„ë£Œ, ?€?¥ëœ Q/A ???? {n}")
                except Exception as e:
                    print(f"?™ìŠµ ?¤íŒ¨: {e}")
                continue
            if cmd == '/check-key':
                ok, src = check_openai_key()
                if ok:
                    print(f"OPENAI_API_KEYê°€ ?¤ì •?˜ì–´ ?ˆìŠµ?ˆë‹¤. ì¶œì²˜: {src}")
                else:
                    print('OPENAI_API_KEYê°€ ?¤ì •?˜ì–´ ?ˆì? ?ŠìŠµ?ˆë‹¤.')
                continue
            if cmd == '/clear':
                try:
                    open(HISTORY_PATH, 'w', encoding='utf-8').close()
                    print(f"{ASSISTANT_NAME}: ê¸°ë¡???? œ?ˆìŠµ?ˆë‹¤.")
                except Exception:
                    print(f"{ASSISTANT_NAME}: ê¸°ë¡ ?? œ???¤íŒ¨?ˆìŠµ?ˆë‹¤.")
                continue
            if cmd == '/help':
                print('''?¬ìš© ê°€?¥í•œ ëª…ë ¹:
/setname ?´ë¦„  - ?¹ì‹ ???´ë¦„???€?¥í•©?ˆë‹¤.
/name         - ?€?¥ëœ ?´ë¦„ ?•ì¸
/history      - ?€??ê¸°ë¡ ë³´ê¸°
/clear        - ?€??ê¸°ë¡ ?? œ
/help         - ?„ì?ë§?
exit ?ëŠ” ì¢…ë£Œ - ì¢…ë£Œ''')
                continue
            if cmd == '/teach':
                # format: /teach ì§ˆë¬¸ => ?µë?
                if arg and '=>' in arg:
                    q,a = arg.split('=>',1)
                    teach_pair(q.strip(), a.strip())
                    print(f"{ASSISTANT_NAME}: ?™ìŠµ ?„ë£Œ?ˆìŠµ?ˆë‹¤. ì§ˆë¬¸: '{q.strip()}' -> ?µë? ?€?¥ë¨")
                else:
                    # interactive teach
                    q = input('ì§ˆë¬¸???…ë ¥?˜ì„¸?? ').strip()
                    if not q:
                        print('ì·¨ì†Œ??')
                        continue
                    a = input('?µë????…ë ¥?˜ì„¸?? ').strip()
                    if not a:
                        print('ì·¨ì†Œ??')
                        continue
                    teach_pair(q, a)
                    print(f"{ASSISTANT_NAME}: ?™ìŠµ ?„ë£Œ?ˆìŠµ?ˆë‹¤. ì§ˆë¬¸: '{q}' -> ?µë? ?€?¥ë¨")
                continue
        if prompt.lower() in ('exit', 'ì¢…ë£Œ'):
            print('ì¢…ë£Œ?©ë‹ˆ??')
            break

        # Get response (will consult knowledge base first, then OpenAI/fallback)
        out = get_response(prompt)
        print(f'\n{ASSISTANT_NAME}:', out, '\n')


def run_test():
    print('?ŒìŠ¤??ëª¨ë“œ: ?˜í”Œ ?…ë ¥?¤ë¡œ ?™ì‘???•ì¸?©ë‹ˆ??')
    samples = [
        '?ˆë…•',
        'ì§€ê¸?ëª??œì•¼?',
        '2+3*4 ê³„ì‚°?´ì¤˜',
        '?ˆì˜ ?´ë¦„?€ ë­ì•¼?'
    ]
    for s in samples:
        print('\nYou:', s)
        if _OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            try:
                out = call_openai(s)
            except Exception as e:
                out = f"OpenAI ?¤ë¥˜: {e} ??fallback ?¬ìš©\n" + fallback_response(s)
        else:
            out = fallback_response(s)
        print('Assistant:', out)
        time.sleep(0.2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--set-key', metavar='KEY', help='OPENAI API ?¤ë? ?¤ì •?˜ê³  (? íƒ) ?¤ì • ?Œì¼???€?¥í•©?ˆë‹¤')
    parser.add_argument('--secure-set-key', metavar='KEY', help='API ?¤ë? ?”í˜¸ë¡?ë³´í˜¸?´ì„œ ?¤ì • ?Œì¼???€?¥í•©?ˆë‹¤ (?”í˜¸ ?…ë ¥???”ì²­?©ë‹ˆ??')
    parser.add_argument('--decrypt-config', action='store_true', help='?”í˜¸?”ëœ ?¤ì • ?Œì¼??API ?¤ë? ë³µí˜¸?”í•˜??ì¶œë ¥?©ë‹ˆ??)
    parser.add_argument('--test', action='store_true', help='?˜í”Œ ?€???¤í–‰ ??ì¢…ë£Œ')
    args = parser.parse_args()
    # --set-keyë¥??¬ìš©?˜ë©´ ?¤ì • ?Œì¼???¤ë? ?€?¥í•˜ê³??„ì¬ ?¸ì…˜ ENV?ë„ ?ìš©
    if getattr(args, 'set_key', None):
        key = args.set_key
        cfg = load_config()
        cfg['openai_api_key'] = key
        save_config(cfg)
        # set for current session
        os.environ['OPENAI_API_KEY'] = key
        print('OPENAI_API_KEYê°€ ?¤ì • ?Œì¼???€?¥ë˜ê³??„ì¬ ?¸ì…˜???ìš©?˜ì—ˆ?µë‹ˆ??')
        return

    if getattr(args, 'secure_set_key', None):
        key = args.secure_set_key
        if not _CRYPTO_AVAILABLE:
            print('cryptography ?¨í‚¤ì§€ê°€ ?„ìš”?©ë‹ˆ?? requirements.txtë¥??…ë°?´íŠ¸?˜ê³  ?¤ì¹˜?˜ì„¸??')
            return
        pwd = getpass.getpass('?”í˜¸ë¥??…ë ¥?˜ì„¸??(ë³µêµ¬??: ')
        payload = encrypt_api_key(key, pwd)
        cfg = load_config()
        cfg['openai_api_key_encrypted'] = payload
        # remove plain key if present
        cfg.pop('openai_api_key', None)
        save_config(cfg)
        print('?”í˜¸?”ëœ API ?¤ê? ?¤ì • ?Œì¼???€?¥ë˜?ˆìŠµ?ˆë‹¤.')
        return

    if getattr(args, 'decrypt_config', False):
        cfg = load_config()
        payload = cfg.get('openai_api_key_encrypted')
        if not payload:
            print('?”í˜¸?”ëœ API ?¤ê? ?¤ì • ?Œì¼???†ìŠµ?ˆë‹¤.')
            return
        pwd = getpass.getpass('?”í˜¸ë¥??…ë ¥?˜ì„¸?? ')
        try:
            key = decrypt_api_key(payload, pwd)
            print('ë³µí˜¸?”ëœ ??', key)
        except Exception:
            print('ë³µí˜¸???¤íŒ¨: ?”í˜¸ê°€ ?€ë¦¬ê±°???°ì´?°ê? ?ìƒ?˜ì—ˆ?µë‹ˆ??')
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
