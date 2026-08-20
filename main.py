import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.uix.filechooser import FileChooserListView

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

        root = BoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10
        )

        self.title_label = Label(
            text="Persian AI Dubber",
            font_size="28sp",
            size_hint_y=None,
            height=60
        )

        root.add_widget(
            self.title_label
        )

        self.status_label = Label(
            text="Select a video",
            font_size="18sp"
        )

        root.add_widget(
            self.status_label
        )

        self.language_spinner = Spinner(
            text="English",
            values=[
                "English",
                "Persian"
            ],
            size_hint_y=None,
            height=50
        )

        root.add_widget(
            self.language_spinner
        )

        self.select_button = Button(
            text="Select Video",
            size_hint_y=None,
            height=60
        )

        self.select_button.bind(
            on_release=self.open_video_picker
        )

        root.add_widget(
            self.select_button
        )

        self.start_button = Button(
            text="Start Dubbing",
            size_hint_y=None,
            height=60,
            disabled=True
        )

        self.start_button.bind(
            on_release=self.start_dubbing
        )

        root.add_widget(
            self.start_button
        )

        self.progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=20
        )

        root.add_widget(
            self.progress
        )

        self.log_label = Label(
            text="Ready",
            font_size="14sp"
        )

        root.add_widget(
            self.log_label
        )

        return root

    # -------------------------------------------------
    # VIDEO PICKER
    # -------------------------------------------------

    def open_video_picker(self, instance):

        picker = FileChooserListView(
            path="/storage/emulated/0",
            filters=[
                "*.mp4",
                "*.mkv",
                "*.avi",
                "*.mov",
                "*.webm",
                "*.m4v"
            ]
        )

        layout = BoxLayout(
            orientation="vertical"
        )

        layout.add_widget(picker)

        buttons = BoxLayout(
            size_hint_y=None,
            height=60
        )

        select = Button(
            text="Select"
        )

        cancel = Button(
            text="Cancel"
        )

        buttons.add_widget(select)
        buttons.add_widget(cancel)

        layout.add_widget(buttons)

        from kivy.uix.popup import Popup

        popup = Popup(
            title="Select Video",
            content=layout,
            size_hint=(0.95, 0.95)
        )

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
