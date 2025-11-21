import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import threading
import io
from PIL import Image, ImageDraw
import pystray
import os
import sys
from chatbot import get_response, load_config, save_config, ASSISTANT_NAME, teach_pair
import tkinter.scrolledtext as scrolled
import pyperclip

class JarvisGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{ASSISTANT_NAME} 데스크톱")
        self.geometry('600x500')

        # Menu
        menubar = tk.Menu(self)
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label='API 키 설정', command=self.set_api_key)
    config_menu.add_command(label='온라인 학습 (URL)', command=self.learn_from_url_dialog)
        config_menu.add_command(label='히스토리 열기', command=self.open_history)
        config_menu.add_separator()
        # Auto-learn toggle
        def _toggle_autolearn():
            try:
                cfg = load_config()
                cur = cfg.get('auto_learn', False)
                cfg['auto_learn'] = not cur
                save_config(cfg)
                messagebox.showinfo('설정', f"자동 학습 {'활성화' if not cur else '비활성화'} 되었습니다.")
            except Exception as e:
                messagebox.showerror('오류', f'설정 변경 실패: {e}')
        config_menu.add_command(label='자동 학습 토글', command=_toggle_autolearn)
        config_menu.add_separator()
        config_menu.add_command(label='종료', command=self.quit)
        menubar.add_cascade(label='설정', menu=config_menu)
        self.config(menu=menubar)

        # Chat display
        self.text = scrolled.ScrolledText(self, wrap='word', state='disabled')
        self.text.pack(expand=True, fill='both')

        # Entry
        bottom = tk.Frame(self)
        self.entry = tk.Entry(bottom)
        self.entry.pack(side='left', expand=True, fill='x', padx=4, pady=4)
        self.entry.bind('<Return>', self.on_send)
        send_btn = tk.Button(bottom, text='전송', command=self.on_send)
        send_btn.pack(side='right', padx=4)
        copy_btn = tk.Button(bottom, text='복사', command=self.copy_last)
        copy_btn.pack(side='right', padx=4)
        teach_btn = tk.Button(bottom, text='학습', command=self.open_teach_dialog)
        teach_btn.pack(side='right', padx=4)
        save_btn = tk.Button(bottom, text='저장', command=self.save_history)
        save_btn.pack(side='right', padx=4)
        bottom.pack(fill='x')

        # load last config
        self.cfg = load_config()

    def set_api_key(self):
        cur = self.cfg.get('openai_api_key') or os.getenv('OPENAI_API_KEY', '')
        val = simpledialog.askstring('API 키 설정', 'OpenAI API 키를 입력하세요 (sk-...)', initialvalue=cur, show='*')
        if val is None:
            return
        self.cfg['openai_api_key'] = val
        save_config(self.cfg)
        os.environ['OPENAI_API_KEY'] = val
        messagebox.showinfo('저장', 'API 키가 설정 파일에 저장되고 현재 세션에 적용되었습니다.')

    def open_history(self):
        hist = os.path.join(os.path.dirname(__file__), 'jarvis_history.txt')
        if os.path.exists(hist):
            try:
                with open(hist, 'r', encoding='utf-8') as f:
                    content = f.read()
                # show in a new window
                win = tk.Toplevel(self)
                win.title('대화 기록')
                t = tk.Text(win, wrap='word')
                t.insert('1.0', content)
                t.config(state='disabled')
                t.pack(expand=True, fill='both')
            except Exception as e:
                messagebox.showerror('오류', f'기록을 열 수 없습니다: {e}')
        else:
            messagebox.showinfo('정보', '대화 기록이 없습니다.')

    def append_message(self, who, text):
        self.text.config(state='normal')
        self.text.insert('end', f'[{who}] {text}\n')
        self.text.see('end')
        self.text.config(state='disabled')

    def on_send(self, event=None):
        prompt = self.entry.get().strip()
        if not prompt:
            return
        self.entry.delete(0, 'end')
        self.append_message('You', prompt)
        # call get_response in background
        threading.Thread(target=self._worker, args=(prompt,), daemon=True).start()

    def _worker(self, prompt):
        try:
            out = get_response(prompt)
        except Exception as e:
            out = f'오류 발생: {e}'
        self.append_message('Assistant', out)

    def copy_last(self):
        try:
            text = self.text.get('end-2l linestart', 'end-1l')
            pyperclip.copy(text)
            messagebox.showinfo('복사', '마지막 응답이 클립보드에 복사되었습니다.')
        except Exception as e:
            messagebox.showerror('오류', f'복사 실패: {e}')

    def open_teach_dialog(self):
        try:
            q = simpledialog.askstring('학습 (질문)', '학습할 질문을 입력하세요:')
            if not q:
                return
            a = simpledialog.askstring('학습 (답변)', '해당 질문에 대한 답변을 입력하세요:')
            if not a:
                return
            teach_pair(q, a)
            messagebox.showinfo('학습 완료', '질문/답변을 학습했습니다.')
            # also append to chat view
            self.append_message('System', f"학습: '{q}' -> 저장됨")
        except Exception as e:
            messagebox.showerror('오류', f'학습 실패: {e}')

    def learn_from_url_dialog(self):
        try:
            url = simpledialog.askstring('온라인 학습', '학습할 웹페이지의 URL을 입력하세요:')
            if not url:
                return
            # run in background
            def _run():
                try:
                    from chatbot import learn_from_url
                    n = learn_from_url(url)
                    self.append_message('System', f'온라인 학습 완료: 저장된 Q/A 수 = {n}')
                except Exception as e:
                    self.append_message('System', f'온라인 학습 실패: {e}')
            threading.Thread(target=_run, daemon=True).start()
        except Exception as e:
            messagebox.showerror('오류', f'온라인 학습 실패: {e}')

    def save_history(self):
        try:
            fname = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text', '*.txt')])
            if not fname:
                return
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(self.text.get('1.0', 'end'))
            messagebox.showinfo('저장', f'기록을 {fname}에 저장했습니다.')
        except Exception as e:
            messagebox.showerror('오류', f'저장 실패: {e}')

def main():
    # support start minimized to tray via env var START_MINIMIZED or arg later
    start_min = os.getenv('START_MINIMIZED', '0') in ('1', 'true', 'True')
    app = JarvisGUI()

    # create tray icon and menu
    def create_image():
        # Try to load 'icon.png' from project root; otherwise generate simple icon
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        if os.path.exists(icon_path):
            return Image.open(icon_path)
        # generate 64x64 icon
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((4, 4, 60, 60), fill=(30, 144, 255, 255))
        d.text((18, 18), 'J', fill='white')
        return img

    icon_image = create_image()

    def on_show(icon, item):
        app.after(0, lambda: (app.deiconify(), app.lift()))

    def on_hide(icon, item):
        app.after(0, lambda: app.withdraw())

    def on_quit(icon, item):
        try:
            icon.stop()
        except Exception:
            pass
        app.after(0, app.destroy)

    tray_icon = pystray.Icon('jarvis', icon_image, 'Jarvis', menu=pystray.Menu(
        pystray.MenuItem('Show', on_show),
        pystray.MenuItem('Hide', on_hide),
        pystray.MenuItem('Exit', on_quit)
    ))

    def run_tray():
        tray_icon.run()

    t = threading.Thread(target=run_tray, daemon=True)
    t.start()

    if start_min:
        app.withdraw()

    try:
        app.mainloop()
    finally:
        try:
            tray_icon.stop()
        except Exception:
            pass

if __name__ == '__main__':
    main()
