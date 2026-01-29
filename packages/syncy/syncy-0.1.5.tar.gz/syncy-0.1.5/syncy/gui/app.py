"""Minimal GUI scaffold (tkinter-based).

This file intentionally keeps the UI simple: two frames (Inputs, Results) and a
controller hook that will call the service layer. Full wiring and styling can
be added incrementally.
"""

from __future__ import annotations

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    import webbrowser
    import threading
except Exception:  # pragma: no cover - GUI only
    tk = None
    ttk = None
    messagebox = None
    filedialog = None

if tk is not None:
    try:
        import ttkbootstrap as tb  # type: ignore
    except Exception:  # pragma: no cover - optional styling
        tb = None
else:
    tb = None

import re
from pathlib import Path
from urllib.parse import quote_plus, urlencode

from .state import RunConfig
from .service import run_validation
from .widgets import labeled_entry, checkbox, attach_tooltip


class SyncyApp(tk.Tk):  # type: ignore[misc]
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Syncy Validator")
        self.geometry("920x620")
        self.resizable(True, True)

        self._style = None
        self._has_bootstrap = tb is not None
        self._dark_var = tk.BooleanVar(value=False)
        self._init_theme()

        # Scrollable root content
        self._canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self._vscroll = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vscroll.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._content = ttk.Frame(self._canvas)
        self._content.bind(
            "<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )
        self._content_window = self._canvas.create_window((0, 0), window=self._content, anchor="nw")
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        self._inputs = {}
        self._build_inputs()
        self._build_results()

    def _build_inputs(self) -> None:
        header = ttk.Frame(self._content)
        header.pack(fill=tk.X, padx=10, pady=(10, 0))
        self._theme_toggle = ttk.Checkbutton(
            header,
            text="Dark mode",
            variable=self._dark_var,
            command=self._toggle_theme,
        )
        if not self._has_bootstrap:
            self._theme_toggle.config(state=tk.DISABLED, text="Dark mode (install ttkbootstrap)")
        self._theme_toggle.pack(side=tk.RIGHT)

        frame = ttk.LabelFrame(self._content, text="Connections", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=10)

        # Source panel
        src_frame = ttk.LabelFrame(frame, text="Source", padding=8)
        tgt_frame = ttk.LabelFrame(frame, text="Target", padding=8)
        src_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 6))
        tgt_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(6, 0))

        self._inputs["src"] = self._build_connection_panel(src_frame, default_engine="mssql")
        self._inputs["tgt"] = self._build_connection_panel(tgt_frame, default_engine="postgresql")

        scope = ttk.LabelFrame(self._content, text="Scope and Options", padding=10)
        scope.pack(fill=tk.X, padx=10, pady=(0, 10))

        label_width = 40
        self._inputs["cfg"] = self._labeled_file_picker(
            scope, "Config file (validator.yaml, optional):", label_width=label_width
        )
        _, inc = labeled_entry(scope, "Include schemas (comma):", label_width=label_width)
        _, exc = labeled_entry(scope, "Exclude schemas (comma):", label_width=label_width)
        self._inputs["rules"] = self._labeled_file_picker(
            scope, "Rules file (optional):", label_width=label_width
        )
        validate_frame = ttk.Frame(scope)
        validate_label = ttk.Label(validate_frame, text="Validate objects:", width=label_width, anchor="w")
        validate_group = ttk.Frame(validate_frame)
        validate_label.grid(row=0, column=0, sticky="w", padx=(0, 6))
        validate_group.grid(row=0, column=1, sticky="w")
        self._inputs["validate"] = {}
        for name in ["tables", "views", "procedures", "functions", "triggers"]:
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(validate_group, text=name.title(), variable=var)
            cb.pack(side=tk.LEFT, padx=(0, 8))
            self._inputs["validate"][name] = var
        attach_tooltip(
            self._inputs["cfg"],
            "Optional validator.yaml; values are used when fields are empty.",
        )
        attach_tooltip(
            inc,
            "Comma-separated schemas to include (leave blank for all).",
        )
        attach_tooltip(
            exc,
            "Comma-separated schemas to exclude.",
        )
        attach_tooltip(
            self._inputs["rules"],
            "Optional rules YAML to override built-in rules.",
        )
        attach_tooltip(
            validate_label,
            "Select which objects to validate (tables/columns, views, procedures, functions, triggers).",
        )
        scope.columnconfigure(1, weight=1)
        for widget in scope.winfo_children():
            widget.pack(fill=tk.X, pady=3)

        self._inputs["inc"] = inc
        self._inputs["exc"] = exc

        actions = ttk.Frame(self._content)
        actions.pack(fill=tk.X, padx=10, pady=(0, 10))
        self._fail_var = tk.BooleanVar(value=True)
        cb_fail = checkbox(actions, "Fail on findings", self._fail_var)
        cb_fail.pack(side=tk.LEFT)
        attach_tooltip(
            cb_fail,
            "Fail the run if any findings exist.",
        )

        self._run_btn = ttk.Button(actions, text="Run validation", command=self._on_run)
        self._run_btn.pack(side=tk.RIGHT)

    def _build_results(self) -> None:
        frame = ttk.LabelFrame(self._content, text="Results", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self._status_lbl = ttk.Label(frame, text="Status: -")
        self._coverage_lbl = ttk.Label(frame, text="Coverage: -")
        self._sev_lbl = ttk.Label(frame, text="Findings: -")
        self._reasons_lbl = ttk.Label(frame, text="Thresholds: -")
        attach_tooltip(self._status_lbl, "Overall validation status based on findings.")
        attach_tooltip(self._coverage_lbl, "Compared objects vs total discovered.")
        attach_tooltip(self._sev_lbl, "Counts of rule hits, mismatches, and missing objects.")
        attach_tooltip(self._reasons_lbl, "Threshold evaluation for this run.")
        self._findings_box = tk.Text(frame, height=15, wrap="word")
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=self._findings_box.yview)
        self._findings_box.configure(yscrollcommand=yscroll.set)
        self._buttons = ttk.Frame(frame)
        self._open_html_btn = ttk.Button(self._buttons, text="Open HTML report", command=self._open_report_html, state=tk.DISABLED)
        self._open_json_btn = ttk.Button(self._buttons, text="Show JSON", command=self._open_report_json, state=tk.DISABLED)

        self._status_lbl.pack(anchor="w")
        self._coverage_lbl.pack(anchor="w")
        self._sev_lbl.pack(anchor="w")
        self._reasons_lbl.pack(anchor="w", pady=(0, 6))
        self._buttons.pack(fill=tk.X, pady=(0, 6))
        self._open_html_btn.pack(side=tk.LEFT, padx=(0, 6))
        self._open_json_btn.pack(side=tk.LEFT)
        self._findings_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _init_theme(self) -> None:
        if self._has_bootstrap:
            self._style = tb.Style("flatly")
        else:
            self._style = ttk.Style()
            if "clam" in self._style.theme_names():
                self._style.theme_use("clam")

    def _apply_theme(self, mode: str) -> None:
        if not self._has_bootstrap:
            return
        theme = "darkly" if mode == "dark" else "flatly"
        self._style.theme_use(theme)

    def _toggle_theme(self) -> None:
        mode = "dark" if self._dark_var.get() else "light"
        self._apply_theme(mode)

    def _on_canvas_configure(self, event) -> None:
        """Keep the content frame width in sync with the canvas."""
        self._canvas.itemconfigure(self._content_window, width=event.width)

    def _on_run(self) -> None:
        cfg = self._collect_config()
        if not cfg.validate_objects:
            if messagebox:
                messagebox.showerror("Error", "Select at least one object type to validate.")
            return
        self._run_btn.config(state=tk.DISABLED)
        self._status_lbl.config(text="Status: Running...")
        self._findings_box.delete("1.0", tk.END)
        self._open_html_btn.config(state=tk.DISABLED)
        self._open_json_btn.config(state=tk.DISABLED)
        self._last_report_dir = None

        def worker():
            try:
                result = run_validation(cfg)
            except Exception as exc:
                self.after(0, lambda: self._on_error(exc))
                return
            self.after(0, lambda: self._render_result(result))

        threading.Thread(target=worker, daemon=True).start()

    def _collect_config(self) -> RunConfig:
        def split_csv(val: str):
            return [s.strip() for s in val.split(",") if s.strip()]

        src_cfg = self._inputs["src"]
        tgt_cfg = self._inputs["tgt"]

        return RunConfig(
            source_url=self._resolve_url(src_cfg),
            target_url=self._resolve_url(tgt_cfg),
            config_path=self._inputs["cfg"].get() or None,
            include_schemas=split_csv(self._inputs["inc"].get() or ""),
            exclude_schemas=split_csv(self._inputs["exc"].get() or ""),
            rules_path=self._inputs["rules"].get() or None,
            validate_objects=[
                name for name, var in self._inputs.get("validate", {}).items() if var.get()
            ],
            min_coverage=None,
            fail_on_findings=bool(self._fail_var.get()),
        )

    def _resolve_url(self, panel_cfg) -> str:
        if panel_cfg["mode"].get() == "url":
            return panel_cfg["url"].get() or ""
        engine = panel_cfg["engine"].get()
        h = panel_cfg["host"].get().strip() or "localhost"
        p = panel_cfg["port"].get().strip()
        dbn = panel_cfg["db"].get().strip()
        u = panel_cfg["user"].get().strip()
        pw = panel_cfg["pwd"].get().strip()
        sslmode = panel_cfg.get("sslmode")
        extra_params = panel_cfg.get("params")
        if not dbn:
            if engine.startswith("mssql"):
                dbn = "master"
            elif engine.startswith("postgres"):
                dbn = "postgres"
        auth = ""
        if u:
            auth = quote_plus(u)
            if pw:
                auth = f"{auth}:{quote_plus(pw)}"
            auth = f"{auth}@"
        elif pw:
            auth = f":{quote_plus(pw)}@"
        hostpart = h
        if p:
            hostpart = f"{h}:{p}"
        path = f"/{dbn}" if dbn else ""
        params = {}
        if extra_params:
            extra_raw = extra_params.get().strip()
            if extra_raw:
                for chunk in extra_raw.split("&"):
                    if "=" not in chunk:
                        continue
                    key, value = chunk.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key:
                        params[key] = value
        if sslmode and engine.startswith("postgres"):
            ssl_val = sslmode.get().strip()
            if ssl_val:
                params["sslmode"] = ssl_val
        query = urlencode(params) if params else ""
        if query:
            return f"{engine}://{auth}{hostpart}{path}?{query}"
        return f"{engine}://{auth}{hostpart}{path}"

    def _build_connection_panel(self, parent, default_engine: str):
        mode = tk.StringVar(value="url")
        engine_var = tk.StringVar(value=default_engine)

        # Mode radio buttons
        mode_frame = ttk.Frame(parent)
        ttk.Radiobutton(mode_frame, text="Full URL", variable=mode, value="url").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Radiobutton(mode_frame, text="Build from fields", variable=mode, value="fields").pack(side=tk.LEFT)
        mode_frame.pack(anchor="w", pady=(0, 6))

        url_frame, url_entry = labeled_entry(parent, "Connection URL:")
        url_frame.pack(fill=tk.X, pady=3)

        # Field-based inputs
        engine_label = ttk.Label(parent, text="Database Engine:")
        engine_combo = ttk.Combobox(parent, textvariable=engine_var, values=["mssql", "postgresql"], state="readonly")
        host_frame, host_entry = labeled_entry(parent, "Host:", width=28)
        port_frame, port_entry = labeled_entry(parent, "Port:", width=10)
        db_frame, db_entry = labeled_entry(parent, "Database Name:", width=28)
        user_frame, user_entry = labeled_entry(parent, "Username:", width=28)
        pwd_frame, pwd_entry = labeled_entry(parent, "Password:", width=28, show="*")
        ssl_frame = ttk.Frame(parent)
        ssl_label = ttk.Label(ssl_frame, text="SSL mode:", width=18, anchor="w")
        ssl_entry = ttk.Combobox(
            ssl_frame,
            values=["", "prefer", "require", "verify-ca", "verify-full", "disable", "allow"],
            state="readonly",
            width=28,
        )
        ssl_frame.columnconfigure(1, weight=1)
        ssl_label.grid(row=0, column=0, sticky="w", padx=(0, 6))
        ssl_entry.grid(row=0, column=1, sticky="ew")
        params_frame, params_entry = labeled_entry(parent, "Extra params:", width=28)

        engine_label.pack(anchor="w")
        engine_combo.pack(fill=tk.X, pady=3)
        host_frame.pack(fill=tk.X, pady=3)
        port_frame.pack(fill=tk.X, pady=3)
        db_frame.pack(fill=tk.X, pady=3)
        user_frame.pack(fill=tk.X, pady=3)
        pwd_frame.pack(fill=tk.X, pady=3)
        ssl_frame.pack(fill=tk.X, pady=3)
        params_frame.pack(fill=tk.X, pady=3)

        def toggle_fields(*args):
            use_fields = mode.get() == "fields"
            for w in [
                engine_combo,
                host_entry,
                port_entry,
                db_entry,
                user_entry,
                pwd_entry,
                ssl_entry,
                params_entry,
            ]:
                if use_fields:
                    state = "readonly" if isinstance(w, ttk.Combobox) else tk.NORMAL
                else:
                    state = tk.DISABLED
                w.config(state=state)
            url_entry.config(state=(tk.NORMAL if not use_fields else tk.DISABLED))

        mode.trace_add("write", lambda *args: toggle_fields())
        toggle_fields()

        panel = {
            "mode": mode,
            "engine": engine_var,
            "url": url_entry,
            "host": host_entry,
            "port": port_entry,
            "db": db_entry,
            "user": user_entry,
            "pwd": pwd_entry,
            "sslmode": ssl_entry,
            "params": params_entry,
            "status": ttk.Label(parent, text="Not tested", foreground="gray"),
            "test_btn": None,
        }

        status_lbl = panel["status"]
        test_btn = ttk.Button(parent, text="Test connection", command=lambda p=panel: self._test_connection(p))
        panel["test_btn"] = test_btn

        test_btn.pack(pady=(4, 2), anchor="w")
        status_lbl.pack(anchor="w", pady=(0, 4))

        return panel

    def _labeled_file_picker(self, parent, label_text: str, label_width: int = 40):
        """Create a labeled entry with a browse button for file selection."""
        frame = ttk.Frame(parent)
        label = ttk.Label(frame, text=label_text, width=label_width, anchor="w")
        entry = ttk.Entry(frame, width=60)
        btn = ttk.Button(
            frame,
            text="Browse",
            command=lambda e=entry: self._browse_file(e),
        )
        frame.columnconfigure(1, weight=1)
        label.grid(row=0, column=0, sticky="w", padx=(0, 6))
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        btn.grid(row=0, column=2, sticky="w")
        return entry

    def _browse_file(self, entry_widget) -> None:
        if filedialog is None:
            return
        path = filedialog.askopenfilename()
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)

    def _render_result(self, result) -> None:
        self._run_btn.config(state=tk.NORMAL)
        self._status_lbl.config(text=f"Status: {result.status}")
        self._coverage_lbl.config(
            text=f"Coverage: {result.coverage_pct:.2f}% ({result.compared}/{result.total})"
        )
        self._sev_lbl.config(
            text=f"Findings: Rules {result.rule_hits} | Mismatch {result.mismatches} | Missing {result.missing}"
        )
        if result.fail_reasons:
            self._reasons_lbl.config(text="Thresholds: FAILED — " + "; ".join(result.fail_reasons))
        else:
            self._reasons_lbl.config(text="Thresholds: OK")

        self._findings_box.delete("1.0", tk.END)
        if result.findings:
            for obj_key in sorted(result.findings.keys()):
                item = result.findings.get(obj_key) or {}
                st = item.get("status", "unknown")
                rules = item.get("rules", [])
                if rules:
                    rules_str = "; ".join(
                        f"{r.get('id','?')} {r.get('desc','')}"
                        for r in rules
                    )
                else:
                    rules_str = "-"
                line = f"{obj_key}: {st} | {rules_str}\n"
                self._findings_box.insert(tk.END, line)
        else:
            self._findings_box.insert(tk.END, "No findings.\n")

        # Add a clickable prompt to open the report
        if result.report_dir:
            self._last_report_dir = result.report_dir
            self._findings_box.insert(
                tk.END, f"\nReports written to: {result.report_dir}\nDouble-click to open HTML.\n"
            )
            def _open_report(event=None):
                try:
                    webbrowser.open(Path(result.report_dir, "index.html").resolve().as_uri())
                except Exception:
                    messagebox.showerror("Error", "Could not open report.")
            self._findings_box.tag_add("report", "end-2l", "end-1l")
            self._findings_box.tag_bind("report", "<Double-Button-1>", _open_report)
            self._open_html_btn.config(state=tk.NORMAL)
            self._open_json_btn.config(state=tk.NORMAL)

    def _on_error(self, exc: Exception) -> None:
        self._run_btn.config(state=tk.NORMAL)
        if messagebox:
            messagebox.showerror("Error", str(exc))
        else:
            raise exc

    def _open_report_html(self) -> None:
        if not self._last_report_dir:
            return
        try:
            webbrowser.open(Path(self._last_report_dir, "index.html").resolve().as_uri())
        except Exception as exc:
            messagebox.showerror("Error", f"Could not open HTML report: {exc}")

    def _open_report_json(self) -> None:
        if not self._last_report_dir:
            return
        try:
            webbrowser.open(Path(self._last_report_dir, "summary.json").resolve().as_uri())
        except Exception as exc:
            messagebox.showerror("Error", f"Could not open JSON report: {exc}")

    def _test_connection(self, panel_cfg) -> None:
        """Lightweight connection test using the current panel settings."""
        url = self._resolve_url(panel_cfg)
        if not url:
            messagebox.showerror("Error", "Please provide a connection URL or fill the fields.")
            return

        status_lbl = panel_cfg.get("status")
        btn = panel_cfg.get("test_btn")
        if btn:
            btn.config(state=tk.DISABLED)
        if status_lbl:
            status_lbl.config(text="Testing...", foreground="orange")

        def worker():
            try:
                from ..core.connectors import MSSQLConnector, PostgresConnector  # type: ignore

                test_url = url
                if url.lower().startswith("postgres") and "connect_timeout" not in url.lower():
                    sep = "&" if "?" in url else "?"
                    test_url = f"{url}{sep}connect_timeout=3"
                if url.lower().startswith("mssql") and "connect_timeout" not in url.lower() and "connection timeout" not in url.lower():
                    sep = "&" if "?" in url else "?"
                    test_url = f"{url}{sep}connect_timeout=3"

                schemas = []
                if test_url.lower().startswith("mssql"):
                    conn = MSSQLConnector.from_url(test_url)
                    row = conn.fetchone("SELECT @@VERSION")
                    schemas = self._get_schemas(conn)
                    conn.close()
                elif test_url.lower().startswith("postgres"):
                    conn = PostgresConnector.from_url(test_url)
                    row = conn.fetchone("SELECT version()")
                    schemas = self._get_schemas(conn)
                    conn.close()
                else:
                    raise ValueError("Unsupported scheme. Use mssql:// or postgresql://")
                msg = "Connected"
                if row and len(row) > 0 and row[0]:
                    msg = f"Connected: {str(row[0])[:60]}..."
                self.after(0, lambda m=msg: self._set_status(status_lbl, btn, m, "green"))
                if schemas:
                    self.after(0, lambda sc=schemas: self._maybe_autofill_schemas(sc))
            except Exception as exc:
                self.after(0, lambda e=exc: self._set_status(status_lbl, btn, f"Error: {e}", "red"))

        threading.Thread(target=worker, daemon=True).start()

    def _set_status(self, lbl, btn, text: str, color: str) -> None:
        if lbl:
            display, full = self._format_status_text(text)
            lbl.config(text=display, foreground=color)
            if full != display and messagebox:
                lbl.bind("<Button-1>", lambda _e, t=full: messagebox.showerror("Details", t))
                lbl.config(cursor="hand2")
            else:
                lbl.bind("<Button-1>", "")
                lbl.config(cursor="")
        if btn:
            btn.config(state=tk.NORMAL)

    def _format_status_text(self, text: str, max_len: int = 180) -> tuple[str, str]:
        """Normalize status text to a single line and truncate long errors."""
        raw = str(text or "")
        cleaned = re.sub(r"[\r\n]+", " | ", raw)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if len(cleaned) > max_len:
            return f"{cleaned[: max_len - 1]}…", raw
        return cleaned, raw

    def _get_schemas(self, conn):
        """Return non-system schema names for the given connector."""
        try:
            from ..core.connectors import MSSQLConnector, PostgresConnector  # type: ignore
        except Exception:
            return []
        try:
            if isinstance(conn, MSSQLConnector):
                rows = conn.fetchall(
                    "SELECT name FROM sys.schemas WHERE name NOT IN ('sys','INFORMATION_SCHEMA')"
                )
            elif isinstance(conn, PostgresConnector):
                rows = conn.fetchall(
                    "SELECT nspname FROM pg_namespace WHERE nspname NOT IN ('pg_catalog','information_schema')"
                )
            else:
                return []
            return sorted(str(r[0]) for r in rows if r and r[0])
        except Exception:
            return []

    def _maybe_autofill_schemas(self, schemas):
        """Populate include schemas if empty, based on discovered schemas."""
        if not schemas:
            return
        inc_entry = self._inputs.get("inc")
        if not inc_entry:
            return
        current = inc_entry.get().strip()
        if current:
            return  # do not override user input
        inc_entry.delete(0, tk.END)
        inc_entry.insert(0, ",".join(schemas))


def main() -> None:
    if tk is None:
        raise RuntimeError("tkinter is required for the GUI.")
    app = SyncyApp()
    # Ensure canvas expands
    app._canvas.bind_all("<MouseWheel>", lambda e: app._canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    app.mainloop()


__all__ = ["SyncyApp", "main"]
