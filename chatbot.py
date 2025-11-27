#!/usr/bin/env python3
"""
개인 비서 'NEURON' (Google Gemini 기반 챗봇)

기능 요약:
- 규칙 기반 응답 및 선택적 Google Gemini 통합
- 명령: `/setname 이름`, `/name`, `/history`, `/clear`, `/help`, `exit`
- 대화 히스토리 저장: `neuron_history.txt` (타임스탬프 포함)
- 설정 저장: `neuron_config.json`

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
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except Exception:
    genai = None
    _GEMINI_AVAILABLE = False

# 파일 경로 / 기본값
ASSISTANT_NAME = "NEURON"
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'neuron_config.json')
HISTORY_PATH = os.path.join(os.path.dirname(__file__), 'neuron_history.txt')
KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), 'neuron_knowledge.json')
QUEUE_PATH = os.path.join(os.path.dirname(__file__), 'neuron_learning_queue.jsonl')


def load_config():
    # Returns a dict with at least 'user_name'
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
    """Process queued prompts: generate answers via Gemini and save to knowledge.

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
            # ask Gemini for a concise answer
            answer_prompt = f"다음 질문에 대해 짧고 친절한 한국어 답변을 작성해줘:\n{prompt}\n답변:\n"
            ans = call_gemini(answer_prompt)
            if ans:
                if not dry_run:
                    teach_pair(prompt, ans)
                processed += 1
            else:
                remaining.append(it)
        except Exception:
            logging.exception('학습 처리 중 오류')
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
        raise RuntimeError('cryptography 패키지가 필요합니다.')
    salt = os.urandom(16)
    k = _derive_key(password, salt)
    f = Fernet(k)
    token = f.encrypt(key_str.encode())
    # store salt + token, both base64
    payload = base64.urlsafe_b64encode(salt).decode() + '::' + token.decode()
    return payload


def decrypt_api_key(payload: str, password: str) -> str:
    if not _CRYPTO_AVAILABLE:
        raise RuntimeError('cryptography 패키지가 필요합니다.')
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


def call_gemini(prompt):
    # priority: env var -> config file -> .env
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        cfg = load_config()
        key = cfg.get('gemini_api_key') or cfg.get('api_key')
    if not key and _DOTENV_AVAILABLE:
        # attempt to load .env and retry
        try:
            load_dotenv()
            key = os.getenv("GEMINI_API_KEY")
        except Exception:
            pass
    if not key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.")
    if not _GEMINI_AVAILABLE:
        raise RuntimeError("google-generativeai 패키지가 설치되어 있지 않습니다. `pip install google-generativeai`를 실행하세요.")
    
    start = time.time()
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        elapsed = time.time() - start
        logging.info('Gemini API call success (%.3fs)', elapsed)
        
        # Extract text from response
        if hasattr(response, 'text'):
            content = response.text
        elif hasattr(response, 'parts'):
            content = ''.join(part.text for part in response.parts)
        else:
            content = str(response)
            
        return content.strip() if isinstance(content, str) else str(content)
    except Exception as e:
        # if authentication error (invalid key), disable auto_learn to avoid repeated charges
        msg = str(e)
        logging.exception('Gemini API 호출 실패, 시도 중단')
        try:
            if 'invalid' in msg.lower() or 'api_key' in msg.lower() or 'authentication' in msg.lower():
                cfg = load_config()
                cfg['gemini_api_key_valid'] = False
                # disable autonomous processing to be safe
                cfg['auto_learn'] = False
                save_config(cfg)
                logging.warning('Invalid Gemini API key detected; auto_learn disabled in config')
        except Exception:
            logging.exception('Failed to disable auto_learn after auth error')
        raise


