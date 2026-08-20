import os
import shutil
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget

from android import activity
from jnius import autoclass

from engine.model_manager import ModelManager
from engine.whisper_engine import WhisperEngine
from engine.audio_converter import AudioConverter


class DubaAI(App):

    APP_NAME = "DubaAI"
    APP_VERSION = "1.0.0"
    DEVELOPER = "Abdullah Jafari"

    def build(self):

        self.selected_video = None
        self.work_dir = None

        self.root_dir = self.user_data_dir

        self.work_dir = os.path.join(
            self.root_dir,
            "work"
        )

        os.makedirs(
            self.work_dir,
            exist_ok=True
        )

        self.model_manager = ModelManager(
            self.root_dir
        )

        self.audio_converter = AudioConverter()

        self.whisper_engine = None

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12)
        )

        # TOP BAR

        top_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(55),
            spacing=dp(8)
        )

        title = Label(
            text="[b]DubaAI[/b]",
            markup=True,
            font_size="27sp",
            halign="left",
            valign="middle"
        )

        title.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        info_button = Button(
            text="ⓘ",
            font_size="27sp",
            size_hint_x=None,
            width=dp(55)
        )

        info_button.bind(
            on_release=self.show_information
        )

        share_button = Button(
            text="↗",
            font_size="27sp",
            size_hint_x=None,
            width=dp(55)
        )

        share_button.bind(
            on_release=self.share_app
        )

        top_bar.add_widget(title)
        top_bar.add_widget(Widget())
        top_bar.add_widget(info_button)
        top_bar.add_widget(share_button)

        root.add_widget(top_bar)

        # DESCRIPTION

        description = Label(
            text=(
                "AI Video Dubbing\n"
                "One video. More languages. "
                "More audience."
            ),
            font_size="17sp",
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(70)
        )

        description.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        root.add_widget(description)

        # SOURCE

        root.add_widget(
            Label(
                text="Source Language",
                font_size="17sp",
                size_hint_y=None,
                height=dp(35)
            )
        )

        self.source_spinner = Spinner(
            text="Auto Detect",
            values=self.get_languages(),
            font_size="17sp",
            size_hint_y=None,
            height=dp(52)
        )

        root.add_widget(
            self.source_spinner
        )

        # TARGET

        root.add_widget(
            Label(
                text="Dub Into",
                font_size="17sp",
                size_hint_y=None,
                height=dp(35)
            )
        )

        self.target_spinner = Spinner(
            text="Persian",
            values=self.get_languages(),
            font_size="17sp",
            size_hint_y=None,
            height=dp(52)
        )

        root.add_widget(
            self.target_spinner
        )

        # VIDEO

        select_button = Button(
            text="Select Video",
            font_size="19sp",
            size_hint_y=None,
            height=dp(62)
        )

        select_button.bind(
            on_release=self.select_video
        )

        root.add_widget(
            select_button
        )

        # STATUS

        self.status_label = Label(
            text="No video selected",
            font_size="16sp",
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(65)
        )

        self.status_label.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        root.add_widget(
            self.status_label
        )

        # PROGRESS

        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(12)
        )

        root.add_widget(
            self.progress_bar
        )

        # START

        self.dubbing_button = Button(
            text="Start Dubbing",
            font_size="20sp",
            size_hint_y=None,
            height=dp(65)
        )

        self.dubbing_button.bind(
            on_release=self.start_dubbing
        )

        root.add_widget(
            self.dubbing_button
        )

        activity.bind(
            on_activity_result=
            self.on_activity_result
        )

        return root

    # ==================================================
    # LANGUAGES
    # ==================================================

    def get_languages(self):

        return [
            "Auto Detect",
            "Persian",
            "English",
            "Arabic",
            "Turkish",
            "Urdu",
            "Hindi",
            "Spanish",
            "French",
            "German",
            "Italian",
            "Portuguese",
            "Dutch",
            "Polish",
            "Romanian",
            "Greek",
            "Swedish",
            "Danish",
            "Norwegian",
            "Finnish",
            "Czech",
            "Slovak",
            "Hungarian",
            "Bulgarian",
            "Croatian",
            "Serbian",
            "Ukrainian",
            "Russian",
            "Chinese",
            "Japanese",
            "Korean",
            "Indonesian",
            "Malay",
            "Vietnamese",
            "Thai",
            "Bengali",
            "Tamil",
            "Telugu",
            "Marathi",
            "Gujarati",
            "Punjabi",
            "Hebrew",
            "Armenian",
            "Georgian",
            "Azerbaijani",
            "Kazakh",
            "Uzbek",
            "Swahili",
            "Afrikaans"
        ]

    # ==================================================
    # SELECT VIDEO
    # ==================================================

    def select_video(self, instance):

        try:

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            current_activity = (
                PythonActivity.mActivity
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

            current_activity.startActivityForResult(
                intent,
                1001
            )

            self.status_label.text = (
                "Select a video..."
            )

        except Exception as error:

            self.show_error(
                "Video Picker Error",
                str(error)
            )

    # ==================================================
    # ACTIVITY RESULT
    # ==================================================

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        if request_code != 1001:
            return

        if result_code != -1:
            self.status_label.text = (
                "Video selection cancelled"
            )
            return

        if intent is None:
            return

        uri = intent.getData()

        if uri is None:
            return

        self.selected_video = (
            uri.toString()
        )

        self.status_label.text = (
            "Video selected successfully"
        )

    # ==================================================
    # COPY URI TO LOCAL FILE
    # ==================================================

    def copy_uri_to_file(
        self,
        uri_string
    ):

        PythonActivity = autoclass(
            "org.kivy.android.PythonActivity"
        )

        current_activity = (
            PythonActivity.mActivity
        )

        Uri = autoclass(
            "android.net.Uri"
        )

        uri = Uri.parse(
            uri_string
        )

        resolver = (
            current_activity
            .getContentResolver()
        )

        input_stream = (
            resolver.openInputStream(uri)
        )

        if input_stream is None:
            raise RuntimeError(
                "Unable to open selected video."
            )

        output_path = os.path.join(
            self.work_dir,
            "input_video.mp4"
        )

        output_file = open(
            output_path,
            "wb"
        )

        buffer = bytearray(
            1024 * 1024
        )

        while True:

            count = input_stream.read(
                buffer
            )

            if count <= 0:
                break

            output_file.write(
                buffer[:count]
            )

        output_file.close()

        input_stream.close()

        return output_path

    # ==================================================
    # START DUBBING
    # ==================================================

    def start_dubbing(self, instance):

        if not self.selected_video:

            self.status_label.text = (
                "Please select a video first."
            )

            return

        target = self.target_spinner.text

        if target == "Auto Detect":

            self.status_label.text = (
                "Please select a target language."
            )

            return

        self.dubbing_button.disabled = True
        self.progress_bar.value = 0

        self.status_label.text = (
            "Starting DubaAI engine..."
        )

        thread = threading.Thread(
            target=self.dubbing_worker,
            daemon=True
        )

        thread.start()

    # ==================================================
    # REAL WORKER
    # ==================================================

    def dubbing_worker(self):

        try:

            self.update_status(
                "Copying selected video..."
            )

            video_path = (
                self.copy_uri_to_file(
                    self.selected_video
                )
            )

            self.update_progress(
                10
            )

            self.update_status(
                "Preparing audio..."
            )

            audio_path = os.path.join(
                self.work_dir,
                "audio.wav"
            )

            self.audio_converter.convert_to_pcm(
                video_path,
                audio_path,
                callback=self.update_status
            )

            self.update_progress(
                35
            )

            self.update_status(
                "Loading Whisper model..."
            )

            model_path = (
                self.model_manager
                .get_model_path()
            )

            if model_path is None:

                self.model_manager.download(
                    finished_callback=
                    self.model_download_finished,
                    error_callback=
                    self.model_download_error
                )

                self.update_status(
                    "Downloading Whisper model..."
                )

                while not self.model_manager.is_downloaded():

                    import time

                    time.sleep(0.5)

                model_path = (
                    self.model_manager
                    .get_model_path()
                )

            self.update_progress(
                50
            )

            self.update_status(
                "Preparing Whisper..."
            )

            native_library = (
                self.find_native_library()
            )

            if native_library is None:

                raise RuntimeError(
                    "DubaAI Whisper native library "
                    "was not found in the APK."
                )

            self.whisper_engine = WhisperEngine(
                model_path
            )

            self.whisper_engine.native = None

            # Native engine is initialized here.
            self.whisper_engine.load()

            self.update_progress(
                60
            )

            self.update_status(
                "Converting audio for Whisper..."
            )

            samples = (
                self.audio_converter
                .wav_to_float32(
                    audio_path
                )
            )

            self.update_progress(
                70
            )

            source = (
                self.source_spinner.text
            )

            language = (
                self.language_code(
                    source
                )
            )

            self.update_status(
                "Transcribing speech..."
            )

            text = (
                self.whisper_engine.transcribe(
                    samples,
                    language=language,
                    callback=self.update_status
                )
            )

            text_path = os.path.join(
                self.work_dir,
                "transcript.txt"
            )

            with open(
                text_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(text)

            self.update_progress(
                100
            )

            self.update_status(
                "Speech transcription completed."
            )

            Clock.schedule_once(
                lambda dt:
                self.transcription_finished(
                    text
                )
            )

        except Exception as error:

            Clock.schedule_once(
                lambda dt:
                self.dubbing_error(
                    error
                )
            )

    # ==================================================
    # NATIVE LIBRARY
    # ==================================================

    def find_native_library(self):

        possible = [

            "/data/data/org.dubaai.dubaai/"
            "lib/libdubaai_whisper.so",

            "/data/data/org.dubaai.dubaai/"
            "files/libdubaai_whisper.so",

            os.path.join(
                self.root_dir,
                "libdubaai_whisper.so"
            )
        ]

        for path in possible:

            if os.path.isfile(path):
                return path

        return None

    # ==================================================
    # LANGUAGE CODE
    # ==================================================

    def language_code(self, name):

        codes = {

            "English": "en",
            "Persian": "fa",
            "Arabic": "ar",
            "Turkish": "tr",
            "Urdu": "ur",
            "Hindi": "hi",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Italian": "it",
            "Portuguese": "pt",
            "Dutch": "nl",
            "Polish": "pl",
            "Russian": "ru",
            "Ukrainian": "uk",
            "Chinese": "zh",
            "Japanese": "ja",
            "Korean": "ko",
            "Indonesian": "id",
            "Vietnamese": "vi",
            "Thai": "th",
            "Bengali": "bn",
            "Tamil": "ta",
            "Telugu": "te",
            "Marathi": "mr",
            "Gujarati": "gu",
            "Punjabi": "pa",
            "Hebrew": "he",
            "Armenian": "hy",
            "Georgian": "ka",
            "Azerbaijani": "az",
            "Kazakh": "kk",
            "Uzbek": "uz",
            "Swahili": "sw",
            "Afrikaans": "af"
        }

        return codes.get(
            name,
            "en"
        )

    # ==================================================
    # UI HELPERS
    # ==================================================

    def update_status(self, message):

        Clock.schedule_once(
            lambda dt:
            setattr(
                self.status_label,
                "text",
                str(message)
            )
        )

    def update_progress(self, value):

        Clock.schedule_once(
            lambda dt:
            setattr(
                self.progress_bar,
                "value",
                value
            )
        )

    def model_download_finished(
        self,
        path
    ):

        print(
            "MODEL DOWNLOADED:",
            path
        )

    def model_download_error(
        self,
        error
    ):

        print(
            "MODEL DOWNLOAD ERROR:",
            error
        )

    def transcription_finished(
        self,
        text
    ):

        self.dubbing_button.disabled = False

        preview = text.strip()

        if len(preview) > 600:
            preview = (
                preview[:600]
                + "\n..."
            )

        self.show_information_message(
            "Transcription Complete",
            preview if preview else
            "No speech was detected."
        )

    def dubbing_error(
        self,
        error
    ):

        self.dubbing_button.disabled = False

        self.status_label.text = (
            "Dubbing failed."
        )

        self.show_error(
            "DubaAI Error",
            str(error)
        )

    # ==================================================
    # INFORMATION
    # ==================================================

    def show_information(
        self,
        instance
    ):

        self.show_information_message(
            "About DubaAI",
            (
                "DubaAI\n\n"
                "AI Video Dubbing\n\n"
                "One video. More languages. "
                "More audience.\n\n"
                "DubaAI is designed to help "
                "content creators make videos "
                "more accessible across languages.\n\n"
                "Version: 1.0.0\n"
                "Developer: Abdullah Jafari\n\n"
                "Made with ❤️ for creators."
            )
        )

    def show_information_message(
        self,
        title,
        message
    ):

        content = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        label = Label(
            text=message,
            font_size="15sp",
            halign="center",
            valign="middle"
        )

        label.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        close_button = Button(
            text="Close",
            size_hint_y=None,
            height=dp(50)
        )

        content.add_widget(label)
        content.add_widget(
            close_button
        )

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.90, 0.75),
            auto_dismiss=False
        )

        close_button.bind(
            on_release=popup.dismiss
        )

        popup.open()

    # ==================================================
    # SHARE
    # ==================================================

    def share_app(self, instance):

        try:

            Intent = autoclass(
                "android.content.Intent"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            current_activity = (
                PythonActivity.mActivity
            )

            intent = Intent()

            intent.setAction(
                Intent.ACTION_SEND
            )

            intent.setType(
                "text/plain"
            )

            intent.putExtra(
                Intent.EXTRA_TEXT,
                (
                    "DubaAI 🎙️🌍\n\n"
                    "AI Video Dubbing\n"
                    "One video. More languages. "
                    "More audience.\n\n"
                    "Developer: Abdullah Jafari"
                )
            )

            chooser = Intent.createChooser(
                intent,
                "Share DubaAI"
            )

            current_activity.startActivity(
                chooser
            )

        except Exception as error:

            self.show_error(
                "Share Error",
                str(error)
            )

    # ==================================================
    # ERROR
    # ==================================================

    def show_error(
        self,
        title,
        message
    ):

        content = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        label = Label(
            text=str(message),
            font_size="14sp",
            halign="center",
            valign="middle"
        )

        label.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        button = Button(
            text="OK",
            size_hint_y=None,
            height=dp(50)
        )

        content.add_widget(label)
        content.add_widget(button)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.90, 0.55),
            auto_dismiss=False
        )

        button.bind(
            on_release=popup.dismiss
        )

        popup.open()


if __name__ == "__main__":
    DubaAI().run()
