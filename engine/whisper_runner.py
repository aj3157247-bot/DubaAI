import os
import subprocess
import threading


class WhisperRunner:

    def __init__(self, whisper_binary, model_path):

        self.whisper_binary = whisper_binary
        self.model_path = model_path

    def is_ready(self):

        return (
            os.path.isfile(self.whisper_binary)
            and os.path.isfile(self.model_path)
        )

    def run(
        self,
        audio_path,
        language="en",
        output_path=None,
        callback=None
    ):

        if not self.is_ready():
            raise RuntimeError(
                "Whisper engine or model is missing."
            )

        if not os.path.isfile(audio_path):
            raise FileNotFoundError(
                audio_path
            )

        if output_path is None:

            output_path = (
                audio_path + ".txt"
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
            output_path[:-4],
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

        exit_code = process.wait()

        if exit_code != 0:

            raise RuntimeError(
                "Whisper failed. Exit code: "
                + str(exit_code)
            )

        if not os.path.exists(output_path):

            raise RuntimeError(
                "Whisper output file was not created."
            )

        with open(
            output_path,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()

    def run_async(
        self,
        audio_path,
        language="en",
        output_path=None,
        callback=None,
        finished_callback=None,
        error_callback=None
    ):

        def worker():

            try:

                result = self.run(
                    audio_path=audio_path,
                    language=language,
                    output_path=output_path,
                    callback=callback
                )

                if finished_callback:
                    finished_callback(result)

            except Exception as error:

                if error_callback:
                    error_callback(error)

        thread = threading.Thread(
            target=worker,
            daemon=True
        )

        thread.start()

        return thread
