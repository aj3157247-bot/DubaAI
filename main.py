import asyncio
import shutil
import subprocess
import threading
import time
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup


KV = r"""
<DubberUI>:
    orientation: "vertical"
    padding: "14dp"
    spacing: "10dp"

    Label:
        text: root.status
        size_hint_y: None
        height: "48dp"
        text_size: self.width, None
        halign: "center"
        valign: "middle"
        font_size: "18sp"

    BoxLayout:
        size_hint_y: None
        height: "52dp"
        spacing: "8dp"

        Button:
            text: "Select Video"
            on_release: root.open_picker()

        Button:
            text: "Start Dubbing"
            disabled: root.running
            on_release: root.start_dubbing()

    Label:
        text: root.selected_text
        size_hint_y: None
        height: "45dp"
        text_size: self.width, None
        halign: "center"
        valign: "middle"

    ProgressBar:
        id: progress
        max: 100
        value: 0
        size_hint_y: None
        height: "14dp"

    Label:
        text: "English → Persian"
        size_hint_y: None
        height: "35dp"
        halign: "center"

    Label:
        text: "Whisper → Translation → Persian Voice → MP4"
        size_hint_y: None
        height: "35dp"
        halign: "center"
        font_size: "13sp"
"""


class DubberUI(BoxLayout):

    status = StringProperty("Select a video")
    selected_text = StringProperty("No video selected")
    running = BooleanProperty(False)

    selected_file = None

    # ---------------------------------------------------------
    # VIDEO PICKER
    # ---------------------------------------------------------

    def open_picker(self):

        chooser = FileChooserListView(
            path=str(Path.home()),
            filters=[
                "*.mp4",
                "*.mkv",
                "*.mov",
                "*.avi",
                "*.webm",
                "*.m4v"
            ],
            multiselect=False
        )

        container = BoxLayout(
            orientation="vertical",
            spacing=8,
            padding=8
        )

        container.add_widget(chooser)

        buttons = BoxLayout(
            size_hint_y=None,
            height="50dp",
            spacing=8
        )

        from kivy.uix.button import Button

        choose_button = Button(
            text="Select"
        )

        cancel_button = Button(
            text="Cancel"
        )

        buttons.add_widget(
            choose_button
        )

        buttons.add_widget(
            cancel_button
        )

        container.add_widget(
            buttons
        )

        popup = Popup(
            title="Select Video",
            content=container,
            size_hint=(0.95, 0.9)
        )

        def choose(_):

            if chooser.selection:

                self.selected_file = (
                    chooser.selection[0]
                )

                self.selected_text = (
                    Path(
                        self.selected_file
                    ).name
                )

                self.status = (
                    "Video selected. "
                    "Click Start Dubbing."
                )

                popup.dismiss()

        choose_button.bind(
            on_release=choose
        )

        cancel_button.bind(
            on_release=popup.dismiss
        )

        popup.open()

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def set_status(
        self,
        text,
        progress=None
    ):

        def update(_):

            self.status = text

            if progress is not None:

                self.ids.progress.value = (
                    progress
                )

        Clock.schedule_once(
            update
        )

    # ---------------------------------------------------------
    # START
    # ---------------------------------------------------------

    def start_dubbing(self):

        if not self.selected_file:

            self.status = (
                "Please select a video first."
            )

            return

        if self.running:
            return

        self.running = True

        self.ids.progress.value = 0

        self.status = (
            "Starting..."
        )

        worker = threading.Thread(
            target=self._worker,
            daemon=True
        )

        worker.start()

    # ---------------------------------------------------------
    # WORKER
    # ---------------------------------------------------------

    def _worker(self):

        try:

            output = dub_video(
                Path(
                    self.selected_file
                ),
                self.set_status
            )

            self.running = False

            self.set_status(
                f"Completed: {output.name}",
                100
            )

        except Exception as error:

            self.running = False

            self.set_status(
                f"Error: {error}",
                0
            )


