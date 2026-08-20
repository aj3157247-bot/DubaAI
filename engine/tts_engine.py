import os
import subprocess


class TTSEngine:

    def __init__(
        self,
        language="fa",
        voice=None
    ):
        self.language = language
        self.voice = voice

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

    def check_android_tts(self):

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity = (
                PythonActivity.mActivity
            )

            TextToSpeech = autoclass(
                "android.speech.tts.TextToSpeech"
            )

            Locale = autoclass(
                "java.util.Locale"
            )

            locale = Locale(
                "fa",
                "IR"
            )

            return True

        except Exception:

            return False

    def synthesize(
        self,
        text,
        output_path,
        callback=None
    ):

        if not text or not text.strip():

            raise ValueError(
                "TTS text is empty."
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
                "Starting Persian TTS..."
            )

        # ------------------------------------------
        # Android native TTS
        # ------------------------------------------

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            TextToSpeech = autoclass(
                "android.speech.tts.TextToSpeech"
            )

            Locale = autoclass(
                "java.util.Locale"
            )

            activity = (
                PythonActivity.mActivity
            )

            locale = Locale(
                "fa",
                "IR"
            )

            tts_ready = []

            class Listener:

                def onInit(
                    self,
                    status
                ):

                    tts_ready.append(
                        status
                    )

            listener = Listener()

            tts = TextToSpeech(
                activity,
                listener
            )

            tts.setLanguage(
                locale
            )

            # Android TTS normally writes WAV
            # through synthesizeToFile.
            #
            # The exact Android API differs between
            # Android versions, so failure here falls
            # through to the online TTS method.

            Bundle = autoclass(
                "android.os.Bundle"
            )

            bundle = Bundle()

            result = tts.synthesizeToFile(
                text,
                bundle,
                output_path,
                "dubaai_tts"
            )

            if result == TextToSpeech.SUCCESS:

                if callback:

                    callback(
                        "Persian TTS completed."
                    )

                return output_path

            try:

                tts.shutdown()

            except Exception:

                pass

        except Exception:

            pass

        # ------------------------------------------
        # Online fallback
        # ------------------------------------------

        try:

            import urllib.parse
            import urllib.request

            encoded = urllib.parse.quote(
                text
            )

            url = (
                "https://translate.google.com/"
                "translate_tts"
                "?ie=UTF-8"
                "&client=tw-ob"
                "&tl=fa"
                "&q="
                + encoded
            )

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent":
                    "Mozilla/5.0"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=60
            ) as response:

                audio_data = (
                    response.read()
                )

            if not audio_data:

                raise RuntimeError(
                    "Online TTS returned empty audio."
                )

            mp3_path = output_path

            if not mp3_path.lower().endswith(
                ".mp3"
            ):

                mp3_path = (
                    os.path.splitext(
                        output_path
                    )[0]
                    + ".mp3"
                )

            with open(
                mp3_path,
                "wb"
            ) as file:

                file.write(
                    audio_data
                )

            if callback:

                callback(
                    "Persian TTS completed."
                )

            return mp3_path

        except Exception as error:

            raise RuntimeError(
                "Persian TTS failed: "
                + str(error)
            )

    def is_available(self):

        return (
            self.check_android_tts()
            or
            self.find_ffmpeg() is not None
      )
