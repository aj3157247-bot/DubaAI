import asyncio
import os
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

    _picker_callback = None

    # =========================================================
    # ANDROID VIDEO PICKER
    # =========================================================

    def open_picker(self):

        try:
            from android import activity
            from jnius import autoclass

            Intent = autoclass(
                "android.content.Intent"
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

            intent.addFlags(
                Intent.FLAG_GRANT_READ_URI_PERMISSION
            )

            intent.addFlags(
                Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
            )

            self._picker_callback = (
                self._on_video_selected
            )

            activity.bind(
                on_activity_result=
                self._picker_callback
            )

            activity.startActivityForResult(
                intent,
                1001
            )

            self.status = "Choose a video..."

        except Exception as error:

            self.status = (
                f"Picker error: {error}"
            )

    # =========================================================
    # PICKER RESULT
    # =========================================================

    def _on_video_selected(
        self,
        request_code,
        result_code,
        intent
    ):

        if request_code != 1001:
            return

        try:

            from android import activity
            from jnius import autoclass

            Activity = autoclass(
                "android.app.Activity"
            )

            # Unbind callback
            try:

                activity.unbind(
                    on_activity_result=
                    self._picker_callback
                )

            except Exception:
                pass

            # User cancelled
            if result_code != Activity.RESULT_OK:

                self.status = (
                    "Video selection cancelled."
                )

                return

            if intent is None:

                self.status = (
                    "No video was selected."
                )

                return

            uri = intent.getData()

            if uri is None:

                self.status = (
                    "Could not get selected video."
                )

                return

            self.status = (
                "Preparing selected video..."
            )

            # Copy Android URI to local storage
            local_file = (
                self._copy_uri_to_cache(
                    uri
                )
            )

            self.selected_file = (
                local_file
            )

            self.selected_text = (
                Path(
                    local_file
                ).name
            )

            self.status = (
                "Video selected. "
                "Click Start Dubbing."
            )

        except Exception as error:

            self.selected_file = None

            self.selected_text = (
                "No video selected"
            )

            self.status = (
                f"Video error: {error}"
            )

    # =========================================================
    # COPY ANDROID URI TO LOCAL FILE
    # =========================================================

    def _copy_uri_to_cache(
        self,
        uri
    ):

        from jnius import autoclass

        PythonActivity = autoclass(
            "org.kivy.android.PythonActivity"
        )

        activity_instance = (
            PythonActivity.mActivity
        )

        resolver = (
            activity_instance
            .getContentResolver()
        )

        # -----------------------------------------------------
        # Get original filename
        # -----------------------------------------------------

        filename = None
        cursor = None

        try:

            OpenableColumns = autoclass(
                "android.provider.OpenableColumns"
            )

            projection = [
                OpenableColumns.DISPLAY_NAME
            ]

            cursor = resolver.query(
                uri,
                projection,
                None,
                None,
                None
            )

            if cursor is not None:

                if cursor.moveToFirst():

                    index = (
                        cursor.getColumnIndex(
                            OpenableColumns.DISPLAY_NAME
                        )
                    )

                    if index >= 0:

                        filename = (
                            cursor.getString(
                                index
                            )
                        )

        except Exception:

            filename = None

        finally:

            if cursor is not None:

                try:
                    cursor.close()
                except Exception:
                    pass

        # -----------------------------------------------------
        # Fallback filename
        # -----------------------------------------------------

        if not filename:

            filename = (
                "selected_video.mp4"
            )

        filename = os.path.basename(
            str(filename)
        )

        # -----------------------------------------------------
        # Cache directory
        # -----------------------------------------------------

        cache_dir = Path(
            self._picker_cache_dir()
        )

        cache_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        destination = (
            cache_dir /
            filename
        )

        if destination.exists():

            destination = (
                cache_dir /
                f"video_{int(time.time())}_{filename}"
            )

        input_stream = None
        output_stream = None

        try:

            input_stream = (
                resolver.openInputStream(
                    uri
                )
            )

            if input_stream is None:

                raise RuntimeError(
                    "Android could not open "
                    "the selected video."
                )

            FileOutputStream = autoclass(
                "java.io.FileOutputStream"
            )

            output_stream = (
                FileOutputStream(
                    str(destination)
                )
            )

            # 1 MB buffer
            buffer = bytearray(
                1024 * 1024
            )

            while True:

                count = input_stream.read(
                    buffer
                )

                if count == -1:
                    break

                if count > 0:

                    output_stream.write(
                        buffer,
                        0,
                        count
                    )

            output_stream.flush()

        finally:

            if input_stream is not None:

                try:
                    input_stream.close()
                except Exception:
                    pass

            if output_stream is not None:

                try:
                    output_stream.close()
                except Exception:
                    pass

        # -----------------------------------------------------
        # Verify copied file
        # -----------------------------------------------------

        if not destination.exists():

            raise RuntimeError(
                "Failed to copy video."
            )

        if destination.stat().st_size <= 0:

            raise RuntimeError(
                "Selected video is empty."
            )

        return str(destination)

    # =========================================================
    # APP STORAGE
    # =========================================================

    def _picker_cache_dir(self):

        try:

            from android.storage import (
                app_storage_path
            )

            base = Path(
                app_storage_path()
            )

        except Exception:

            base = Path(
                self._fallback_storage_path()
            )

        return str(
            base /
            "selected_videos"
        )

    # =========================================================
    # FALLBACK STORAGE
    # =========================================================

    def _fallback_storage_path(self):

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity_instance = (
                PythonActivity.mActivity
            )

            cache_dir = (
                activity_instance.getCacheDir()
            )

            return str(
                cache_dir.getAbsolutePath()
            )

        except Exception:

            return str(
                Path.home()
            )

    # =========================================================
    # STATUS
    # =========================================================

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

    # =========================================================
    # START DUBBING
    # =========================================================

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

        self.status = "Starting..."

        worker = threading.Thread(
            target=self._worker,
            daemon=True
        )

        worker.start()

    # =========================================================
    # WORKER
    # =========================================================

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


# =============================================================
# CHECK COMMAND
# =============================================================

def check_command(name):

    if shutil.which(name) is None:

        raise RuntimeError(
            f"{name} was not found. "
            f"Please install it and add it to PATH."
        )


# =============================================================
# RUN COMMAND
# =============================================================

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


# =============================================================
# VIDEO DURATION
# =============================================================

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


# =============================================================
# EXTRACT AUDIO
# =============================================================

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


# =============================================================
# WHISPER
# =============================================================

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

            "start":
                float(segment.start),

            "end":
                float(segment.end),

            "text":
                text
        })

    return result


