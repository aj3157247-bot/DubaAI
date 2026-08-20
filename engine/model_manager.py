import os
import threading
import urllib.request

from .whisper_config import (
    MODEL_URL,
    MODEL_FILE,
    MODEL_DIR_NAME,
)


class ModelManager:

    def __init__(self, base_dir):

        self.base_dir = base_dir

        self.model_dir = os.path.join(
            self.base_dir,
            MODEL_DIR_NAME
        )

        self.model_path = os.path.join(
            self.model_dir,
            MODEL_FILE
        )

    def is_downloaded(self):

        return (
            os.path.exists(self.model_path)
            and os.path.getsize(self.model_path) > 0
        )

    def get_model_path(self):

        if not self.is_downloaded():
            return None

        return self.model_path

    def download(
        self,
        progress_callback=None,
        finished_callback=None,
        error_callback=None
    ):

        if self.is_downloaded():

            if finished_callback:
                finished_callback(
                    self.model_path
                )

            return

        os.makedirs(
            self.model_dir,
            exist_ok=True
        )

        def worker():

            try:

                def report(
                    block_number,
                    block_size,
                    total_size
                ):

                    if total_size <= 0:
                        return

                    downloaded = (
                        block_number *
                        block_size
                    )

                    progress = (
                        downloaded /
                        total_size
                    ) * 100

                    progress = max(
                        0,
                        min(100, progress)
                    )

                    if progress_callback:
                        progress_callback(
                            progress
                        )

                urllib.request.urlretrieve(
                    MODEL_URL,
                    self.model_path,
                    report
                )

                if finished_callback:
                    finished_callback(
                        self.model_path
                    )

            except Exception as error:

                try:

                    if os.path.exists(
                        self.model_path
                    ):
                        os.remove(
                            self.model_path
                        )

                except Exception:
                    pass

                if error_callback:
                    error_callback(error)

        thread = threading.Thread(
            target=worker,
            daemon=True
        )

        thread.start()

        return thread
