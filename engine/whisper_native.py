import os
import ctypes
import logging


class WhisperNative:

    def __init__(self, library_path):
        self.library_path = library_path
        self.lib = None
        self.context = None

    # -------------------------------------------------
    # LOAD NATIVE LIBRARY
    # -------------------------------------------------

    def load(self):

        if not self.library_path:
            raise RuntimeError(
                "Whisper native library path is empty."
            )

        if not os.path.isfile(self.library_path):
            raise FileNotFoundError(
                "Whisper native library was not found:\n"
                + self.library_path
            )

        try:

            self.lib = ctypes.CDLL(
                self.library_path,
                mode=ctypes.RTLD_LOCAL
            )

        except OSError as error:

            raise RuntimeError(
                "Could not load DubaAI Whisper native library.\n\n"
                "Library:\n"
                + self.library_path
                + "\n\n"
                "Native error:\n"
                + str(error)
            )

        # -------------------------------------------------
        # FUNCTION: dubaai_whisper_init
        # -------------------------------------------------

        if not hasattr(
            self.lib,
            "dubaai_whisper_init"
        ):
            raise RuntimeError(
                "dubaai_whisper_init was not found "
                "inside libdubaai_whisper.so."
            )

        self.lib.dubaai_whisper_init.argtypes = [
            ctypes.c_char_p
        ]

        self.lib.dubaai_whisper_init.restype = (
            ctypes.c_void_p
        )

        # -------------------------------------------------
        # FUNCTION: dubaai_whisper_transcribe
        # -------------------------------------------------

        if not hasattr(
            self.lib,
            "dubaai_whisper_transcribe"
        ):
            raise RuntimeError(
                "dubaai_whisper_transcribe was not found "
                "inside libdubaai_whisper.so."
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

        # -------------------------------------------------
        # FUNCTION: segment count
        # -------------------------------------------------

        if not hasattr(
            self.lib,
            "dubaai_whisper_segment_count"
        ):
            raise RuntimeError(
                "dubaai_whisper_segment_count was not found."
            )

        self.lib.dubaai_whisper_segment_count.argtypes = [
            ctypes.c_void_p
        ]

        self.lib.dubaai_whisper_segment_count.restype = (
            ctypes.c_int
        )

        # -------------------------------------------------
        # FUNCTION: segment text
        # -------------------------------------------------

        if not hasattr(
            self.lib,
            "dubaai_whisper_segment_text"
        ):
            raise RuntimeError(
                "dubaai_whisper_segment_text was not found."
            )

        self.lib.dubaai_whisper_segment_text.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self.lib.dubaai_whisper_segment_text.restype = (
            ctypes.c_char_p
        )

        # -------------------------------------------------
        # FUNCTION: free
        # -------------------------------------------------

        if not hasattr(
            self.lib,
            "dubaai_whisper_free"
        ):
            raise RuntimeError(
                "dubaai_whisper_free was not found."
            )

        self.lib.dubaai_whisper_free.argtypes = [
            ctypes.c_void_p
        ]

        self.lib.dubaai_whisper_free.restype = None

        logging.info(
            "DubaAI Whisper native library loaded successfully."
        )

        return True

    # -------------------------------------------------
    # INITIALIZE MODEL
    # -------------------------------------------------

    def initialize_model(self, model_path):

        if not model_path:
            raise RuntimeError(
                "Whisper model path is empty."
            )

        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                "Whisper model was not found:\n"
                + model_path
            )

        if self.lib is None:
            self.load()

        model_bytes = model_path.encode(
            "utf-8"
        )

        try:

            self.context = (
                self.lib.dubaai_whisper_init(
                    model_bytes
                )
            )

        except Exception as error:

            raise RuntimeError(
                "Whisper native initialization failed:\n"
                + str(error)
            )

        if not self.context:

            raise RuntimeError(
                "Whisper model could not be initialized."
            )

        logging.info(
            "Whisper model initialized successfully."
        )

        return True

    # -------------------------------------------------
    # TRANSCRIBE
    # -------------------------------------------------

    def transcribe(
        self,
        samples,
        language="en"
    ):

        if self.lib is None:
            raise RuntimeError(
                "Whisper native library is not loaded."
            )

        if self.context is None:
            raise RuntimeError(
                "Whisper model is not initialized."
            )

        if samples is None:
            raise ValueError(
                "Audio samples are empty."
            )

        count = len(samples)

        if count <= 0:
            raise ValueError(
                "Audio sample count is zero."
            )

        logging.info(
            "Preparing %d audio samples for Whisper.",
            count
        )

        # -------------------------------------------------
        # Convert Python list to native float array
        # -------------------------------------------------

        array_type = (
            ctypes.c_float * count
        )

        try:

            audio = array_type(
                *samples
            )

        except MemoryError:

            raise RuntimeError(
                "Not enough memory to prepare "
                "audio for Whisper."
            )

        # -------------------------------------------------
        # Run native Whisper
        # -------------------------------------------------

        try:

            result = (
                self.lib.dubaai_whisper_transcribe(
                    self.context,
                    audio,
                    count,
                    language.encode("utf-8")
                )
            )

        except Exception as error:

            raise RuntimeError(
                "Whisper native transcription crashed:\n"
                + str(error)
            )

        if result != 0:

            raise RuntimeError(
                "Whisper transcription failed. "
                "Native error code: "
                + str(result)
            )

        # -------------------------------------------------
        # Read segments
        # -------------------------------------------------

        segments = []

        segment_count = (
            self.lib.dubaai_whisper_segment_count(
                self.context
            )
        )

        if segment_count < 0:

            raise RuntimeError(
                "Whisper returned an invalid segment count."
            )

        for index in range(
            segment_count
        ):

            text_ptr = (
                self.lib.dubaai_whisper_segment_text(
                    self.context,
                    index
                )
            )

            if text_ptr:

                try:

                    text = text_ptr.decode(
                        "utf-8",
                        errors="replace"
                    )

                except Exception:

                    text = str(text_ptr)

                text = text.strip()

                if text:
                    segments.append(
                        text
                    )

        result_text = "\n".join(
            segments
        )

        logging.info(
            "Whisper transcription completed. "
            "Segments: %d",
            segment_count
        )

        return result_text

    # -------------------------------------------------
    # CLOSE
    # -------------------------------------------------

    def close(self):

        if self.context is None:
            return

        if self.lib is None:
            self.context = None
            return

        try:

            self.lib.dubaai_whisper_free(
                self.context
            )

        except Exception:
            pass

        self.context = None
