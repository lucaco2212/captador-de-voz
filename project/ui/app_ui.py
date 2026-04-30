"""Interfaz Tkinter estilo dashboard oscuro para captura de pedidos por voz.

Nota: archivo reindentado para evitar errores de indentación en entornos Windows.
"""
"""Interfaz Tkinter estilo dashboard oscuro para captura de pedidos por voz."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, TOP, Button, Frame, Label, StringVar, Text, Tk, Toplevel, X, Y, filedialog, messagebox
from tkinter import ttk
"""Interfaz Tkinter para captura de pedidos de voz."""

from __future__ import annotations

from pathlib import Path
from tkinter import BOTH, END, LEFT, Button, Frame, Label, StringVar, Text, Tk, Toplevel, filedialog, messagebox
from tkinter import ttk
import inspect
from tkinter import BOTH, END, LEFT, Button, Frame, Label, StringVar, Text, Tk, Toplevel, filedialog, messagebox
from tkinter import ttk
from tkinter import BOTH, END, LEFT, Button, Frame, Label, StringVar, Text, Tk, Toplevel, filedialog, messagebox
from tkinter import ttk
from tkinter import BOTH, END, LEFT, Button, Frame, Label, Text, Tk, filedialog, messagebox

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
BG = "#101010"
FG = "#F5F5F5"
BTN_BG = "#232323"
BTN_FG = "#FFFFFF"
ACCENT = "#3A86FF"


class AppUI:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("Sistema de Boletas por Voz - FRUNA")
        self.root.geometry("1320x760")
        self.root.configure(bg=BG)

        self.catalog = ProductCatalog.default()
        self.parser = OrderParser(self.catalog)
        self.recognizer: SpeechRecognizer | None = None

        self.root.title("Captador de voz FRUNA")
        self.root.geometry("980x680")
        self.root.configure(bg=BG)

class AppUI:
    """Controlador principal de interfaz y flujo de negocio."""

    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("Captador de voz FRUNA")
        self.root.geometry("900x650")

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
        self.is_listening = False

        self._build_widgets()

    def _styled_button(self, parent, text: str, command):
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
    def _build_widgets(self) -> None:
        top = Frame(self.root)
        top.pack(fill="x", padx=10, pady=10)

        self.listen_btn = Button(top, text="Iniciar escucha", command=self.toggle_listening)
        self.listen_btn.pack(side=LEFT, padx=5)
        Button(top, text="Ajustes", command=self.open_settings_window).pack(side=LEFT, padx=5)
        Button(top, text="Cerrar boleta pendiente", command=self.commit_pending_receipt).pack(side=LEFT, padx=5)
        Button(top, text="Guardar última boleta", command=self.save_last_receipt).pack(side=LEFT, padx=5)
        Button(top, text="Guardar historial", command=self.save_receipt_history).pack(side=LEFT, padx=5)

        Label(self.root, text="Texto reconocido en vivo:").pack(anchor="w", padx=10)
        self.live_text = Text(self.root, height=6)
        self.live_text.pack(fill="x", padx=10, pady=5)

        Label(self.root, text="Boletas generadas:").pack(anchor="w", padx=10)
        self.receipt_text = Text(self.root)
        self.receipt_text.pack(fill=BOTH, expand=True, padx=10, pady=5)

    def open_settings_window(self) -> None:
        """Ventana de ajustes para seleccionar micrófono de entrada."""
        settings = Toplevel(self.root)
        settings.title("Ajustes")
        settings.geometry("560x220")

        Label(settings, text="Selecciona el micrófono para captura de voz:").pack(anchor="w", padx=12, pady=(12, 4))

        try:
            devices = SpeechRecognizer.list_input_devices()
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudieron listar micrófonos: {exc}")
            messagebox.showerror("Error de audio", f"No se pudieron listar micrófonos: {exc}")
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
            Label(settings, text="No se detectaron micrófonos de entrada.", bg=BG, fg=FG).pack(anchor="w", padx=12, pady=10)
            Label(settings, text="No se detectaron micrófonos de entrada.").pack(anchor="w", padx=12, pady=10)
            return

        device_map = {
            f"[{device['index']}] {device['name']} (canales: {device['channels']}, rate: {device['default_rate']})": device["index"]
            for device in devices
        }

        combo_value = StringVar()
        combo = ttk.Combobox(settings, textvariable=combo_value, state="readonly", width=85)
        combo["values"] = list(device_map.keys())
        combo.pack(fill="x", padx=12, pady=4)

        combo = ttk.Combobox(settings, textvariable=combo_value, state="readonly", width=75)
        combo["values"] = list(device_map.keys())
        combo.pack(fill="x", padx=12, pady=4)

        # Selección por defecto: el primero o el actualmente seleccionado
        default_key = combo["values"][0]
        if self.selected_input_device_index is not None:
            for key, index in device_map.items():
                if index == self.selected_input_device_index:
                    default_key = key
                    break
        combo_value.set(default_key)

        status_label = Label(settings, text="", bg=BG, fg=FG)
        status_label = Label(settings, text="")
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
        Button(settings, text="Guardar micrófono", command=save_settings).pack(anchor="w", padx=12, pady=6)

    def toggle_listening(self) -> None:
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self) -> None:
        model_dir = Path(self.model_path)
        if not model_dir.exists():
            messagebox.showerror("Modelo no encontrado", f"No existe: {self.model_path}")
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

        """Construye SpeechRecognizer compatible con distintas firmas de __init__."""
        signature = inspect.signature(SpeechRecognizer.__init__)
        params = signature.parameters

        kwargs = {}
        if "model_path" in params:
            kwargs["model_path"] = self.model_path

        # Compatibilidad entre versiones/nombres de parámetro.
        if "input_device_index" in params:
            kwargs["input_device_index"] = self.selected_input_device_index
        elif "input_device_idx" in params:
            kwargs["input_device_idx"] = self.selected_input_device_index
        elif "device_index" in params:
            kwargs["device_index"] = self.selected_input_device_index

        # Si no existe model_path como keyword, usar posición.
        if not kwargs.get("model_path"):
            recognizer = SpeechRecognizer(self.model_path)
        else:
            recognizer = SpeechRecognizer(**kwargs)

        # Fallback por atributo para implementaciones legacy.
        if hasattr(recognizer, "input_device_index"):
            setattr(recognizer, "input_device_index", self.selected_input_device_index)
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
            self.status_var.set("ON AIR")
            self.listen_btn.config(text="Detener escucha", bg="#3A1620")
            # Compatibilidad: si existe una versión antigua de SpeechRecognizer en el entorno,
            # reintenta sin el argumento de micrófono para evitar TypeError por firma distinta.
            try:
                self.recognizer = SpeechRecognizer(
                    model_path=self.model_path,
                    input_device_index=self.selected_input_device_index,
                )
            except TypeError as exc:
                if "input_device_index" not in str(exc):
                    raise
                self.recognizer = SpeechRecognizer(model_path=self.model_path)
                if hasattr(self.recognizer, "input_device_index"):
                    setattr(self.recognizer, "input_device_index", self.selected_input_device_index)

            self.recognizer = SpeechRecognizer(
                model_path=self.model_path,
                input_device_index=self.selected_input_device_index,
            )
            self.recognizer = SpeechRecognizer(model_path=self.model_path)
            self.recognizer.start_listening(on_partial=self.on_partial_text, on_final=self.on_final_text)
            self.is_listening = True
            self.listen_btn.config(text="Detener escucha")
        except Exception as exc:
            messagebox.showerror("Error al iniciar audio", str(exc))

    def stop_listening(self) -> None:
        if self.recognizer:
            self.recognizer.stop_listening()
        self.is_listening = False
        self.status_var.set("Detenido")
        self.listen_btn.config(text="Iniciar escucha", bg="#1A2438")
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
        self.receipt_counter += 1
        self.counter_label.config(text=f"{self.receipt_counter} boletas")

    def commit_pending_receipt(self) -> None:

    def commit_pending_receipt(self) -> None:
        """Cierra manualmente la boleta en curso aunque no se haya dicho 'aparte'."""
        parsed_orders = self.parser.parse_orders(self.live_buffer)
        if not parsed_orders:
            messagebox.showwarning("Sin ítems", "No hay una boleta pendiente válida para cerrar.")
            return

        # Toma sólo la última boleta parseable del buffer actual.
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
        self.receipt_text.insert(END, receipt + "\n\n")
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
        """Guarda todas las boletas de la sesión en un solo TXT."""
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
