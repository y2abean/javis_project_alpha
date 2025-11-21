import importlib, traceback, json, sys

log = []
try:
    m = importlib.import_module('chatbot')
    ok, src = m.check_openai_key()
    log.append({'check_openai_key': {'ok': ok, 'source': src}})
    if not ok:
        log.append({'note': 'No OpenAI API key found; aborting process_learning_queue.'})
    else:
        try:
            n = m.process_learning_queue()
            log.append({'processed': n})
        except Exception:
            tb = traceback.format_exc()
            log.append({'exception': tb})
except Exception:
    tb = traceback.format_exc()
    log.append({'import_error': tb})

with open('autolearn_run.log', 'w', encoding='utf-8') as f:
    f.write(json.dumps(log, ensure_ascii=False, indent=2))

print('WROTE autolearn_run.log')
