"""
国际化工具模块
负责自动检测语言并提供翻译函数
"""

from __future__ import annotations

import gettext
import locale
import os
from pathlib import Path


SUPPORTED_LANGS = {"en", "zh_CN", "ja", "es", "fr"}


def detect_language() -> str:
    """
    自动检测系统语言,返回支持的语言代码
    """
    lang = (
        os.environ.get("LC_ALL")
        or os.environ.get("LC_MESSAGES")
        or os.environ.get("LANG")
        or ""
    )
    if not lang:
        try:
            lang = locale.getdefaultlocale()[0] or ""
        except Exception:
            lang = ""

    lang = lang.split(".")[0].replace("-", "_")
    lang_lower = lang.lower()

    if lang_lower.startswith("zh"):
        return "zh_CN"
    if lang_lower.startswith("ja"):
        return "ja"
    if lang_lower.startswith("es"):
        return "es"
    if lang_lower.startswith("fr"):
        return "fr"
    if lang_lower.startswith("en"):
        return "en"
    return "en"


def setup_i18n():
    """
    初始化gettext并返回翻译函数
    """
    locale_dir = Path(__file__).parent / "locales"
    language = detect_language()

    try:
        translation = gettext.translation(
            "messages", localedir=locale_dir, languages=[language]
        )
    except Exception:
        translation = gettext.NullTranslations()

    return translation.gettext
