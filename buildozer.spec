[app]
title = 联系人提醒
package.name = contactreminder
package.domain = org.contactreminder

source.dir = .
source.include_exts = py,png,jpg,kv,json
source.exclude_dirs = .venv,.buildozer,bin,.git,.github

version = 1.0.0

requirements = python3,kivy
orientation = portrait
fullscreen = 0

# Android 配置
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# 图标和启动画面（可选，有的话放上）
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1