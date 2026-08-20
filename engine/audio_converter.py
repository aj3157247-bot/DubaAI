import os
import subprocess
import wave
import struct


class AudioConverter:

    def __init__(self):
        self.sample_rate = 16000
        self.channels = 1

    def find_ffmpeg(self):

        possible = [
            "/system/bin/ffmpeg",
            "/data/data/org.dubaai.dubaai/files/ffmpeg",
            "/data/data/org.dubaai.dubaai/files/bin/ffmpeg",
            "ffmpeg",
        ]

        for path in possible:

            if path == "ffmpeg":
                return path

            if os.path.isfile(path):
                return path

        return None

    def convert_to_pcm(
        self,
        input_path,
        output_wav,
        callback=None
    ):

        if not os.path.isfile(input_path):
            raise FileNotFoundError(
                input_path
            )

        ffmpeg = self.find_ffmpeg()

        if ffmpeg is None:
            raise RuntimeError(
                "FFmpeg was not found on the device."
            )

        output_dir = os.path.dirname(
            output_wav
        )

        if output_dir:
            os.makedirs(
                output_dir,
                exist_ok=True
            )

        command = [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            output_wav,
        ]

        if callback:
            callback(
                "Extracting audio from video..."
            )

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

            if callback and line:
                callback(line)

        result = process.wait()

        if result != 0:
            raise RuntimeError(
                "FFmpeg audio extraction failed. "
                "Exit code: "
                + str(result)
            )

        if not os.path.isfile(output_wav):
            raise RuntimeError(
                "FFmpeg did not create the WAV file."
            )

        if callback:
            callback(
                "Audio extraction completed."
            )

        return output_wav

    def wav_to_float32(
        self,
        wav_path
    ):

        if not os.path.isfile(wav_path):
            raise FileNotFoundError(
                wav_path
            )

        with wave.open(
            wav_path,
            "rb"
        ) as wav:

            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            frame_count = wav.getnframes()

            if channels != 1:
                raise RuntimeError(
                    "Audio must be mono."
                )

            if sample_rate != 16000:
                raise RuntimeError(
                    "Audio must be 16000 Hz."
                )

            if sample_width != 2:
                raise RuntimeError(
                    "Audio must be 16-bit PCM."
                )

            raw = wav.readframes(
                frame_count
            )

        count = len(raw) // 2

        samples = []

        for i in range(count):

            value = struct.unpack_from(
                "<h",
                raw,
                i * 2
            )[0]

            samples.append(
                value / 32768.0
            )

        return samples
