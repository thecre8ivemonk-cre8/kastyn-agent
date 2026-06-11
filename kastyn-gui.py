import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os
import json

CONFIG_FILE = os.path.expanduser("~/.kastyn_gui.json")
AGENT_NAME = "kastyn-agent-linux"

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
        self.root.geometry("700x620")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f0f0f")

        self.cfg = load_config()
        self.process = None
        self.running = False

        self._build_ui()
        self._detect_agent()

    def _detect_agent(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            self.cfg.get("agent_path", ""),
            os.path.join(script_dir, AGENT_NAME),
            os.path.join(os.path.expanduser("~/Downloads"), AGENT_NAME),
            os.path.join(os.path.expanduser("~"), AGENT_NAME),
        ]
        for p in candidates:
            if p and os.path.isfile(p):
                self.agent_path_var.set(p)
                self.cfg["agent_path"] = p
                return

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

        # Config card
        cfg_frame = tk.Frame(self.root, bg=card, highlightbackground=border,
                             highlightthickness=1)
        cfg_frame.pack(fill="x", padx=24, pady=(0, 12))
        inner = tk.Frame(cfg_frame, bg=card, padx=20, pady=16)
        inner.pack(fill="x")
        inner.columnconfigure(1, weight=1)

        # Agent binary
        self._make_row(inner, card, border, amber, muted, text,
                       "Agent binary", "agent_path_var", self._browse_agent, 0, secret=False)
        tk.Frame(inner, bg=border, height=1).grid(row=1, column=0, columnspan=3, sticky="ew", pady=8)

        # API token
        self._make_row(inner, card, border, amber, muted, text,
                       "API key", "api_token_var", None, 2, secret=True)
        tk.Frame(inner, bg=border, height=1).grid(row=3, column=0, columnspan=3, sticky="ew", pady=8)

        # Station ID
        self._make_row(inner, card, border, amber, muted, text,
                       "Station ID", "station_id_var", None, 4, secret=False)
        tk.Frame(inner, bg=border, height=1).grid(row=5, column=0, columnspan=3, sticky="ew", pady=8)

        # Music folder
        self._make_row(inner, card, border, amber, muted, text,
                       "Music folder", "music_path_var", self._browse_folder, 6, secret=False)

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
                       variable=self.writeback_var,
                       font=("Inter", 12), fg=muted, bg=bg,
                       selectcolor=bg, activebackground=bg,
                       activeforeground=text,
                       highlightthickness=0).pack(side="left", padx=(20, 0))

        # Watch interval (hidden by default)
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
            setattr(self, f"_{var_attr}_entry", entry)
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
            self.agent_path_var.set(path)
            self.cfg["agent_path"] = path

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
        agent = self.agent_path_var.get().strip()
        token = self.api_token_var.get().strip()
        station = self.station_id_var.get().strip()
        music = self.music_path_var.get().strip()
        if not agent or not os.path.isfile(agent):
            messagebox.showerror("Missing agent",
                                 "Can't find the kastyn-agent binary.\nUse Browse to locate it.")
            return False
        if not token:
            messagebox.showerror("Missing API key", "Enter your API key from the Kastyn dashboard.")
            return False
        if not station:
            messagebox.showerror("Missing Station ID",
                                 "Enter your Station ID.\nFind it in the Kastyn dashboard under your station settings.")
            return False
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

        agent = self.agent_path_var.get().strip()
        token = self.api_token_var.get().strip()
        station = self.station_id_var.get().strip()
        music = self.music_path_var.get().strip()
        mode = self.mode_var.get()
        writeback = self.writeback_var.get()

        self.cfg.update({"api_token": token, "station_id": station,
                         "music_path": music, "agent_path": agent})
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
                mins = int(self.interval_var.get())
                cmd += ["-i", str(mins)]
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
