import os
import shutil
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

from android import activity
from jnius import autoclass


class DubaAI(App):

    APP_NAME = "DubaAI"
    APP_VERSION = "1.0.0"
    DEVELOPER = "Abdullah Jafari"

    REQUEST_VIDEO = 1001

    def build(self):

        self.selected_video = None
        self.selected_video_path = None

        self.dubbing_running = False

        # =================================================
        # Main Layout
        # =================================================

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(10)
        )

        # =================================================
        # Top Bar
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
        # Description
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
            height=dp(65)
        )

        description.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        root.add_widget(description)

        # =================================================
        # Source Language
        # =================================================

        source_label = Label(
            text="Source Language",
            font_size="17sp",
            size_hint_y=None,
            height=dp(32)
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
        # Target Language
        # =================================================

        target_label = Label(
            text="Dub Into",
            font_size="17sp",
            size_hint_y=None,
            height=dp(32)
        )

        root.add_widget(target_label)

        self.target_spinner = Spinner(
            text="Persian",
            values=self.get_target_languages(),
            font_size="17sp",
            size_hint_y=None,
            height=dp(52)
        )

        root.add_widget(self.target_spinner)

        # =================================================
        # Select Video
        # =================================================

        self.select_button = Button(
            text="Select Video",
            font_size="19sp",
            size_hint_y=None,
            height=dp(62)
        )

        self.select_button.bind(
            on_release=self.select_video
        )

        root.add_widget(self.select_button)

        # =================================================
        # Status
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
        # Progress
        # =================================================

        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(12)
        )

        root.add_widget(self.progress_bar)

        # =================================================
        # Start Dubbing
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
        # Android Activity Result
        # =================================================

        try:

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
    # Languages
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

    def get_target_languages(self):

        languages = self.get_languages()

        if "Auto Detect" in languages:
            languages.remove("Auto Detect")

        return languages

    # =====================================================
    # Select Video
    # =====================================================

    def select_video(self, instance):

        if self.dubbing_running:
            return

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

            # اجازه دسترسی طولانی‌تر به فایل
            try:

                intent.addFlags(
                    Intent.FLAG_GRANT_READ_URI_PERMISSION
                )

                intent.addFlags(
                    Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
                )

            except Exception:
                pass

            current_activity.startActivityForResult(
                intent,
                self.REQUEST_VIDEO
            )

            self.status_label.text = (
                "Select a video..."
            )

        except Exception as e:

            print(
                "VIDEO PICKER ERROR:",
                repr(e)
            )

            traceback.print_exc()

            self.status_label.text = (
                "Video picker error"
            )

            self.show_error(
                "Video Picker Error",
                str(e)
            )

    # =====================================================
    # Activity Result
    # =====================================================

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        try:

            if request_code != self.REQUEST_VIDEO:
                return

            RESULT_OK = -1

            if result_code != RESULT_OK:

                Clock.schedule_once(
                    lambda dt:
                    setattr(
                        self.status_label,
                        "text",
                        "Video selection cancelled"
                    )
                )

                return

            if intent is None:

                Clock.schedule_once(
                    lambda dt:
                    setattr(
                        self.status_label,
                        "text",
                        "No video selected"
                    )
                )

                return

            uri = intent.getData()

            if uri is None:

                Clock.schedule_once(
                    lambda dt:
                    setattr(
                        self.status_label,
                        "text",
                        "No video selected"
                    )
                )

                return

            self.selected_video = (
                uri.toString()
            )

            print(
                "SELECTED VIDEO URI:",
                self.selected_video
            )

            # نگه داشتن دسترسی به URI
            try:

                PythonActivity = autoclass(
                    "org.kivy.android.PythonActivity"
                )

                current_activity = (
                    PythonActivity.mActivity
                )

                content_resolver = (
                    current_activity.getContentResolver()
                )

                take_flags = (
                    intent.getFlags()
                    & 3
                )

                content_resolver.takePersistableUriPermission(
                    uri,
                    take_flags
                )

            except Exception as permission_error:

                print(
                    "PERSIST URI WARNING:",
                    repr(permission_error)
                )

            # کپی کردن فایل URI به cache
            self.status_label.text = (
                "Preparing selected video..."
            )

            threading.Thread(
                target=self.prepare_video_file,
                args=(uri,),
                daemon=True
            ).start()

        except Exception as e:

            print(
                "ACTIVITY RESULT ERROR:",
                repr(e)
            )

            traceback.print_exc()

            Clock.schedule_once(
                lambda dt:
                self.set_status(
                    "Video selection error"
                )
            )

    # =====================================================
    # Copy Android URI to local file
    # =====================================================

    def prepare_video_file(self, uri):

        try:

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            current_activity = (
                PythonActivity.mActivity
            )

            resolver = (
                current_activity.getContentResolver()
            )

            input_stream = (
                resolver.openInputStream(uri)
            )

            if input_stream is None:

                raise RuntimeError(
                    "Android could not open the selected video."
                )

            cache_dir = self.user_data_dir

            os.makedirs(
                cache_dir,
                exist_ok=True
            )

            output_path = os.path.join(
                cache_dir,
                "selected_video.mp4"
            )

            with open(
                output_path,
                "wb"
            ) as output_file:

                buffer = bytearray(1024 * 1024)

                while True:

                    count = input_stream.read(
                        buffer
                    )

                    if count <= 0:
                        break

                    output_file.write(
                        bytes(buffer[:count])
                    )

            input_stream.close()

            if not os.path.isfile(
                output_path
            ):

                raise RuntimeError(
                    "Video file was not copied."
                )

            if os.path.getsize(
                output_path
            ) <= 0:

                raise RuntimeError(
                    "Selected video file is empty."
                )

            self.selected_video_path = (
                output_path
            )

            print(
                "LOCAL VIDEO:",
                output_path
            )

            Clock.schedule_once(
                lambda dt:
                self.video_ready()
            )

        except Exception as e:

            print(
                "VIDEO COPY ERROR:",
                repr(e)
            )

            traceback.print_exc()

            Clock.schedule_once(
                lambda dt:
                self.video_prepare_failed(
                    str(e)
                )
            )

    # =====================================================
    # Video Ready
    # =====================================================

    def video_ready(self):

        self.status_label.text = (
            "Video selected successfully."
        )

        self.progress_bar.value = 0

        self.dubbing_button.disabled = False

    def video_prepare_failed(
        self,
        error
    ):

        self.selected_video_path = None

        self.status_label.text = (
            "Could not prepare video."
        )

        self.show_error(
            "Video Error",
            (
                "The video was selected, "
                "but Android could not copy it "
                "for processing.\n\n"
                + error
            )
        )

    # =====================================================
    # Start Dubbing
    # =====================================================

    def start_dubbing(self, instance):

        try:

            if self.dubbing_running:

                return

            if not self.selected_video:

                self.status_label.text = (
                    "Please select a video first."
                )

                return

            if not self.selected_video_path:

                self.status_label.text = (
                    "Please wait. Preparing video..."
                )

                return

            if not os.path.isfile(
                self.selected_video_path
            ):

                self.status_label.text = (
                    "Video file is unavailable."
                )

                return

            source = (
                self.source_spinner.text
            )

            target = (
                self.target_spinner.text
            )

            if target == "Auto Detect":

                self.status_label.text = (
                    "Please select a target language."
                )

                return

            if (
                source != "Auto Detect"
                and source == target
            ):

                self.status_label.text = (
                    "Source and target languages "
                    "must be different."
                )

                return

            # =============================================
            # IMPORTANT
            # =============================================

            # فعلاً موتور واقعی دوبله به APK متصل نیست.
            #
            # بنابراین این نسخه عمداً برنامه را
            # crash نمی‌کند و به‌جای اجرای fake dubbing
            # پیام واضح نمایش می‌دهد.

            self.status_label.text = (
                "Video is ready for the AI engine."
            )

            self.progress_bar.value = 100

            print(
                "================================"
            )

            print(
                "DubaAI"
            )

            print(
                "VIDEO:",
                self.selected_video_path
            )

            print(
                "SOURCE:",
                source
            )

            print(
                "TARGET:",
                target
            )

            print(
                "================================"
            )

            self.show_engine_not_connected()

        except Exception as e:

            print(
                "START DUBBING ERROR:",
                repr(e)
            )

            traceback.print_exc()

            self.dubbing_running = False

            self.dubbing_button.disabled = False

            self.show_error(
                "Dubbing Error",
                str(e)
            )

    # =====================================================
    # Engine Not Connected
    # =====================================================

    def show_engine_not_connected(self):

        content = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12)
        )

        message = Label(
            text=(
                "[b]Video is ready.[/b]\n\n"
                "The application is stable, "
                "but the real AI dubbing engine "
                "has not been connected yet.\n\n"
                "The next step is to connect:\n\n"
                "1. Speech recognition\n"
                "2. Translation\n"
                "3. Persian/target-language voice\n"
                "4. Audio/video merging\n\n"
                "Your selected video is ready."
            ),
            markup=True,
            font_size="15sp",
            halign="center",
            valign="middle"
        )

        message.bind(
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
            height=dp(52)
        )

        content.add_widget(message)
        content.add_widget(close_button)

        popup = Popup(
            title="DubaAI",
            content=content,
            size_hint=(0.90, 0.78),
            auto_dismiss=False
        )

        close_button.bind(
            on_release=popup.dismiss
        )

        popup.open()

    # =====================================================
    # Set Status
    # =====================================================

    def set_status(self, text):

        self.status_label.text = text

    # =====================================================
    # Information
    # =====================================================

    def show_information(self, instance):

        content = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12)
        )

        info_text = (
            "[b]DubaAI[/b]\n\n"
            "AI Video Dubbing\n\n"
            "Choose a video, select the "
            "source and target languages, "
            "and prepare it for AI dubbing.\n\n"
            "[b]Our vision[/b]\n"
            "Great content should never be "
            "limited by language.\n\n"
            "One video. More languages. "
            "More audience. 🌍\n\n"
            "Version: 1.0.0\n"
            "Developer: Abdullah Jafari"
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

        content.add_widget(info_label)
        content.add_widget(close_button)

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
    # Share
    # =====================================================

    def share_app(self, instance):

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

        except Exception as e:

            print(
                "SHARE ERROR:",
                repr(e)
            )

            self.show_error(
                "Share Error",
                str(e)
            )

    # =====================================================
    # Error Popup
    # =====================================================

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
            text=message,
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

        content.add_widget(label)
        content.add_widget(close_button)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.90, 0.60),
            auto_dismiss=False
        )

        close_button.bind(
            on_release=popup.dismiss
        )

        popup.open()


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":

    try:

        DubaAI().run()

    except Exception as e:

        print(
            "FATAL APPLICATION ERROR:",
            repr(e)
        )

        traceback.print_exc()
