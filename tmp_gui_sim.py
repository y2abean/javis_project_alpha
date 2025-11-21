import time
from gui_chatbot import JarvisGUI

print('START GUI SIM')
app = JarvisGUI()
print('APP CREATED')
# hide (simulate minimize to tray)
app.withdraw()
print('WITHDRAWN')
time.sleep(2)
# show
app.deiconify()
print('DEICONIFIED')
# close after short delay
time.sleep(2)
app.destroy()
print('DESTROYED')
