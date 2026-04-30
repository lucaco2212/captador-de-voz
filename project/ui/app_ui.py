"""Interfaz Tkinter para captura de pedidos de voz."""

from __future__ import annotations

from pathlib import Path
from tkinter import BOTH, END, LEFT, Button, Frame, Label, StringVar, Text, Tk, Toplevel, filedialog, messagebox
from tkinter import ttk

from models.order import Order
from models.product_catalog import ProductCatalog
from models.receipt_generator import ReceiptGenerator
from parser.order_parser import OrderParser
from speech.speech_recognizer import SpeechRecognizer

BG = "#101010"
FG = "#F5F5F5"
BTN_BG = "#232323"
BTN_FG = "#FFFFFF"
ACCENT = "#3A86FF"


class AppUI:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("Captador de voz FRUNA")
        self.root.geometry("980x680")
        self.root.configure(bg=BG)

        self.catalog = ProductCatalog.default()
        self.parser = OrderParser(self.catalog)

        self.recognizer: SpeechRecognizer | None = None
        self.model_path = "vosk-model-small-es-0.42"
        self.selected_input_device_index: int | None = None

        self.live_buffer = ""
        self.last_receipt_text = ""
        self.receipt_history: list[str] = []
        self.is_listening = False

        self._build_widgets()

    def _styled_button(self, parent, text: str, command):
        return Button(
            parent,
            text=text,
            command=command,
            bg=BTN_BG,
            fg=BTN_FG,
            activebackground=ACCENT,
            activeforeground=BTN_FG,
            relief="flat",
            padx=8,
            pady=6,
        )

    def _build_widgets(self) -> None:
        top = Frame(self.root, bg=BG)
        top.pack(fill="x", padx=10, pady=10)

        self.listen_btn = self._styled_button(top, "Iniciar escucha", self.toggle_listening)
        self.listen_btn.pack(side=LEFT, padx=5)
        self._styled_button(top, "Ajustes", self.open_settings_window).pack(side=LEFT, padx=5)
        self._styled_button(top, "Cerrar boleta pendiente", self.commit_pending_receipt).pack(side=LEFT, padx=5)
        self._styled_button(top, "Guardar última boleta", self.save_last_receipt).pack(side=LEFT, padx=5)
        self._styled_button(top, "Guardar historial", self.save_receipt_history).pack(side=LEFT, padx=5)

        Label(self.root, text="Texto reconocido en vivo:", bg=BG, fg=FG).pack(anchor="w", padx=10)
        self.live_text = Text(self.root, height=6, bg="#1A1A1A", fg=FG, insertbackground=FG)
        self.live_text.pack(fill="x", padx=10, pady=5)

        Label(self.root, text="Boletas generadas:", bg=BG, fg=FG).pack(anchor="w", padx=10)
        self.receipt_text = Text(self.root, bg="#151515", fg=FG, insertbackground=FG)
        self.receipt_text.pack(fill=BOTH, expand=True, padx=10, pady=5)

    def open_settings_window(self) -> None:
        settings = Toplevel(self.root)
        settings.title("Ajustes")
        settings.geometry("620x290")
        settings.configure(bg=BG)

        Label(settings, text="Selecciona el micrófono para captura de voz:", bg=BG, fg=FG).pack(anchor="w", padx=12, pady=(12, 4))

        try:
            devices = SpeechRecognizer.list_input_devices()
        except Exception as exc:
            messagebox.showerror("Error de audio", f"No se pudieron listar micrófonos: {exc}")
            settings.destroy()
            return

        if not devices:
            Label(settings, text="No se detectaron micrófonos de entrada.", bg=BG, fg=FG).pack(anchor="w", padx=12, pady=10)
            return

        device_map = {
            f"[{device['index']}] {device['name']} (canales: {device['channels']}, rate: {device['default_rate']})": device["index"]
            for device in devices
        }

        combo_value = StringVar()
        combo = ttk.Combobox(settings, textvariable=combo_value, state="readonly", width=85)
        combo["values"] = list(device_map.keys())
        combo.pack(fill="x", padx=12, pady=4)

        default_key = combo["values"][0]
        if self.selected_input_device_index is not None:
            for key, index in device_map.items():
                if index == self.selected_input_device_index:
                    default_key = key
                    break
        combo_value.set(default_key)

        status_label = Label(settings, text="", bg=BG, fg=FG)
        status_label.pack(anchor="w", padx=12, pady=(8, 6))

        def save_settings() -> None:
            selected = combo_value.get().strip()
            if selected not in device_map:
                messagebox.showwarning("Selección inválida", "Debes seleccionar un micrófono válido.")
                return

            self.selected_input_device_index = device_map[selected]
            status_label.config(text=f"Micrófono seleccionado: {selected}")
            messagebox.showinfo("Ajustes guardados", "Micrófono guardado correctamente.")

        def test_microphone() -> None:
            selected = combo_value.get().strip()
            if selected not in device_map:
                messagebox.showwarning("Selección inválida", "Selecciona un micrófono antes de probar.")
                return

            status_label.config(text="Probando micrófono 2 segundos... habla ahora.")
            settings.update_idletasks()
            try:
                ok, rms = SpeechRecognizer.test_input_device(input_device_index=device_map[selected])
                if ok:
                    status_label.config(text=f"✅ Micrófono operativo. Nivel detectado (RMS): {rms}")
                else:
                    status_label.config(text=f"⚠️ Señal muy baja. Nivel detectado (RMS): {rms}. Acércate al micrófono.")
            except Exception as exc:
                status_label.config(text=f"❌ Error al probar micrófono: {exc}")

        self._styled_button(settings, "Guardar micrófono", save_settings).pack(anchor="w", padx=12, pady=6)
        self._styled_button(settings, "Probar micrófono", test_microphone).pack(anchor="w", padx=12, pady=4)

    def toggle_listening(self) -> None:
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def _build_recognizer_compatible(self) -> SpeechRecognizer:
        """Construye SpeechRecognizer sin depender de keywords en __init__."""
        # Instancia por posición para evitar errores por firmas legacy que no aceptan kwargs.
        recognizer = SpeechRecognizer(self.model_path)

        # Aplicar índice de dispositivo por atributo en distintas implementaciones posibles.
        if hasattr(recognizer, "input_device_index"):
            setattr(recognizer, "input_device_index", self.selected_input_device_index)
        elif hasattr(recognizer, "input_device_idx"):
            setattr(recognizer, "input_device_idx", self.selected_input_device_index)
        elif hasattr(recognizer, "device_index"):
            setattr(recognizer, "device_index", self.selected_input_device_index)

        return recognizer

    def start_listening(self) -> None:
        model_dir = Path(self.model_path)
        if not model_dir.exists():
            messagebox.showerror(
                "Modelo no encontrado",
                (
                    "No se encontró el modelo Vosk en la carpeta esperada:\n"
                    f"{self.model_path}\n\n"
                    "Descarga un modelo español y descomprímelo con ese nombre."
                ),
            )
            return

        try:
            self.recognizer = self._build_recognizer_compatible()
            self.recognizer.start_listening(on_partial=self.on_partial_text, on_final=self.on_final_text)
            self.is_listening = True
            self.listen_btn.config(text="Detener escucha")
        except Exception as exc:
            messagebox.showerror("Error al iniciar audio", str(exc))

    def stop_listening(self) -> None:
        if self.recognizer:
            self.recognizer.stop_listening()
        self.is_listening = False
        self.listen_btn.config(text="Iniciar escucha")

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
        self.receipt_text.insert(END, receipt + "\n\n")
        self.receipt_text.see(END)

    def save_last_receipt(self) -> None:
        if not self.last_receipt_text:
            messagebox.showwarning("Sin boletas", "Aún no hay boletas para guardar.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")],
            title="Guardar boleta",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.last_receipt_text)
            messagebox.showinfo("Boleta guardada", f"Boleta guardada en:\n{file_path}")
        except OSError as exc:
            messagebox.showerror("Error al guardar", str(exc))

    def save_receipt_history(self) -> None:
        if not self.receipt_history:
            messagebox.showwarning("Sin historial", "No hay boletas en el historial para guardar.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")],
            title="Guardar historial de boletas",
        )
        if not file_path:
            return

        try:
            content = "\n\n==== BOLETA ====\n\n".join(self.receipt_history)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)
            messagebox.showinfo("Historial guardado", f"Historial guardado en:\n{file_path}")
        except OSError as exc:
            messagebox.showerror("Error al guardar historial", str(exc))

    def run(self) -> None:
        def on_close() -> None:
            self.stop_listening()
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_close)
        self.root.mainloop()
