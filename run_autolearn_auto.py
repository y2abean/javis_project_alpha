import importlib, traceback, json
m = importlib.import_module('chatbot')
log = []
# example prompts to enqueue
prompts = [
    "자비스, 내일 날씨 알려줘",
    "파이썬에서 리스트를 정렬하는 방법",
    "서울에서 가볼만한 관광지 추천"
]
added = []
for p in prompts:
    try:
        ok = m.queue_for_learning(p)
        added.append({'prompt': p, 'queued': ok})
    except Exception as e:
        added.append({'prompt': p, 'error': str(e)})
log.append({'queued': added})
try:
    n = m.process_learning_queue()
    log.append({'processed': n})
except Exception:
    log.append({'exception': traceback.format_exc()})
with open('autolearn_run2.log', 'w', encoding='utf-8') as f:
    f.write(json.dumps(log, ensure_ascii=False, indent=2))
print('WROTE autolearn_run2.log')
