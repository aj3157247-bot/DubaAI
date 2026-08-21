[app]

title = Persian AI Dubber
package.name = dubaai
package.domain = org.dubaai

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt,bin,so,ffmpeg,mp4,avi,mov

requirements = python3==3.14.2,kivy==2.3.1,pyjnius==1.7.0

orientation = portrait

version = 1.0


# ==================================================
# ANDROID
# ==================================================

android.api = 30
android.minapi = 21

android.ndk = 25c
android.ndk_api = 21

android.archs = arm64-v8a

android.accept_sdk_license = True

android.enable_androidx = True


# ==================================================
# NATIVE LIBRARIES
# ==================================================

android.add_libs_armeabi_v7a =
android.add_libs_arm64_v8a =


# ==================================================
# ANDROID PERMISSIONS
# ==================================================

android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE


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
