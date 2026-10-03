"""HexAscii GUI — text ↔ bytes in base 2/8/10/16."""

from __future__ import annotations

import ctypes
import tkinter as tk

from . import __version__
from .engine import from_bytes_view, to_bytes_view
from .instance import WINDOW_TITLE

BG = "#111111"
FG = "#ffffff"
MUTED = "#999999"
CARD = "#1a1a1a"
OK = "#86efac"
BAD = "#fca5a5"
ACCENT = "#93c5fd"

BASE_LABELS = (
    (2, "2 · двоичная"),
    (8, "8 · восьмеричная"),
    (10, "10 · десятичная"),
    (16, "16 · hex"),
)


class HexAsciiApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry("900x600")
        self.minsize(680, 460)
        self.configure(bg=BG)

        self._spaced = tk.BooleanVar(value=True)
        self._upper = tk.BooleanVar(value=True)
        self._mode = "to_bytes"  # to_bytes | to_text
        self._base = 16
        self._mode_btns: dict[str, tk.Label] = {}
        self._base_btns: dict[int, tk.Label] = {}
        self._after_id: str | None = None

        pad = tk.Frame(self, bg=BG)
        pad.pack(fill="both", expand=True, padx=22, pady=18)

        head = tk.Frame(pad, bg=BG)
        head.pack(fill="x")
        tk.Label(head, text="HexAscii", bg=BG, fg=FG, font=("Segoe UI Semibold", 18)).pack(
            side="left"
        )
        tk.Label(
            head,
            text="неделя 6 · Текст · день 41",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="right")

        tk.Label(
            pad,
            text="Текст ↔ байты: 2 / 8 / 10 / 16",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 10))

        modes = tk.Frame(pad, bg=BG)
        modes.pack(fill="x")
        for key, label in (("to_bytes", "Текст → байты"), ("to_text", "Байты → текст")):
            btn = tk.Label(
                modes,
                text=label,
                bg="#333333",
                fg=FG,
                font=("Segoe UI", 9),
                padx=12,
                pady=6,
                cursor="hand2",
            )
            btn.pack(side="left", padx=(0, 6))
            btn.bind("<Button-1>", lambda _e, k=key: self.set_mode(k))
            self._mode_btns[key] = btn

        bases = tk.Frame(pad, bg=BG)
        bases.pack(fill="x", pady=(8, 0))
        tk.Label(bases, text="система:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(
            side="left", padx=(0, 8)
        )
        for base, label in BASE_LABELS:
            btn = tk.Label(
                bases,
                text=label,
                bg="#333333",
                fg=FG,
                font=("Segoe UI", 9),
                padx=10,
                pady=5,
                cursor="hand2",
            )
            btn.pack(side="left", padx=(0, 6))
            btn.bind("<Button-1>", lambda _e, b=base: self.set_base(b))
            self._base_btns[base] = btn

        opts = tk.Frame(pad, bg=BG)
        opts.pack(fill="x", pady=(8, 0))
        self._opt_spaced = tk.Checkbutton(
            opts,
            text="пробелы между байтами",
            variable=self._spaced,
            bg=BG,
            fg=FG,
            selectcolor=CARD,
            activebackground=BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
            command=self.convert,
        )
        self._opt_spaced.pack(side="left", padx=(0, 16))
        self._opt_upper = tk.Checkbutton(
            opts,
            text="ВЕРХНИЙ hex",
            variable=self._upper,
            bg=BG,
            fg=FG,
            selectcolor=CARD,
            activebackground=BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
            command=self.convert,
        )
        self._opt_upper.pack(side="left")

        footer = tk.Frame(pad, bg=BG)
        footer.pack(side="bottom", fill="x")
        row = tk.Frame(footer, bg=BG)
        row.pack(side="bottom", fill="x", pady=(10, 0))
        self._mk_btn(row, "Из буфера", self.from_clip).pack(side="left")
        self._mk_btn(row, "В буфер", self.to_clip, accent=True).pack(side="left", padx=(8, 0))
        self._mk_btn(row, "Очистить", self.clear_all).pack(side="left", padx=(8, 0))
        tk.Label(
            row,
            text=f"v{__version__} · darkshade",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="right")

        self._status = tk.Label(
            footer,
            text="",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 11),
            anchor="w",
            pady=4,
        )
        self._status.pack(side="bottom", fill="x")

        panes = tk.Frame(pad, bg=BG)
        panes.pack(fill="both", expand=True, pady=(12, 0))
        panes.columnconfigure(0, weight=1)
        panes.columnconfigure(1, weight=0)
        panes.columnconfigure(2, weight=1)
        panes.rowconfigure(1, weight=1)

        self._in_cap = tk.Label(panes, text="ввод", bg=BG, fg=MUTED, font=("Segoe UI", 10))
        self._in_cap.grid(row=0, column=0, sticky="w")
        self._out_cap = tk.Label(panes, text="вывод", bg=BG, fg=MUTED, font=("Segoe UI", 10))
        self._out_cap.grid(row=0, column=2, sticky="w")

        self._inp = tk.Text(
            panes,
            height=14,
            bg=CARD,
            fg=FG,
            insertbackground=FG,
            relief="flat",
            font=("Consolas", 12),
            wrap="word",
            padx=12,
            pady=10,
            undo=True,
        )
        self._inp.grid(row=1, column=0, sticky="nsew")

        mid = tk.Frame(panes, bg=BG)
        mid.grid(row=1, column=1, sticky="ns", padx=8)
        mid.rowconfigure(0, weight=1)
        mid.rowconfigure(2, weight=1)
        self._swap_btn = tk.Label(
            mid,
            text="⇄",
            bg="#333333",
            fg=FG,
            font=("Segoe UI", 16),
            padx=10,
            pady=8,
            cursor="hand2",
        )
        self._swap_btn.grid(row=1, column=0)
        self._swap_btn.bind("<Button-1>", lambda _e: self.swap())

        self._out = tk.Text(
            panes,
            height=14,
            bg=CARD,
            fg=FG,
            insertbackground=FG,
            relief="flat",
            font=("Consolas", 12),
            wrap="word",
            padx=12,
            pady=10,
            state="disabled",
        )
        self._out.grid(row=1, column=2, sticky="nsew")

        self._inp.bind("<<Modified>>", self._on_modified)

        self.after(20, self._place)
        self.after(80, self._inp.focus_set)
        self.set_mode("to_bytes")
        self.set_base(16)

    def _mk_btn(self, parent, text, cmd, accent: bool = False) -> tk.Label:
        lbl = tk.Label(
            parent,
            text=text,
            bg=ACCENT if accent else "#333333",
            fg=BG if accent else FG,
            font=("Segoe UI", 10),
            padx=12,
            pady=7,
            cursor="hand2",
        )
        lbl.bind("<Button-1>", lambda _e: cmd())
        return lbl

    def _place(self) -> None:
        self.update_idletasks()
        w, h = self.winfo_width() or 900, self.winfo_height() or 600
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 4}")

    def set_mode(self, key: str) -> None:
        self._mode = key
        for k, btn in self._mode_btns.items():
            if k == key:
                btn.configure(bg=ACCENT, fg=BG)
            else:
                btn.configure(bg="#333333", fg=FG)
        self._sync_caps()
        self.convert()

    def set_base(self, base: int) -> None:
        self._base = base
        for b, btn in self._base_btns.items():
            if b == base:
                btn.configure(bg=ACCENT, fg=BG)
            else:
                btn.configure(bg="#333333", fg=FG)
        # upper only for hex
        state = "normal" if base == 16 and self._mode == "to_bytes" else "disabled"
        self._opt_upper.configure(state=state)
        self._sync_caps()
        self.convert()

    def _sync_caps(self) -> None:
        names = {2: "двоичная", 8: "восьмеричная", 10: "десятичная", 16: "hex"}
        name = names[self._base]
        if self._mode == "to_bytes":
            self._in_cap.configure(text="текст")
            self._out_cap.configure(text=name)
            self._opt_spaced.configure(state="normal")
            self._opt_upper.configure(
                state="normal" if self._base == 16 else "disabled"
            )
        else:
            self._in_cap.configure(text=name)
            self._out_cap.configure(text="текст")
            self._opt_spaced.configure(state="disabled")
            self._opt_upper.configure(state="disabled")

    def _on_modified(self, _event=None) -> None:
        self._inp.edit_modified(False)
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._after_id = self.after(50, self.convert)

    def _input(self) -> str:
        return self._inp.get("1.0", "end-1c")

    def _set_out(self, text: str) -> None:
        self._out.configure(state="normal")
        self._out.delete("1.0", "end")
        self._out.insert("1.0", text)
        self._out.configure(state="disabled")

    def convert(self) -> None:
        self._after_id = None
        raw = self._input()
        if self._mode == "to_bytes":
            result = to_bytes_view(
                raw,
                base=self._base,
                spaced=self._spaced.get(),
                upper=self._upper.get(),
            )
        else:
            result = from_bytes_view(raw, base=self._base)
        if result.ok:
            self._set_out(result.text)
            if raw:
                self._status.configure(
                    text=f"ок · base {self._base} · ввод {len(raw)} · вывод {len(result.text)}",
                    fg=OK,
                )
            else:
                self._status.configure(text="", fg=MUTED)
        else:
            self._set_out("")
            self._status.configure(text=result.error, fg=BAD)

    def from_clip(self) -> None:
        try:
            data = self.clipboard_get()
        except tk.TclError:
            self._status.configure(text="буфер пуст", fg=MUTED)
            return
        if not isinstance(data, str):
            data = str(data)
        self._inp.delete("1.0", "end")
        self._inp.insert("1.0", data)
        self.convert()

    def to_clip(self) -> None:
        text = self._out.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_idletasks()
        self._status.configure(text=f"скопирован вывод · {len(text)} симв.", fg=OK)

    def clear_all(self) -> None:
        self._inp.delete("1.0", "end")
        self._set_out("")
        self._status.configure(text="", fg=MUTED)

    def swap(self) -> None:
        out = self._out.get("1.0", "end-1c")
        new_mode = "to_text" if self._mode == "to_bytes" else "to_bytes"
        if out:
            self._inp.delete("1.0", "end")
            self._inp.insert("1.0", out)
        self.set_mode(new_mode)


def run() -> None:
    HexAsciiApp().mainloop()
