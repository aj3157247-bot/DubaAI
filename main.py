import os
import threading
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup

from engine.audio_converter import AudioConverter
from engine.model_manager import ModelManager
from engine.whisper_engine import WhisperEngine
from engine.translator import Translator
from engine.tts_engine import TTSEngine
from engine.video_dubber import VideoDubber


class DubaAIApp(App):

    def build(self):

        self.title = "Persian AI Dubber"

        self.selected_video = None

        root = BoxLayout(
            orientation="vertical",
            padding=20,
            spacing=15
        )

        self.status = Label(
            text="Persian AI Dubber\nReady",
            size_hint_y=None,
            height=90,
            halign="center",
            valign="middle"
        )

        self.status.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
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

        root.add_widget(
            self.select_button
        )

        self.video_label = Label(
            text="No video selected",
            size_hint_y=None,
            height=50
        )

        root.add_widget(
            self.video_label
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

        self.start_button = Button(
            text="Start Dubbing",
            size_hint_y=None,
            height=65,
            disabled=True
        )

        self.start_button.bind(
            on_release=self.start_dubbing
        )

        root.add_widget(
            self.start_button
        )

        return root

    # ==================================================
    # VIDEO PICKER
    # ==================================================

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

        layout.add_widget(
            chooser
        )

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

        layout.add_widget(
            buttons
        )

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

    # ==================================================
    # UI HELPERS
    # ==================================================

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
                max(
                    0,
                    min(
                        100,
                        value
                    )
                )
            )
        )

    # ==================================================
    # START
    # ==================================================

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

    # ==================================================
    # MAIN DUBBING PIPELINE
    # ==================================================

    def process_video(self):

        try:

            video_path = (
                self.selected_video
            )

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
            # 1. WHISPER MODEL
            # ------------------------------------------

            self.set_status(
                "Checking Whisper model..."
            )

            model_manager = ModelManager(
                app_dir
            )

            if not model_manager.is_downloaded():

                self.set_status(
                    "Downloading Whisper model..."
                )

                finished = threading.Event()
                errors = []

                def download_progress(percent):

                    self.set_progress(
                        percent
                    )

                    self.set_status(
                        "Downloading Whisper model: "
                        + str(
                            int(percent)
                        )
                        + "%"
                    )

                def download_finished(path):

                    finished.set()

                def download_error(error):

                    errors.append(error)
                    finished.set()

                model_manager.download(
                    progress_callback=
                    download_progress,

                    finished_callback=
                    download_finished,

                    error_callback=
                    download_error
                )

                while not finished.is_set():

                    threading.Event().wait(
                        0.2
                    )

                if errors:

                    raise errors[0]

            model_path = (
                model_manager.get_model_path()
            )

            if not model_path:

                raise RuntimeError(
                    "Whisper model is unavailable."
                )

            # ------------------------------------------
            # 2. EXTRACT AUDIO
            # ------------------------------------------

            self.set_progress(0)

            self.set_status(
                "Extracting audio..."
            )

            converter = AudioConverter()

            wav_path = os.path.join(
                temp_dir,
                "audio.wav"
            )

            converter.convert_to_pcm(
                video_path,
                wav_path,
                callback=self.set_status
            )

            # ------------------------------------------
            # 3. WAV → FLOAT32
            # ------------------------------------------

            self.set_status(
                "Preparing audio..."
            )

            samples = (
                converter.wav_to_float32(
                    wav_path
                )
            )

            if not samples:

                raise RuntimeError(
                    "Audio contains no samples."
                )

            # ------------------------------------------
            # 4. WHISPER TRANSCRIPTION
            # ------------------------------------------

            self.set_status(
                "Running Whisper AI..."
            )

            whisper = WhisperEngine(
                model_path=model_path
            )

            english_text = (
                whisper.transcribe(
                    samples,
                    language="en",
                    callback=self.set_status
                )
            )

            if not english_text.strip():

                raise RuntimeError(
                    "Whisper detected no speech."
                )

            transcript_path = os.path.join(
                temp_dir,
                "english.txt"
            )

            with open(
                transcript_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    english_text
                )

            # ------------------------------------------
            # 5. TRANSLATION
            # ------------------------------------------

            self.set_status(
                "Translating English → Persian..."
            )

            translator = Translator(
                source_language="en",
                target_language="fa"
            )

            persian_text = (
                translator.translate_lines(
                    english_text,
                    callback=self.set_status
                )
            )

            if not persian_text.strip():

                raise RuntimeError(
                    "Translation returned empty text."
                )

            translation_path = os.path.join(
                temp_dir,
                "persian.txt"
            )

            with open(
                translation_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    persian_text
                )

            # ------------------------------------------
            # 6. PERSIAN TTS
            # ------------------------------------------

            self.set_status(
                "Generating Persian voice..."
            )

            tts = TTSEngine(
                language="fa"
            )

            tts_path = os.path.join(
                temp_dir,
                "persian_tts.mp3"
            )

            generated_audio = (
                tts.synthesize(
                    persian_text,
                    tts_path,
                    callback=self.set_status
                )
            )

            if not os.path.isfile(
                generated_audio
            ):

                raise RuntimeError(
                    "TTS audio was not created."
                )

            # ------------------------------------------
            # 7. FINAL MP4
            # ------------------------------------------

            self.set_status(
                "Creating final dubbed MP4..."
            )

            output_path = os.path.join(
                output_dir,
                "DubaAI_Dubbed.mp4"
            )

            video_dubber = VideoDubber()

            final_video = (
                video_dubber.create_dubbed_video(
                    video_path,
                    generated_audio,
                    output_path,
                    callback=self.set_status
                )
            )

            if not os.path.isfile(
                final_video
            ):

                raise RuntimeError(
                    "Final MP4 was not created."
                )

            self.set_progress(100)

            self.set_status(
                "DUBBING COMPLETED!\n\n"
                "Output:\n"
                + final_video
            )

        except Exception as error:

            traceback.print_exc()

            self.set_status(
                "Dubbing failed:\n"
                + str(error)
            )

        finally:

            Clock.schedule_once(
                lambda dt:
                self.enable_buttons()
            )

    # ==================================================
    # ENABLE BUTTONS
    # ==================================================

    def enable_buttons(self):

        self.select_button.disabled = False

        self.start_button.disabled = (
            self.selected_video is None
        )


if __name__ == "__main__":

    DubaAIApp().run()
