"""
学习中心插件 - 使用 pywebview 打开本地或远程文档
工具栏在外部 HTML 中，通过 iframe 加载内容
"""

import os
import sys
import logging
import subprocess
import tempfile
import atexit
from typing import Optional

import pystart
from pystart import get_workbench
from pystart.languages import tr

logger = logging.getLogger(__name__)

_LOCK_FILE = os.path.join(tempfile.gettempdir(), "pystart_learning_center.lock")
_PID_FILE = os.path.join(tempfile.gettempdir(), "pystart_learning_center.pid")
_WRAPPER_FILE = os.path.join(tempfile.gettempdir(), "pystart_lc_wrapper.html")
_subprocess = None


def get_learning_center_dir() -> str:
    language = get_workbench().get_option("general.language")
    base_dir = os.path.dirname(pystart.__file__)
    
    lang_dir = os.path.join(base_dir, "locale", language, "LEARNING_CENTER")
    if os.path.exists(lang_dir):
        return lang_dir
    
    zh_dir = os.path.join(base_dir, "locale", "zh_CN", "LEARNING_CENTER")
    if os.path.exists(zh_dir):
        return zh_dir
    
    return os.path.join(base_dir, "plugins", "learning_center_docs")


def get_default_url() -> str:
    doc_dir = get_learning_center_dir()
    index_file = os.path.join(doc_dir, "index.html")
    if os.path.exists(index_file):
        return index_file
    return "https://www.aeknow.org/pystart/learning"


def _cleanup_subprocess():
    """清理学习中心子进程"""
    global _subprocess
    
    # 方法1：通过进程对象终止
    if _subprocess is not None:
        try:
            _subprocess.terminate()
            _subprocess.wait(timeout=2)
        except:
            try:
                _subprocess.kill()
            except:
                pass
        _subprocess = None
    
    # 方法2：通过 PID 文件终止
    if os.path.exists(_PID_FILE):
        try:
            with open(_PID_FILE, "r") as f:
                pid = int(f.read().strip())
            # Windows 下强制终止进程
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                             capture_output=True, timeout=5)
            else:
                os.kill(pid, 9)
        except:
            pass
    
    # 清理临时文件
    for f in [_PID_FILE, _LOCK_FILE, _WRAPPER_FILE]:
        try:
            os.remove(f)
        except:
            pass
    
    logger.info("学习中心进程已清理")


def _create_wrapper_html(content_url: str, home_url: str) -> str:
    """创建包装 HTML 页面，包含工具栏和 iframe"""
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PyStart 学习中心</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ height: 100%; overflow: hidden; }}
        
        #toolbar {{
            height: 45px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            padding: 0 15px;
            gap: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        #toolbar button {{
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }}
        
        #toolbar button:hover {{
            background: rgba(255,255,255,0.3);
        }}
        
        #toolbar .home-btn {{
            background: rgba(255,255,255,0.9);
            color: #667eea;
            font-weight: 600;
            padding: 8px 16px;
        }}
        
        #toolbar .home-btn:hover {{
            background: white;
        }}
        
        #toolbar .spacer {{
            flex: 1;
        }}
        
        #toolbar .title {{
            color: rgba(255,255,255,0.8);
            font-size: 13px;
        }}
        
        #content {{
            height: calc(100% - 45px);
            width: 100%;
            border: none;
        }}
    </style>
</head>
<body>
    <div id="toolbar">
        <button onclick="goBack()" title="后退">◀ 后退</button>
        <button onclick="goForward()" title="前进">前进 ▶</button>
        <button class="home-btn" onclick="goHome()" title="返回主页">🏠 主页</button>
        <button onclick="refresh()" title="刷新">🔄 刷新</button>
        <span class="spacer"></span>
        <span class="title">PyStart 学习中心</span>
    </div>
    <iframe id="content" src="{content_url}"></iframe>
    
    <script>
        var iframe = document.getElementById('content');
        var homeUrl = '{home_url}';
        
        function goBack() {{
            try {{ iframe.contentWindow.history.back(); }} catch(e) {{}}
        }}
        
        function goForward() {{
            try {{ iframe.contentWindow.history.forward(); }} catch(e) {{}}
        }}
        
        function goHome() {{
            iframe.src = homeUrl;
        }}
        
        function refresh() {{
            iframe.src = iframe.src;
        }}
    </script>
</body>
</html>'''


def open_learning_center(url: Optional[str] = None):
    global _subprocess
    
    if url is None:
        url = get_default_url()
    
    # 转换为 file:// URL
    if os.path.exists(url):
        url = "file:///" + url.replace("\\", "/")
    
    home_url = get_default_url()
    if os.path.exists(home_url):
        home_url = "file:///" + home_url.replace("\\", "/")
    
    logger.info(f"打开学习中心: {url}")
    
    # 创建包装 HTML
    wrapper_html = _create_wrapper_html(url, home_url)
    with open(_WRAPPER_FILE, "w", encoding="utf-8") as f:
        f.write(wrapper_html)
    
    wrapper_url = "file:///" + _WRAPPER_FILE.replace("\\", "/")
    
    # 创建启动脚本
    script_content = f'''# -*- coding: utf-8 -*-
import os
import webview
import ctypes
import threading

user32 = ctypes.windll.user32
sw = user32.GetSystemMetrics(0)
sh = user32.GetSystemMetrics(1)

# 全高度，宽度 40%，靠右
ww = int(sw * 0.4)
wh = sh  # 全高度
wx = sw - ww
wy = 0

LOCK = r"{_LOCK_FILE}"
PIDF = r"{_PID_FILE}"

with open(PIDF, "w") as f:
    f.write(str(os.getpid()))

def cleanup():
    for p in [LOCK, PIDF]:
        try: os.remove(p)
        except: pass

window = webview.create_window(
    "PyStart 学习中心",
    r"{wrapper_url}",
    width=ww, height=wh, x=wx, y=wy,
    resizable=True, min_size=(400, 500)
)
window.events.closing += cleanup

def alive():
    import time
    while True:
        try:
            with open(LOCK, "w") as f: f.write(str(os.getpid()))
        except: pass
        time.sleep(3)

threading.Thread(target=alive, daemon=True).start()
webview.start()
cleanup()
'''
    
    script_file = os.path.join(tempfile.gettempdir(), "pystart_lc_script.py")
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_content)
    
    python_exe = sys.executable
    pythonw = python_exe.replace("python.exe", "pythonw.exe")
    if os.path.exists(pythonw):
        python_exe = pythonw
    
    try:
        _subprocess = subprocess.Popen(
            [python_exe, script_file],
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except Exception as e:
        logger.error(f"启动学习中心失败: {e}")
        from tkinter import messagebox
        messagebox.showerror(tr("错误"), f"启动学习中心失败: {e}")


def _on_workbench_close(event=None):
    _cleanup_subprocess()


def load_plugin():
    get_workbench().add_command("learning_center", "help", tr("学习中心"), open_learning_center, group=40)
    get_workbench().bind("WorkbenchClose", _on_workbench_close, True)
    atexit.register(_cleanup_subprocess)
