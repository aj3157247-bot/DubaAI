import os
import subprocess
import threading
from pathlib import Path


class WhisperEngine:

    def __init__(self, model_path=None):
        self.model_path = model_path
        self.whisper_binary = None

    def set_model(self, model_path):
        self.model_path = model_path

    def set_binary(self, binary_path):
        self.whisper_binary = binary_path

    def is_ready(self):
        return (
            self.model_path is not None
            and os.path.exists(self.model_path)
            and self.whisper_binary is not None
            and os.path.exists(self.whisper_binary)
        )

    def transcribe(
        self,
        audio_path,
        language="en",
        output_path=None,
        callback=None
    ):
        if not self.is_ready():
            raise RuntimeError(
                "Whisper engine is not ready."
            )

        if not os.path.exists(audio_path):
            raise FileNotFoundError(
                audio_path
            )

        if output_path is None:
            output_path = str(
                Path(audio_path).with_suffix(".txt")
            )

        command = [
            self.whisper_binary,
            "-m",
            self.model_path,
            "-f",
            audio_path,
            "-l",
            language,
            "-otxt",
            "-of",
            output_path[:-4]
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        while True:
            line = process.stdout.readline()

            if not line:
                break

            line = line.strip()

            if callback:
                callback(line)

        return_code = process.wait()

        if return_code != 0:
            raise RuntimeError(
                "Whisper failed with code "
                + str(return_code)
            )

        if not os.path.exists(output_path):
            raise RuntimeError(
                "Whisper did not create output."
            )

        with open(
            output_path,
            "r",
            encoding="utf-8"
        ) as file:
            return file.read()


class AsyncWhisper:

    def __init__(self, engine):
        self.engine = engine
        self.thread = None
        self.result = None
        self.error = None

    def start(
        self,
        audio_path,
        language="en",
        callback=None
    ):

        self.result = None
        self.error = None

        def worker():

            try:

                self.result = self.engine.transcribe(
                    audio_path,
                    language=language,
                    callback=callback
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
