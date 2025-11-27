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

class NEURONGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{ASSISTANT_NAME} ?�스?�톱")
        self.geometry('600x500')

        # Menu
        menubar = tk.Menu(self)
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label='API ???�정', command=self.set_api_key)
    config_menu.add_command(label='?�라???�습 (URL)', command=self.learn_from_url_dialog)
        config_menu.add_command(label='?�스?�리 ?�기', command=self.open_history)
        config_menu.add_separator()
        # Auto-learn toggle
        def _toggle_autolearn():
            try:
                cfg = load_config()
                cur = cfg.get('auto_learn', False)
                cfg['auto_learn'] = not cur
                save_config(cfg)
                messagebox.showinfo('?�정', f"?�동 ?�습 {'?�성?? if not cur else '비활?�화'} ?�었?�니??")
            except Exception as e:
                messagebox.showerror('?�류', f'?�정 변�??�패: {e}')
        config_menu.add_command(label='?�동 ?�습 ?��?', command=_toggle_autolearn)
        config_menu.add_separator()
        config_menu.add_command(label='종료', command=self.quit)
        menubar.add_cascade(label='?�정', menu=config_menu)
        self.config(menu=menubar)

        # Chat display
        self.text = scrolled.ScrolledText(self, wrap='word', state='disabled')
        self.text.pack(expand=True, fill='both')

        # Entry
        bottom = tk.Frame(self)
        self.entry = tk.Entry(bottom)
        self.entry.pack(side='left', expand=True, fill='x', padx=4, pady=4)
        self.entry.bind('<Return>', self.on_send)
        send_btn = tk.Button(bottom, text='?�송', command=self.on_send)
        send_btn.pack(side='right', padx=4)
        copy_btn = tk.Button(bottom, text='복사', command=self.copy_last)
        copy_btn.pack(side='right', padx=4)
        teach_btn = tk.Button(bottom, text='?�습', command=self.open_teach_dialog)
        teach_btn.pack(side='right', padx=4)
        save_btn = tk.Button(bottom, text='?�??, command=self.save_history)
        save_btn.pack(side='right', padx=4)
        bottom.pack(fill='x')

        # load last config
        self.cfg = load_config()

    def set_api_key(self):
        cur = self.cfg.get('gemini_api_key') or os.getenv('gemini_api_key', '')
        val = simpledialog.askstring('API ???�정', 'Gemini API ?��? ?�력?�세??(sk-...)', initialvalue=cur, show='*')
        if val is None:
            return
        self.cfg['gemini_api_key'] = val
        save_config(self.cfg)
        os.environ['gemini_api_key'] = val
        messagebox.showinfo('?�??, 'API ?��? ?�정 ?�일???�?�되�??�재 ?�션???�용?�었?�니??')

    def open_history(self):
        hist = os.path.join(os.path.dirname(__file__), 'NEURON_history.txt')
        if os.path.exists(hist):
            try:
                with open(hist, 'r', encoding='utf-8') as f:
                    content = f.read()
                # show in a new window
                win = tk.Toplevel(self)
                win.title('?�??기록')
                t = tk.Text(win, wrap='word')
                t.insert('1.0', content)
                t.config(state='disabled')
                t.pack(expand=True, fill='both')
            except Exception as e:
                messagebox.showerror('?�류', f'기록???????�습?�다: {e}')
        else:
            messagebox.showinfo('?�보', '?�??기록???�습?�다.')

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
            out = f'?�류 발생: {e}'
        self.append_message('Assistant', out)

    def copy_last(self):
        try:
            text = self.text.get('end-2l linestart', 'end-1l')
            pyperclip.copy(text)
            messagebox.showinfo('복사', '마�?�??�답???�립보드??복사?�었?�니??')
        except Exception as e:
            messagebox.showerror('?�류', f'복사 ?�패: {e}')

    def open_teach_dialog(self):
        try:
            q = simpledialog.askstring('?�습 (질문)', '?�습??질문???�력?�세??')
            if not q:
                return
            a = simpledialog.askstring('?�습 (?��?)', '?�당 질문???�???��????�력?�세??')
            if not a:
                return
            teach_pair(q, a)
            messagebox.showinfo('?�습 ?�료', '질문/?��????�습?�습?�다.')
            # also append to chat view
            self.append_message('System', f"?�습: '{q}' -> ?�?�됨")
        except Exception as e:
            messagebox.showerror('?�류', f'?�습 ?�패: {e}')

    def learn_from_url_dialog(self):
        try:
            url = simpledialog.askstring('?�라???�습', '?�습???�페?��???URL???�력?�세??')
            if not url:
                return
            # run in background
            def _run():
                try:
                    from chatbot import learn_from_url
                    n = learn_from_url(url)
                    self.append_message('System', f'?�라???�습 ?�료: ?�?�된 Q/A ??= {n}')
                except Exception as e:
                    self.append_message('System', f'?�라???�습 ?�패: {e}')
            threading.Thread(target=_run, daemon=True).start()
        except Exception as e:
            messagebox.showerror('?�류', f'?�라???�습 ?�패: {e}')

    def save_history(self):
        try:
            fname = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text', '*.txt')])
            if not fname:
                return
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(self.text.get('1.0', 'end'))
            messagebox.showinfo('?�??, f'기록??{fname}???�?�했?�니??')
        except Exception as e:
            messagebox.showerror('?�류', f'?�???�패: {e}')

def main():
    # support start minimized to tray via env var START_MINIMIZED or arg later
    start_min = os.getenv('START_MINIMIZED', '0') in ('1', 'true', 'True')
    app = NEURONGUI()

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

    tray_icon = pystray.Icon('NEURON', icon_image, 'NEURON', menu=pystray.Menu(
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

