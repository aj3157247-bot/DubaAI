[app]

title = Persian AI Dubber
package.name = dubaai
package.domain = org.dubaai

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt,bin,so

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.1,pyjnius==1.7.0

orientation = portrait

version = 1.0

# --------------------------------------------------
# Android
# --------------------------------------------------

android.api = 35
android.minapi = 24

android.ndk = 27c
android.ndk_api = 24

android.archs = arm64-v8a

android.accept_sdk_license = True

android.enable_androidx = True

# --------------------------------------------------
# Native libraries
# --------------------------------------------------

android.add_libs_armeabi_v7a =
android.add_libs_arm64_v8a = native/libs/arm64-v8a/*.so

# --------------------------------------------------
# Android permissions
# --------------------------------------------------

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# --------------------------------------------------
# Android application settings
# --------------------------------------------------

android.private_storage = True

android.allow_backup = False

# --------------------------------------------------
# Python-for-Android
# --------------------------------------------------

p4a.branch = master

# --------------------------------------------------
# Build
# --------------------------------------------------

log_level = 2

warn_on_root = 1

# --------------------------------------------------
# Console
# --------------------------------------------------

fullscreen = 0

# --------------------------------------------------
# Splash
# --------------------------------------------------

presplash.filename =

# --------------------------------------------------
# Icon
# --------------------------------------------------

icon.filename =
