import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup

from engine.audio_converter import AudioConverter
from engine.model_manager import ModelManager
from engine.whisper_engine import WhisperEngine


class DubaAIApp(App):

    def build(self):

        self.title = "Persian AI Dubber"

        self.base_dir = self.user_data_dir
        self.selected_video = None

        self.audio_converter = AudioConverter()

        self.model_manager = ModelManager(
            self.base_dir
        )

        self.whisper_engine = None

        # ==================================================
        # ROOT
        # ==================================================

        root = BoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10
        )

        # ==================================================
        # TITLE
        # ==================================================

        self.title_label = Label(
            text="Persian AI Dubber",
            font_size="28sp",
            size_hint_y=None,
            height=60
        )

        root.add_widget(self.title_label)

        # ==================================================
        # STATUS
        # ==================================================

        self.status_label = Label(
            text="Select a video",
            font_size="18sp"
        )

        root.add_widget(self.status_label)

        # ==================================================
        # LANGUAGE
        # ==================================================

        self.language_spinner = Spinner(
            text="English",
            values=[
                "English",
                "Persian"
            ],
            size_hint_y=None,
            height=50
        )

        root.add_widget(self.language_spinner)

        # ==================================================
        # SELECT VIDEO
        # ==================================================

        self.select_button = Button(
            text="Select Video",
            size_hint_y=None,
            height=60
        )

        self.select_button.bind(
            on_release=self.open_video_picker
        )

        root.add_widget(self.select_button)

        # ==================================================
        # START DUBBING
        # ==================================================

        self.start_button = Button(
            text="Start Dubbing",
            size_hint_y=None,
            height=60,
            disabled=True
        )

        self.start_button.bind(
            on_release=self.start_dubbing
        )

        root.add_widget(self.start_button)

        # ==================================================
        # PROGRESS
        # ==================================================

        self.progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=20
        )

        root.add_widget(self.progress)

        # ==================================================
        # LOG
        # ==================================================

        self.log_label = Label(
            text="Ready",
            font_size="14sp"
        )

        root.add_widget(self.log_label)

        return root

    # ==================================================
    # ANDROID VIDEO PICKER
    # ==================================================

    def open_video_picker(self, instance):

        self.update_status(
            "Opening video picker..."
        )

        try:

            from android import activity
            from jnius import autoclass

            Intent = autoclass(
                "android.content.Intent"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            intent = Intent(
                Intent.ACTION_OPEN_DOCUMENT
            )

            intent.addCategory(
                Intent.CATEGORY_OPENABLE
            )

            intent.setType(
                "video/*"
            )

            activity.bind(
                on_activity_result=self.on_android_file_result
            )

            self._picker_activity = activity

            PythonActivity.mActivity.startActivityForResult(
                intent,
                1001
            )

        except Exception as error:

            self.update_status(
                "Video picker error: "
                + str(error)
            )

    # ==================================================
    # ANDROID PICKER RESULT
    # ==================================================

    def on_android_file_result(
        self,
        request_code,
        result_code,
        intent
    ):

        try:

            if request_code != 1001:
                return

            from jnius import autoclass

            Activity = autoclass(
                "android.app.Activity"
            )

            if result_code != Activity.RESULT_OK:
                self.update_status(
                    "Video selection cancelled."
                )
                return

            if intent is None:
                self.update_status(
                    "No video was selected."
                )
                return

            uri = intent.getData()

            if uri is None:
                self.update_status(
                    "Could not read selected video."
                )
                return

            # --------------------------------------------------
            # Convert Android URI to a local accessible file
            # --------------------------------------------------

            selected_path = self.copy_uri_to_private_storage(
                uri
            )

            if selected_path is None:
                self.update_status(
                    "Could not access selected video."
                )
                return

            self.selected_video = selected_path

            self.start_button.disabled = False

            self.update_status(
                "Video selected successfully."
            )

            self.log_label.text = (
                "Selected:\n"
                + os.path.basename(
                    selected_path
                )
            )

        except Exception as error:

            self.update_status(
                "Selection error: "
                + str(error)
            )

    # ==================================================
    # COPY ANDROID URI TO APP STORAGE
    # ==================================================

    def copy_uri_to_private_storage(
        self,
        uri
    ):

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            context = PythonActivity.mActivity

            content_resolver = context.getContentResolver()

            input_stream = (
                content_resolver.openInputStream(uri)
            )

            if input_stream is None:
                return None

            video_dir = os.path.join(
                self.user_data_dir,
                "videos"
            )

            os.makedirs(
                video_dir,
                exist_ok=True
            )

            # Try to get original file name
            file_name = "selected_video.mp4"

            try:

                OpenableColumns = autoclass(
                    "android.provider.OpenableColumns"
                )

                cursor = content_resolver.query(
                    uri,
                    None,
                    None,
                    None,
                    None
                )

                if cursor is not None:

                    name_index = cursor.getColumnIndex(
                        OpenableColumns.DISPLAY_NAME
                    )

                    if cursor.moveToFirst():

                        if name_index >= 0:

                            name = cursor.getString(
                                name_index
                            )

                            if name:
                                file_name = name

                    cursor.close()

            except Exception:
                pass

            # Clean unsafe filename
            file_name = os.path.basename(
                file_name
            )

            if not file_name:
                file_name = "selected_video.mp4"

            output_path = os.path.join(
                video_dir,
                file_name
            )

            # Avoid overwriting
            base, ext = os.path.splitext(
                output_path
            )

            counter = 1

            while os.path.exists(output_path):

                output_path = (
                    base
                    + "_"
                    + str(counter)
                    + ext
                )

                counter += 1

            output_file = None

            try:

                output_file = open(
                    output_path,
                    "wb"
                )

                buffer_size = 1024 * 1024

                while True:

                    data = input_stream.read(
                        buffer_size
                    )

                    if data is None:
                        break

                    if len(data) == 0:
                        break

                    output_file.write(
                        bytes(data)
                    )

            finally:

                if output_file is not None:
                    output_file.close()

                input_stream.close()

            if not os.path.isfile(
                output_path
            ):
                return None

            if os.path.getsize(
                output_path
            ) <= 0:
                return None

            return output_path

        except Exception as error:

            self.update_status(
                "Video copy error: "
                + str(error)
            )

            return None

    # ==================================================
    # STATUS
    # ==================================================

    def update_status(self, text):

        Clock.schedule_once(
            lambda dt: self._set_status(text)
        )

    def _set_status(self, text):

        self.status_label.text = text
        self.log_label.text = text

    # ==================================================
    # PROGRESS
    # ==================================================

    def update_progress(self, value):

        Clock.schedule_once(
            lambda dt: self._set_progress(value)
        )

    def _set_progress(self, value):

        self.progress.value = value

    # ==================================================
    # START DUBBING
    # ==================================================

    def start_dubbing(self, instance):

        if not self.selected_video:

            self.update_status(
                "Please select a video first."
            )

            return

        if not os.path.isfile(
            self.selected_video
        ):

            self.update_status(
                "Selected video is no longer available."
            )

            self.selected_video = None
            self.start_button.disabled = True

            return

        self.start_button.disabled = True
        self.select_button.disabled = True

        thread = threading.Thread(
            target=self.process_video,
            daemon=True
        )

        thread.start()

    # ==================================================
    # PROCESS VIDEO
    # ==================================================

    def process_video(self):

        try:

            video = self.selected_video

            self.update_status(
                "Preparing video..."
            )

            self.update_progress(5)

            temp_dir = os.path.join(
                self.user_data_dir,
                "temp"
            )

            os.makedirs(
                temp_dir,
                exist_ok=True
            )

            audio_path = os.path.join(
                temp_dir,
                "audio.wav"
            )

            # -----------------------------------------
            # STEP 1: EXTRACT AUDIO
            # -----------------------------------------

            self.update_status(
                "Extracting audio from video..."
            )

            self.audio_converter.convert_to_pcm(
                video,
                audio_path,
                callback=self.update_status
            )

            self.update_progress(25)

            # -----------------------------------------
            # STEP 2: READ WAV
            # -----------------------------------------

            self.update_status(
                "Preparing audio for Whisper..."
            )

            samples = (
                self.audio_converter.wav_to_float32(
                    audio_path
                )
            )

            self.update_progress(35)

            # -----------------------------------------
            # STEP 3: MODEL
            # -----------------------------------------

            model_path = (
                self.model_manager.get_model_path()
            )

            if model_path is None:

                self.update_status(
                    "Whisper model is not installed."
                )

                self.update_progress(0)

                self.download_model()

                return

            self.update_progress(45)

            # -----------------------------------------
            # STEP 4: LOAD WHISPER
            # -----------------------------------------

            self.update_status(
                "Loading Whisper AI..."
            )

            self.whisper_engine = WhisperEngine(
                model_path
            )

            self.whisper_engine.load()

            self.update_progress(55)

            # -----------------------------------------
            # STEP 5: TRANSCRIPTION
            # -----------------------------------------

            source_language = "en"

            if self.language_spinner.text == "Persian":
                source_language = "fa"

            self.update_status(
                "AI is transcribing the video..."
            )

            text = self.whisper_engine.transcribe(
                samples,
                language=source_language,
                callback=self.update_status
            )

            self.update_progress(80)

            # -----------------------------------------
            # SAVE TRANSCRIPTION
            # -----------------------------------------

            output_dir = os.path.join(
                self.user_data_dir,
                "output"
            )

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            transcript_path = os.path.join(
                output_dir,
                "transcription.txt"
            )

            with open(
                transcript_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(text)

            self.update_progress(100)

            self.update_status(
                "Whisper transcription completed."
            )

            self.show_result(
                text,
                transcript_path
            )

        except Exception as error:

            self.update_progress(0)

            self.update_status(
                "ERROR: " + str(error)
            )

        finally:

            Clock.schedule_once(
                lambda dt: self.enable_buttons()
            )

    # ==================================================
    # MODEL DOWNLOAD
    # ==================================================

    def download_model(self):

        self.update_status(
            "Downloading Whisper model..."
        )

        self.update_progress(0)

        def progress(value):

            self.update_progress(
                min(value, 100)
            )

        def finished(path):

            self.update_progress(100)

            self.update_status(
                "Whisper model downloaded."
            )

            Clock.schedule_once(
                lambda dt: self.start_dubbing(
                    self.start_button
                )
            )

        def error(error):

            self.update_status(
                "Model download failed: "
                + str(error)
            )

            self.enable_buttons()

        self.model_manager.download(
            progress_callback=progress,
            finished_callback=finished,
            error_callback=error
        )

    # ==================================================
    # RESULT
    # ==================================================

    def show_result(
        self,
        text,
        transcript_path
    ):

        preview = text.strip()

        if len(preview) > 500:
            preview = preview[:500] + "..."

        result_label = Label(
            text=(
                "Transcription completed.\n\n"
                + preview
                + "\n\n"
                "Saved to:\n"
                + transcript_path
            )
        )

        popup = Popup(
            title="DubaAI Result",
            content=result_label,
            size_hint=(0.9, 0.8)
        )

        popup.open()

    # ==================================================
    # ENABLE BUTTONS
    # ==================================================

    def enable_buttons(self):

        self.select_button.disabled = False

        if self.selected_video:

            self.start_button.disabled = False


if __name__ == "__main__":
    DubaAIApp().run()        )

        def choose_video(instance):

            if not picker.selection:
                self.update_status(
                    "Please select a video."
                )
                return

            path = picker.selection[0]

            if not os.path.isfile(path):
                self.update_status(
                    "Invalid video file."
                )
                return

            self.selected_video = path

            self.start_button.disabled = False

            self.update_status(
                "Video was selected successfully."
            )

            popup.dismiss()

        def cancel_picker(instance):

            popup.dismiss()

        select.bind(
            on_release=choose_video
        )

        cancel.bind(
            on_release=cancel_picker
        )

        popup.open()

    # -------------------------------------------------
    # STATUS
    # -------------------------------------------------

    def update_status(self, text):

        Clock.schedule_once(
            lambda dt: self._set_status(text)
        )

    def _set_status(self, text):

        self.status_label.text = text
        self.log_label.text = text

    def update_progress(self, value):

        Clock.schedule_once(
            lambda dt: self._set_progress(value)
        )

    def _set_progress(self, value):

        self.progress.value = value

    # -------------------------------------------------
    # DUBBING
    # -------------------------------------------------

    def start_dubbing(self, instance):

        if not self.selected_video:

            self.update_status(
                "Please select a video first."
            )

            return

        self.start_button.disabled = True
        self.select_button.disabled = True

        thread = threading.Thread(
            target=self.process_video,
            daemon=True
        )

        thread.start()

    # -------------------------------------------------
    # PROCESS VIDEO
    # -------------------------------------------------

    def process_video(self):

        try:

            video = self.selected_video

            self.update_status(
                "Preparing video..."
            )

            self.update_progress(5)

            temp_dir = os.path.join(
                self.user_data_dir,
                "temp"
            )

            os.makedirs(
                temp_dir,
                exist_ok=True
            )

            audio_path = os.path.join(
                temp_dir,
                "audio.wav"
            )

            # -----------------------------------------
            # STEP 1: EXTRACT AUDIO
            # -----------------------------------------

            self.update_status(
                "Extracting audio from video..."
            )

            self.audio_converter.convert_to_pcm(
                video,
                audio_path,
                callback=self.update_status
            )

            self.update_progress(25)

            # -----------------------------------------
            # STEP 2: READ WAV
            # -----------------------------------------

            self.update_status(
                "Preparing audio for Whisper..."
            )

            samples = (
                self.audio_converter.wav_to_float32(
                    audio_path
                )
            )

            self.update_progress(35)

            # -----------------------------------------
            # STEP 3: MODEL
            # -----------------------------------------

            model_path = (
                self.model_manager.get_model_path()
            )

            if model_path is None:

                self.update_status(
                    "Whisper model is not installed."
                )

                self.update_progress(0)

                self.download_model()

                return

            self.update_progress(45)

            # -----------------------------------------
            # STEP 4: LOAD WHISPER
            # -----------------------------------------

            self.update_status(
                "Loading Whisper AI..."
            )

            self.whisper_engine = WhisperEngine(
                model_path
            )

            self.whisper_engine.load()

            self.update_progress(55)

            # -----------------------------------------
            # STEP 5: TRANSCRIPTION
            # -----------------------------------------

            source_language = "en"

            if self.language_spinner.text == "Persian":
                source_language = "fa"

            self.update_status(
                "AI is transcribing the video..."
            )

            text = self.whisper_engine.transcribe(
                samples,
                language=source_language,
                callback=self.update_status
            )

            self.update_progress(80)

            # -----------------------------------------
            # SAVE TRANSCRIPTION
            # -----------------------------------------

            output_dir = os.path.join(
                self.user_data_dir,
                "output"
            )

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            transcript_path = os.path.join(
                output_dir,
                "transcription.txt"
            )

            with open(
                transcript_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(text)

            self.update_progress(100)

            self.update_status(
                "Whisper transcription completed."
            )

            self.show_result(
                text,
                transcript_path
            )

        except Exception as error:

            self.update_progress(0)

            self.update_status(
                "ERROR: " + str(error)
            )

        finally:

            Clock.schedule_once(
                lambda dt: self.enable_buttons()
            )

    # -------------------------------------------------
    # MODEL DOWNLOAD
    # -------------------------------------------------

    def download_model(self):

        self.update_status(
            "Downloading Whisper model..."
        )

        self.update_progress(0)

        def progress(value):

            self.update_progress(
                min(value, 100)
            )

        def finished(path):

            self.update_progress(100)

            self.update_status(
                "Whisper model downloaded."
            )

            Clock.schedule_once(
                lambda dt: self.start_dubbing(
                    self.start_button
                )
            )

        def error(error):

            self.update_status(
                "Model download failed: "
                + str(error)
            )

            self.enable_buttons()

        self.model_manager.download(
            progress_callback=progress,
            finished_callback=finished,
            error_callback=error
        )

    # -------------------------------------------------
    # RESULT
    # -------------------------------------------------

    def show_result(
        self,
        text,
        transcript_path
    ):

        preview = text.strip()

        if len(preview) > 500:
            preview = preview[:500] + "..."

        from kivy.uix.popup import Popup

        result_label = Label(
            text=(
                "Transcription completed.\n\n"
                + preview
                + "\n\n"
                "Saved to:\n"
                + transcript_path
            )
        )

        popup = Popup(
            title="DubaAI Result",
            content=result_label,
            size_hint=(0.9, 0.8)
        )

        popup.open()

    # -------------------------------------------------
    # ENABLE BUTTONS
    # -------------------------------------------------

    def enable_buttons(self):

        self.select_button.disabled = False

        if self.selected_video:
            self.start_button.disabled = False


if __name__ == "__main__":
    DubaAIApp().run()
