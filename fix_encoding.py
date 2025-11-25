# -*- coding: utf-8 -*-
import codecs
import re

# Fix chatbot.py encoding issue - convert entire file to UTF-8
# and remove all broken characters
with codecs.open('chatbot.py', 'r', encoding='cp949', errors='replace') as f:
    content = f.read()

# Remove all replacement characters (�) and other broken patterns
content = content.replace('�', '')
content = content.replace('?', '')
content = content.replace('∽', '')

# Fix known Korean strings
content = re.sub(r'ASSISTANT_NAME\s*=\s*"[^"]*"', 'ASSISTANT_NAME = "뉴런"', content)
content = re.sub(r'#.*寃쎈줈.*湲곕낯媛?', '# 파일 경로 / 기본값', content)

# Remove lines with remaining invalid characters
lines = content.split('\n')
clean_lines = []
for line in lines:
    # Keep line if it doesn't have weird characters
    if not any(ord(c) > 127 and c not in '가-힣ㄱ-ㅎㅏ-ㅣ' for c in line if c not in ['\r', '\n', '\t']):
        clean_lines.append(line)
    elif 'import' in line or 'def ' in line or 'class ' in line or '=' in line:
        # Keep important structure lines even if they have some issues
        clean_lines.append(re.sub(r'[^\x00-\x7F가-힣ㄱ-ㅎㅏ-ㅣ\s]', '', line))

content = '\n'.join(clean_lines)

# Write as UTF-8
with codecs.open('chatbot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("chatbot.py cleaned and converted to UTF-8!")
