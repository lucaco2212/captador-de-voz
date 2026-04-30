"""Interfaz Tkinter estilo dashboard oscuro para captura de pedidos por voz."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, TOP, Button, Frame, Label, StringVar, Text, Tk, Toplevel, X, Y, filedialog, messagebox
from tkinter import ttk

from models.order import Order
from models.product_catalog import ProductCatalog
from models.receipt_generator import ReceiptGenerator
from parser.order_parser import OrderParser
from speech.speech_recognizer import SpeechRecognizer

# Paleta estilo referencia
BG = "#0A0B10"
CARD = "#12141D"
CARD_2 = "#171A25"
BORDER = "#262A3A"
FG = "#F4F7FF"
MUTED = "#8E95AA"
ACCENT = "#F2A900"
GREEN = "#00C56E"
RED = "#F04E59"


class AppUI:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("Sistema de Boletas por Voz - FRUNA")
        self.root.geometry("1320x760")
        self.root.configure(bg=BG)

        self.catalog = ProductCatalog.default()
        self.parser = OrderParser(self.catalog)
        self.recognizer: SpeechRecognizer | None = None

        self.model_path = "vosk-model-small-es-0.42"
        self.selected_input_device_index: int | None = None

        self.live_buffer = ""
        self.last_receipt_text = ""
        self.receipt_history: list[str] = []
        self.receipt_counter = 0
        self.is_listening = False

        self.status_var = StringVar(value="Detenido")
        self.datetime_var = StringVar(value="")

        self._build_layout()
        self._tick_clock()

    def _button(self, parent, text: str, command, color: str = CARD_2, fg: str = FG):
        return Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=fg,
            activebackground=ACCENT,
            activeforeground="#111",
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
        )

    def _build_layout(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self._build_sidebar()
        self._build_header()
        self._build_main_content()

    def _build_sidebar(self) -> None:
        sidebar = Frame(self.root, bg="#0B0D14", width=230, highlightbackground=BORDER, highlightthickness=1)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        sidebar.grid_propagate(False)

        Label(sidebar, text="FRUNA", bg="#0B0D14", fg=FG, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=16, pady=(16, 0))
        Label(sidebar, text="VOICEPOS", bg="#0B0D14", fg=ACCENT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=(0, 14))

        status_card = Frame(sidebar, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        status_card.pack(fill=X, padx=12, pady=8)
        Label(status_card, text="● Escuchando", bg=CARD, fg=GREEN, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        Label(status_card, textvariable=self.status_var, bg=CARD, fg=MUTED).pack(anchor="w", padx=12, pady=(0, 10))

        Label(sidebar, text="CONTROL DE VOZ", bg="#0B0D14", fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        self.listen_btn = self._button(sidebar, "Iniciar escucha", self.toggle_listening, color="#1A2438")
        self.listen_btn.pack(fill=X, padx=12, pady=5)
        self._button(sidebar, "Guardar última boleta", self.save_last_receipt).pack(fill=X, padx=12, pady=5)

        Label(sidebar, text="ACCIONES RÁPIDAS", bg="#0B0D14", fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        self._button(sidebar, "Ver historial", self.save_receipt_history).pack(fill=X, padx=12, pady=5)
        self._button(sidebar, "Configuración", self.open_settings_window).pack(fill=X, padx=12, pady=5)
        self._button(sidebar, "Cerrar boleta pendiente", self.commit_pending_receipt).pack(fill=X, padx=12, pady=5)

    def _build_header(self) -> None:
        header = Frame(self.root, bg="#10131B", height=58, highlightbackground=BORDER, highlightthickness=1)
        header.grid(row=0, column=1, sticky="ew")
        header.grid_propagate(False)

        Label(header, text="Sistema de Boletas por Voz", bg="#10131B", fg=FG, font=("Segoe UI", 15, "bold")).pack(side=LEFT, padx=18)
        Label(header, textvariable=self.datetime_var, bg="#10131B", fg=MUTED, font=("Segoe UI", 10)).pack(side=RIGHT, padx=(0, 20))

    def _build_main_content(self) -> None:
        container = Frame(self.root, bg=BG)
        container.grid(row=1, column=1, sticky="nsew")
        container.grid_columnconfigure(0, weight=3)
        container.grid_columnconfigure(1, weight=2)
        container.grid_rowconfigure(0, weight=1)

        # Panel centro
        center = Frame(container, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        center.grid(row=0, column=0, sticky="nsew", padx=(8, 6), pady=8)

        top_row = Frame(center, bg=CARD)
        top_row.pack(fill=X, padx=14, pady=(12, 8))
        Label(top_row, text="Texto reconocido en tiempo real", bg=CARD, fg=FG, font=("Segoe UI", 12, "bold")).pack(side=LEFT)
        Label(top_row, text="● Procesando audio...", bg=CARD, fg=ACCENT).pack(side=RIGHT)

        self.live_text = Text(center, height=12, bg="#0F121A", fg=FG, insertbackground=FG, relief="flat")
        self.live_text.pack(fill=BOTH, expand=True, padx=14, pady=(0, 14))

        # Panel derecha
        right = Frame(container, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 8), pady=8)
        Label(right, text="Boletas generadas", bg=CARD, fg=FG, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 8))

        self.counter_label = Label(right, text="0 boletas", bg=CARD, fg=MUTED)
        self.counter_label.pack(anchor="w", padx=14, pady=(0, 8))

        self.receipt_text = Text(right, bg="#0E1118", fg=FG, insertbackground=FG, relief="flat")
        self.receipt_text.pack(fill=BOTH, expand=True, padx=14, pady=(0, 14))

    def _tick_clock(self) -> None:
        self.datetime_var.set(datetime.now().strftime("%A, %d de %B de %Y  %H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    def _build_recognizer_compatible(self) -> SpeechRecognizer:
        recognizer = SpeechRecognizer(self.model_path)
        if hasattr(recognizer, "input_device_index"):
            setattr(recognizer, "input_device_index", self.selected_input_device_index)
        elif hasattr(recognizer, "input_device_idx"):
            setattr(recognizer, "input_device_idx", self.selected_input_device_index)
        elif hasattr(recognizer, "device_index"):
            setattr(recognizer, "device_index", self.selected_input_device_index)
        return recognizer

    def open_settings_window(self) -> None:
        settings = Toplevel(self.root)
        settings.title("Configuración")
        settings.geometry("620x300")
        settings.configure(bg=BG)

        Label(settings, text="Selecciona el micrófono:", bg=BG, fg=FG).pack(anchor="w", padx=12, pady=(12, 4))

        try:
            devices = SpeechRecognizer.list_input_devices()
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudieron listar micrófonos: {exc}")
            settings.destroy()
            return

        if not devices:
            Label(settings, text="No hay micrófonos detectados.", bg=BG, fg=MUTED).pack(anchor="w", padx=12, pady=10)
            return

        device_map = {f"[{d['index']}] {d['name']}": d["index"] for d in devices}
        combo_value = StringVar(value=list(device_map.keys())[0])
        combo = ttk.Combobox(settings, textvariable=combo_value, state="readonly", width=80)
        combo["values"] = list(device_map.keys())
        combo.pack(fill=X, padx=12, pady=6)

        status = Label(settings, text="", bg=BG, fg=MUTED)
        status.pack(anchor="w", padx=12, pady=8)

        def save_mic() -> None:
            selected = combo_value.get()
            self.selected_input_device_index = device_map[selected]
            status.config(text=f"Micrófono seleccionado: {selected}")

        def test_mic() -> None:
            selected = combo_value.get()
            status.config(text="Probando micrófono...")
            settings.update_idletasks()
            ok, rms = SpeechRecognizer.test_input_device(device_map[selected])
            status.config(text=f"{'✅ OK' if ok else '⚠️ Bajo nivel'} - RMS: {rms}")

        self._button(settings, "Guardar micrófono", save_mic).pack(anchor="w", padx=12, pady=5)
        self._button(settings, "Probar micrófono", test_mic).pack(anchor="w", padx=12, pady=5)

    def toggle_listening(self) -> None:
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self) -> None:
        model_dir = Path(self.model_path)
        if not model_dir.exists():
            messagebox.showerror("Modelo no encontrado", f"No existe: {self.model_path}")
            return

        try:
            self.recognizer = self._build_recognizer_compatible()
            self.recognizer.start_listening(on_partial=self.on_partial_text, on_final=self.on_final_text)
            self.is_listening = True
            self.status_var.set("ON AIR")
            self.listen_btn.config(text="Detener escucha", bg="#3A1620")
        except Exception as exc:
            messagebox.showerror("Error al iniciar audio", str(exc))

    def stop_listening(self) -> None:
        if self.recognizer:
            self.recognizer.stop_listening()
        self.is_listening = False
        self.status_var.set("Detenido")
        self.listen_btn.config(text="Iniciar escucha", bg="#1A2438")

    def on_partial_text(self, text: str) -> None:
        self.root.after(0, self._set_live_text, f"(parcial) {text}")

    def on_final_text(self, text: str) -> None:
        self.live_buffer = f"{self.live_buffer} {text}".strip()
        committed_orders, pending = self.parser.split_committed_and_pending(self.live_buffer)

        for items in committed_orders:
            self._create_and_show_receipt(items)

        self.live_buffer = pending
        self.root.after(0, self._set_live_text, self.live_buffer)

    def _create_and_show_receipt(self, items: dict[str, int]) -> None:
        order = Order(items=items, catalog=self.catalog)
        if not order.items:
            return

        receipt = ReceiptGenerator.generate_receipt_text(order)
        self.root.after(0, self._append_receipt, receipt)
        self.last_receipt_text = receipt
        self.receipt_history.append(receipt)
        self.receipt_counter += 1
        self.counter_label.config(text=f"{self.receipt_counter} boletas")

    def commit_pending_receipt(self) -> None:
        parsed_orders = self.parser.parse_orders(self.live_buffer)
        if not parsed_orders:
            messagebox.showwarning("Sin ítems", "No hay una boleta pendiente válida para cerrar.")
            return

        self._create_and_show_receipt(parsed_orders[-1])
        self.live_buffer = ""
        self._set_live_text("")

    def _set_live_text(self, content: str) -> None:
        self.live_text.delete("1.0", END)
        self.live_text.insert(END, content)

    def _append_receipt(self, receipt: str) -> None:
        code = f"RCP-{self.receipt_counter:03d}"
        section = f"[{code}]\n{receipt}\n\n{'='*30}\n\n"
        self.receipt_text.insert(END, section)
        self.receipt_text.see(END)

    def save_last_receipt(self) -> None:
        if not self.last_receipt_text:
            messagebox.showwarning("Sin boletas", "Aún no hay boletas para guardar.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivo de texto", "*.txt")])
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.last_receipt_text)
        messagebox.showinfo("Guardado", "Boleta guardada correctamente.")

    def save_receipt_history(self) -> None:
        if not self.receipt_history:
            messagebox.showwarning("Sin historial", "No hay boletas en el historial.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivo de texto", "*.txt")])
        if not file_path:
            return

        content = "\n\n==== BOLETA ====\n\n".join(self.receipt_history)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        messagebox.showinfo("Guardado", "Historial guardado correctamente.")

    def run(self) -> None:
        def on_close() -> None:
            self.stop_listening()
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_close)
        self.root.mainloop()
