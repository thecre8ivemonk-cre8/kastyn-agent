import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import json
import sys
import platform
import urllib.request

CONFIG_FILE = os.path.expanduser("~/.kastyn_gui.json")

AGENT_URLS = {
    "Windows": "https://github.com/thecre8ivemonk-cre8/kastyn-agent/releases/latest/download/kastyn-agent-windows.exe",
    "Darwin":  "https://github.com/thecre8ivemonk-cre8/kastyn-agent/releases/latest/download/kastyn-agent-mac",
    "Linux":   "https://github.com/thecre8ivemonk-cre8/kastyn-agent/releases/latest/download/kastyn-agent-linux",
}

AGENT_NAMES = {
    "Windows": "kastyn-agent-windows.exe",
    "Darwin":  "kastyn-agent-mac",
    "Linux":   "kastyn-agent-linux",
}

def get_platform():
    return platform.system()

def get_agent_default_path():
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(script_dir, AGENT_NAMES.get(get_platform(), "kastyn-agent"))

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"api_token": "", "station_id": "", "music_path": "", "agent_path": ""}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)

class KastynGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kastyn Agent")
        self.root.geometry("700x640")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f0f0f")

        self.cfg = load_config()
        self.process = None
        self.running = False

        self._build_ui()
        self._check_agent()

    def _check_agent(self):
        # Check saved path first
        saved = self.cfg.get("agent_path", "")
        if saved and os.path.isfile(saved):
            self.agent_status_var.set(f"Agent ready: {os.path.basename(saved)}")
            self._set_agent_status(True)
            return

        # Check default location (same dir as GUI)
        default = get_agent_default_path()
        if os.path.isfile(default):
            self.cfg["agent_path"] = default
            self.agent_status_var.set(f"Agent ready: {os.path.basename(default)}")
            self._set_agent_status(True)
            return

        # Not found — auto download
        self.agent_status_var.set("Agent not found — downloading...")
        self._set_agent_status(None)
        threading.Thread(target=self._download_agent, args=(default,), daemon=True).start()

    def _download_agent(self, dest_path):
        plat = get_platform()
        url = AGENT_URLS.get(plat)
        if not url:
            self.root.after(0, self._agent_download_failed, f"Unsupported platform: {plat}")
            return
        try:
            self.root.after(0, self._log, f"Downloading agent from GitHub...\n", "info")
            urllib.request.urlretrieve(url, dest_path,
                reporthook=lambda b, bs, ts: self.root.after(0, self._download_progress, b, bs, ts))
            if plat != "Windows":
                os.chmod(dest_path, 0o755)
            self.cfg["agent_path"] = dest_path
            save_config(self.cfg)
            self.root.after(0, self._agent_download_done, dest_path)
        except Exception as e:
            self.root.after(0, self._agent_download_failed, str(e))

    def _download_progress(self, blocks, block_size, total_size):
        if total_size > 0:
            pct = min(100, int(blocks * block_size * 100 / total_size))
            self.agent_status_var.set(f"Downloading agent... {pct}%")

    def _agent_download_done(self, path):
        self.agent_status_var.set(f"Agent ready: {os.path.basename(path)}")
        self._set_agent_status(True)
        self._log(f"Agent downloaded and ready.\n", "ok")

    def _agent_download_failed(self, err):
        self.agent_status_var.set("Agent download failed — use Browse to locate it manually")
        self._set_agent_status(False)
        self._log(f"Agent download failed: {err}\n", "err")

    def _set_agent_status(self, ok):
        if ok is True:
            self.agent_dot.config(fg=self.green)
            self.agent_status_label.config(fg=self.green)
        elif ok is False:
            self.agent_dot.config(fg=self.red)
            self.agent_status_label.config(fg=self.red)
        else:
            self.agent_dot.config(fg=self.amber)
            self.agent_status_label.config(fg=self.amber)

    def _build_ui(self):
        bg = "#0f0f0f"
        card = "#1a1a1a"
        border = "#2a2a2a"
        amber = "#f59e0b"
        amber_dark = "#d97706"
        text = "#f0f0f0"
        muted = "#888888"
        green = "#10b981"
        red = "#ef4444"

        self.amber = amber
        self.green = green
        self.red = red
        self.muted = muted
        self.text_col = text

        # Header
        header = tk.Frame(self.root, bg=bg)
        header.pack(fill="x", padx=24, pady=(24, 0))
        tk.Label(header, text="Kastyn", font=("Inter", 22, "bold"),
                 fg=amber, bg=bg).pack(side="left")
        tk.Label(header, text="  Agent Launcher", font=("Inter", 16),
                 fg=muted, bg=bg).pack(side="left", pady=(4, 0))

        tk.Frame(self.root, bg=border, height=1).pack(fill="x", padx=24, pady=16)

        # Agent status bar
        agent_bar = tk.Frame(self.root, bg=card, highlightbackground=border,
                             highlightthickness=1)
        agent_bar.pack(fill="x", padx=24, pady=(0, 12))
        agent_inner = tk.Frame(agent_bar, bg=card, padx=16, pady=10)
        agent_inner.pack(fill="x")

        self.agent_dot = tk.Label(agent_inner, text="●", font=("Inter", 13),
                                  fg=amber, bg=card)
        self.agent_dot.pack(side="left", padx=(0, 8))
        self.agent_status_var = tk.StringVar(value="Checking for agent...")
        self.agent_status_label = tk.Label(agent_inner, textvariable=self.agent_status_var,
                                           font=("Inter", 12), fg=amber, bg=card)
        self.agent_status_label.pack(side="left")
        tk.Button(agent_inner, text="Browse", font=("Inter", 11),
                  fg=amber, bg=card, activebackground=card,
                  activeforeground=amber, relief="flat", bd=0,
                  cursor="hand2", command=self._browse_agent).pack(side="right")

        # Config card
        cfg_frame = tk.Frame(self.root, bg=card, highlightbackground=border,
                             highlightthickness=1)
        cfg_frame.pack(fill="x", padx=24, pady=(0, 12))
        inner = tk.Frame(cfg_frame, bg=card, padx=20, pady=16)
        inner.pack(fill="x")
        inner.columnconfigure(1, weight=1)

        # API token
        self._make_row(inner, card, border, amber, muted, text,
                       "API key", "api_token_var", None, 0, secret=True)
        tk.Frame(inner, bg=border, height=1).grid(row=1, column=0, columnspan=3, sticky="ew", pady=8)

        # Station ID
        self._make_row(inner, card, border, amber, muted, text,
                       "Station ID", "station_id_var", None, 2, secret=False)
        tk.Frame(inner, bg=border, height=1).grid(row=3, column=0, columnspan=3, sticky="ew", pady=8)

        # Music folder
        self._make_row(inner, card, border, amber, muted, text,
                       "Music folder", "music_path_var", self._browse_folder, 4, secret=False)

        # Pre-fill
        self.api_token_var.set(self.cfg.get("api_token", ""))
        self.station_id_var.set(self.cfg.get("station_id", ""))
        self.music_path_var.set(self.cfg.get("music_path", ""))

        # Mode
        mode_frame = tk.Frame(self.root, bg=bg)
        mode_frame.pack(fill="x", padx=24, pady=(8, 4))
        tk.Label(mode_frame, text="Mode", font=("Inter", 12),
                 fg=muted, bg=bg).pack(side="left", padx=(0, 12))
        self.mode_var = tk.StringVar(value="scan")
        for val, label in [("scan", "Scan once"), ("watch", "Watch (continuous)")]:
            tk.Radiobutton(mode_frame, text=label, variable=self.mode_var,
                           value=val, font=("Inter", 12), fg=text, bg=bg,
                           selectcolor=bg, activebackground=bg,
                           activeforeground=amber, highlightthickness=0, bd=0,
                           command=self._on_mode_change).pack(side="left", padx=(0, 20))
        self.writeback_var = tk.BooleanVar(value=False)
        tk.Checkbutton(mode_frame, text="Write corrections back to files",
                       variable=self.writeback_var, font=("Inter", 12),
                       fg=muted, bg=bg, selectcolor=bg, activebackground=bg,
                       activeforeground=text, highlightthickness=0).pack(side="left", padx=(20, 0))

        # Watch interval
        self.interval_frame = tk.Frame(self.root, bg=bg)
        tk.Label(self.interval_frame, text="Watch interval (minutes):",
                 font=("Inter", 12), fg=muted, bg=bg).pack(side="left", padx=(0, 8))
        self.interval_var = tk.StringVar(value="60")
        tk.Entry(self.interval_frame, textvariable=self.interval_var,
                 font=("Inter", 12), bg="#1a1a1a", fg=text,
                 insertbackground=text, relief="flat",
                 highlightbackground=border, highlightthickness=1,
                 width=6).pack(side="left")

        # Run button
        btn_frame = tk.Frame(self.root, bg=bg)
        btn_frame.pack(fill="x", padx=24, pady=(10, 10))
        self.run_btn = tk.Button(btn_frame, text="▶  Run scan",
                                 font=("Inter", 13, "bold"),
                                 fg="#0f0f0f", bg=amber,
                                 activebackground=amber_dark,
                                 activeforeground="#0f0f0f",
                                 relief="flat", bd=0, padx=24, pady=10,
                                 cursor="hand2", command=self._toggle_run)
        self.run_btn.pack(side="left")
        self.status_dot = tk.Label(btn_frame, text="●", font=("Inter", 14),
                                   fg=muted, bg=bg)
        self.status_dot.pack(side="left", padx=(16, 4))
        self.status_label = tk.Label(btn_frame, text="Idle",
                                     font=("Inter", 12), fg=muted, bg=bg)
        self.status_label.pack(side="left")

        # Log
        log_frame = tk.Frame(self.root, bg=card, highlightbackground=border,
                             highlightthickness=1)
        log_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        log_header = tk.Frame(log_frame, bg=card, padx=12, pady=8)
        log_header.pack(fill="x")
        tk.Label(log_header, text="Output", font=("Inter", 11),
                 fg=muted, bg=card).pack(side="left")
        tk.Button(log_header, text="Clear", font=("Inter", 11),
                  fg=muted, bg=card, activebackground=card,
                  activeforeground=text, relief="flat", bd=0,
                  cursor="hand2", command=self._clear_log).pack(side="right")
        tk.Frame(log_frame, bg=border, height=1).pack(fill="x")
        self.log = tk.Text(log_frame, font=("Monospace", 11),
                           bg="#0d0d0d", fg="#cccccc",
                           insertbackground=text, relief="flat",
                           padx=12, pady=10, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True)
        self.log.tag_config("ok", foreground=green)
        self.log.tag_config("err", foreground=red)
        self.log.tag_config("info", foreground=amber)

    def _make_row(self, parent, card, border, amber, muted, text,
                  label, var_attr, browse_cmd, row, secret=False):
        tk.Label(parent, text=label, font=("Inter", 12),
                 fg=muted, bg=card, width=14, anchor="w").grid(
            row=row, column=0, sticky="w", pady=4)
        var = tk.StringVar()
        setattr(self, var_attr, var)
        entry = tk.Entry(parent, textvariable=var,
                         font=("Inter", 12), bg="#0f0f0f", fg=text,
                         insertbackground=text, relief="flat",
                         highlightbackground=border, highlightthickness=1,
                         show="●" if secret else "")
        entry.grid(row=row, column=1, sticky="ew", padx=(8, 8), pady=4)
        if secret:
            tk.Button(parent, text="Show", font=("Inter", 11),
                      fg=amber, bg=card, activebackground=card,
                      activeforeground=amber, relief="flat", bd=0,
                      cursor="hand2",
                      command=lambda e=entry: self._toggle_show(e)).grid(
                row=row, column=2, pady=4)
        elif browse_cmd:
            tk.Button(parent, text="Browse", font=("Inter", 11),
                      fg=amber, bg=card, activebackground=card,
                      activeforeground=amber, relief="flat", bd=0,
                      cursor="hand2", command=browse_cmd).grid(
                row=row, column=2, pady=4)

    def _toggle_show(self, entry):
        entry.config(show="" if entry.cget("show") == "●" else "●")

    def _browse_agent(self):
        path = filedialog.askopenfilename(title="Select kastyn-agent binary")
        if path:
            self.cfg["agent_path"] = path
            save_config(self.cfg)
            self.agent_status_var.set(f"Agent ready: {os.path.basename(path)}")
            self._set_agent_status(True)

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Select music folder")
        if path:
            self.music_path_var.set(path)

    def _on_mode_change(self):
        if self.mode_var.get() == "watch":
            self.interval_frame.pack(fill="x", padx=24, pady=(0, 4),
                                     before=self.run_btn.master)
            self.run_btn.config(text="▶  Start watching")
        else:
            self.interval_frame.pack_forget()
            self.run_btn.config(text="▶  Run scan")

    def _toggle_run(self):
        if self.running:
            self._stop()
        else:
            self._run()

    def _validate(self):
        agent = self.cfg.get("agent_path", "")
        if not agent or not os.path.isfile(agent):
            messagebox.showerror("Agent not ready",
                                 "The agent binary is still downloading or not found.\nPlease wait or use Browse to locate it.")
            return False
        if not self.api_token_var.get().strip():
            messagebox.showerror("Missing API key", "Enter your API key from the Kastyn dashboard.")
            return False
        if not self.station_id_var.get().strip():
            messagebox.showerror("Missing Station ID",
                                 "Enter your Station ID from the Kastyn dashboard.")
            return False
        music = self.music_path_var.get().strip()
        if not music or not os.path.isdir(music):
            messagebox.showerror("Missing folder", "Select a valid music folder.")
            return False
        return True

    def _write_env(self, agent_dir, token, station, music):
        env_path = os.path.join(agent_dir, ".env")
        with open(env_path, "w") as f:
            f.write(f"KASTYN_API_TOKEN={token}\n")
            f.write(f"KASTYN_STATION_ID={station}\n")
            f.write(f"KASTYN_LIBRARY_PATH={music}\n")
            f.write("KASTYN_API_URL=https://api.kastyn.co.uk\n")

    def _run(self):
        if not self._validate():
            return

        agent = self.cfg.get("agent_path")
        token = self.api_token_var.get().strip()
        station = self.station_id_var.get().strip()
        music = self.music_path_var.get().strip()
        mode = self.mode_var.get()
        writeback = self.writeback_var.get()

        self.cfg.update({"api_token": token, "station_id": station, "music_path": music})
        save_config(self.cfg)

        agent_dir = os.path.dirname(os.path.abspath(agent))
        self._write_env(agent_dir, token, station, music)

        try:
            os.chmod(agent, 0o755)
        except:
            pass

        cmd = [agent, mode, "-p", music]
        if writeback:
            cmd.append("-w")
        if mode == "watch":
            try:
                cmd += ["-i", str(int(self.interval_var.get()))]
            except:
                pass

        self.running = True
        self.run_btn.config(text="■  Stop", bg="#ef4444", fg="#ffffff",
                            activebackground="#dc2626")
        self._set_status("Running", self.green)
        self._log(f"$ {' '.join(cmd)}\n", "info")

        threading.Thread(target=self._stream, args=(cmd, agent_dir), daemon=True).start()

    def _stream(self, cmd, cwd):
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, cwd=cwd)
            for line in self.process.stdout:
                tag = "err" if any(w in line.lower() for w in
                                   ["error", "failed", "exception"]) else None
                self.root.after(0, self._log, line, tag)
            self.process.wait()
            self.root.after(0, self._on_done, self.process.returncode)
        except Exception as e:
            self.root.after(0, self._log, f"Error: {e}\n", "err")
            self.root.after(0, self._on_done, 1)

    def _on_done(self, returncode):
        self.running = False
        self.process = None
        mode = self.mode_var.get()
        label = "▶  Run scan" if mode == "scan" else "▶  Start watching"
        self.run_btn.config(text=label, bg=self.amber, fg="#0f0f0f",
                            activebackground="#d97706")
        if returncode == 0:
            self._set_status("Done ✓", self.green)
            self._log("\nCompleted successfully.\n", "ok")
        else:
            self._set_status(f"Exited ({returncode})", self.red)
            self._log(f"\nExited with code {returncode}\n", "err")

    def _stop(self):
        if self.process:
            self.process.terminate()
        self._on_done(0)

    def _set_status(self, msg, color):
        self.status_dot.config(fg=color)
        self.status_label.config(text=msg, fg=color)

    def _log(self, text, tag=None):
        self.log.config(state="normal")
        if tag:
            self.log.insert("end", text, tag)
        else:
            self.log.insert("end", text)
        self.log.see("end")
        self.log.config(state="disabled")

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = KastynGUI(root)
    root.mainloop()
