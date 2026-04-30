"""Reconocedor de voz en tiempo real usando Vosk + PyAudio."""

from __future__ import annotations

import json
import queue
import threading
from typing import Callable, Optional

import pyaudio
from vosk import KaldiRecognizer, Model


class SpeechRecognizer:
    """Administra captura de audio y transcripción continua."""

    def __init__(self, model_path: str, sample_rate: int = 16000) -> None:
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, sample_rate)
        self.sample_rate = sample_rate

        self._audio_interface: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._audio_queue: queue.Queue[bytes] = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _audio_callback(self, in_data, frame_count, time_info, status):
        self._audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def start_listening(self, on_partial: Callable[[str], None], on_final: Callable[[str], None]) -> None:
        """Inicia el hilo de escucha y notifica parciales/finales mediante callbacks."""
        if self._running:
            return

        self._audio_interface = pyaudio.PyAudio()
        self._stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=8000,
            stream_callback=self._audio_callback,
        )

        self._running = True
        self._stream.start_stream()

        def worker() -> None:
            while self._running:
                try:
                    data = self._audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if self.recognizer.AcceptWaveform(data):
                    result_json = json.loads(self.recognizer.Result())
                    text = result_json.get("text", "").strip()
                    if text:
                        on_final(text)
                else:
                    partial_json = json.loads(self.recognizer.PartialResult())
                    partial_text = partial_json.get("partial", "").strip()
                    if partial_text:
                        on_partial(partial_text)

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def stop_listening(self) -> None:
        """Detiene la captura y libera recursos de audio."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        if self._audio_interface is not None:
            self._audio_interface.terminate()
            self._audio_interface = None
