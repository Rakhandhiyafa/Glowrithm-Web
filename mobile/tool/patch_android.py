#!/usr/bin/env python3
"""Apply Glowrithm's Android settings after `flutter create` has generated the android/ folder.

Run from mobile/:   python tool/patch_android.py
  - INTERNET and CAMERA permissions, app label "Glowrithm"
  - android:allowBackup="false": encrypted secure-storage keys cannot be restored on another device
  - debug builds only: allow plain HTTP to a development server (release builds require HTTPS)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "android/app/src/main/AndroidManifest.xml"
DEBUG = ROOT / "android/app/src/debug/AndroidManifest.xml"


def main() -> None:
    if not MAIN.exists():
        sys.exit("android/ not found. Run first:  flutter create --org id.glowrithm --platforms android .")
    text = MAIN.read_text(encoding="utf-8")
    for permission in ("android.permission.INTERNET", "android.permission.CAMERA"):
        if permission not in text:
            text = text.replace("<application", f'<uses-permission android:name="{permission}"/>\n    <application', 1)
    text = re.sub(r'android:label="[^"]*"', 'android:label="Glowrithm"', text, count=1)
    if "android:allowBackup" not in text:
        text = text.replace("<application", '<application\n        android:allowBackup="false"', 1)
    MAIN.write_text(text, encoding="utf-8")

    if DEBUG.exists():
        debug = DEBUG.read_text(encoding="utf-8")
        if "usesCleartextTraffic" not in debug:
            debug = debug.replace("</manifest>", '    <application android:usesCleartextTraffic="true"/>\n</manifest>')
            DEBUG.write_text(debug, encoding="utf-8")
    print("Patched", MAIN.relative_to(ROOT), "and", DEBUG.relative_to(ROOT))


if __name__ == "__main__":
    main()
