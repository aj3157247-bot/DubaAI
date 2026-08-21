[app]

title = Persian AI Dubber
package.name = dubaai
package.domain = org.dubaai

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt,bin,so,ffmpeg,mp4,avi,mov

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.1,pyjnius==1.7.0,faster-whisper==1.2.0,deep-translator==1.11.4,edge-tts==7.2.1,pydub==0.25.1,moviepy==1.0.3,gTTS==2.3.2,numpy==1.26.4

orientation = portrait

version = 1.0


# ==================================================
# ANDROID
# ==================================================

android.api = 33
android.minapi = 24

android.ndk = 27c
android.ndk_api = 24

android.archs = arm64-v8a

android.accept_sdk_license = True

android.enable_androidx = True


# ==================================================
# NATIVE LIBRARIES
# ==================================================

android.add_libs_armeabi_v7a =
android.add_libs_arm64_v8a = native/libs/arm64-v8a/*.so


# ==================================================
# ✅ ANDROID PERMISSIONS (FIXED)
# ==================================================

android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE


# ==================================================
# ✅ ANDROID MANIFEST
# ==================================================

android.manifest.extra = <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" android:minSdkVersion="33" />


# ==================================================
# ANDROID APPLICATION SETTINGS
# ==================================================

android.private_storage = True
android.allow_backup = False


# ==================================================
# PYTHON-FOR-ANDROID
# ==================================================

p4a.branch = master


# ==================================================
# BUILD
# ==================================================

log_level = 2
warn_on_root = 1


# ==================================================
# CONSOLE
# ==================================================

fullscreen = 0


# ==================================================
# SPLASH
# ==================================================

presplash.filename =


# ==================================================
# ICON
# ==================================================

icon.filename =
