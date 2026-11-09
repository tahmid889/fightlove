[app]
title = Dhaka Fight
package.name = dhakafight
package.domain = org.tahmid
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3,wav,ttf
version = 1.0
requirements = python3,kivy
orientation = landscape
fullscreen = 1

android.archs = arm64-v8a, armeabi-v7a
android.api = 33
android.minapi = 21
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
