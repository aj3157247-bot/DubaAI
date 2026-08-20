import os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

from android import activity
from jnius import autoclass, cast


class DubbingApp(App):

    def build(self):
        self.selected_video = None

        layout = BoxLayout(
            orientation="vertical",
            padding=30,
            spacing=20
        )

        self.title_label = Label(
            text="Persian AI Dubber",
            font_size="28sp",
            size_hint_y=None,
            height=70
        )

        self.status_label = Label(
            text="Please select a video",
            font_size="18sp"
        )

        select_button = Button(
            text="Select Video",
            font_size="20sp",
            size_hint_y=None,
            height=65
        )
        select_button.bind(on_release=self.select_video)

        dubbing_button = Button(
            text="Start Dubbing",
            font_size="20sp",
            size_hint_y=None,
            height=65
        )
        dubbing_button.bind(on_release=self.start_dubbing)

        layout.add_widget(self.title_label)
        layout.add_widget(self.status_label)
        layout.add_widget(select_button)
        layout.add_widget(dubbing_button)

        # Android activity result callback
        activity.bind(on_activity_result=self.on_activity_result)

        return layout

    def select_video(self, instance):
        try:
            # Android classes
            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            current_activity = PythonActivity.mActivity

            # Create Android file picker
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)

            intent.addCategory(
                Intent.CATEGORY_OPENABLE
            )

            # Select video files
            intent.setType("video/*")

            # Start Android picker
            current_activity.startActivityForResult(
                intent,
                1001
            )

            self.status_label.text = "Select a video..."

        except Exception as e:
            self.status_label.text = "Picker error"
            print("VIDEO PICKER ERROR:", repr(e))

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
                self.status_label.text = "Video selection cancelled"
                return

            if intent is None:
                self.status_label.text = "No video selected"
                return

            uri = intent.getData()

            if uri is None:
                self.status_label.text = "No video selected"
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
            self.status_label.text = "Selection error"
            print(
                "ACTIVITY RESULT ERROR:",
                repr(e)
            )

    def start_dubbing(self, instance):

        if not self.selected_video:
            self.status_label.text = (
                "Please select a video first"
            )
            return

        self.status_label.text = (
            "Dubbing started..."
        )

        print(
            "DUBBING VIDEO:",
            self.selected_video
        )

        # -------------------------------------------------
        # Dubbing engine will be connected here.
        # The selected video URI is available in:
        #
        # self.selected_video
        #
        # -------------------------------------------------


if __name__ == "__main__":
    DubbingApp().run()
