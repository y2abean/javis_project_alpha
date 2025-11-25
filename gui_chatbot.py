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
        self.title(f"{ASSISTANT_NAME} ?∞Ïä§?¨ÌÜ±")
        self.geometry('600x500')

        # Menu
        menubar = tk.Menu(self)
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label='API ???§Ï†ï', command=self.set_api_key)
    config_menu.add_command(label='?®Îùº???ôÏäµ (URL)', command=self.learn_from_url_dialog)
        config_menu.add_command(label='?àÏä§?†Î¶¨ ?¥Í∏∞', command=self.open_history)
        config_menu.add_separator()
        # Auto-learn toggle
        def _toggle_autolearn():
            try:
                cfg = load_config()
                cur = cfg.get('auto_learn', False)
                cfg['auto_learn'] = not cur
                save_config(cfg)
                messagebox.showinfo('?§Ï†ï', f"?êÎèô ?ôÏäµ {'?úÏÑ±?? if not cur else 'ÎπÑÌôú?±Ìôî'} ?òÏóà?µÎãà??")
            except Exception as e:
                messagebox.showerror('?§Î•ò', f'?§Ï†ï Î≥ÄÍ≤??§Ìå®: {e}')
        config_menu.add_command(label='?êÎèô ?ôÏäµ ?†Í?', command=_toggle_autolearn)
        config_menu.add_separator()
        config_menu.add_command(label='Ï¢ÖÎ£å', command=self.quit)
        menubar.add_cascade(label='?§Ï†ï', menu=config_menu)
        self.config(menu=menubar)

        # Chat display
        self.text = scrolled.ScrolledText(self, wrap='word', state='disabled')
        self.text.pack(expand=True, fill='both')

        # Entry
        bottom = tk.Frame(self)
        self.entry = tk.Entry(bottom)
        self.entry.pack(side='left', expand=True, fill='x', padx=4, pady=4)
        self.entry.bind('<Return>', self.on_send)
        send_btn = tk.Button(bottom, text='?ÑÏÜ°', command=self.on_send)
        send_btn.pack(side='right', padx=4)
        copy_btn = tk.Button(bottom, text='Î≥µÏÇ¨', command=self.copy_last)
        copy_btn.pack(side='right', padx=4)
        teach_btn = tk.Button(bottom, text='?ôÏäµ', command=self.open_teach_dialog)
        teach_btn.pack(side='right', padx=4)
        save_btn = tk.Button(bottom, text='?Ä??, command=self.save_history)
        save_btn.pack(side='right', padx=4)
        bottom.pack(fill='x')

        # load last config
        self.cfg = load_config()

    def set_api_key(self):
        cur = self.cfg.get('openai_api_key') or os.getenv('OPENAI_API_KEY', '')
        val = simpledialog.askstring('API ???§Ï†ï', 'OpenAI API ?§Î? ?ÖÎ†•?òÏÑ∏??(sk-...)', initialvalue=cur, show='*')
        if val is None:
            return
        self.cfg['openai_api_key'] = val
        save_config(self.cfg)
        os.environ['OPENAI_API_KEY'] = val
        messagebox.showinfo('?Ä??, 'API ?§Í? ?§Ï†ï ?åÏùº???Ä?•ÎêòÍ≥??ÑÏû¨ ?∏ÏÖò???ÅÏö©?òÏóà?µÎãà??')

    def open_history(self):
        hist = os.path.join(os.path.dirname(__file__), 'NEURON_history.txt')
        if os.path.exists(hist):
            try:
                with open(hist, 'r', encoding='utf-8') as f:
                    content = f.read()
                # show in a new window
                win = tk.Toplevel(self)
                win.title('?Ä??Í∏∞Î°ù')
                t = tk.Text(win, wrap='word')
                t.insert('1.0', content)
                t.config(state='disabled')
                t.pack(expand=True, fill='both')
            except Exception as e:
                messagebox.showerror('?§Î•ò', f'Í∏∞Î°ù???????ÜÏäµ?àÎã§: {e}')
        else:
            messagebox.showinfo('?ïÎ≥¥', '?Ä??Í∏∞Î°ù???ÜÏäµ?àÎã§.')

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
            out = f'?§Î•ò Î∞úÏÉù: {e}'
        self.append_message('Assistant', out)

    def copy_last(self):
        try:
            text = self.text.get('end-2l linestart', 'end-1l')
            pyperclip.copy(text)
            messagebox.showinfo('Î≥µÏÇ¨', 'ÎßàÏ?Îß??ëÎãµ???¥Î¶ΩÎ≥¥Îìú??Î≥µÏÇ¨?òÏóà?µÎãà??')
        except Exception as e:
            messagebox.showerror('?§Î•ò', f'Î≥µÏÇ¨ ?§Ìå®: {e}')

    def open_teach_dialog(self):
        try:
            q = simpledialog.askstring('?ôÏäµ (ÏßàÎ¨∏)', '?ôÏäµ??ÏßàÎ¨∏???ÖÎ†•?òÏÑ∏??')
            if not q:
                return
            a = simpledialog.askstring('?ôÏäµ (?µÎ?)', '?¥Îãπ ÏßàÎ¨∏???Ä???µÎ????ÖÎ†•?òÏÑ∏??')
            if not a:
                return
            teach_pair(q, a)
            messagebox.showinfo('?ôÏäµ ?ÑÎ£å', 'ÏßàÎ¨∏/?µÎ????ôÏäµ?àÏäµ?àÎã§.')
            # also append to chat view
            self.append_message('System', f"?ôÏäµ: '{q}' -> ?Ä?•Îê®")
        except Exception as e:
            messagebox.showerror('?§Î•ò', f'?ôÏäµ ?§Ìå®: {e}')

    def learn_from_url_dialog(self):
        try:
            url = simpledialog.askstring('?®Îùº???ôÏäµ', '?ôÏäµ???πÌéò?¥Ï???URL???ÖÎ†•?òÏÑ∏??')
            if not url:
                return
            # run in background
            def _run():
                try:
                    from chatbot import learn_from_url
                    n = learn_from_url(url)
                    self.append_message('System', f'?®Îùº???ôÏäµ ?ÑÎ£å: ?Ä?•Îêú Q/A ??= {n}')
                except Exception as e:
                    self.append_message('System', f'?®Îùº???ôÏäµ ?§Ìå®: {e}')
            threading.Thread(target=_run, daemon=True).start()
        except Exception as e:
            messagebox.showerror('?§Î•ò', f'?®Îùº???ôÏäµ ?§Ìå®: {e}')

    def save_history(self):
        try:
            fname = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text', '*.txt')])
            if not fname:
                return
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(self.text.get('1.0', 'end'))
            messagebox.showinfo('?Ä??, f'Í∏∞Î°ù??{fname}???Ä?•Ìñà?µÎãà??')
        except Exception as e:
            messagebox.showerror('?§Î•ò', f'?Ä???§Ìå®: {e}')

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
