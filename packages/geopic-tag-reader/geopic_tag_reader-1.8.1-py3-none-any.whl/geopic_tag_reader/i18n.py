import gettext
import os
from typing import Callable

localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "translations")


def init(lang_code: str = "en") -> Callable[[str], str]:
    lang = gettext.translation("geopic_tag_reader", localedir, languages=[lang_code], fallback=True)
    lang.install()
    return lang.gettext
