import os
import threading

from .whisper_native import WhisperNative


class WhisperEngine:

    def __init__(self, model_path=None):
        self.model_path = model_path
        self.native = None

    def set_model(self, model_path):
        self.model_path = model_path

    def find_library(self):

        possible_paths = [

            "/data/data/org.dubaai.dubaai/files/libdubaai_whisper.so",

            "/data/data/org.dubaai.dubaai/lib/libdubaai_whisper.so",

            os.path.join(
                os.path.dirname(__file__),
                "libdubaai_whisper.so"
            ),

            os.path.join(
                os.getcwd(),
                "libdubaai_whisper.so"
            ),

        ]

        for path in possible_paths:

            if os.path.exists(path):
                return path

        return None

    def load(self):

        if not self.model_path:
            raise RuntimeError(
                "Whisper model path is not set."
            )

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                self.model_path
            )

        library_path = self.find_library()

        if library_path is None:
            raise RuntimeError(
                "DubaAI Whisper native library "
                "was not found."
            )

        self.native = WhisperNative(
            library_path
        )

        self.native.load()

        self.native.initialize_model(
            self.model_path
        )

        return True

    def is_ready(self):

        return (
            self.model_path is not None
            and os.path.exists(
                self.model_path
            )
            and self.native is not None
            and self.native.context is not None
        )

    def transcribe(
        self,
        samples,
        language="en",
        callback=None
    ):

        if not self.is_ready():
            self.load()

        if samples is None:
            raise ValueError(
                "Audio samples are empty."
            )

        if callback:
            callback(
                "Whisper transcription started..."
            )

        result = self.native.transcribe(
            samples,
            language=language
        )

        if callback:
            callback(
                "Whisper transcription completed."
            )

        return result


class AsyncWhisper:

    def __init__(self, engine):

        self.engine = engine

        self.thread = None

        self.result = None

        self.error = None

    def start(
        self,
        samples,
        language="en",
        callback=None
    ):

        self.result = None

        self.error = None

        def worker():

            try:

                self.result = (
                    self.engine.transcribe(
                        samples,
                        language=language,
                        callback=callback
                    )
                )

            except Exception as error:

                self.error = error

        self.thread = threading.Thread(
            target=worker,
            daemon=True
        )

        self.thread.start()

    def is_running(self):

        return (
            self.thread is not None
            and self.thread.is_alive()
        )

    def get_result(self):

        if self.error:
            raise self.error

        return self.result