# =============================================================
# TRANSLATION
# =============================================================

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


# =============================================================
# TEXT TO SPEECH
# =============================================================

async def create_voice(
    text,
    filename
):

    import edge_tts

    voice = edge_tts.Communicate(
        text=text,
        voice="fa-IR-FaridNeural",
        rate="+0%",
        volume="+0%"
    )

    await voice.save(
        str(filename)
    )


# =============================================================
# GENERATE ALL VOICES
# =============================================================

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


# =============================================================
# CHANGE AUDIO SPEED
# =============================================================

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


# =============================================================
# BUILD DUBBED AUDIO
# =============================================================

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


# =============================================================
# CREATE FINAL VIDEO
# =============================================================

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


# =============================================================
# COMPLETE DUBBING PROCESS
# =============================================================

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

    # ---------------------------------------------------------
    # STEP 1
    # ---------------------------------------------------------

    progress(
        "Extracting audio...",
        5
    )

    audio = extract_audio(
        video,
        job
    )

    # ---------------------------------------------------------
    # STEP 2
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # STEP 3
    # ---------------------------------------------------------

    progress(
        "Translating English to Persian...",
        40
    )

    segments = (
        translate_segments(
            segments
        )
    )

    # ---------------------------------------------------------
    # STEP 4
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # STEP 5
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # STEP 6
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # DONE
    # ---------------------------------------------------------

    progress(
        "Dubbing completed successfully.",
        100
    )

    return output


# =============================================================
# APP
# =============================================================

class PersianDubberApp(App):

    title = "Persian AI Dubber"

    def build(self):

        Builder.load_string(
            KV
        )

        return DubberUI()


# =============================================================
# START
# =============================================================

if __name__ == "__main__":

    PersianDubberApp().run()
