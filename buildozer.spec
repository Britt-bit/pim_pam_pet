[app]

# App info
title = SpinAlert
package.name = spinalert
package.domain = org.spinalert
version = 1.0

# Source
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# Requirements
requirements = python3,kivy,plyer

# Android permissions
android.permissions = RECEIVE_BOOT_COMPLETED,VIBRATE,POST_NOTIFICATIONS

# Orientation
orientation = portrait

# Fullscreen
fullscreen = 0

# Android API
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True

# Icons (replace with your own 512x512 PNG)
# icon.filename = %(source.dir)s/icon.png

# Android entry point
android.entrypoint = org.kivy.android.PythonActivity

[buildozer]
log_level = 2
# 0 = no "running as root" prompt (OK for Docker/headless; never use `sudo buildozer` on native Linux)
warn_on_root = 0
