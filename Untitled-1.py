#!/usr/bin/env python3
"""
간단한 ChatGPT 스타일 챗봇 예제

- OpenAI API 키가 `OPENAI_API_KEY` 환경변수로 설정되어 있고
  `openai` 패키지가 설치되어 있으면 실제 OpenAI ChatCompletion을 호출합니다.
- 그렇지 않으면 간단한 규칙 기반(fallback) 응답을 제공합니다.

사용법:
  python Untitled-1.py          # REPL 모드
  python Untitled-1.py --test   # 샘플 대화 실행 후 종료
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
	개인 비서 '자비스' (간단한 ChatGPT 스타일 챗봇)

	기능 요약:
	- 규칙 기반 응답 및 선택적 OpenAI 통합
	- 명령: `/setname 이름`, `/name`, `/history`, `/clear`, `/help`, `exit`
	- 대화 히스토리 저장: `jarvis_history.txt` (타임스탬프 포함)
	- 설정 저장: `jarvis_config.json`

	사용법:
	  python Untitled-1.py          # REPL 모드
	  python Untitled-1.py --test   # 샘플 대화 실행 후 종료
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

	# 파일 경로 / 기본값
	ASSISTANT_NAME = "자비스"
	CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'jarvis_config.json')
	HISTORY_PATH = os.path.join(os.path.dirname(__file__), 'jarvis_history.txt')


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
			raise RuntimeError("OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")
		if not _OPENAI_AVAILABLE:
			raise RuntimeError("openai 패키지가 설치되어 있지 않습니다. `pip install openai`를 실행하세요.")
		openai.api_key = key
		messages = [{"role": "user", "content": prompt}]
		resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, max_tokens=512)
		return resp.choices[0].message.content.strip()


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
			if prompt.lower() in ('exit', '종료'):
				print('종료합니다.')
				break

			# OpenAI 사용 가능하면 우선 시도
			if _OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
				try:
					out = call_openai(prompt)
				except Exception as e:
					out = f"OpenAI 호출 중 오류가 발생했습니다: {e}\n(fallback 응답을 제공합니다)\n" + fallback_response(prompt)
			else:
				out = fallback_response(prompt)

			# 히스토리 저장
			append_history('You', prompt)
			append_history(ASSISTANT_NAME, out)

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
			if _OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
				try:
					out = call_openai(s)
				except Exception as e:
					out = f"OpenAI 오류: {e} — fallback 사용\n" + fallback_response(s)
			else:
				out = fallback_response(s)
			print('Assistant:', out)
			time.sleep(0.2)


	def main():
		parser = argparse.ArgumentParser()
		parser.add_argument('--test', action='store_true', help='샘플 대화 실행 후 종료')
		args = parser.parse_args()
		if args.test:
			run_test()
			return
		repl()


	if __name__ == '__main__':
		main()

