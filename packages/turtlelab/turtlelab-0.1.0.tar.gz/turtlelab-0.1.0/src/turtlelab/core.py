"""
================= Interactive Turtle Lab =================
Loads turtle code from external Python files and executes.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import traceback
import turtle
import os


class TurtleLab:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Interactive Turtle Lab - File Based")
        self.root.state('zoomed')

        self.current_file = None
        self.file_content = ""
        self.code_panel_visible = True

        self._build_ui()
        self._create_renderer()

    # -------- UI --------
    def _build_ui(self):
        self.main = ttk.Frame(self.root)
        self.main.pack(fill=tk.BOTH, expand=True)

        # Left panel: File selection + Code display
        self.left = ttk.Frame(self.main)
        self.left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

        # File selection area
        file_frame = ttk.LabelFrame(self.left, text="File", padding=8)
        file_frame.pack(fill=tk.X, padx=8, pady=6)

        ttk.Button(file_frame, text="Browse...", command=self.browse_file).pack(fill=tk.X)
        
        self.file_label = ttk.Label(file_frame, text="No file selected", foreground="gray")
        self.file_label.pack(fill=tk.X, pady=4)

        # Code display header
        code_header = ttk.Frame(self.left)
        code_header.pack(fill=tk.X, padx=8, pady=(6, 2))
        ttk.Label(code_header, text="Code Editor", font=(None, 11, "bold")).pack(side=tk.LEFT)

        # Code display with scrollbar
        code_frame = ttk.Frame(self.left)
        code_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.code_display = tk.Text(code_frame, font=("Consolas", 10), wrap=tk.WORD, height=20, undo=True)
        self.code_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(code_frame, orient=tk.VERTICAL, command=self.code_display.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_display.config(yscrollcommand=scrollbar.set)

        self.code_display.bind("<Return>", self._smart_indent)
        self.code_display.bind("<Tab>", self._tab)
        self.code_display.bind("<Control-Return>", lambda e: self.run_code())

        # Right panel: Canvas + Controls
        self.right = ttk.Frame(self.main)
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(self.right, text="Canvas", font=(None, 11, "bold")).pack(anchor=tk.W, padx=8, pady=6)

        self.canvas = tk.Canvas(self.right, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Control buttons (below canvas)
        controls = ttk.Frame(self.right)
        controls.pack(fill=tk.X, padx=8, pady=6)

        ttk.Button(controls, text="Run", command=self.run_code).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(controls, text="Clear", command=self.clear).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        ttk.Button(controls, text="Toggle Code Editor", command=self.toggle_code_panel).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

        # Status bar
        self.status = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)

        # Shortcuts
        self.root.bind("<Control-Return>", lambda e: self.run_code())

    # -------- Renderer --------
    def _create_renderer(self):
        self.canvas.delete("all")

        self.screen = turtle.TurtleScreen(self.canvas)
        self.screen.tracer(0)

        self.t = turtle.RawTurtle(self.screen)
        self.t.speed(0)
        self.t.shape("turtle")
        self.t.penup()
        self.t.setposition(150, -150)
        self.t.pendown()

        self.exec_globals = {
            "t": self.t,
            "screen": self.screen,
            "__builtins__": __builtins__,
        }

        self.screen.update()

    # -------- File Operations --------
    def browse_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
            initialdir=os.getcwd()
        )
        
        if filename:
            self.load_file(filename)

    def read_file(self, filepath: str):
        with open(filepath, 'r') as f:
            return f.read()

    def load_file(self, filepath: str):
        try:
            self.file_content = self.read_file(filepath)
            self.current_file = filepath
            self.file_label.config(text=os.path.basename(filepath), foreground="black")
            self.code_display.delete("1.0", tk.END)
            self.code_display.insert(tk.END, self.file_content)
            self.status.set(f"Loaded: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file:\n{str(e)}")
            self.status.set("Error loading file")

    # -------- Execution --------
    def run_code(self):
        code = self.code_display.get("1.0", tk.END)
        
        if not code.strip():
            messagebox.showwarning("No Code", "Please enter some code first.")
            return

        if "import turtle" in code:
            messagebox.showerror(
                "Invalid Code",
                "Do NOT import turtle.\nUse the provided `t` and `screen`."
            )
            return

        self.status.set("Running…")
        self._create_renderer()

        try:
            exec(code, self.exec_globals)
            self.screen.update()
            self.status.set("Execution complete")
        except Exception:
            messagebox.showerror(
                "Execution Error",
                traceback.format_exc()
            )
            self.status.set("Error")

    # -------- UI Toggle --------
    def toggle_code_panel(self):
        self.code_panel_visible = not self.code_panel_visible
        if self.code_panel_visible:
            self.left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, before=self.right)
        else:
            self.left.pack_forget()

    def _smart_indent(self, event):
        """Smart indentation: when Enter is pressed, indent the next line to match the previous line's indentation."""
        self.code_display.insert(tk.INSERT, "\n")
        line_start = self.code_display.get("insert-1c linestart", "insert-1c")
        indent = len(line_start) - len(line_start.lstrip())
        self.code_display.insert(tk.INSERT, " " * indent)
        return "break"
    
    def _tab(self, event):
        self.code_display.insert(tk.INSERT, "    ")
        return "break"

    # -------- Clear --------
    def clear(self):
        self._create_renderer()
        self.status.set("Cleared")


def main():
    root = tk.Tk()
    TurtleLab(root)
    root.mainloop()

#main()