def get_response(prompt: str) -> str:
    """Central entrypoint: try Gemini (if configured) else fallback.

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

        # 2) Try Gemini if configured
        if _GEMINI_AVAILABLE and (os.getenv('GEMINI_API_KEY') or load_config().get('gemini_api_key')):
            try:
                out = call_gemini(prompt)
            except Exception as e:
                logging.warning('Gemini 호출 실패, fallback 사용: %s', e)
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
            logging.exception('히스토리 쓰기 실패')


def check_gemini_key() -> tuple[bool, str]:
    """Check for a Gemini API key in environment or config. Returns (present, source)."""
    key = os.getenv('GEMINI_API_KEY')
    if key:
        return True, 'env'
    cfg = load_config()
    if cfg.get('gemini_api_key'):
        return True, 'config'
    if cfg.get('gemini_api_key_encrypted'):
        return True, 'config_encrypted'
    # attempt .env if available
    if _DOTENV_AVAILABLE:
        try:
            load_dotenv()
            if os.getenv('GEMINI_API_KEY'):
                return True, '.env'
        except Exception:
            pass
    return False, ''


def learn_from_url(url: str, max_pairs: int = 5) -> int:
    """Fetch URL, extract main text, ask Gemini to generate Q/A pairs, store them via teach_pair.

    Returns the number of Q/A pairs saved.
    Requires requests and BeautifulSoup installed and Gemini configured.
    """
    if not _WEBREQ_AVAILABLE:
        raise RuntimeError('웹 요청 기능을 사용하려면 requests 및 beautifulsoup4 패키지가 필요합니다.')
    ok, src = check_gemini_key()
    if not ok or not _GEMINI_AVAILABLE:
        raise RuntimeError('온라인 학습에는 Gemini API 키와 google-generativeai 패키지가 필요합니다.')

    # fetch page
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f'URL을 가져오는 중 오류: {e}')

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
        raise RuntimeError(f'HTML 파싱 중 오류: {e}')

    if not text:
        raise RuntimeError('추출된 텍스트가 없습니다.')

    # prepare a prompt for generating Q/A pairs
    prompt = (
        f"다음 텍스트를 읽고 최대 {max_pairs}개의 간단한 질문-답변(Q/A) 쌍을 만들어줘."
        " 각 질문은 사용자 질문 형태로, 각 답변은 짧고 명확하게 작성해줘."
        " 출력은 JSON 배열 형식으로 [{\"q\":...,\"a\":...}, ...] 만 출력해줘.\n\n"
        + text[:20000]
    )

    try:
        out = call_gemini(prompt)
    except Exception as e:
        raise RuntimeError(f'Gemini 호출 실패: {e}')

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
    # 간단하고 안전한 수식 평가: AST로 허용된 노드만 허용
    allowed_nodes = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
                     ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
                     ast.USub, ast.UAdd, ast.Load, ast.FloorDiv)

    node = ast.parse(expr, mode='eval')

    for n in ast.walk(node):
        if not isinstance(n, allowed_nodes):
            raise ValueError("허용되지 않는 연산입니다.")
    return eval(compile(node, '<string>', mode='eval'))


def fallback_response(prompt):
    cfg = load_config()
    user_name = cfg.get('user_name') or ''
    p = prompt.strip().lower()
    if any(g in p for g in ["안녕", "안녕하세요", "ㅎㅇ"]):
        if user_name:
            return f"안녕하세요, {user_name}님! 무엇을 도와드릴까요?"
        return f"안녕하세요! 저는 {ASSISTANT_NAME}입니다. 무엇을 도와드릴까요?"
    if "이름" in p:
        if user_name:
            return f"{user_name}님, 저는 개인 비서 {ASSISTANT_NAME}입니다. 필요하신 작업을 알려주세요."
        return f"저는 개인 비서 {ASSISTANT_NAME}입니다. 먼저 이름을 알려주시면 더 친근하게 부를게요. (/setname 이름)"
    if "시간" in p or "몇 시" in p:
        return f"지금 시간은 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 입니다."

    # 수학 계산 요청 감지: 숫자와 연산기호 포함
    if re.search(r"[0-9]+\s*[-+*/%^]", p) or p.startswith("계산"):
        # 수식만 추출해보기
        expr = re.sub(r"[가-힣\s:]*", "", prompt)
        expr = expr.replace('^', '**')
        try:
            val = safe_eval_math(expr)
            return f"계산 결과: {val}"
        except Exception:
            return "죄송합니다. 계산을 해석하지 못했습니다. 예: 2+3*4"

    # 기본 에코 / 안내
    # queue for potential autonomous learning
    try:
        cfg = load_config()
        if cfg.get('auto_learn', False):
            # when auto_learn_confirm is True, we queue but require manual processing
            queued = queue_for_learning(prompt)
            if cfg.get('auto_learn_confirm', True):
                return f"아직 학습이 제한적입니다. 입력하신 내용: {prompt}\n(학습 후보로 큐에 추가되었습니다)"
            # if no confirm, we still inform user that learning is scheduled
            return f"아직 학습이 제한적입니다. 입력하신 내용: {prompt}\n(자동 학습이 활성화되어 있습니다 — 곧 학습됩니다)"
    except Exception:
        logging.exception('queue_for_learning 실패')
    return f"아직 학습이 제한적입니다. 입력하신 내용: {prompt}"


def repl():
    cfg = load_config()
    user_name = cfg.get('user_name') or ''
    print(f"{ASSISTANT_NAME}에 오신 것을 환영합니다. 종료하려면 'exit' 또는 '종료'를 입력하세요.")
    print("도움말: /help 를 입력하세요.")
    while True:
        try:
            prompt = input('You: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n종료합니다.')
            break
        if not prompt:
            continue
        # 명령어 처리
        if prompt.startswith('/'):
            parts = prompt.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ''
            if cmd == '/setname' and arg:
                cfg['user_name'] = arg
                save_config(cfg)
                print(f"{ASSISTANT_NAME}: 알겠습니다. 이제 {arg}님이라고 부를게요.")
                continue
            if cmd == '/name':
                if cfg.get('user_name'):
                    print(f"{ASSISTANT_NAME}: 사용자 이름은 {cfg['user_name']} 입니다.")
                else:
                    print(f"{ASSISTANT_NAME}: 사용자의 이름이 설정되어 있지 않습니다. '/setname 이름' 으로 설정하세요.")
                continue
            if cmd == '/history':
                if os.path.exists(HISTORY_PATH):
                    with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                        print(f.read())
                else:
                    print(f"{ASSISTANT_NAME}: 대화 기록이 없습니다.")
                continue
            if cmd == '/teach':
                # format: /teach 질문 => 답변
                if arg and '=>' in arg:
                    q,a = arg.split('=>',1)
                    teach_pair(q.strip(), a.strip())
                    print(f"{ASSISTANT_NAME}: 학습 완료했습니다. 질문: '{q.strip()}' -> 답변 저장됨")
                else:
                    # interactive teach
                    q = input('질문을 입력하세요: ').strip()
                    if not q:
                        print('취소됨.')
                        continue
                    a = input('답변을 입력하세요: ').strip()
                    if not a:
                        print('취소됨.')
                        continue
                    teach_pair(q, a)
                    print(f"{ASSISTANT_NAME}: 학습 완료했습니다. 질문: '{q}' -> 답변 저장됨")
                continue
            if cmd == '/autolearn':
                # usage: /autolearn on|off|status|process|clear
                sub = (arg or '').lower()
                cfg = load_config()
                if sub == 'on':
                    cfg['auto_learn'] = True
                    save_config(cfg)
                    print('자동 학습이 활성화되었습니다.')
                elif sub == 'off':
                    cfg['auto_learn'] = False
                    save_config(cfg)
                    print('자동 학습이 비활성화되었습니다.')
                elif sub == 'status':
                    print(f"auto_learn={cfg.get('auto_learn', False)}, auto_learn_confirm={cfg.get('auto_learn_confirm', True)}")
                elif sub == 'process':
                    n = process_learning_queue()
                    print(f"처리된 학습 항목 수: {n}")
                elif sub == 'clear':
                    _save_learning_queue([])
                    print('학습 큐를 비웠습니다.')
                else:
                    print("사용법: /autolearn on|off|status|process|clear")
                continue
            if cmd == '/learn-url' and arg:
                try:
                    n = learn_from_url(arg)
                    print(f"{ASSISTANT_NAME}: 온라인 학습 완료, 저장된 Q/A 쌍 수: {n}")
                except Exception as e:
                    print(f"학습 실패: {e}")
                continue
            if cmd == '/check-key':
                ok, src = check_gemini_key()
                if ok:
                    print(f"GEMINI_API_KEY가 설정되어 있습니다. 출처: {src}")
                else:
                    print('GEMINI_API_KEY가 설정되어 있지 않습니다.')
                continue
            if cmd == '/clear':
                try:
                    open(HISTORY_PATH, 'w', encoding='utf-8').close()
                    print(f"{ASSISTANT_NAME}: 기록을 삭제했습니다.")
                except Exception:
                    print(f"{ASSISTANT_NAME}: 기록 삭제에 실패했습니다.")
                continue
            if cmd == '/help':
                print('''사용 가능한 명령:
/setname 이름  - 당신의 이름을 저장합니다.
/name         - 저장된 이름 확인
/history      - 대화 기록 보기
/clear        - 대화 기록 삭제
/help         - 도움말
exit 또는 종료 - 종료''')
                continue
            if cmd == '/teach':
                # format: /teach 질문 => 답변
                if arg and '=>' in arg:
                    q,a = arg.split('=>',1)
                    teach_pair(q.strip(), a.strip())
                    print(f"{ASSISTANT_NAME}: 학습 완료했습니다. 질문: '{q.strip()}' -> 답변 저장됨")
                else:
                    # interactive teach
                    q = input('질문을 입력하세요: ').strip()
                    if not q:
                        print('취소됨.')
                        continue
                    a = input('답변을 입력하세요: ').strip()
                    if not a:
                        print('취소됨.')
                        continue
                    teach_pair(q, a)
                    print(f"{ASSISTANT_NAME}: 학습 완료했습니다. 질문: '{q}' -> 답변 저장됨")
                continue
        if prompt.lower() in ('exit', '종료'):
            print('종료합니다.')
            break

        # Get response (will consult knowledge base first, then Gemini/fallback)
        out = get_response(prompt)
        print(f'\n{ASSISTANT_NAME}:', out, '\n')


def run_test():
    print('테스트 모드: 샘플 입력들로 동작을 확인합니다.')
    samples = [
        '안녕',
        '지금 몇 시야?',
        '2+3*4 계산해줘',
        '너의 이름은 뭐야?'
    ]
    for s in samples:
        print('\nYou:', s)
        if _GEMINI_AVAILABLE and os.getenv('GEMINI_API_KEY'):
            try:
                out = call_gemini(s)
            except Exception as e:
                out = f"Gemini 오류: {e} — fallback 사용\n" + fallback_response(s)
        else:
            out = fallback_response(s)
        print('Assistant:', out)
        time.sleep(0.2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--set-key', metavar='KEY', help='GEMINI API 키를 설정하고 (선택) 설정 파일에 저장합니다')
    parser.add_argument('--secure-set-key', metavar='KEY', help='API 키를 암호로 보호해서 설정 파일에 저장합니다 (암호 입력을 요청합니다)')
    parser.add_argument('--decrypt-config', action='store_true', help='암호화된 설정 파일의 API 키를 복호화하여 출력합니다')
    parser.add_argument('--test', action='store_true', help='샘플 대화 실행 후 종료')
    args = parser.parse_args()
    # --set-key를 사용하면 설정 파일에 키를 저장하고 현재 세션 ENV에도 적용
    if getattr(args, 'set_key', None):
        key = args.set_key
        cfg = load_config()
        cfg['gemini_api_key'] = key
        save_config(cfg)
        # set for current session
        os.environ['GEMINI_API_KEY'] = key
        print('GEMINI_API_KEY가 설정 파일에 저장되고 현재 세션에 적용되었습니다.')
        return

    if getattr(args, 'secure_set_key', None):
        key = args.secure_set_key
        if not _CRYPTO_AVAILABLE:
            print('cryptography 패키지가 필요합니다. requirements.txt를 업데이트하고 설치하세요.')
            return
        pwd = getpass.getpass('암호를 입력하세요 (복구용): ')
        payload = encrypt_api_key(key, pwd)
        cfg = load_config()
        cfg['gemini_api_key_encrypted'] = payload
        # remove plain key if present
        cfg.pop('gemini_api_key', None)
        save_config(cfg)
        print('암호화된 API 키가 설정 파일에 저장되었습니다.')
        return

    if getattr(args, 'decrypt_config', False):
        cfg = load_config()
        payload = cfg.get('gemini_api_key_encrypted')
        if not payload:
            print('암호화된 API 키가 설정 파일에 없습니다.')
            return
        pwd = getpass.getpass('암호를 입력하세요: ')
        try:
            key = decrypt_api_key(payload, pwd)
            print('복호화된 키:', key)
        except Exception:
            print('복호화 실패: 암호가 틀리거나 데이터가 손상되었습니다.')
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
