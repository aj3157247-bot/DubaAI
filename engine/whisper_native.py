import os
import ctypes


class WhisperNative:

    def __init__(self, library_path):

        self.library_path = library_path
        self.library = None

    def load(self):

        if not os.path.exists(self.library_path):
            raise FileNotFoundError(
                "Whisper native library not found:\n"
                + self.library_path
            )

        try:

            self.library = ctypes.CDLL(
                self.library_path
            )

        except Exception as error:

            raise RuntimeError(
                "Could not load Whisper native library: "
                + str(error)
            )

        return True

    def is_loaded(self):

        return self.library is not None
