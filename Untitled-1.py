#!/usr/bin/env python3
"""
ê°„ë‹¨??ChatGPT ?¤í???ì±—ë´‡ ?ˆì œ

- OpenAI API ?¤ê? `OPENAI_API_KEY` ?˜ê²½ë³€?˜ë¡œ ?¤ì •?˜ì–´ ?ˆê³ 
  `openai` ?¨í‚¤ì§€ê°€ ?¤ì¹˜?˜ì–´ ?ˆìœ¼ë©??¤ì œ OpenAI ChatCompletion???¸ì¶œ?©ë‹ˆ??
- ê·¸ë ‡ì§€ ?Šìœ¼ë©?ê°„ë‹¨??ê·œì¹™ ê¸°ë°˜(fallback) ?‘ë‹µ???œê³µ?©ë‹ˆ??

?¬ìš©ë²?
  python Untitled-1.py          # REPL ëª¨ë“œ
  python Untitled-1.py --test   # ?˜í”Œ ?€???¤í–‰ ??ì¢…ë£Œ
"""

import os
import sys
import argparse
import time
import re
from datetime import datetime
import ast

try:
	import openai
	_OPENAI_AVAILABLE = True
except Exception:
	openai = None
	#!/usr/bin/env python3
	"""
	ê°œì¸ ë¹„ì„œ '?ë¹„?? (ê°„ë‹¨??ChatGPT ?¤í???ì±—ë´‡)

	ê¸°ëŠ¥ ?”ì•½:
	- ê·œì¹™ ê¸°ë°˜ ?‘ë‹µ ë°?? íƒ??OpenAI ?µí•©
	- ëª…ë ¹: `/setname ?´ë¦„`, `/name`, `/history`, `/clear`, `/help`, `exit`
	- ?€???ˆìŠ¤? ë¦¬ ?€?? `NEURON_history.txt` (?€?„ìŠ¤?¬í”„ ?¬í•¨)
	- ?¤ì • ?€?? `NEURON_config.json`

	?¬ìš©ë²?
	  python Untitled-1.py          # REPL ëª¨ë“œ
	  python Untitled-1.py --test   # ?˜í”Œ ?€???¤í–‰ ??ì¢…ë£Œ
	"""

	import os
	import sys
	import argparse
	import time
	import re
	from datetime import datetime
	import ast

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


	def load_config():
		try:
			import json
			if os.path.exists(CONFIG_PATH):
				with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
					return json.load(f)
		except Exception:
			pass
		return {"user_name": ""}


	def save_config(cfg: dict):
		import json
		try:
			with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
				json.dump(cfg, f, ensure_ascii=False, indent=2)
		except Exception:
			pass


	def append_history(role: str, text: str):
		try:
			now = datetime.now().isoformat()
			with open(HISTORY_PATH, 'a', encoding='utf-8') as f:
				f.write(f"[{now}] [{role}] {text}\n")
		except Exception:
			pass


	def call_openai(prompt):
		key = os.getenv("OPENAI_API_KEY")
		if not key:
			raise RuntimeError("OPENAI_API_KEY ?˜ê²½ë³€?˜ê? ?¤ì •?˜ì–´ ?ˆì? ?ŠìŠµ?ˆë‹¤.")
		if not _OPENAI_AVAILABLE:
			raise RuntimeError("openai ?¨í‚¤ì§€ê°€ ?¤ì¹˜?˜ì–´ ?ˆì? ?ŠìŠµ?ˆë‹¤. `pip install openai`ë¥??¤í–‰?˜ì„¸??")
		openai.api_key = key
		messages = [{"role": "user", "content": prompt}]
		resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, max_tokens=512)
		return resp.choices[0].message.content.strip()


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
			if prompt.lower() in ('exit', 'ì¢…ë£Œ'):
				print('ì¢…ë£Œ?©ë‹ˆ??')
				break

			# OpenAI ?¬ìš© ê°€?¥í•˜ë©??°ì„  ?œë„
			if _OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
				try:
					out = call_openai(prompt)
				except Exception as e:
					out = f"OpenAI ?¸ì¶œ ì¤??¤ë¥˜ê°€ ë°œìƒ?ˆìŠµ?ˆë‹¤: {e}\n(fallback ?‘ë‹µ???œê³µ?©ë‹ˆ??\n" + fallback_response(prompt)
			else:
				out = fallback_response(prompt)

			# ?ˆìŠ¤? ë¦¬ ?€??
			append_history('You', prompt)
			append_history(ASSISTANT_NAME, out)

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
		parser.add_argument('--test', action='store_true', help='?˜í”Œ ?€???¤í–‰ ??ì¢…ë£Œ')
		args = parser.parse_args()
		if args.test:
			run_test()
			return
		repl()


	if __name__ == '__main__':
		main()

