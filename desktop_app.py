import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import webbrowser
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.base import AVAILABLE_MODELS, DEFAULT_MODEL
from agents.pipeline import PIPELINE_STEPS, PipelineAgent, run_pipeline
from utils.document_parser import parse_document_from_path
from utils.html_generator import generate_proposal_html

BG = "#1e1e2e"
BG_LIGHT = "#2a2a3d"
BG_INPUT = "#313145"
FG = "#cdd6f4"
FG_DIM = "#6c7086"
ACCENT = "#89b4fa"
GREEN = "#a6e3a1"
RED = "#f38ba8"
YELLOW = "#f9e2af"
FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_MONO = ("Consolas", 10)
FONT_SMALL = ("Segoe UI", 9)


class RFPAgentApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RFP Agent Suite  -  Powered by Factory AI Droid")
        self.root.geometry("1280x820")
        self.root.minsize(960, 600)
        self.root.configure(bg=BG)

        self.rfp_text = ""
        self.rfp_filename = ""
        self.kb_texts = []
        self.kb_filenames = []
        self.step_outputs = {}
        self.running = False
        self.cancel_flag = False

        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        self.title_var = tk.StringVar(value="Proposal Response")
        self.status_var = tk.StringVar(value="Ready")
        self.mode_var = tk.StringVar(value="Full Pipeline")
        self.step_var = tk.StringVar(value=PIPELINE_STEPS[0]["name"])

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        top = tk.Frame(self.root, bg=BG, height=50)
        top.pack(fill=tk.X, padx=0, pady=0)
        top.pack_propagate(False)
        tk.Label(top, text="  RFP Agent Suite", font=FONT_TITLE,
                 bg=BG, fg=ACCENT).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Label(top, text="Factory AI Droid", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side=tk.LEFT, padx=4)

        body = tk.PanedWindow(self.root, orient=tk.HORIZONTAL,
                              bg=BG, sashwidth=4, bd=0)
        body.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        sidebar = tk.Frame(body, bg=BG_LIGHT, width=300)
        sidebar.pack_propagate(False)
        body.add(sidebar, minsize=260)
        self._build_sidebar(sidebar)

        main_frame = tk.Frame(body, bg=BG)
        body.add(main_frame, minsize=500)
        self._build_main(main_frame)

        status_bar = tk.Frame(self.root, bg=BG_INPUT, height=28)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        tk.Label(status_bar, textvariable=self.status_var, font=FONT_SMALL,
                 bg=BG_INPUT, fg=FG_DIM, anchor="w").pack(side=tk.LEFT, padx=10)

    def _build_sidebar(self, parent):
        pad = {"padx": 12, "pady": (10, 2)}
        pad_btn = {"padx": 12, "pady": 4}

        tk.Label(parent, text="1. RFP Document", font=FONT_BOLD,
                 bg=BG_LIGHT, fg=FG).pack(anchor="w", **pad)
        self.rfp_label = tk.Label(parent, text="No file loaded",
                                  font=FONT_SMALL, bg=BG_LIGHT, fg=FG_DIM,
                                  wraplength=250, anchor="w", justify="left")
        self.rfp_label.pack(anchor="w", padx=12)
        tk.Button(parent, text="Upload RFP", command=self.upload_rfp,
                  bg=ACCENT, fg=BG, font=FONT, bd=0, cursor="hand2",
                  activebackground="#b4d0fb").pack(fill=tk.X, **pad_btn)

        tk.Label(parent, text="2. Knowledge Base", font=FONT_BOLD,
                 bg=BG_LIGHT, fg=FG).pack(anchor="w", **pad)
        self.kb_label = tk.Label(parent, text="No files loaded",
                                 font=FONT_SMALL, bg=BG_LIGHT, fg=FG_DIM,
                                 wraplength=250, anchor="w", justify="left")
        self.kb_label.pack(anchor="w", padx=12)
        tk.Button(parent, text="Upload Knowledge Base", command=self.upload_kb,
                  bg=BG_INPUT, fg=FG, font=FONT, bd=0, cursor="hand2",
                  activebackground=BG).pack(fill=tk.X, **pad_btn)

        sep = tk.Frame(parent, bg=FG_DIM, height=1)
        sep.pack(fill=tk.X, padx=12, pady=10)

        tk.Label(parent, text="3. Model", font=FONT_BOLD,
                 bg=BG_LIGHT, fg=FG).pack(anchor="w", **pad)
        model_menu = ttk.Combobox(parent, textvariable=self.model_var,
                                  values=AVAILABLE_MODELS, state="readonly")
        model_menu.pack(fill=tk.X, padx=12, pady=4)

        tk.Label(parent, text="4. Mode", font=FONT_BOLD,
                 bg=BG_LIGHT, fg=FG).pack(anchor="w", **pad)
        modes = ["Full Pipeline", "Single Agent"]
        for m in modes:
            tk.Radiobutton(parent, text=m, variable=self.mode_var, value=m,
                           bg=BG_LIGHT, fg=FG, selectcolor=BG_INPUT,
                           activebackground=BG_LIGHT, activeforeground=FG,
                           font=FONT, command=self._on_mode_change
                           ).pack(anchor="w", padx=16)

        self.step_frame = tk.Frame(parent, bg=BG_LIGHT)
        self.step_frame.pack(fill=tk.X, padx=12, pady=4)
        step_names = [s["name"] for s in PIPELINE_STEPS]
        self.step_menu = ttk.Combobox(self.step_frame, textvariable=self.step_var,
                                      values=step_names, state="readonly")
        self.step_menu.pack(fill=tk.X)
        self.step_frame.pack_forget()

        tk.Label(parent, text="5. Proposal Title", font=FONT_BOLD,
                 bg=BG_LIGHT, fg=FG).pack(anchor="w", **pad)
        tk.Entry(parent, textvariable=self.title_var, font=FONT,
                 bg=BG_INPUT, fg=FG, insertbackground=FG, bd=0,
                 relief="flat").pack(fill=tk.X, padx=12, pady=4, ipady=4)

        sep2 = tk.Frame(parent, bg=FG_DIM, height=1)
        sep2.pack(fill=tk.X, padx=12, pady=10)

        self.run_btn = tk.Button(parent, text="  Run Pipeline  ",
                                 command=self.run_pipeline, bg=GREEN, fg=BG,
                                 font=FONT_BOLD, bd=0, cursor="hand2",
                                 activebackground="#c6f6d5")
        self.run_btn.pack(fill=tk.X, **pad_btn)

        self.cancel_btn = tk.Button(parent, text="  Cancel  ",
                                    command=self.cancel, bg=RED, fg=BG,
                                    font=FONT, bd=0, cursor="hand2",
                                    state="disabled")
        self.cancel_btn.pack(fill=tk.X, **pad_btn)

        tk.Button(parent, text="  Save HTML Proposal  ",
                  command=self.save_html, bg=YELLOW, fg=BG,
                  font=FONT, bd=0, cursor="hand2",
                  activebackground="#fef3c7").pack(fill=tk.X, padx=12, pady=(4, 2))

        tk.Button(parent, text="  Preview in Browser  ",
                  command=self.preview_html, bg=BG_INPUT, fg=FG,
                  font=FONT, bd=0, cursor="hand2").pack(fill=tk.X, padx=12, pady=2)

        tk.Button(parent, text="Clear Output",
                  command=self.clear_output, bg=BG_INPUT, fg=FG_DIM,
                  font=FONT_SMALL, bd=0, cursor="hand2"
                  ).pack(fill=tk.X, padx=12, pady=(8, 4))

    def _build_main(self, parent):
        self.output_text = tk.Text(parent, wrap=tk.WORD, font=FONT_MONO,
                                   bg=BG, fg=FG, insertbackground=FG,
                                   bd=0, padx=16, pady=12,
                                   selectbackground=ACCENT,
                                   selectforeground=BG, spacing3=4)
        scrollbar = ttk.Scrollbar(parent, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        self.output_text.tag_configure("step_header", foreground=ACCENT,
                                       font=("Segoe UI", 12, "bold"))
        self.output_text.tag_configure("status", foreground=GREEN,
                                       font=FONT_BOLD)
        self.output_text.tag_configure("error", foreground=RED, font=FONT_BOLD)
        self.output_text.tag_configure("dim", foreground=FG_DIM, font=FONT_SMALL)
        self.output_text.tag_configure("user_msg", foreground=YELLOW,
                                       font=FONT_BOLD)

        input_frame = tk.Frame(parent, bg=BG_INPUT, height=50)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=0, pady=0)
        input_frame.pack_propagate(False)

        self.input_entry = tk.Entry(input_frame, font=FONT, bg=BG_INPUT,
                                    fg=FG, insertbackground=FG, bd=0,
                                    relief="flat")
        self.input_entry.insert(0, "Generate a complete proposal for this RFP")
        self.input_entry.pack(fill=tk.BOTH, expand=True, side=tk.LEFT,
                              padx=12, pady=10)
        self.input_entry.bind("<Return>", lambda e: self.run_pipeline())

        tk.Button(input_frame, text=" Send ", command=self.run_pipeline,
                  bg=ACCENT, fg=BG, font=FONT_BOLD, bd=0,
                  cursor="hand2").pack(side=tk.RIGHT, padx=8, pady=8)

        self._append_output("Welcome to RFP Agent Suite\n", "step_header")
        self._append_output(
            "All LLM requests are routed through Factory AI Droid CLI.\n"
            "No external API keys required.\n\n", "dim")
        self._append_output(
            "Steps:\n"
            "1. Upload your RFP document (PDF / PPTX / TXT)\n"
            "2. Optionally upload knowledge base files\n"
            "3. Pick a model and click Run Pipeline\n"
            "4. Save or preview the HTML proposal when done\n\n", "dim")

    # -------------------------------------------------------------- Actions
    def _on_mode_change(self):
        if self.mode_var.get() == "Single Agent":
            self.step_frame.pack(fill=tk.X, padx=12, pady=4)
            self.run_btn.configure(text="  Run Agent  ")
        else:
            self.step_frame.pack_forget()
            self.run_btn.configure(text="  Run Pipeline  ")

    def upload_rfp(self):
        path = filedialog.askopenfilename(
            title="Select RFP Document",
            filetypes=[("Supported files", "*.pdf *.pptx *.ppt *.txt"),
                       ("PDF", "*.pdf"), ("PowerPoint", "*.pptx *.ppt"),
                       ("Text", "*.txt"), ("All", "*.*")])
        if not path:
            return
        try:
            self.rfp_text = parse_document_from_path(path)
            self.rfp_filename = os.path.basename(path)
            self.rfp_label.configure(
                text=f"{self.rfp_filename}\n({len(self.rfp_text):,} chars)", fg=GREEN)
            self._append_output(f"Loaded RFP: {self.rfp_filename}\n", "status")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse file:\n{e}")

    def upload_kb(self):
        paths = filedialog.askopenfilenames(
            title="Select Knowledge Base Files",
            filetypes=[("Supported files", "*.pdf *.pptx *.ppt *.txt *.md *.csv"),
                       ("All", "*.*")])
        if not paths:
            return
        self.kb_texts = []
        self.kb_filenames = []
        for p in paths:
            try:
                self.kb_texts.append(parse_document_from_path(p))
                self.kb_filenames.append(os.path.basename(p))
            except Exception as e:
                self._append_output(f"Skipped {os.path.basename(p)}: {e}\n", "error")
        self.kb_label.configure(
            text="\n".join(self.kb_filenames) or "No files loaded",
            fg=GREEN if self.kb_filenames else FG_DIM)
        self._append_output(f"Loaded {len(self.kb_filenames)} KB file(s)\n", "status")

    def run_pipeline(self):
        if self.running:
            return
        if not self.rfp_text:
            messagebox.showwarning("No RFP", "Upload an RFP document first.")
            return

        user_prompt = self.input_entry.get().strip()
        if not user_prompt:
            messagebox.showwarning("No Prompt", "Enter instructions in the input bar.")
            return

        self.running = True
        self.cancel_flag = False
        self.run_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")

        self._append_output(f"\nYou: {user_prompt}\n\n", "user_msg")

        thread = threading.Thread(
            target=self._pipeline_worker,
            args=(user_prompt,),
            daemon=True)
        thread.start()

    def _pipeline_worker(self, user_prompt: str):
        model = self.model_var.get()
        mode = self.mode_var.get()

        try:
            if mode == "Single Agent":
                self._run_single_agent(model, user_prompt)
            else:
                self._run_full_pipeline(model, user_prompt)
        except Exception as e:
            self._safe_append(f"\n[Error] {e}\n", "error")
        finally:
            self.running = False
            self.root.after(0, lambda: self.run_btn.configure(state="normal"))
            self.root.after(0, lambda: self.cancel_btn.configure(state="disabled"))

    def _run_single_agent(self, model: str, user_prompt: str):
        step_name = self.step_var.get()
        step_cfg = next(s for s in PIPELINE_STEPS if s["name"] == step_name)

        self._safe_append(f"--- Running: {step_name} ---\n", "step_header")
        self._set_status(f"Running {step_name}...")

        agent = PipelineAgent(model, step_cfg)
        context = f"RFP DOCUMENT:\n{self.rfp_text}"
        if self.kb_texts:
            context += "\n\nKNOWLEDGE BASE:\n" + "\n---\n".join(self.kb_texts)
        if self.step_outputs:
            prev = "\n\n".join(f"[{n}]: {t}" for n, t in self.step_outputs.items())
            context += f"\n\nPREVIOUS STEPS:\n{prev}"

        result = agent.run(f"{user_prompt}\n\nGenerate the '{step_name}' section.", context)
        self.step_outputs[step_name] = result
        self._safe_append(f"{result}\n\n", None)
        self._set_status(f"{step_name} complete.")

    def _run_full_pipeline(self, model: str, user_prompt: str):
        self._safe_append("Starting 7-step pipeline via droid CLI...\n\n", "status")

        def on_progress(i, step, output):
            if self.cancel_flag:
                return
            if i == -1:
                self._safe_append("RFP document summarized.\n\n", "dim")
                self._set_status("RFP summarized. Running pipeline...")
                return
            self._safe_append(
                f"\n{'='*60}\n  Step {i+1}/7: {step['name']}\n{'='*60}\n\n",
                "step_header")
            self._safe_append(f"{output}\n", None)
            self._set_status(f"Step {i+1}/7 complete: {step['name']}")

        results = run_pipeline(
            model=model,
            rfp_text=self.rfp_text,
            kb_texts=self.kb_texts,
            user_prompt=user_prompt,
            progress_callback=on_progress,
        )

        self.step_outputs = results
        self._safe_append(
            "\n\nPipeline complete! Use 'Save HTML' or 'Preview in Browser'.\n",
            "status")
        self._set_status("Pipeline complete. Ready to export.")

    def cancel(self):
        self.cancel_flag = True
        self._set_status("Cancelling...")

    def clear_output(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.step_outputs = {}

    def save_html(self):
        if not self.step_outputs:
            messagebox.showwarning("No Output", "Run the pipeline first.")
            return
        html = generate_proposal_html(self.step_outputs, self.title_var.get())
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html")],
            initialfile=f"{self.title_var.get().replace(' ', '_')}.html")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            self._append_output(f"\nSaved: {path}\n", "status")
            messagebox.showinfo("Saved", f"Proposal saved to:\n{path}")

    def preview_html(self):
        if not self.step_outputs:
            messagebox.showwarning("No Output", "Run the pipeline first.")
            return
        html = generate_proposal_html(self.step_outputs, self.title_var.get())
        fd, tmp = tempfile.mkstemp(suffix=".html", prefix="rfp_preview_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open(f"file:///{tmp}")

    # ------------------------------------------------------------ Helpers
    def _append_output(self, text: str, tag=None):
        self.output_text.configure(state="normal")
        if tag:
            self.output_text.insert(tk.END, text, tag)
        else:
            self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)

    def _safe_append(self, text: str, tag=None):
        self.root.after(0, lambda: self._append_output(text, tag))

    def _set_status(self, text: str):
        self.root.after(0, lambda: self.status_var.set(text))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = RFPAgentApp()
    app.run()
