import importlib, traceback, json
m = importlib.import_module('chatbot')
log = []
# example prompts to enqueue
prompts = [
    "?ë¹„?? ?´ì¼ ? ì”¨ ?Œë ¤ì¤?,
    "?Œì´?¬ì—??ë¦¬ìŠ¤?¸ë? ?•ë ¬?˜ëŠ” ë°©ë²•",
    "?œìš¸?ì„œ ê°€ë³¼ë§Œ??ê´€ê´‘ì? ì¶”ì²œ"
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
