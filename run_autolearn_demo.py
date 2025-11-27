import importlib, traceback

m = importlib.import_module('chatbot')
ok, src = m.check_gemini_key()
print('check_gemini_key ->', ok, src)
if not ok:
    print('Not attempting process_learning_queue because Gemini key not found.')
else:
    try:
        n = m.process_learning_queue()
        print('process_learning_queue ->', n, 'items processed and saved')
    except Exception:
        print('process_learning_queue raised exception:')
        traceback.print_exc()
