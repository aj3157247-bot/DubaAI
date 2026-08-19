[app]

title = Persian AI Dubber
package.name = persiandubber
package.domain = org.dubaai

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas

version = 1.0

orientation = portrait

requirements = python3,kivy

fullscreen = 0

android.api = 35
android.minapi = 24

android.archs = arm64-v8a

android.accept_sdk_license = True
android.enable_androidx = True

android.permissions = READ_MEDIA_VIDEO,READ_MEDIA_AUDIO,WRITE_EXTERNAL_STORAGE,INTERNET

p4a.branch = master

log_level = 2


[buildozer]

log_level = 2
warn_on_root = 1