# ============================================================
# CHECK COMMAND
# ============================================================

def check_command(name):

    if shutil.which(name) is None:

        raise RuntimeError(
            f"{name} was not found. "
            f"Please install it and add it to PATH."
        )


# ============================================================
# RUN COMMAND
# ============================================================

def run_command(command):

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:

        raise RuntimeError(
            result.stderr[-4000:]
        )

    return result


# ============================================================
# VIDEO DURATION
# ============================================================

def get_duration(video):

    result = run_command([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video)
    ])

    return float(
        result.stdout.strip()
    )


# ============================================================
# EXTRACT AUDIO
# ============================================================

def extract_audio(
    video,
    work
):

    output = (
        work /
        "audio.wav"
    )

    run_command([
        "ffmpeg",
        "-y",

        "-i",
        str(video),

        "-vn",

        "-ac",
        "1",

        "-ar",
        "16000",

        "-c:a",
        "pcm_s16le",

        str(output)
    ])

    return output


# ============================================================
# WHISPER
# ============================================================

def transcribe(audio):

    from faster_whisper import WhisperModel

    model = WhisperModel(
        "small",
        device="cpu",
        compute_type="int8"
    )

    segments, info = model.transcribe(
        str(audio),
        language="en",
        beam_size=5,
        vad_filter=True
    )

    result = []

    for segment in segments:

        text = (
            segment.text
            .strip()
        )

        if not text:
            continue

        result.append({
            "start": float(
                segment.start
            ),

            "end": float(
                segment.end
            ),

            "text": text
        })

    return result


# ============================================================
# TRANSLATION
# ============================================================

def translate_segments(
    segments
):

    from deep_translator import (
        GoogleTranslator
    )

    translator = (
        GoogleTranslator(
            source="en",
            target="fa"
        )
    )

    translated = []

    for segment in segments:

        try:

            translated_text = (
                translator.translate(
                    segment["text"]
                )
            )

            if not translated_text:

                translated_text = (
                    segment["text"]
                )

        except Exception:

            translated_text = (
                segment["text"]
            )

        translated.append({

            "start":
                segment["start"],

            "end":
                segment["end"],

            "text":
                segment["text"],

            "fa":
                translated_text

        })

    return translated


# ============================================================
# TEXT TO SPEECH
# ============================================================

async def create_voice(
    text,
    filename
):

    import edge_tts

    voice = edge_tts.Communicate(

        text=text,

        voice=
        "fa-IR-FaridNeural",

        rate="+0%",

        volume="+0%"
    )

    await voice.save(
        str(filename)
    )


# ============================================================
# GENERATE ALL VOICES
# ============================================================

async def create_all_voices(
    segments,
    work
):

    files = []

    for index, segment in enumerate(
        segments
    ):

        filename = (
            work /
            f"voice_{index:05d}.mp3"
        )

        await create_voice(
            segment["fa"],
            filename
        )

        files.append(
            filename
        )

    return files


# ============================================================
# CHANGE AUDIO SPEED
# ============================================================

def change_speed(
    audio,
    ratio,
    work
):

    from pydub import AudioSegment

    source = (
        work /
        "speed_input.wav"
    )

    target = (
        work /
        "speed_output.wav"
    )

    audio.export(
        source,
        format="wav"
    )

    filters = []

    remaining = ratio

    while remaining > 2:

        filters.append(
            "atempo=2.0"
        )

        remaining /= 2

    while remaining < 0.5:

        filters.append(
            "atempo=0.5"
        )

        remaining /= 0.5

    filters.append(
        f"atempo={remaining:.5f}"
    )

    run_command([
        "ffmpeg",
        "-y",

        "-i",
        str(source),

        "-filter:a",
        ",".join(filters),

        str(target)
    ])

    return AudioSegment.from_file(
        target
    )


# ============================================================
# BUILD DUBBED AUDIO
# ============================================================

