import os
import shutil
import subprocess
import threading
import traceback

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

try:
    from android import activity
    ANDROID_AVAILABLE = True
except Exception:
    activity = None
    ANDROID_AVAILABLE = False

try:
    from jnius import autoclass
    PYJUS_AVAILABLE = True
except Exception:
    autoclass = None
    PYJUS_AVAILABLE = False


class DubaAI(App):

    APP_NAME = "DubaAI"
    APP_VERSION = "1.0.0"
    DEVELOPER = "Abdullah Jafari"

    VIDEO_REQUEST_CODE = 1001

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.selected_video = None
        self.selected_video_uri = None

        self.progress_value = 0
        self.progress_event = None

        self.processing = False

    # =====================================================
    # BUILD
    # =====================================================

    def build(self):

        self.selected_video = None
        self.selected_video_uri = None
        self.processing = False
        self.progress_value = 0

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12)
        )

        # =================================================
        # TOP BAR
        # =================================================

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
            setattr(instance, "text_size", value)
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

        # =================================================
        # DESCRIPTION
        # =================================================

        description = Label(
            text=(
                "AI Video Dubbing\n"
                "One video. More languages. More audience."
            ),
            font_size="17sp",
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(70)
        )

        description.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        root.add_widget(description)

        # =================================================
        # SOURCE LANGUAGE
        # =================================================

        source_label = Label(
            text="Source Language",
            font_size="17sp",
            size_hint_y=None,
            height=dp(35)
        )

        root.add_widget(source_label)

        self.source_spinner = Spinner(
            text="Auto Detect",
            values=self.get_languages(),
            font_size="17sp",
            size_hint_y=None,
            height=dp(52)
        )

        root.add_widget(self.source_spinner)

        # =================================================
        # TARGET LANGUAGE
        # =================================================

        target_label = Label(
            text="Dub Into",
            font_size="17sp",
            size_hint_y=None,
            height=dp(35)
        )

        root.add_widget(target_label)

        self.target_spinner = Spinner(
            text="Persian",
            values=self.get_languages(),
            font_size="17sp",
            size_hint_y=None,
            height=dp(52)
        )

        root.add_widget(self.target_spinner)

        # =================================================
        # SELECT VIDEO
        # =================================================

        select_button = Button(
            text="Select Video",
            font_size="19sp",
            size_hint_y=None,
            height=dp(62)
        )

        select_button.bind(
            on_release=self.select_video
        )

        root.add_widget(select_button)

        self.select_button = select_button

        # =================================================
        # STATUS
        # =================================================

        self.status_label = Label(
            text="No video selected",
            font_size="16sp",
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(55)
        )

        self.status_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        root.add_widget(self.status_label)

        # =================================================
        # PROGRESS BAR
        # =================================================

        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(12)
        )

        root.add_widget(self.progress_bar)

        # =================================================
        # START DUBBING
        # =================================================

        self.dubbing_button = Button(
            text="Start Dubbing",
            font_size="20sp",
            size_hint_y=None,
            height=dp(65)
        )

        self.dubbing_button.bind(
            on_release=self.start_dubbing
        )

        root.add_widget(self.dubbing_button)

        # =================================================
        # ANDROID ACTIVITY RESULT
        # =================================================

        try:

            if ANDROID_AVAILABLE and activity:

                activity.bind(
                    on_activity_result=self.on_activity_result
                )

        except Exception as e:

            print(
                "ACTIVITY BIND ERROR:",
                repr(e)
            )

        return root

    # =====================================================
    # LANGUAGES
    # =====================================================

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

    # =====================================================
    # VIDEO PICKER
    # =====================================================

    def select_video(self, instance):

        if self.processing:

            return

        try:

            if not ANDROID_AVAILABLE:

                self.show_error(
                    "Android Error",
                    "Android environment is not available."
                )

                return

            if not PYJUS_AVAILABLE:

                self.show_error(
                    "Android Error",
                    "PyJNIus is not available."
                )

                return

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

            # اجازه دسترسی پایدار به URI
            try:

                intent.addFlags(
                    Intent.FLAG_GRANT_READ_URI_PERMISSION
                )

                intent.addFlags(
                    Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
                )

            except Exception as e:

                print(
                    "URI FLAG ERROR:",
                    repr(e)
                )

            current_activity.startActivityForResult(
                intent,
                self.VIDEO_REQUEST_CODE
            )

            self.status_label.text = (
                "Select a video..."
            )

        except Exception as e:

            print(
                "VIDEO PICKER ERROR:",
                repr(e)
            )

            self.status_label.text = (
                "Video picker error"
            )

            self.show_error(
                "Video Picker Error",
                str(e)
            )

    # =====================================================
    # ACTIVITY RESULT
    # =====================================================

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        try:

            if request_code != self.VIDEO_REQUEST_CODE:

                return

            RESULT_OK = -1

            if result_code != RESULT_OK:

                self.selected_video = None
                self.selected_video_uri = None

                self.status_label.text = (
                    "Video selection cancelled"
                )

                return

            if intent is None:

                self.status_label.text = (
                    "No video selected"
                )

                return

            uri = intent.getData()

            if uri is None:

                self.status_label.text = (
                    "No video selected"
                )

                return

            uri_string = uri.toString()

            if not uri_string:

                self.status_label.text = (
                    "Invalid video URI"
                )

                return

            self.selected_video_uri = uri_string

            self.selected_video = uri_string

            # تلاش برای گرفتن دسترسی دائمی
            try:

                PythonActivity = autoclass(
                    "org.kivy.android.PythonActivity"
                )

                current_activity = (
                    PythonActivity.mActivity
                )

                flags = (
                    IntentFlags.FLAG_GRANT_READ_URI_PERMISSION
                    if False
                    else 1
                )

                current_activity.getContentResolver().takePersistableUriPermission(
                    uri,
                    flags
                )

            except Exception as e:

                print(
                    "PERSISTABLE URI ERROR:",
                    repr(e)
                )

            self.status_label.text = (
                "Video selected successfully"
            )

            print(
                "SELECTED VIDEO URI:",
                self.selected_video
            )

        except Exception as e:

            print(
                "ACTIVITY RESULT ERROR:",
                repr(e)
            )

            self.status_label.text = (
                "Video selection error"
            )

            Clock.schedule_once(
                lambda dt:
                self.show_error(
                    "Video Selection Error",
                    str(e)
                ),
                0
            )

    # =====================================================
    # START DUBBING
    # =====================================================

    def start_dubbing(self, instance):

        if self.processing:

            return

        try:

            if not self.selected_video:

                self.status_label.text = (
                    "Please select a video first"
                )

                return

            source = self.source_spinner.text
            target = self.target_spinner.text

            if target == "Auto Detect":

                self.status_label.text = (
                    "Please select a target language"
                )

                return

            if (
                source != "Auto Detect"
                and source == target
            ):

                self.status_label.text = (
                    "Source and target languages "
                    "must be different"
                )

                return

            self.processing = True

            self.progress_value = 0

            self.progress_bar.value = 0

            self.dubbing_button.disabled = True
            self.select_button.disabled = True

            self.status_label.text = (
                "Starting dubbing..."
            )

            print("================================")
            print("DubaAI Dubbing")
            print(
                "Video:",
                self.selected_video
            )
            print(
                "Source:",
                source
            )
            print(
                "Target:",
                target
            )
            print("================================")

            # بررسی اولیه بدون اجرای موتور واقعی
            thread = threading.Thread(
                target=self.dubbing_worker,
                args=(
                    self.selected_video,
                    source,
                    target
                ),
                daemon=True
            )

            thread.start()

        except Exception as e:

            self.handle_error(
                "START DUBBING ERROR",
                e
            )

    # =====================================================
    # DUBBING WORKER
    # =====================================================

    def dubbing_worker(
        self,
        video_uri,
        source,
        target
    ):

        try:

            self.update_status(
                "Preparing video..."
            )

            self.update_progress_safe(10)

            # ---------------------------------------------
            # بررسی FFmpeg
            # ---------------------------------------------

            ffmpeg_path = shutil.which(
                "ffmpeg"
            )

            if ffmpeg_path:

                print(
                    "FFmpeg found:",
                    ffmpeg_path
                )

            else:

                print(
                    "FFmpeg is not available."
                )

            self.update_progress_safe(20)

            self.update_status(
                "Checking selected video..."
            )

            # ---------------------------------------------
            # URI بررسی
            # ---------------------------------------------

            if video_uri.startswith(
                "content://"
            ):

                self.update_status(
                    "Android video selected."
                )

                print(
                    "Android Content URI:",
                    video_uri
                )

            elif video_uri.startswith(
                "file://"
            ):

                print(
                    "File URI:",
                    video_uri
                )

            elif os.path.isfile(
                video_uri
            ):

                print(
                    "Local video:",
                    video_uri
                )

            else:

                print(
                    "Video reference:",
                    video_uri
                )

            self.update_progress_safe(35)

            self.update_status(
                "Preparing audio processing..."
            )

            self.update_progress_safe(50)

            self.update_status(
                "Preparing speech processing..."
            )

            self.update_progress_safe(65)

            self.update_status(
                "Preparing translation..."
            )

            self.update_progress_safe(80)

            self.update_status(
                "Preparing dubbed audio..."
            )

            self.update_progress_safe(95)

            # ---------------------------------------------
            # فعلاً موتور واقعی را اجرا نمی‌کنیم
            # ---------------------------------------------

            self.update_progress_safe(100)

            Clock.schedule_once(
                lambda dt:
                self.dubbing_finished(),
                0
            )

        except Exception as e:

            print(
                "DUBBING WORKER ERROR:",
                repr(e)
            )

            print(
                traceback.format_exc()
            )

            Clock.schedule_once(
                lambda dt:
                self.dubbing_failed(str(e)),
                0
            )

    # =====================================================
    # PROGRESS
    # =====================================================

    def update_progress_safe(
        self,
        value
    ):

        Clock.schedule_once(
            lambda dt:
            self.set_progress(value),
            0
        )

    def set_progress(
        self,
        value
    ):

        try:

            self.progress_value = value

            self.progress_bar.value = value

        except Exception as e:

            print(
                "PROGRESS ERROR:",
                repr(e)
            )

    def update_status(
        self,
        text
    ):

        Clock.schedule_once(
            lambda dt:
            self.set_status(text),
            0
        )

    def set_status(
        self,
        text
    ):

        try:

            self.status_label.text = text

        except Exception as e:

            print(
                "STATUS ERROR:",
                repr(e)
            )

    # =====================================================
    # DUBBING FINISHED
    # =====================================================

    def dubbing_finished(self):

        self.processing = False

        self.progress_bar.value = 100

        self.dubbing_button.disabled = False
        self.select_button.disabled = False

        self.status_label.text = (
            "Ready for AI dubbing engine"
        )

        self.show_error(
            "DubaAI",
            (
                "Video was selected successfully.\n\n"
                "The application is stable, but the "
                "real AI dubbing engine has not been "
                "connected yet."
            )
        )

    # =====================================================
    # DUBBING FAILED
    # =====================================================

    def dubbing_failed(
        self,
        message
    ):

        self.processing = False

        self.dubbing_button.disabled = False
        self.select_button.disabled = False

        self.status_label.text = (
            "Dubbing error"
        )

        self.show_error(
            "Dubbing Error",
            message
        )

    # =====================================================
    # GENERAL ERROR
    # =====================================================

    def handle_error(
        self,
        title,
        error
    ):

        print(
            title,
            repr(error)
        )

        print(
            traceback.format_exc()
        )

        self.processing = False

        try:

            self.dubbing_button.disabled = False
            self.select_button.disabled = False

        except Exception:

            pass

        try:

            self.status_label.text = (
                "Error occurred"
            )

            self.show_error(
                title,
                str(error)
            )

        except Exception:

            pass

    # =====================================================
    # INFORMATION
    # =====================================================

    def show_information(
        self,
        instance
    ):

        content = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12)
        )

        info_text = (
            "[b]DubaAI[/b]\n\n"
            "AI Video Dubbing\n\n"
            "DubaAI is an intelligent video dubbing "
            "application designed to help creators "
            "make their content available to a wider "
            "audience in different languages.\n\n"
            "Choose a video, select the source and "
            "target languages, and let DubaAI handle "
            "the dubbing process.\n\n"
            "[b]Our vision[/b]\n"
            "Great content should never be limited "
            "by language.\n\n"
            "One video. More languages. "
            "More audience. 🌍\n\n"
            "Version: 1.0.0\n"
            "Developer: Abdullah Jafari\n\n"
            "Made with ❤️ for content creators."
        )

        info_label = Label(
            text=info_text,
            markup=True,
            font_size="15sp",
            halign="center",
            valign="middle"
        )

        info_label.bind(
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
            height=dp(52)
        )

        content.add_widget(
            info_label
        )

        content.add_widget(
            close_button
        )

        popup = Popup(
            title="About DubaAI",
            content=content,
            size_hint=(0.90, 0.80),
            auto_dismiss=False
        )

        close_button.bind(
            on_release=popup.dismiss
        )

        popup.open()

    # =====================================================
    # SHARE
    # =====================================================

    def share_app(
        self,
        instance
    ):

        try:

            if not ANDROID_AVAILABLE:

                raise RuntimeError(
                    "Android environment is not available."
                )

            if not PYJUS_AVAILABLE:

                raise RuntimeError(
                    "PyJNIus is not available."
                )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            current_activity = (
                PythonActivity.mActivity
            )

            share_intent = Intent()

            share_intent.setAction(
                Intent.ACTION_SEND
            )

            share_intent.setType(
                "text/plain"
            )

            share_text = (
                "DubaAI 🎙️🌍\n\n"
                "AI Video Dubbing\n\n"
                "One video. More languages. "
                "More audience.\n\n"
                "Developer: Abdullah Jafari"
            )

            share_intent.putExtra(
                Intent.EXTRA_TEXT,
                share_text
            )

            chooser = Intent.createChooser(
                share_intent,
                "Share DubaAI"
            )

            current_activity.startActivity(
                chooser
            )

            print(
                "Share intent launched successfully."
            )

        except Exception as e:

            self.status_label.text = (
                "Share error"
            )

            print(
                "SHARE ERROR:",
                repr(e)
            )

            self.show_error(
                "Share Error",
                str(e)
            )

    # =====================================================
    # ERROR POPUP
    # =====================================================

    def show_error(
        self,
        title,
        message
    ):

        try:

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

            close_button = Button(
                text="OK",
                size_hint_y=None,
                height=dp(50)
            )

            content.add_widget(
                label
            )

            content.add_widget(
                close_button
            )

            popup = Popup(
                title=str(title),
                content=content,
                size_hint=(0.90, 0.55),
                auto_dismiss=False
            )

            close_button.bind(
                on_release=popup.dismiss
            )

            popup.open()

        except Exception as e:

            print(
                "ERROR POPUP FAILED:",
                repr(e)
            )


# =========================================================
# APP START
# =========================================================

if __name__ == "__main__":

    try:

        DubaAI().run()

    except Exception as e:

        print(
            "FATAL APPLICATION ERROR:",
            repr(e)
        )

        print(
            traceback.format_exc()
        )
