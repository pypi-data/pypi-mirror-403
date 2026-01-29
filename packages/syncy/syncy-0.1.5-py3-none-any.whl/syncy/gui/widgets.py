"""Reusable widget helpers for the GUI layer."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover - GUI only
    tk = None
    ttk = None


def labeled_entry(parent, text: str, show: str = "", width: int = 40, label_width: int = 18):
    """Create a labeled text entry with aligned fields."""
    frame = ttk.Frame(parent)
    label = ttk.Label(frame, text=text, width=label_width, anchor="w")
    entry = ttk.Entry(frame, width=width, show=show)
    frame.columnconfigure(1, weight=1)
    label.grid(row=0, column=0, sticky="w", padx=(0, 6))
    entry.grid(row=0, column=1, sticky="ew")
    return frame, entry


def checkbox(parent, text: str, var):
    """Create a checkbox bound to a Tk variable."""
    cb = ttk.Checkbutton(parent, text=text, variable=var)
    return cb


class _Tooltip:
    def __init__(self, widget, text: str, delay_ms: int = 500) -> None:
        self._widget = widget
        self._text = text
        self._delay_ms = delay_ms
        self._tip = None
        self._after_id = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event=None) -> None:
        self._schedule()

    def _on_leave(self, _event=None) -> None:
        self._cancel()
        self._hide()

    def _schedule(self) -> None:
        self._cancel()
        self._after_id = self._widget.after(self._delay_ms, self._show)

    def _cancel(self) -> None:
        if self._after_id:
            try:
                self._widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self) -> None:
        if self._tip or not self._text:
            return
        x = self._widget.winfo_rootx() + 10
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip,
            text=self._text,
            justify=tk.LEFT,
            background="#1f1f1f",
            foreground="#ffffff",
            relief=tk.SOLID,
            borderwidth=1,
        )
        label.pack(ipadx=6, ipady=3)

    def _hide(self) -> None:
        if self._tip:
            self._tip.destroy()
            self._tip = None


def attach_tooltip(widget, text: str, delay_ms: int = 500):
    """Attach a tooltip to a widget if Tk is available."""
    if tk is None:
        return None
    return _Tooltip(widget, text, delay_ms=delay_ms)