def build_dubbed_audio(
    segments,
    voice_files,
    duration,
    work
):

    from pydub import AudioSegment

    final_audio = (
        AudioSegment.silent(
            duration=int(
                duration * 1000
            )
        )
    )

    for segment, voice_file in zip(
        segments,
        voice_files
    ):

        if not voice_file.exists():
            continue

        audio = (
            AudioSegment.from_file(
                voice_file
            )
        )

        start = int(
            segment["start"] *
            1000
        )

        end = int(
            segment["end"] *
            1000
        )

        target_duration = (
            end - start
        )

        if target_duration <= 0:
            continue

        if len(audio) > target_duration:

            ratio = (
                len(audio) /
                target_duration
            )

            audio = change_speed(
                audio,
                ratio,
                work
            )

        if len(audio) > target_duration:

            audio = audio[
                :target_duration
            ]

        final_audio = (
            final_audio.overlay(
                audio,
                position=start
            )
        )

    output = (
        work /
        "persian_audio.wav"
    )

    final_audio.export(
        output,
        format="wav"
    )

    return output


# ============================================================
# CREATE FINAL VIDEO
# ============================================================

def create_video(
    original,
    audio,
    output
):

    run_command([

        "ffmpeg",
        "-y",

        "-i",
        str(original),

        "-i",
        str(audio),

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        "-c:v",
        "copy",

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-shortest",

        str(output)
    ])


# ============================================================
# COMPLETE DUBBING PROCESS
# ============================================================

def dub_video(
    video,
    progress
):

    check_command(
        "ffmpeg"
    )

    check_command(
        "ffprobe"
    )

    root = (
        Path(__file__)
        .resolve()
        .parent
    )

    temp_root = (
        root /
        "temp"
    )

    output_root = (
        root /
        "output"
    )

    temp_root.mkdir(
        exist_ok=True
    )

    output_root.mkdir(
        exist_ok=True
    )

    job = (
        temp_root /
        f"job_{int(time.time())}"
    )

    job.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    progress(
        "Extracting audio...",
        5
    )

    audio = extract_audio(
        video,
        job
    )

    # --------------------------------------------------------
    # STEP 2
    # --------------------------------------------------------

    progress(
        "Recognizing speech with Whisper...",
        20
    )

    segments = transcribe(
        audio
    )

    if not segments:

        raise RuntimeError(
            "No speech was detected."
        )

    # --------------------------------------------------------
    # STEP 3
    # --------------------------------------------------------

    progress(
        "Translating English to Persian...",
        40
    )

    segments = (
        translate_segments(
            segments
        )
    )

    # --------------------------------------------------------
    # STEP 4
    # --------------------------------------------------------

    progress(
        "Generating Persian voice...",
        60
    )

    voice_files = (
        asyncio.run(
            create_all_voices(
                segments,
                job
            )
        )
    )

    # --------------------------------------------------------
    # STEP 5
    # --------------------------------------------------------

    progress(
        "Synchronizing Persian audio...",
        75
    )

    duration = get_duration(
        video
    )

    dubbed_audio = (
        build_dubbed_audio(
            segments,
            voice_files,
            duration,
            job
        )
    )

    # --------------------------------------------------------
    # STEP 6
    # --------------------------------------------------------

    progress(
        "Creating final MP4...",
        90
    )

    output = (
        output_root /
        f"{video.stem}_persian.mp4"
    )

    create_video(
        video,
        dubbed_audio,
        output
    )

    # --------------------------------------------------------
    # DONE
    # --------------------------------------------------------

    progress(
        "Dubbing completed successfully.",
        100
    )

    return output


# ============================================================
# APP
# ============================================================

class PersianDubberApp(
    App
):

    title = (
        "Persian AI Dubber"
    )

    def build(self):

        Builder.load_string(
            KV
        )

        return DubberUI()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    PersianDubberApp().run()
