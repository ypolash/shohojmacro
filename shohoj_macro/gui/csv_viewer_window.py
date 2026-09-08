import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from shohoj_macro.gui.glass_theme import GlassTheme
from shohoj_macro.core.csv_engine import CSVDataEngine

class CSVViewerWindow(ctk.CTkToplevel):
    """A live spreadsheet-like viewer for CSV data and execution status."""
    def __init__(self, master, csv_engine: CSVDataEngine, **kwargs):
        super().__init__(master, **kwargs)
        self.csv_engine = csv_engine
        
        self.title("Live CSV Data Viewer")
        self.geometry("900x600")
        self.minsize(600, 400)
        self.configure(fg_color=GlassTheme.BG_DARK)
        
        # Bring to front
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        self._setup_styles()
        self._build_ui()
        self._load_data()
        
        # Register callback for live updates
        self._old_callback = self.csv_engine.on_status_change
        self.csv_engine.on_status_change = self._on_status_change
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("default")
        
        style.configure("LiveViewer.Treeview",
            background=GlassTheme.CARD_BG,
            foreground=GlassTheme.TEXT_PRIMARY,
            fieldbackground=GlassTheme.CARD_BG,
            rowheight=30,
            borderwidth=0,
            font=("Inter", 10)
        )
        
        style.map("LiveViewer.Treeview",
            background=[("selected", GlassTheme.ACCENT_CYAN)],
            foreground=[("selected", "#000000")]
        )
        
        style.configure("LiveViewer.Treeview.Heading",
            background=GlassTheme.CARD_BG_SECONDARY,
            foreground=GlassTheme.TEXT_MUTED,
            borderwidth=1,
            relief="flat",
            font=("Inter", 10, "bold")
        )
        
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(header, text="📊 Live Execution Tracker", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        
        # Controls
        self.switch_autoscroll = ctk.CTkSwitch(header, text="Auto-Scroll", progress_color=GlassTheme.ACCENT_CYAN)
        self.switch_autoscroll.pack(side="right")
        self.switch_autoscroll.select()
        
        # Treeview Frame
        tv_frame = ctk.CTkFrame(self, fg_color="transparent")
        tv_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(tv_frame)
        y_scroll.pack(side="right", fill="y")
        x_scroll = ttk.Scrollbar(tv_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")
        
        self.tree = ttk.Treeview(tv_frame, style="LiveViewer.Treeview", yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.pack(fill="both", expand=True)
        
        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)
        
        # Tags for colors
        self.tree.tag_configure("status_IN PROGRESS", background="#3b3b11", foreground="#ffea00")
        self.tree.tag_configure("status_DONE", background="#113b22", foreground="#00ff88")
        self.tree.tag_configure("status_ERROR", background="#3b1111", foreground="#ff4444")
        
    def _load_data(self):
        if not self.csv_engine.is_loaded:
            return
            
        columns = ["Row"] + self.csv_engine.headers + ["Status"]
        self.tree["columns"] = columns
        
        self.tree.heading("#0", text="", anchor="w")
        self.tree.column("#0", width=0, stretch=False)
        
        for col in columns:
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, width=120, anchor="w")
            
        self.tree.column("Row", width=50, anchor="center")
        self.tree.column("Status", width=150, anchor="w")
        
        for idx, row_dict in enumerate(self.csv_engine.rows):
            # idx in rows is 0-indexed, which corresponds to Row 2 in Excel (due to headers)
            excel_row = idx + 2
            status = row_dict.get("_macro_status", "Pending")
            
            values = [str(excel_row)]
            for h in self.csv_engine.headers:
                values.append(row_dict.get(h, ""))
            values.append(status)
            
            tag = ""
            if "IN PROGRESS" in status:
                tag = "status_IN PROGRESS"
            elif "DONE" in status:
                tag = "status_DONE"
            elif "ERROR" in status:
                tag = "status_ERROR"
                
            self.tree.insert("", "end", iid=str(idx), values=values, tags=(tag,))
            
    def _on_status_change(self, row_idx: int, status: str):
        def update_ui():
            if not self.tree.exists(str(row_idx)):
                return
                
            # Get current values, update the last one (Status)
            values = list(self.tree.item(str(row_idx), "values"))
            if values:
                values[-1] = status
                
                tag = ""
                if "IN PROGRESS" in status:
                    tag = "status_IN PROGRESS"
                elif "DONE" in status:
                    tag = "status_DONE"
                elif "ERROR" in status:
                    tag = "status_ERROR"
                    
                self.tree.item(str(row_idx), values=values, tags=(tag,))
                
                if self.switch_autoscroll.get():
                    self.tree.see(str(row_idx))
                    self.tree.selection_set(str(row_idx))
                    
        self.after(0, update_ui)
        
        # Pass through to old callback if it existed
        if self._old_callback:
            self._old_callback(row_idx, status)
            
    def _on_close(self):
        self.csv_engine.on_status_change = self._old_callback
        self.destroy()
