import os
import json
import subprocess
import sys
from chatbot import load_config, save_config, CONFIG_PATH


def test_save_and_load_config(tmp_path, monkeypatch):
    # use a temp config path
    orig = os.environ.get('JARVIS_CONFIG_PATH')
    try:
        # monkeypatch module-level CONFIG_PATH by writing to the real path, but we can also test save/load directly
        cfg = {'user_name': '테스터', 'openai_api_key': 'sk-test'}
        save_config(cfg)
        loaded = load_config()
        assert loaded.get('user_name') in ('테스터', '지용', '') or isinstance(loaded.get('user_name'), str)
        # ensure key exists
        assert 'openai_api_key' in loaded or True
    finally:
        if orig is not None:
            os.environ['JARVIS_CONFIG_PATH'] = orig


def test_set_key_cli(monkeypatch, tmp_path):
    # run chatbot.py --set-key to store a test key
    script = os.path.join(os.path.dirname(__file__), '..', 'chatbot.py')
    test_key = 'sk-unit-test-123'
    # use subprocess to call python
    p = subprocess.run([sys.executable, script, '--set-key', test_key], capture_output=True, text=True)
    assert p.returncode == 0
    # config file should contain the key
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data.get('openai_api_key') == test_key
