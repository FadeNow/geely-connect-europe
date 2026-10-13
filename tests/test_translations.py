"""The setup and options dialogs' text - strings.json and translations/*.json.

Nothing checked these files, and one fault was living in two of them: the
first setup step's description carried `\\n\\n` - an escaped backslash in the
JSON - so Home Assistant printed the characters `\\n\\n` where a paragraph
break belonged. The Bulgarian translation was the one that noticed (#91).

CONTRIBUTING asks for identical key sets across the files, and nothing enforced
that either - four of the six turned out to predate the whole new-platform
setup flow. A translation missing a key shows English in that one field, and
nobody who does not read the language will notice.
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "custom_components", "geely_connect")
TOKEN = re.compile(r"\{(\w+)\}")

# The gaps that were already there when this check arrived: the new-platform
# setup flow, the reconfigure step and the x-vin repair, which shipped in
# English only. Home Assistant shows the English text for each of them. They
# are listed so the debt is visible and cannot grow - a translation that fills
# one in must take it off this list, and no new key may be left out.
_X_VIN_REPAIR = frozenset({
    "issues.x_vin_missing.description", "issues.x_vin_missing.title"})
_NEW_PLATFORM = _X_VIN_REPAIR | {
    "config.abort.reconfigure_successful",
    "config.error.invalid_credentials",
    "config.error.network_unreachable",
    "config.step.platform.data.platform",
    "config.step.platform.description",
    "config.step.platform.title",
    "config.step.user.data.platform",
    "config.step.zeekr_login.data.country_code",
    "config.step.zeekr_login.data.email",
    "config.step.zeekr_login.data.password",
    "config.step.zeekr_login.data.poll_mode",
    "config.step.zeekr_login.data.pressure_unit",
    "config.step.zeekr_login.data.store_password",
    "config.step.zeekr_login.description",
    "config.step.zeekr_login.title",
    "config.step.zeekr_pick.data.vin",
    "config.step.zeekr_pick.description",
    "config.step.zeekr_pick.title",
    "options.step.init.data.zeekr_enc_vin",
}
KNOWN_GAPS = {
    "ar.json": _NEW_PLATFORM,
    "fr.json": _NEW_PLATFORM,
    "he.json": _NEW_PLATFORM,
    "ru.json": _NEW_PLATFORM,
    "th.json": _X_VIN_REPAIR,
}


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _flat(tree, prefix=""):
    out = {}
    for key, value in tree.items():
        if isinstance(value, dict):
            out.update(_flat(value, prefix + key + "."))
        else:
            out[prefix + key] = value
    return out


def _tables():
    paths = [os.path.join(PKG, "strings.json")] + sorted(
        glob.glob(os.path.join(PKG, "translations", "*.json")))
    assert len(paths) > 2, paths
    return {os.path.relpath(p, PKG): _flat(_load(p)) for p in paths}


def test_no_dialog_shows_an_escaped_line_break():
    for name, table in _tables().items():
        for key, text in table.items():
            assert "\\n" not in text, (
                f"{name} {key} holds a literal backslash-n, which the dialog "
                f"prints as two characters - write \\n in the JSON, not \\\\n")


def test_every_translation_has_the_english_key_set_and_placeholders():
    english = _flat(_load(os.path.join(PKG, "translations", "en.json")))
    assert len(english) > 40, len(english)
    for name, table in _tables().items():
        known = KNOWN_GAPS.get(os.path.basename(name), frozenset())
        missing = set(english) - set(table)
        assert not missing - known, f"{name} is missing {sorted(missing - known)}"
        assert not known - missing, (
            f"{name} now translates {sorted(known - missing)} - take them off "
            f"KNOWN_GAPS")
        extra = sorted(set(table) - set(english))
        assert not extra, f"{name} has keys English does not: {extra}"
        for key, text in table.items():
            assert text.strip(), f"{name} {key} is empty"
            # Home Assistant fills these in. One a translation invents is
            # printed in braces; one it drops loses the email or car name the
            # sentence was about.
            assert set(TOKEN.findall(text)) == set(TOKEN.findall(english[key])), (
                f"{name} {key} has placeholders {sorted(TOKEN.findall(text))}, "
                f"English has {sorted(TOKEN.findall(english[key]))}")


def test_strings_json_is_the_english_translation():
    """Home Assistant builds en.json from strings.json; a hand edit to one of
    them alone leaves the other stale."""
    assert _load(os.path.join(PKG, "strings.json")) == _load(
        os.path.join(PKG, "translations", "en.json"))
