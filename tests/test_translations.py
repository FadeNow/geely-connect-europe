"""The setup and options dialogs' text - strings.json and translations/*.json.

Nothing checked these files, and one fault was living in two of them: the
first setup step's description carried `\\n\\n` - an escaped backslash in the
JSON - so Home Assistant printed the characters `\\n\\n` where a paragraph
break belonged. The Bulgarian translation was the one that noticed (#91).

CONTRIBUTING asks for identical key sets across the files, and nothing enforced
that either - four of the six turned out to predate the whole new-platform
setup flow, since translated. A translation missing a key shows English in
that one field, and nobody who does not read the language will notice.
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "custom_components", "geely_connect")
TOKEN = re.compile(r"\{(\w+)\}")

# Keys a translation may still leave to English, by file. Empty: the gaps that
# were there when this check arrived - the new-platform setup flow, the
# reconfigure step and the x-vin repair in ar, fr, he and ru, and the repair in
# th - are translated. Kept so a future gap is a decision someone writes down,
# not something nobody notices.
KNOWN_GAPS: dict[str, frozenset] = {}


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
