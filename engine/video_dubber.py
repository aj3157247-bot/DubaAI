import os
import subprocess


class VideoDubber:

    def __init__(self):
        self.ffmpeg = self.find_ffmpeg()

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

    def check(self):

        if self.ffmpeg is None:

            raise RuntimeError(
                "FFmpeg was not found."
            )

        return True

    def create_dubbed_video(
        self,
        video_path,
        dubbed_audio,
        output_path,
        callback=None
    ):

        self.check()

        if not os.path.isfile(video_path):

            raise FileNotFoundError(
                video_path
            )

        if not os.path.isfile(dubbed_audio):

            raise FileNotFoundError(
                dubbed_audio
            )

        output_dir = os.path.dirname(
            output_path
        )

        if output_dir:

            os.makedirs(
                output_dir,
                exist_ok=True
            )

        if callback:

            callback(
                "Creating final MP4..."
            )

        command = [
            self.ffmpeg,
            "-y",

            "-i",
            video_path,

            "-i",
            dubbed_audio,

            "-map",
            "0:v:0",

            "-map",
            "1:a:0",

            "-c:v",
            "copy",

            "-c:a",
            "aac",

            "-b:a",
            "192k",

            "-shortest",

            "-movflags",
            "+faststart",

            output_path,
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

            if callback and line:

                callback(line)

        exit_code = process.wait()

        if exit_code != 0:

            raise RuntimeError(
                "FFmpeg failed while creating "
                "the final MP4. Exit code: "
                + str(exit_code)
            )

        if not os.path.isfile(
            output_path
        ):

            raise RuntimeError(
                "Final MP4 was not created."
            )

        if os.path.getsize(
            output_path
        ) <= 0:

            raise RuntimeError(
                "Final MP4 is empty."
            )

        if callback:

            callback(
                "Final MP4 created successfully."
            )

        return output_path
