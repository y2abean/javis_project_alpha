from chatbot import get_response
r = get_response('안녕')
print('RESPONSE>>>')
print(r)
# print last 5 lines of history
with open('jarvis_history.txt','r',encoding='utf-8') as f:
    lines = f.readlines()
print('\nHISTORY TAIL>>>')
for ln in lines[-10:]:
    print(ln.strip())
