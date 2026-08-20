import os
import threading
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserListView

from engine.audio_converter import AudioConverter
from engine.model_manager import ModelManager
from engine.whisper_engine import WhisperEngine


class DubaAIApp(App):

    def build(self):
        self.title = "Persian AI Dubber"

        self.selected_video = None
        self.whisper_engine = None
        self.model_manager = None

        root = BoxLayout(
            orientation="vertical",
            padding=20,
            spacing=15
        )

        self.status = Label(
            text="Persian AI Dubber\nReady",
            size_hint_y=None,
            height=80,
            halign="center",
            valign="middle"
        )

        self.status.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        root.add_widget(self.status)

        self.select_button = Button(
            text="Select Video",
            size_hint_y=None,
            height=60
        )

        self.select_button.bind(
            on_release=self.open_file_picker
        )

        root.add_widget(self.select_button)

        self.video_label = Label(
            text="No video selected",
            size_hint_y=None,
            height=50
        )

        root.add_widget(self.video_label)

        self.progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=20
        )

        root.add_widget(self.progress)

        self.start_button = Button(
            text="Start Dubbing",
            size_hint_y=None,
            height=65,
            disabled=True
        )

        self.start_button.bind(
            on_release=self.start_dubbing
        )

        root.add_widget(self.start_button)

        return root

    # --------------------------------------------------
    # File picker
    # --------------------------------------------------

    def open_file_picker(self, *args):

        chooser = FileChooserListView(
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
            orientation="vertical",
            spacing=10,
            padding=10
        )

        layout.add_widget(chooser)

        buttons = BoxLayout(
            size_hint_y=None,
            height=60,
            spacing=10
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
            size_hint=(0.95, 0.9)
        )

        def choose_video(*_):

            if not chooser.selection:
                self.set_status(
                    "Please select a video."
                )
                return

            video = chooser.selection[0]

            if not os.path.isfile(video):
                self.set_status(
                    "Selected file does not exist."
                )
                return

            self.selected_video = video

            self.video_label.text = (
                os.path.basename(video)
            )

            self.start_button.disabled = False

            self.set_status(
                "Video selected successfully."
            )

            popup.dismiss()

        select.bind(
            on_release=choose_video
        )

        cancel.bind(
            on_release=popup.dismiss
        )

        popup.open()

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def set_status(self, text):

        Clock.schedule_once(
            lambda dt:
            setattr(
                self.status,
                "text",
                text
            )
        )

    def set_progress(self, value):

        Clock.schedule_once(
            lambda dt:
            setattr(
                self.progress,
                "value",
                max(0, min(100, value))
            )
        )

    # --------------------------------------------------
    # Start dubbing
    # --------------------------------------------------

    def start_dubbing(self, *args):

        if not self.selected_video:
            self.set_status(
                "Please select a video first."
            )
            return

        self.start_button.disabled = True
        self.select_button.disabled = True
        self.progress.value = 0

        self.set_status(
            "Starting AI dubbing..."
        )

        thread = threading.Thread(
            target=self.process_video,
            daemon=True
        )

        thread.start()

    # --------------------------------------------------
    # Main processing
    # --------------------------------------------------

    def process_video(self):

        try:

            video_path = self.selected_video

            app_dir = self.user_data_dir

            temp_dir = os.path.join(
                app_dir,
                "temp"
            )

            output_dir = os.path.join(
                app_dir,
                "output"
            )

            os.makedirs(
                temp_dir,
                exist_ok=True
            )

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            # ------------------------------------------
            # Step 1 - Model manager
            # ------------------------------------------

            self.set_status(
                "Checking Whisper AI model..."
            )

            self.model_manager = ModelManager(
                app_dir
            )

            if not self.model_manager.is_downloaded():

                self.set_status(
                    "Downloading Whisper AI model..."
                )

                finished = threading.Event()
                download_error = []

                def progress(percent):
                    self.set_progress(percent)

                    self.set_status(
                        "Downloading Whisper model: "
                        + str(int(percent))
                        + "%"
                    )

                def done(path):
                    finished.set()

                def failed(error):
                    download_error.append(error)
                    finished.set()

                self.model_manager.download(
                    progress_callback=progress,
                    finished_callback=done,
                    error_callback=failed
                )

                while not finished.is_set():
                    threading.Event().wait(0.2)

                if download_error:
                    raise download_error[0]

            model_path = (
                self.model_manager.get_model_path()
            )

            if not model_path:
                raise RuntimeError(
                    "Whisper model is not available."
                )

            # ------------------------------------------
            # Step 2 - FFmpeg audio extraction
            # ------------------------------------------

            self.set_progress(0)

            self.set_status(
                "Extracting audio from video..."
            )

            audio_converter = AudioConverter()

            wav_path = os.path.join(
                temp_dir,
                "audio.wav"
            )

            audio_converter.convert_to_pcm(
                video_path,
                wav_path,
                callback=self.set_status
            )

            # ------------------------------------------
            # Step 3 - Convert WAV to float samples
            # ------------------------------------------

            self.set_status(
                "Preparing audio for Whisper..."
            )

            samples = (
                audio_converter.wav_to_float32(
                    wav_path
                )
            )

            if not samples:
                raise RuntimeError(
                    "No audio samples were found."
                )

            # ------------------------------------------
            # Step 4 - Whisper
            # ------------------------------------------

            self.set_status(
                "Running Whisper AI..."
            )

            self.whisper_engine = WhisperEngine(
                model_path=model_path
            )

            text = self.whisper_engine.transcribe(
                samples,
                language="en",
                callback=self.set_status
            )

            if not text or not text.strip():
                raise RuntimeError(
                    "Whisper did not detect any speech."
                )

            # ------------------------------------------
            # Save transcription
            # ------------------------------------------

            transcript_path = os.path.join(
                temp_dir,
                "transcript.txt"
            )

            with open(
                transcript_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    text
                )

            # ------------------------------------------
            # Step 5 - Temporary result
            # ------------------------------------------

            self.set_progress(100)

            self.set_status(
                "Whisper completed successfully.\n"
                "Transcription saved."
            )

            # ------------------------------------------
            # Current engine checkpoint
            # ------------------------------------------

            output_text = os.path.join(
                output_dir,
                "transcription.txt"
            )

            with open(
                output_text,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    text
                )

            # ------------------------------------------
            # Important:
            # Translation/TTS/video rendering will be
            # connected in the next engine layer.
            # ------------------------------------------

            self.set_status(
                "AI transcription completed.\n\n"
                "Next engine stage is ready:\n"
                "Translation → Persian TTS → MP4"
            )

        except Exception as error:

            traceback.print_exc()

            self.set_status(
                "Dubbing error:\n"
                + str(error)
            )

        finally:

            Clock.schedule_once(
                lambda dt: self.enable_buttons()
            )

    # --------------------------------------------------
    # Re-enable UI
    # --------------------------------------------------

    def enable_buttons(self):

        self.start_button.disabled = (
            self.selected_video is None
        )

        self.select_button.disabled = False


if __name__ == "__main__":
    DubaAIApp().run()
