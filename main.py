import os

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget

from android import activity
from jnius import autoclass


class DubaAI(App):

    def build(self):
        self.selected_video = None
        self.progress_value = 0

        # -------------------------------------------------
        # Main layout
        # -------------------------------------------------

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12)
        )

        # -------------------------------------------------
        # Top bar
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Description
        # -------------------------------------------------

        description = Label(
            text="AI Video Dubbing\n"
                 "One video. More languages. More audience.",
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

        # -------------------------------------------------
        # Source language
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Target language
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Select Video
        # -------------------------------------------------

        select_button = Button(
            text="🎬  Select Video",
            font_size="19sp",
            size_hint_y=None,
            height=dp(62)
        )

        select_button.bind(
            on_release=self.select_video
        )

        root.add_widget(select_button)

        # -------------------------------------------------
        # Selected video status
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Progress bar
        # -------------------------------------------------

        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(12)
        )

        root.add_widget(self.progress_bar)

        # -------------------------------------------------
        # Start Dubbing
        # -------------------------------------------------

        self.dubbing_button = Button(
            text="▶  Start Dubbing",
            font_size="20sp",
            size_hint_y=None,
            height=dp(65)
        )

        self.dubbing_button.bind(
            on_release=self.start_dubbing
        )

        root.add_widget(self.dubbing_button)

        # Android activity result callback
        activity.bind(
            on_activity_result=self.on_activity_result
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

    # =====================================================
    # Select Video
    # =====================================================

    def select_video(self, instance):

        try:

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            current_activity = PythonActivity.mActivity

            intent = Intent(
                Intent.ACTION_OPEN_DOCUMENT
            )

            intent.addCategory(
                Intent.CATEGORY_OPENABLE
            )

            intent.setType("video/*")

            current_activity.startActivityForResult(
                intent,
                1001
            )

            self.status_label.text = (
                "Select a video..."
            )

        except Exception as e:

            self.status_label.text = (
                "Picker error"
            )

            print(
                "VIDEO PICKER ERROR:",
                repr(e)
            )

    # =====================================================
    # Android Activity Result
    # =====================================================

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        try:

            if request_code != 1001:
                return

            RESULT_OK = -1

            if result_code != RESULT_OK:

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

            self.selected_video = uri_string

            self.status_label.text = (
                "Video selected successfully"
            )

            print(
                "SELECTED VIDEO URI:",
                self.selected_video
            )

        except Exception as e:

            self.status_label.text = (
                "Selection error"
            )

            print(
                "ACTIVITY RESULT ERROR:",
                repr(e)
            )

    # =====================================================
    # Start Dubbing
    # =====================================================

    def start_dubbing(self, instance):

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

        self.progress_value = 0
        self.progress_bar.value = 0

        self.dubbing_button.disabled = True

        self.status_label.text = (
            "Dubbing started..."
        )

        print("================================")
        print("DUBAI DUBBING")
        print("Video:", self.selected_video)
        print("Source:", source)
        print("Target:", target)
        print("================================")

        # Temporary progress simulation.
        # The real AI dubbing engine will replace this.
        Clock.schedule_interval(
            self.update_progress,
            0.15
        )

    # =====================================================
    # Progress
    # =====================================================

    def update_progress(self, dt):

        self.progress_value += 1

        self.progress_bar.value = (
            self.progress_value
        )

        if self.progress_value < 20:

            self.status_label.text = (
                "Preparing video..."
            )

        elif self.progress_value < 40:

            self.status_label.text = (
                "Extracting audio..."
            )

        elif self.progress_value < 60:

            self.status_label.text = (
                "Processing speech..."
            )

        elif self.progress_value < 80:

            self.status_label.text = (
                "Translating..."
            )

        elif self.progress_value < 100:

            self.status_label.text = (
                "Preparing dubbed audio..."
            )

        else:

            self.status_label.text = (
                "Ready for AI dubbing engine"
            )

            self.dubbing_button.disabled = False

            return False

        return True

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
            "صدای هر زبان، به زبان تو 🌍🎙️\n\n"
            "DubaAI یک ابزار هوشمند برای دوبله "
            "ویدئو است که برای کمک به تولیدکنندگان "
            "محتوا ساخته شده است.\n\n"
            "هدف ما ساده است:\n"
            "محتوای خوب نباید به خاطر زبان محدود بماند.\n\n"
            "یک ویدئو، زبان‌های بیشتر، "
            "مخاطبان بیشتر.\n\n"
            "نسخه: 1.0.0\n"
            "سازنده: عبدالله جعفری\n\n"
            "ساخته‌شده با ❤️ برای دوستداران محتوا"
        )

        info_label = Label(
            text=info_text,
            markup=True,
            font_size="16sp",
            halign="center",
            valign="middle"
        )

        info_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
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
            size_hint=(0.90, 0.78),
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

            String = autoclass(
                "java.lang.String"
            )

            current_activity = PythonActivity.mActivity

            share_intent = Intent(
                Intent.ACTION_SEND
            )

            share_intent.setType(
                "text/plain"
            )

            share_text = (
                "DubaAI 🎙️🌍\n\n"
                "AI Video Dubbing\n"
                "یک ویدئو، زبان‌های بیشتر، "
                "مخاطبان بیشتر."
            )

            share_intent.putExtra(
                Intent.EXTRA_TEXT,
                String(share_text)
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


if __name__ == "__main__":
    DubaAI().run()
