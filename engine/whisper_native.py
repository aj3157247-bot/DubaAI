import os
import ctypes


class WhisperNative:

    def __init__(self, library_path):
        self.library_path = library_path
        self.lib = None
        self.context = None

    def load(self):
        if not os.path.exists(self.library_path):
            raise FileNotFoundError(
                "Whisper library not found:\n"
                + self.library_path
            )

        self.lib = ctypes.CDLL(self.library_path)

        self.lib.dubaai_whisper_init.argtypes = [
            ctypes.c_char_p
        ]
        self.lib.dubaai_whisper_init.restype = (
            ctypes.c_void_p
        )

        self.lib.dubaai_whisper_transcribe.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_int,
            ctypes.c_char_p
        ]
        self.lib.dubaai_whisper_transcribe.restype = (
            ctypes.c_int
        )

        self.lib.dubaai_whisper_segment_count.argtypes = [
            ctypes.c_void_p
        ]
        self.lib.dubaai_whisper_segment_count.restype = (
            ctypes.c_int
        )

        self.lib.dubaai_whisper_segment_text.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int
        ]
        self.lib.dubaai_whisper_segment_text.restype = (
            ctypes.c_char_p
        )

        self.lib.dubaai_whisper_free.argtypes = [
            ctypes.c_void_p
        ]
        self.lib.dubaai_whisper_free.restype = None

        return True

    def initialize_model(self, model_path):

        if self.lib is None:
            self.load()

        model_bytes = model_path.encode(
            "utf-8"
        )

        self.context = (
            self.lib.dubaai_whisper_init(
                model_bytes
            )
        )

        if not self.context:
            raise RuntimeError(
                "Whisper model could not be loaded."
            )

    def transcribe(
        self,
        samples,
        language="en"
    ):

        if self.context is None:
            raise RuntimeError(
                "Whisper model is not initialized."
            )

        count = len(samples)

        array_type = (
            ctypes.c_float * count
        )

        audio = array_type(*samples)

        result = (
            self.lib.dubaai_whisper_transcribe(
                self.context,
                audio,
                count,
                language.encode("utf-8")
            )
        )

        if result != 0:
            raise RuntimeError(
                "Whisper transcription failed. "
                "Error code: "
                + str(result)
            )

        segments = []

        segment_count = (
            self.lib.dubaai_whisper_segment_count(
                self.context
            )
        )

        for index in range(segment_count):

            text_ptr = (
                self.lib.dubaai_whisper_segment_text(
                    self.context,
                    index
                )
            )

            if text_ptr:

                text = text_ptr.decode(
                    "utf-8",
                    errors="replace"
                )

                segments.append(
                    text
                )

        return "\n".join(segments)

    def close(self):

        if self.context is not None:

            self.lib.dubaai_whisper_free(
                self.context
            )

            self.context = None
