[app]

title = DubaAI
package.name = dubaai
package.domain = org.dubaai

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas,so,bin

version = 1.0.0

orientation = portrait

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.1,ffmpeg,openssl,av_codecs,libx264

fullscreen = 0

android.api = 35
android.minapi = 24

android.ndk = 27c
android.ndk_api = 24

android.archs = arm64-v8a

android.add_libs_arm64_v8a = native/libs/arm64-v8a/*.so

android.accept_sdk_license = True
android.enable_androidx = True

android.permissions = INTERNET

p4a.branch = master

log_level = 2


[buildozer]

log_level = 2
warn_on_root = 1
