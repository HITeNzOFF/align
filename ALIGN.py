from __future__ import annotations
import sys
import os
import re
import json
import time
import struct
import bisect
import shutil
import datetime
import urllib.request
import urllib.error
from typing import List, Dict, Set, Union, Tuple, Optional

try:
    import mobase
    HAS_MOBASE = True
except ImportError:
    mobase = None
    HAS_MOBASE = False

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
        QProgressBar, QMessageBox, QTableWidget, QTableWidgetItem,
        QHeaderView, QLineEdit, QComboBox, QPlainTextEdit,
        QAbstractItemView, QSpinBox, QCheckBox, QMenu, QWidget,
        QApplication, QInputDialog, QFileDialog
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QPoint
    from PyQt6.QtGui import QIcon, QColor, QKeySequence, QShortcut
    IS_QT6 = True
    CHECKED = Qt.CheckState.Checked
    UNCHECKED = Qt.CheckState.Unchecked
    FLAG_USER_CHECKABLE = Qt.ItemFlag.ItemIsUserCheckable
    FLAG_ENABLED = Qt.ItemFlag.ItemIsEnabled
    FLAG_SELECTABLE = Qt.ItemFlag.ItemIsSelectable
    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    SELECT_ROWS = QAbstractItemView.SelectionBehavior.SelectRows
    NO_EDIT_TRIGGERS = QAbstractItemView.EditTrigger.NoEditTriggers
    CUSTOM_CONTEXT_MENU = Qt.ContextMenuPolicy.CustomContextMenu
    ECHO_PASSWORD = QLineEdit.EchoMode.Password
    ECHO_NORMAL = QLineEdit.EchoMode.Normal
    RESIZE_FIXED = QHeaderView.ResizeMode.Fixed
    RESIZE_STRETCH = QHeaderView.ResizeMode.Stretch
    WINDOW_MIN_MAX = Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint
except ImportError:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
        QProgressBar, QMessageBox, QTableWidget, QTableWidgetItem,
        QHeaderView, QLineEdit, QComboBox, QPlainTextEdit,
        QAbstractItemView, QSpinBox, QCheckBox, QMenu, QWidget,
        QApplication, QInputDialog, QShortcut, QFileDialog
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QPoint
    from PyQt5.QtGui import QIcon, QColor, QKeySequence
    IS_QT6 = False
    CHECKED = Qt.Checked
    UNCHECKED = Qt.Unchecked
    FLAG_USER_CHECKABLE = Qt.ItemIsUserCheckable
    FLAG_ENABLED = Qt.ItemIsEnabled
    FLAG_SELECTABLE = Qt.ItemIsSelectable
    ALIGN_CENTER = Qt.AlignCenter
    SELECT_ROWS = QAbstractItemView.SelectRows
    NO_EDIT_TRIGGERS = QAbstractItemView.NoEditTriggers
    CUSTOM_CONTEXT_MENU = Qt.CustomContextMenu
    ECHO_PASSWORD = QLineEdit.Password
    ECHO_NORMAL = QLineEdit.Normal
    RESIZE_FIXED = QHeaderView.Fixed
    RESIZE_STRETCH = QHeaderView.Stretch
    WINDOW_MIN_MAX = Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint

APP_NAME = "Align"
APP_VERSION = "1.4.0"
USER_AGENT = f"{APP_NAME}/{APP_VERSION}"

FLAG_PLAIN = FLAG_ENABLED | FLAG_SELECTABLE

SEPARATOR_SUFFIX = "_separator"
ICON_LOCK = "\U0001f512"
ICON_UNLOCK = "\U0001f513"

MODE_MODS = 0
MODE_PLUGINS = 1

OFFICIAL_MASTERS_LOWER = {
    "skyrim.esm", "update.esm", "dawnguard.esm", "hearthfires.esm", "dragonborn.esm",
    "fallout4.esm", "dlcrobot.esm", "dlcworkshop01.esm", "dlccoast.esm",
    "dlcworkshop02.esm", "dlcworkshop03.esm", "dlcnukaworld.esm",
    "starfield.esm", "sfbgs003.esm", "sfbgs004.esm", "sfbgs006.esm", "sfbgs007.esm", "sfbgs008.esm",
    "falloutnv.esm", "deadmoney.esm", "honesthearts.esm", "oldworldblues.esm", "lonesomeroad.esm",
    "oblivion.esm"
}

KNOWN_GAMES = [
    ("Skyrim Special Edition", "Skyrim.esm", ["Skyrim Special Edition", "Skyrim Special Edition GOG"]),
    ("Skyrim VR", "SkyrimVR.esm", ["Skyrim VR"]),
    ("Fallout 4", "Fallout4.esm", ["Fallout4", "Fallout 4"]),
    ("Starfield", "Starfield.esm", ["Starfield"]),
    ("Fallout New Vegas", "FalloutNV.esm", ["FalloutNV"]),
    ("Skyrim (LE)", "Skyrim.esm", ["Skyrim"]),
    ("Oblivion", "Oblivion.esm", ["Oblivion"])
]

LOOT_GAME_REPOS = {
    "skyrimse": ("Skyrim Special Edition", ["Skyrim Special Edition", "Skyrim Special Edition GOG"]),
    "skyrimvr": ("Skyrim VR", ["Skyrim VR"]),
    "fallout4": ("Fallout 4", ["Fallout 4", "Fallout4"]),
    "starfield": ("Starfield", ["Starfield"]),
    "falloutnv": ("Fallout New Vegas", ["Fallout New Vegas", "FalloutNV"]),
    "skyrim": ("Skyrim (LE)", ["Skyrim"]),
    "oblivion": ("Oblivion", ["Oblivion"])
}

LOOT_BRANCH_CANDIDATES = ("v0.26", "v0.21", "v0.18", "master", "main")


PRESETS = {
    "Google Gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash"
    },
    "OpenRouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "meta-llama/llama-3.3-70b-instruct:free"
    },
    "DeepSeek": {
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat"
    },
    "OpenAI": {
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini"
    },
    "Ollama": {
        "url": "http://localhost:11434/v1/chat/completions",
        "model": "llama3.1:8b"
    },
    "Custom": {
        "url": "",
        "model": ""
    }
}

MO2_CATEGORIES = {
    1: "Armor",
    2: "Audio",
    3: "Cities",
    4: "Clothing",
    5: "Combat",
    6: "Creatures",
    7: "Environment",
    8: "Gameplay",
    9: "Hair/Face",
    10: "Immersion",
    11: "Landscape",
    12: "Models/Textures",
    13: "New Lands",
    14: "NPC",
    15: "Overhauls",
    16: "Patches",
    17: "Bugfixes",
    18: "Quests",
    19: "UI",
    20: "Utilities",
    21: "Visuals",
    22: "Weapons",
    24: "Followers",
    26: "Body/Mesh",
    27: "Animations",
    28: "Skeleton"
}

SYSTEM_PROMPT = """You are Align, an expert game modding assistant for Bethesda games (Skyrim, Fallout, Starfield).
Your task is to organize and sort the provided list of mods for the Mod Organizer 2 Left Panel (resource overwrite order).

CRITICAL OVERRIDE RULES:
- User Custom Rules and Locked Mods have ABSOLUTE PRIORITY over the general overwrite hierarchy. If the user specifies that a mod must stay in a certain position or follow another mod, you MUST obey that rule regardless of category.

METADATA & ASSET TAGS:
- Input items may include bracketed metadata at the end, such as "ModName [SKSE, Mesh, Tex, UI, Anim, Script, FaceGen, ESP, BSA | nx:12345 | cat:UI]".
- Use these physical asset tags and Nexus IDs to accurately determine what files a mod overrides (e.g., pure texture replacers vs. SKSE plugins vs. NPC facegen overhauls).
- Do NOT include the bracketed "[...]" metadata in your output strings.

REQUIREMENTS FOR SEPARATORS:
- Group mods into clear logical sections using separators.
- A separator MUST strictly end with the suffix "_separator" (e.g., "[01] Core & Frameworks_separator", "[02] User Interface_separator", "[03] Audio & Sounds_separator", "[04] Environment & Textures_separator", "[05] Body & Skeletons_separator", "[06] Weapons & Armor_separator", "[07] Animations & Combat_separator", "[08] NPC & Overhauls_separator", "[09] Weather & Lighting_separator", "[10] Patches & Output_separator").
- Existing separators in the input may be kept, renamed or replaced unless instructed otherwise. Never leave a separator empty: every separator must be followed by at least one mod.
- Do not use the characters < > : " / \\ | ? * in separator names.
- In ascending priority order, place the separator DIRECTLY BEFORE the group of mods it categorizes.

GENERAL OVERWRITE ORDER RULES (from LOWEST priority to HIGHEST priority):
1. Engine fixes, SKSE plugins, Base Frameworks (e.g. Address Library, PapyrusTweaks)
2. UI, HUD, Menus, Fonts
3. Audio, Music, Voice lines
4. Base landscape, Architecture, Core Meshes/Textures (e.g. SMIM, Noble Skyrim)
5. Body meshes, Skeletons (XP32), Physics bodies
6. Specific retextures, Armor, Weapons, Clothing
7. Animations & Combat frameworks (Nemesis, Pandora, MCO, Vanargand, OAR)
8. NPC Overhauls, Skin textures, Facegens
9. World edits, City expansions, Weather, Lighting (Lux, ELFX)
10. Dynamic patcher outputs (Synthesis, TexGen, DynDOLOD, Nemesis Output), Late Overwrites, Compatibility Patches

OUTPUT FORMAT:
Return ONLY a valid JSON array containing the exact sorted order (including all mods and newly created/retained separators) from LOWEST to HIGHEST priority.
Copy every existing mod name (or numeric ID if indexed mode is requested) EXACTLY as given, without any bracketed metadata tags. Never rename mods.
Do not omit any existing mods. Do not output markdown commentary or explanations outside the JSON array.
"""

PLUGIN_SYSTEM_PROMPT = """You are Align, an expert Bethesda Load Order optimizer (LOOT + AI hybrid) for Skyrim, Fallout, and Starfield.
Your task is to sort the provided Right Panel plugin load order (.esm, .esp, .esl) from top (earliest loading) to bottom (latest loading / winning record overrides).

STRICT BINARY, LOOT & ENGINE RULES:
1. NEVER invent or output "_separator" entries. Output ONLY the exact plugin filenames (or numeric IDs in Compact ID Mode).
2. All Master files ([ESM] flag or .esm/.esl masters) MUST load before non-master plugins.
3. Every plugin MUST load strictly AFTER all of its listed binary master dependencies ("masters: ...") and LOOT Masterlist rules ("loot_after: ...").
4. Respect LOOT group assignments ("loot_grp: ...#rank") where lower rank numbers load earlier and higher rank numbers load later.
5. User Custom Rules and Locked Plugins have ABSOLUTE PRIORITY (as long as they do not violate binary master dependencies).

LOGICAL PLUGIN LOAD ORDER HIERARCHY (from earliest to latest):
1. Official Game Masters & DLCs, Unofficial Patches (USSEP / UFO4P), Core ESM Frameworks
2. Bugfixes, Engine & Gameplay Frameworks, UI Plugins
3. New Lands, Quests, Factions, Large Overhauls
4. Weather & Audio Overhauls
5. Cities, Settlements, World Edits, Interiors
6. Items, Weapons, Armor, Crafting, Perk/Magic/Combat Overhauls
7. NPCs, Followers, Visual/Appearance Overhauls
8. Interior & Exterior Lighting (e.g., Lux, ELFX, Window Shadows)
9. Compatibility Patches (always placed after both mods they patch)
10. Late Loaders: Alternate Start, Water (Water for ENB, Realistic Water Two), Map plugins (Flat World Map Framework), Bashed Patch, Synthesis.esp, Occlusion.esp, DynDOLOD.esp

OUTPUT FORMAT:
Return ONLY a valid JSON array containing the exact sorted plugin order from earliest to latest.
Do not include bracketed "[...]" metadata tags in output strings. Do not omit any plugins.
"""

LOCKED_HEADER = "CRITICAL LOCKED ITEMS (DO NOT CHANGE THEIR RELATIVE POSITIONS OR DEMOTE THEM):\n"
KEEP_SEPS_RULE = "STRICT SEPARATOR RULE: Do NOT invent new separators. Keep ONLY the existing '_separator' items from the input and sort mods into them."
RULES_HEADER = "USER CUSTOM RULES & INVARIANTS (STRICT PRIORITY OVER STANDARD HIERARCHY):\n"
SORT_HEADER = "Sort and categorize the following items from lowest priority (top) to highest priority (bottom):\n"
COMPACT_SORT_HEADER = (
    "COMPACT ID MODE: Each input item is given as \"ID: Name [optional metadata]\".\n"
    "Return a JSON array containing ONLY the integer IDs (and string names of separators ending with \"_separator\" if sorting Left Panel mods), "
    "ordered from lowest to highest priority.\n"
    "Input items:\n"
)

CHARS_PER_TOKEN = 4
OPTIONAL_PAYLOAD_PARAMS = ("reasoning_effort", "temperature")
RETRYABLE_HTTP_CODES = (429, 500, 502, 503, 504)
MAX_RETRIES = 2

DEFAULT_REQUEST_TIMEOUT = 300
MIN_REQUEST_TIMEOUT = 10
MAX_REQUEST_TIMEOUT = 3600

_INVALID_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_META_TAG_SUFFIX_RE = re.compile(r"\s*\[[^\]]*\]$")
_BYTEARRAY_RE = re.compile(r"^@ByteArray\((.*)\)$")
_ACTIVE_WORKERS: List[QThread] = []


MINIMAL_STYLESHEET = """
QDialog {
    background-color: #141417;
    color: #e4e4e7;
    font-size: 12px;
}
QLabel {
    color: #e4e4e7;
    background: transparent;
}
QCheckBox {
    color: #e4e4e7;
    spacing: 6px;
}
QLineEdit, QPlainTextEdit, QComboBox, QSpinBox {
    background-color: #1f1f24;
    color: #f4f4f5;
    border: 1px solid #32323a;
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #3b82f6;
    background-color: #242429;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #1f1f24;
    color: #f4f4f5;
    border: 1px solid #32323a;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    outline: 0;
}
QPushButton {
    background-color: #242429;
    color: #e4e4e7;
    border: 1px solid #34343d;
    border-radius: 4px;
    padding: 4px 10px;
}
QPushButton:hover {
    background-color: #2e2e36;
    border-color: #4a4a57;
}
QPushButton:pressed {
    background-color: #1c1c21;
}
QPushButton:disabled {
    background-color: #1a1a1f;
    color: #52525b;
    border-color: #27272e;
}
QPushButton:checked {
    background-color: #1e3a8a;
    color: #ffffff;
    border-color: #3b82f6;
}
QPushButton::menu-indicator {
    image: none;
    width: 0px;
}
QPushButton#btnPrimary {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    border: 1px solid #1d4ed8;
}
QPushButton#btnPrimary:hover {
    background-color: #1d4ed8;
}
QPushButton#btnPrimary:disabled {
    background-color: #1f2430;
    color: #52525b;
    border-color: #27272e;
}
QPushButton#btnDanger {
    background-color: #dc2626;
    color: #ffffff;
    font-weight: 600;
    border: 1px solid #b91c1c;
}
QPushButton#btnDanger:hover {
    background-color: #b91c1c;
}
QPushButton#btnSuccess {
    background-color: #16a34a;
    color: #ffffff;
    font-weight: 600;
    border: 1px solid #15803d;
}
QPushButton#btnSuccess:hover {
    background-color: #15803d;
}
QPushButton#btnSuccess:disabled {
    background-color: #1a241e;
    color: #52525b;
    border-color: #27272e;
}
QTableWidget {
    background-color: #18181c;
    alternate-background-color: #1c1c21;
    color: #e4e4e7;
    border: 1px solid #2d2d35;
    border-radius: 4px;
    outline: 0;
    selection-background-color: #27374d;
    selection-color: #ffffff;
}
QTableWidget::item {
    padding: 2px 6px;
    color: #e4e4e7;
}
QTableWidget::item:selected {
    background-color: rgba(59, 130, 246, 75);
    color: #ffffff;
}
QHeaderView::section {
    background-color: #202026;
    color: #a1a1aa;
    border: none;
    border-bottom: 1px solid #2d2d35;
    border-right: 1px solid #27272e;
    padding: 5px 6px;
    font-weight: 600;
}
QMenu {
    background-color: #1f1f24;
    color: #e4e4e7;
    border: 1px solid #32323a;
    padding: 4px;
}
QMenu::item {
    padding: 5px 20px;
    border-radius: 3px;
}
QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background: #32323a;
    margin: 4px 0;
}
QProgressBar {
    border: none;
    background-color: #242429;
    border-radius: 2px;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 2px;
}
"""


def get_app_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def find_app_icon() -> QIcon:
    base = get_app_base_dir()
    for fname in ("align_icon.png", "align_icon.ico", "ai_sorter_icon.png", "ai_sorter_icon.ico"):
        fpath = os.path.join(base, fname)
        if os.path.exists(fpath):
            return QIcon(fpath)
    return QIcon()


def sanitize_separator(name: str) -> str:
    base = name[:-len(SEPARATOR_SUFFIX)] if name.endswith(SEPARATOR_SUFFIX) else name
    base = _INVALID_FS_CHARS.sub("-", base).strip().rstrip(". ")
    base = base[:100].strip()
    if not base:
        base = "Section"
    return base + SEPARATOR_SUFFIX


def _clean_ini_value(raw: str) -> str:
    val = raw.strip().strip('"')
    m = _BYTEARRAY_RE.match(val)
    if m:
        val = m.group(1)
    return val.replace("\\\\", "\\")


def _unquote_yaml_scalar(val: str) -> str:
    s = val.strip()
    if not s:
        return ""
    if s[0] == "'" and "'" in s[1:]:
        end = s.rfind("'")
        return s[1:end].replace("''", "'")
    if s[0] == '"' and '"' in s[1:]:
        end = s.rfind('"')
        return s[1:end].replace('\\"', '"')
    if " #" in s:
        s = s.split(" #", 1)[0].strip()
    return s


def detect_loot_game_repo(plugin_names: List[str], profile_path: str, game_data_path: str) -> str:
    lower_set = {p.lower() for p in plugin_names}
    if "starfield.esm" in lower_set:
        return "starfield"
    if "fallout4.esm" in lower_set:
        return "fallout4"
    if "falloutnv.esm" in lower_set:
        return "falloutnv"
    if "skyrimvr.esm" in lower_set:
        return "skyrimvr"
    if "oblivion.esm" in lower_set:
        return "oblivion"
    if "skyrim.esm" in lower_set:
        if "update.esm" in lower_set or any(p.startswith("cc") for p in lower_set):
            return "skyrimse"
        return "skyrimse"

    hint = (profile_path + " " + game_data_path).lower()
    if "starfield" in hint:
        return "starfield"
    if "fallout 4" in hint or "fallout4" in hint:
        return "fallout4"
    if "new vegas" in hint or "falloutnv" in hint:
        return "falloutnv"
    if "skyrim vr" in hint or "skyrimvr" in hint:
        return "skyrimvr"
    if "oblivion" in hint:
        return "oblivion"
    return "skyrimse"


def find_existing_masterlist_path(game_repo: str) -> str:
    cache_path = os.path.join(get_app_base_dir(), "loot_cache", game_repo, "masterlist.yaml")
    candidates = [cache_path]

    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app and game_repo in LOOT_GAME_REPOS:
        _, folder_names = LOOT_GAME_REPOS[game_repo]
        for fname in folder_names + [game_repo]:
            candidates.append(os.path.join(local_app, "LOOT", "games", fname, "masterlist.yaml"))
            candidates.append(os.path.join(local_app, "LOOT", fname, "masterlist.yaml"))

    existing = [p for p in candidates if os.path.isfile(p)]
    if not existing:
        return ""
    existing.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return existing[0]


def parse_loot_masterlist(
    yaml_path: str,
    installed_plugins_lower: Set[str]
) -> Tuple[Dict[str, int], Dict[str, Tuple[str, List[str], List[str], List[str]]]]:
    """Fast streaming parser for LOOT masterlist.yaml.
    Extracts group hierarchy and rules ONLY for installed plugins.
    Returns (group_ranks_map, plugin_loot_map) where plugin_loot_map[plugin_lower] = (group, after, req, inc)."""
    if not yaml_path or not os.path.isfile(yaml_path) or not installed_plugins_lower:
        return {}, {}

    groups_after: Dict[str, List[str]] = {"default": []}
    groups_order: List[str] = ["default"]
    plugin_rules: Dict[str, Tuple[str, List[str], List[str], List[str]]] = {}

    section = ""
    cur_group = ""
    in_group_after = False

    cur_plugin = ""
    cur_plugin_active = False
    cur_plugin_group = "default"
    cur_after: List[str] = []
    cur_req: List[str] = []
    cur_inc: List[str] = []
    cur_sublist = ""

    def flush_plugin():
        nonlocal cur_plugin, cur_plugin_active, cur_plugin_group, cur_after, cur_req, cur_inc, cur_sublist
        if cur_plugin_active and cur_plugin:
            if cur_plugin in plugin_rules:
                old_g, old_a, old_r, old_i = plugin_rules[cur_plugin]
                g = cur_plugin_group if cur_plugin_group != "default" else old_g
                a = list(dict.fromkeys(old_a + cur_after))
                r = list(dict.fromkeys(old_r + cur_req))
                inc = list(dict.fromkeys(old_i + cur_inc))
                plugin_rules[cur_plugin] = (g, a, r, inc)
            else:
                plugin_rules[cur_plugin] = (
                    cur_plugin_group,
                    list(dict.fromkeys(cur_after)),
                    list(dict.fromkeys(cur_req)),
                    list(dict.fromkeys(cur_inc))
                )
        cur_plugin = ""
        cur_plugin_active = False
        cur_plugin_group = "default"
        cur_after = []
        cur_req = []
        cur_inc = []
        cur_sublist = ""

    try:
        with open(yaml_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                stripped = raw_line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                indent = len(raw_line) - len(raw_line.lstrip(" "))

                if indent == 0:
                    flush_plugin()
                    if stripped.startswith("groups:"):
                        section = "groups"
                    elif stripped.startswith("plugins:"):
                        section = "plugins"
                    else:
                        section = ""
                    continue

                if section == "groups":
                    if indent == 2 and stripped.startswith("- name:"):
                        cur_group = _unquote_yaml_scalar(stripped[7:]).lower()
                        if cur_group and cur_group not in groups_after:
                            groups_after[cur_group] = []
                            groups_order.append(cur_group)
                        in_group_after = False
                    elif indent == 4 and stripped.startswith("after:"):
                        in_group_after = True
                    elif indent == 4:
                        in_group_after = False
                    elif indent == 6 and in_group_after and cur_group and stripped.startswith("- "):
                        item_val = stripped[2:].strip()
                        if item_val.startswith("name:"):
                            dep_g = _unquote_yaml_scalar(item_val[5:]).lower()
                        else:
                            dep_g = _unquote_yaml_scalar(item_val).lower()
                        if dep_g:
                            groups_after.setdefault(cur_group, []).append(dep_g)

                elif section == "plugins":
                    if indent == 2 and stripped.startswith("- name:"):
                        flush_plugin()
                        pname = _unquote_yaml_scalar(stripped[7:])
                        plower = pname.lower()
                        if plower in installed_plugins_lower:
                            cur_plugin = plower
                            cur_plugin_active = True
                    elif cur_plugin_active:
                        if indent == 4:
                            if stripped.startswith("group:"):
                                gval = _unquote_yaml_scalar(stripped[6:]).lower()
                                if gval:
                                    cur_plugin_group = gval
                                cur_sublist = ""
                            elif stripped.startswith("after:"):
                                cur_sublist = "after"
                            elif stripped.startswith("req:"):
                                cur_sublist = "req"
                            elif stripped.startswith("inc:"):
                                cur_sublist = "inc"
                            else:
                                cur_sublist = ""
                        elif indent == 6 and cur_sublist and stripped.startswith("- "):
                            item_val = stripped[2:].strip()
                            if item_val.startswith("name:"):
                                target_p = _unquote_yaml_scalar(item_val[5:])
                            else:
                                target_p = _unquote_yaml_scalar(item_val)
                            if target_p:
                                if cur_sublist == "after":
                                    cur_after.append(target_p)
                                elif cur_sublist == "req":
                                    cur_req.append(target_p)
                                elif cur_sublist == "inc":
                                    cur_inc.append(target_p)
        flush_plugin()
    except Exception:
        return {}, {}

    # Compute topological rank for each LOOT group
    group_ranks: Dict[str, int] = {g: 0 for g in groups_order}
    for _ in range(len(groups_order) + 2):
        changed = False
        for g in groups_order:
            for dep in groups_after.get(g, []):
                dep_r = group_ranks.get(dep, 0)
                if group_ranks.get(g, 0) <= dep_r:
                    group_ranks[g] = dep_r + 1
                    changed = True
        if not changed:
            break

    return group_ranks, plugin_rules


class MasterlistDownloadWorker(QThread):
    finished_ok = pyqtSignal(str, str)
    failed = pyqtSignal(str)
    progress_update = pyqtSignal(str)

    def __init__(self, game_repo: str, target_path: str):
        super().__init__()
        self.game_repo = game_repo
        self.target_path = target_path

    def _resolve_default_branch(self) -> str:
        api_url = f"https://api.github.com/repos/loot/{self.game_repo}"
        req = urllib.request.Request(
            api_url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github.v3+json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                branch = data.get("default_branch", "")
                if branch:
                    return str(branch)
        except Exception:
            pass
        return ""

    def run(self):
        try:
            self.progress_update.emit(f"Checking LOOT repository ({self.game_repo})...")
            default_branch = self._resolve_default_branch()
            branches = []
            if default_branch:
                branches.append(default_branch)
            for b in LOOT_BRANCH_CANDIDATES:
                if b not in branches:
                    branches.append(b)

            raw_bytes = None
            used_branch = ""
            last_err = "Repository not reachable"

            for branch in branches:
                url = f"https://raw.githubusercontent.com/loot/{self.game_repo}/{branch}/masterlist.yaml"
                self.progress_update.emit(f"Downloading LOOT masterlist ({self.game_repo}@{branch})...")
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                try:
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        raw_bytes = resp.read()
                        if raw_bytes and len(raw_bytes) > 512:
                            used_branch = branch
                            break
                except urllib.error.HTTPError as e:
                    last_err = f"HTTP {e.code} on branch {branch}"
                except Exception as e:
                    last_err = str(e)

            if not raw_bytes:
                raise RuntimeError(f"Failed to download masterlist.yaml: {last_err}")

            os.makedirs(os.path.dirname(self.target_path), exist_ok=True)
            tmp_path = self.target_path + ".tmp"
            with open(tmp_path, "wb") as f:
                f.write(raw_bytes)
            os.replace(tmp_path, self.target_path)

            self.finished_ok.emit(self.target_path, used_branch)
        except Exception as e:
            self.failed.emit(str(e) or type(e).__name__)


def parse_mo2_ini(ini_path: str) -> Tuple[str, str, str, str]:
    """Extracts (selected_profile, profiles_dir, mods_dir, game_data_dir) from ModOrganizer.ini."""
    if not os.path.isfile(ini_path):
        return "", "", "", ""
    base_dir = os.path.dirname(os.path.abspath(ini_path))
    selected_profile = ""
    custom_base = ""
    mods_dir = ""
    profiles_dir = ""
    game_path = ""

    try:
        with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith(("#", ";", "[")):
                    continue
                key, sep, raw_val = s.partition("=")
                if not sep:
                    continue
                key = key.strip()
                val = _clean_ini_value(raw_val)
                if key == "selected_profile" and not selected_profile:
                    selected_profile = val
                elif key == "base_directory" and val:
                    custom_base = val
                elif key == "mod_directory" and val:
                    mods_dir = val
                elif key == "profiles_directory" and val:
                    profiles_dir = val
                elif key == "gamePath" and val and not game_path:
                    game_path = val
    except Exception:
        pass

    effective_base = custom_base if (custom_base and os.path.isdir(custom_base)) else base_dir
    if mods_dir:
        mods_dir = mods_dir.replace("%BASE_DIR%", effective_base)
    else:
        cand_mods = os.path.join(effective_base, "mods")
        if os.path.isdir(cand_mods):
            mods_dir = cand_mods

    if profiles_dir:
        profiles_dir = profiles_dir.replace("%BASE_DIR%", effective_base)
    else:
        cand_profs = os.path.join(effective_base, "profiles")
        if os.path.isdir(cand_profs):
            profiles_dir = cand_profs

    game_data_dir = ""
    if game_path and os.path.isdir(game_path):
        cand_data = os.path.join(game_path, "Data")
        game_data_dir = cand_data if os.path.isdir(cand_data) else game_path

    return selected_profile, profiles_dir, mods_dir, game_data_dir


def find_appdata_for_data_dir(data_dir: str) -> str:
    local_app = os.environ.get("LOCALAPPDATA", "")
    if not local_app or not os.path.isdir(data_dir):
        return ""

    existing_files = set()
    try:
        with os.scandir(data_dir) as it:
            for entry in it:
                if entry.is_file():
                    existing_files.add(entry.name.lower())
    except Exception:
        pass

    for _, master_file, appdata_names in KNOWN_GAMES:
        if master_file.lower() in existing_files:
            for folder_name in appdata_names:
                cand = os.path.join(local_app, folder_name)
                if os.path.isdir(cand):
                    return cand
    return ""


def discover_detected_environments() -> List[Tuple[str, str, str]]:
    found: List[Tuple[str, str, str]] = []
    local_app = os.environ.get("LOCALAPPDATA", "")
    if not local_app:
        return found

    mo2_root = os.path.join(local_app, "ModOrganizer")
    if os.path.isdir(mo2_root):
        try:
            for entry in os.scandir(mo2_root):
                if entry.is_dir():
                    p_dir, m_dir, g_dir, _ = resolve_mo2_environment(entry.path)
                    if p_dir:
                        found.append((f"MO2: {entry.name}", p_dir, m_dir or g_dir))
        except Exception:
            pass

    for game_label, _, appdata_names in KNOWN_GAMES:
        for folder_name in appdata_names:
            cand = os.path.join(local_app, folder_name)
            if os.path.isfile(os.path.join(cand, "plugins.txt")):
                found.append((f"Game AppData (Vortex/Vanilla): {game_label}", cand, ""))
                break

    return found


def resolve_mo2_environment(path_hint: str) -> Tuple[str, str, str, List[str]]:
    if not path_hint:
        local_app = os.environ.get("LOCALAPPDATA", "")
        if local_app:
            mo2_appdata = os.path.join(local_app, "ModOrganizer")
            if os.path.isdir(mo2_appdata):
                try:
                    for entry in os.scandir(mo2_appdata):
                        if entry.is_dir():
                            p_dir, m_dir, g_dir, p_list = resolve_mo2_environment(entry.path)
                            if p_dir:
                                return p_dir, m_dir, g_dir, p_list
                except Exception:
                    pass
        return "", "", "", []

    norm = os.path.normpath(os.path.abspath(path_hint))
    if os.path.isfile(norm):
        norm = os.path.dirname(norm)
    if not os.path.isdir(norm):
        return "", "", "", []

    if os.path.isfile(os.path.join(norm, "modlist.txt")) or os.path.isfile(os.path.join(norm, "plugins.txt")):
        prof_parent = os.path.dirname(norm)
        mo2_root = os.path.dirname(prof_parent)
        ini_path = os.path.join(mo2_root, "ModOrganizer.ini")
        _, _, ini_mods, ini_game_data = parse_mo2_ini(ini_path)
        mods_dir = ini_mods if (ini_mods and os.path.isdir(ini_mods)) else os.path.join(mo2_root, "mods")
        if not os.path.isdir(mods_dir):
            mods_dir = ""
        prof_names = []
        if os.path.basename(prof_parent).lower() == "profiles" and os.path.isdir(prof_parent):
            try:
                prof_names = sorted(
                    d.name for d in os.scandir(prof_parent)
                    if d.is_dir() and (
                        os.path.isfile(os.path.join(d.path, "modlist.txt"))
                        or os.path.isfile(os.path.join(d.path, "plugins.txt"))
                    )
                )
            except Exception:
                pass
        return norm, mods_dir, ini_game_data, prof_names

    if os.path.basename(norm).lower() == "profiles":
        mo2_root = os.path.dirname(norm)
        ini_path = os.path.join(mo2_root, "ModOrganizer.ini")
        sel_prof, _, ini_mods, ini_game_data = parse_mo2_ini(ini_path)
        mods_dir = ini_mods if (ini_mods and os.path.isdir(ini_mods)) else os.path.join(mo2_root, "mods")
        if not os.path.isdir(mods_dir):
            mods_dir = ""
        prof_names = []
        try:
            prof_names = sorted(
                d.name for d in os.scandir(norm)
                if d.is_dir() and (
                    os.path.isfile(os.path.join(d.path, "modlist.txt"))
                    or os.path.isfile(os.path.join(d.path, "plugins.txt"))
                )
            )
        except Exception:
            pass
        if not prof_names:
            return "", mods_dir, ini_game_data, []
        chosen = sel_prof if sel_prof in prof_names else prof_names[0]
        return os.path.join(norm, chosen), mods_dir, ini_game_data, prof_names

    ini_path = os.path.join(norm, "ModOrganizer.ini")
    if os.path.isfile(ini_path) or os.path.isdir(os.path.join(norm, "profiles")):
        sel_prof, ini_profs, ini_mods, ini_game_data = parse_mo2_ini(ini_path)
        profs_dir = ini_profs if (ini_profs and os.path.isdir(ini_profs)) else os.path.join(norm, "profiles")
        mods_dir = ini_mods if (ini_mods and os.path.isdir(ini_mods)) else os.path.join(norm, "mods")
        if not os.path.isdir(mods_dir):
            mods_dir = ""

        prof_names = []
        if os.path.isdir(profs_dir):
            try:
                prof_names = sorted(
                    d.name for d in os.scandir(profs_dir)
                    if d.is_dir() and (
                        os.path.isfile(os.path.join(d.path, "modlist.txt"))
                        or os.path.isfile(os.path.join(d.path, "plugins.txt"))
                    )
                )
            except Exception:
                pass
        if prof_names:
            chosen = sel_prof if sel_prof in prof_names else prof_names[0]
            return os.path.join(profs_dir, chosen), mods_dir, ini_game_data, prof_names

    cand_data = os.path.join(norm, "Data") if os.path.isdir(os.path.join(norm, "Data")) else norm
    has_plugins_in_dir = False
    try:
        with os.scandir(cand_data) as it:
            for entry in it:
                if entry.is_file() and entry.name.lower().endswith((".esm", ".esp", ".esl")):
                    has_plugins_in_dir = True
                    break
    except Exception:
        pass

    if has_plugins_in_dir:
        appdata_dir = find_appdata_for_data_dir(cand_data)
        return (appdata_dir or cand_data), "", cand_data, []

    return "", "", "", []


def parse_tes4_header(plugin_path: str) -> Tuple[bool, bool, List[str]]:
    lname = os.path.basename(plugin_path).lower()
    is_esm_ext = lname.endswith(".esm")
    is_esl_ext = lname.endswith(".esl")

    if not plugin_path or not os.path.isfile(plugin_path):
        return is_esm_ext or is_esl_ext, is_esl_ext, []

    try:
        with open(plugin_path, "rb") as f:
            head = f.read(24)
            if len(head) < 24 or head[:4] != b"TES4":
                return is_esm_ext or is_esl_ext, is_esl_ext, []

            data_size, flags = struct.unpack("<II", head[4:12])
            is_esm = bool(flags & 0x00000001) or is_esm_ext or is_esl_ext
            is_esl = bool(flags & 0x00000200) or is_esl_ext

            buf = f.read(min(data_size, 262144))
    except Exception:
        return is_esm_ext or is_esl_ext, is_esl_ext, []

    masters: List[str] = []
    pos = 0
    limit = len(buf)
    override_size = None

    while pos + 6 <= limit:
        sub_type = buf[pos:pos + 4]
        sub_size = struct.unpack("<H", buf[pos + 4:pos + 6])[0]
        pos += 6

        if sub_type == b"XXXX" and sub_size == 4 and pos + 4 <= limit:
            override_size = struct.unpack("<I", buf[pos:pos + 4])[0]
            pos += 4
            continue

        actual_size = override_size if override_size is not None else sub_size
        override_size = None

        if pos + actual_size > limit:
            break

        if sub_type == b"MAST":
            raw_mast = buf[pos:pos + actual_size].split(b"\x00", 1)[0]
            mast_name = raw_mast.decode("utf-8", errors="ignore").strip()
            if mast_name:
                masters.append(mast_name)

        pos += actual_size

    return is_esm, is_esl, masters


def enforce_plugin_constraints(
    items: List[str],
    plugin_meta: Dict[str, Tuple[bool, bool, List[str], str]],
    locked: List[str],
    original_order: List[str],
    loot_group_ranks: Dict[str, int] = None,
    loot_plugin_rules: Dict[str, Tuple[str, List[str], List[str], List[str]]] = None,
    apply_group_sort: bool = False
) -> List[str]:
    present_map = {p.lower(): p for p in items}
    locked_set = set(locked)
    loot_group_ranks = loot_group_ranks or {}
    loot_plugin_rules = loot_plugin_rules or {}
    default_rank = loot_group_ranks.get("default", 0)

    def is_master_file(p: str) -> bool:
        pl = p.lower()
        if pl in OFFICIAL_MASTERS_LOWER or pl.startswith("cc"):
            return True
        if p in plugin_meta:
            return plugin_meta[p][0]
        return pl.endswith((".esm", ".esl"))

    def get_group_rank(p: str) -> int:
        pl = p.lower()
        if pl in loot_plugin_rules:
            grp = loot_plugin_rules[pl][0]
            return loot_group_ranks.get(grp, default_rank)
        return default_rank

    masters_bucket = [p for p in items if is_master_file(p)]
    regular_bucket = [p for p in items if not is_master_file(p)]

    if apply_group_sort and loot_group_ranks:
        orig_idx = {p: i for i, p in enumerate(items)}
        masters_bucket.sort(key=lambda p: (-1000 if p in locked_set else get_group_rank(p), orig_idx[p]))
        regular_bucket.sort(key=lambda p: (get_group_rank(p), orig_idx[p]))

    combined = masters_bucket + regular_bucket

    # Enforce both binary MAST dependencies and LOOT after/req rules
    for _ in range(len(combined)):
        changed = False
        idx_map = {p.lower(): idx for idx, p in enumerate(combined)}
        for p in list(combined):
            pl = p.lower()
            deps: List[str] = []
            if p in plugin_meta:
                deps.extend(plugin_meta[p][2])
            if pl in loot_plugin_rules:
                _, l_after, l_req, _ = loot_plugin_rules[pl]
                for target in l_after + l_req:
                    tl = target.lower()
                    if tl in present_map:
                        target_actual = present_map[tl]
                        # Never force a master file to load after a non-master plugin
                        if is_master_file(p) and not is_master_file(target_actual):
                            continue
                        deps.append(target)

            if not deps:
                continue

            max_dep_idx = -1
            max_dep_name = None
            for d in deps:
                dl = d.lower()
                if dl in idx_map and idx_map[dl] > max_dep_idx and dl != pl:
                    max_dep_idx = idx_map[dl]
                    max_dep_name = present_map.get(dl)

            cur_i = combined.index(p)
            if max_dep_name and max_dep_idx > cur_i:
                combined.pop(cur_i)
                dep_new_idx = combined.index(max_dep_name)
                combined.insert(dep_new_idx + 1, p)
                changed = True
                break
        if not changed:
            break

    leading_locked = []
    for m in original_order:
        if m in locked_set:
            leading_locked.append(m)
        else:
            break
    if leading_locked:
        lead_set = set(leading_locked)
        combined = leading_locked + [x for x in combined if x not in lead_set]

    return combined


def inspect_mod_directory(mod_dir: str) -> Tuple[List[str], int, str]:
    if not mod_dir or not os.path.isdir(mod_dir):
        return [], 0, ""

    tags: List[str] = []
    seen_tags: Set[str] = set()

    def add_tag(t: str):
        if t not in seen_tags:
            seen_tags.add(t)
            tags.append(t)

    has_esp = False
    has_bsa = False

    try:
        with os.scandir(mod_dir) as it:
            for entry in it:
                lname = entry.name.lower()
                if entry.is_dir(follow_symlinks=False):
                    if lname == "skse":
                        plugins_dir = os.path.join(entry.path, "plugins")
                        has_dll = False
                        if os.path.isdir(plugins_dir):
                            try:
                                with os.scandir(plugins_dir) as pit:
                                    for pe in pit:
                                        if pe.is_file() and pe.name.lower().endswith(".dll"):
                                            has_dll = True
                                            break
                            except Exception:
                                pass
                        add_tag("SKSE" if has_dll else "SKSE-Cfg")
                    elif lname in ("nemesis_engine", "pandora_engine"):
                        add_tag("Anim")
                    elif lname == "meshes":
                        add_tag("Mesh")
                        anim_dir = os.path.join(entry.path, "actors", "character", "animations")
                        fg_dir = os.path.join(entry.path, "actors", "character", "facegendata")
                        if os.path.isdir(anim_dir):
                            add_tag("Anim")
                        if os.path.isdir(fg_dir):
                            add_tag("FaceGen")
                    elif lname == "textures":
                        add_tag("Tex")
                        fg_tex = os.path.join(entry.path, "actors", "character", "facegendata")
                        if os.path.isdir(fg_tex):
                            add_tag("FaceGen")
                    elif lname in ("scripts", "seq"):
                        add_tag("Script")
                    elif lname == "interface":
                        add_tag("UI")
                    elif lname in ("sound", "music"):
                        add_tag("Audio")
                    elif lname == "calientetools":
                        add_tag("BodySlide")
                    elif lname in ("grass", "lodsettings", "terrain", "dyndolod"):
                        add_tag("LOD")
                    elif lname == "root":
                        add_tag("Root")
                elif entry.is_file(follow_symlinks=False):
                    if lname.endswith((".esp", ".esm", ".esl")):
                        has_esp = True
                    elif lname.endswith((".bsa", ".ba2")):
                        has_bsa = True
    except Exception:
        pass

    if has_esp:
        add_tag("ESP")
    if has_bsa:
        add_tag("BSA")

    nexus_id = 0
    cat_name = ""
    meta_path = os.path.join(mod_dir, "meta.ini")
    if os.path.isfile(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8", errors="ignore") as f:
                for _ in range(45):
                    line = f.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line.startswith("modid="):
                        val = line.partition("=")[2].strip()
                        if val.isdigit() and int(val) > 0:
                            nexus_id = int(val)
                    elif line.startswith("category="):
                        val = line.partition("=")[2].strip().strip('"')
                        for part in val.split(","):
                            part = part.strip()
                            if part.isdigit():
                                cid = int(part)
                                if cid in MO2_CATEGORIES:
                                    cat_name = MO2_CATEGORIES[cid]
                                    break
        except Exception:
            pass

    return tags, nexus_id, cat_name


def format_mod_with_meta(
    name: str,
    meta_map: Dict[str, Tuple[List[str], int, str]],
    inspect_assets: bool,
    include_nexus_meta: bool
) -> str:
    if name.endswith(SEPARATOR_SUFFIX) or name not in meta_map:
        return name
    tags, nx_id, cat_name = meta_map[name]
    chunks: List[str] = []
    if inspect_assets and tags:
        chunks.append(", ".join(tags))
    if include_nexus_meta:
        nx_parts = []
        if nx_id > 0:
            nx_parts.append(f"nx:{nx_id}")
        if cat_name:
            nx_parts.append(f"cat:{cat_name}")
        if nx_parts:
            chunks.append(" ".join(nx_parts))
    if not chunks:
        return name
    return f"{name} [{' | '.join(chunks)}]"


def format_plugin_with_meta(
    name: str,
    plugin_meta_map: Dict[str, Tuple[bool, bool, List[str], str]],
    loot_group_ranks: Dict[str, int] = None,
    loot_plugin_rules: Dict[str, Tuple[str, List[str], List[str], List[str]]] = None,
    installed_lower: Set[str] = None
) -> str:
    if name not in plugin_meta_map:
        return name
    is_esm, is_esl, masters, src_mod = plugin_meta_map[name]
    flags = []
    if is_esm:
        flags.append("ESM")
    if is_esl:
        flags.append("ESL")
    chunks = []
    if flags:
        chunks.append("/".join(flags))
    if masters:
        chunks.append("masters: " + ", ".join(masters))

    pl = name.lower()
    if loot_plugin_rules and pl in loot_plugin_rules:
        grp, l_after, l_req, _ = loot_plugin_rules[pl]
        rank = (loot_group_ranks or {}).get(grp, 0)
        chunks.append(f"loot_grp: {grp}#{rank}")
        relevant_after = [
            x for x in (l_after + l_req)
            if not installed_lower or x.lower() in installed_lower
        ]
        if relevant_after:
            chunks.append("loot_after: " + ", ".join(relevant_after[:6]))

    if src_mod:
        chunks.append(f"mod: {src_mod}")
    if not chunks:
        return name
    return f"{name} [{' | '.join(chunks)}]"


def build_user_prompt(
    mod_names: List[str],
    locked_mods: List[str],
    custom_rules: str,
    mods_json: str = None,
    compact_mode: bool = False,
    keep_separators: bool = False,
    meta_map: Dict[str, Tuple[List[str], int, str]] = None,
    inspect_assets: bool = False,
    include_nexus_meta: bool = False,
    is_plugin_mode: bool = False,
    plugin_meta_map: Dict[str, Tuple[bool, bool, List[str], str]] = None,
    loot_group_ranks: Dict[str, int] = None,
    loot_plugin_rules: Dict[str, Tuple[str, List[str], List[str], List[str]]] = None
) -> str:
    parts = []
    if locked_mods:
        parts.append(LOCKED_HEADER + "\n".join(f"- {m}" for m in locked_mods))

    rules_block = []
    if keep_separators and not is_plugin_mode:
        rules_block.append(KEEP_SEPS_RULE)
    custom_rules = (custom_rules or "").strip()
    if custom_rules:
        rules_block.append(custom_rules)
    if rules_block:
        parts.append(RULES_HEADER + "\n".join(rules_block))

    if mods_json is None:
        if is_plugin_mode:
            inst_lower = {n.lower() for n in mod_names}
            annotated = [
                format_plugin_with_meta(
                    name, plugin_meta_map or {}, loot_group_ranks, loot_plugin_rules, inst_lower
                )
                for name in mod_names
            ]
            if compact_mode:
                indexed = [f"{i}: {line}" for i, line in enumerate(annotated)]
                mods_json = json.dumps(indexed, ensure_ascii=False)
            else:
                mods_json = json.dumps(annotated, ensure_ascii=False)
        else:
            use_meta = bool(meta_map and (inspect_assets or include_nexus_meta))
            if compact_mode:
                if use_meta:
                    indexed = [
                        f"{i}: {format_mod_with_meta(name, meta_map, inspect_assets, include_nexus_meta)}"
                        for i, name in enumerate(mod_names)
                    ]
                else:
                    indexed = [f"{i}: {name}" for i, name in enumerate(mod_names)]
                mods_json = json.dumps(indexed, ensure_ascii=False)
            else:
                if use_meta:
                    annotated = [
                        format_mod_with_meta(name, meta_map, inspect_assets, include_nexus_meta)
                        for name in mod_names
                    ]
                    mods_json = json.dumps(annotated, ensure_ascii=False)
                else:
                    mods_json = json.dumps(mod_names, ensure_ascii=False)

    header = COMPACT_SORT_HEADER if compact_mode else SORT_HEADER
    parts.append(header + mods_json)
    return "\n\n".join(parts)


def compute_moved(current: List[str], proposed: List[str]) -> Set[str]:
    cur_idx = {}
    for n in current:
        if not n.endswith(SEPARATOR_SUFFIX):
            cur_idx[n] = len(cur_idx)

    names = [n for n in proposed if n in cur_idx]
    seq = [cur_idx[n] for n in names]

    tails: List[int] = []
    tails_pos: List[int] = []
    prev = [-1] * len(seq)
    for pos, val in enumerate(seq):
        k = bisect.bisect_left(tails, val)
        if k == len(tails):
            tails.append(val)
            tails_pos.append(pos)
        else:
            tails[k] = val
            tails_pos[k] = pos
        prev[pos] = tails_pos[k - 1] if k > 0 else -1

    keep: Set[int] = set()
    p = tails_pos[-1] if tails_pos else -1
    while p != -1:
        keep.add(p)
        p = prev[p]

    return {names[i] for i in range(len(names)) if i not in keep}


class ApiHttpError(Exception):
    def __init__(self, code: int, body: str, retry_after=None):
        super().__init__(f"HTTP {code}: {body[:1500]}")
        self.code = code
        self.body = body
        self.retry_after = retry_after


class AISortWorker(QThread):
    sorted_ready = pyqtSignal(list)
    failed = pyqtSignal(str)
    progress_update = pyqtSignal(str)

    def __init__(
        self,
        api_url: str,
        api_key: str,
        model: str,
        mod_names: List[str],
        locked_mods: List[str] = None,
        custom_rules: str = "",
        timeout: int = DEFAULT_REQUEST_TIMEOUT,
        compact_mode: bool = False,
        keep_separators: bool = False,
        meta_map: Dict[str, Tuple[List[str], int, str]] = None,
        inspect_assets: bool = True,
        include_nexus_meta: bool = True,
        is_plugin_mode: bool = False,
        plugin_meta_map: Dict[str, Tuple[bool, bool, List[str], str]] = None,
        loot_group_ranks: Dict[str, int] = None,
        loot_plugin_rules: Dict[str, Tuple[str, List[str], List[str], List[str]]] = None
    ):
        super().__init__()
        self.api_url = api_url.strip()
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.mod_names = mod_names
        self.locked_mods = locked_mods or []
        self.custom_rules = custom_rules.strip()
        self.timeout = int(timeout)
        self.compact_mode = bool(compact_mode)
        self.keep_separators = bool(keep_separators)
        self.meta_map = meta_map or {}
        self.inspect_assets = bool(inspect_assets)
        self.include_nexus_meta = bool(include_nexus_meta)
        self.is_plugin_mode = bool(is_plugin_mode)
        self.plugin_meta_map = plugin_meta_map or {}
        self.loot_group_ranks = loot_group_ranks or {}
        self.loot_plugin_rules = loot_plugin_rules or {}
        self._aborted = False

    def abort(self):
        self._aborted = True

    def _send_request(self, payload: dict) -> str:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.api_url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", "replace")
            except Exception:
                body = str(e.reason)
            retry_after = None
            try:
                ra = e.headers.get("Retry-After") if e.headers else None
                retry_after = float(ra) if ra is not None else None
            except ValueError:
                retry_after = None
            raise ApiHttpError(e.code, body, retry_after) from None

    def _request_with_fallbacks(self, payload: dict) -> str:
        payload = dict(payload)
        retries = 0
        while not self._aborted:
            try:
                return self._send_request(payload)
            except ApiHttpError as err:
                if self._aborted:
                    raise RuntimeError("Cancelled.")
                if err.code in (400, 422):
                    body = err.body.lower()
                    present = [p for p in OPTIONAL_PAYLOAD_PARAMS if p in payload]
                    mentioned = [p for p in present if p in body]
                    candidates = mentioned or present
                    if not candidates:
                        raise
                    dropped = candidates[0]
                    payload.pop(dropped)
                    self.progress_update.emit(f"Retrying without '{dropped}'...")
                    continue
                if err.code in RETRYABLE_HTTP_CODES and retries < MAX_RETRIES:
                    retries += 1
                    delay = err.retry_after if err.retry_after is not None else 5 * retries
                    delay = min(max(delay, 1), 30)
                    self.progress_update.emit(f"HTTP {err.code}, retry {retries}/{MAX_RETRIES} in {int(delay)}s...")
                    for _ in range(int(delay * 2)):
                        if self._aborted:
                            raise RuntimeError("Cancelled.")
                        time.sleep(0.5)
                    continue
                raise
        raise RuntimeError("Cancelled.")

    @staticmethod
    def _extract_json_array(text: str) -> list:
        text = text.strip()
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

        parsed = None
        try:
            parsed = json.loads(text)
        except ValueError:
            decoder = json.JSONDecoder()
            for match in re.finditer(r"\[", text):
                try:
                    obj, _ = decoder.raw_decode(text[match.start():])
                except ValueError:
                    continue
                if isinstance(obj, list) and obj and all(isinstance(x, (str, int)) for x in obj):
                    parsed = obj
                    break

        if isinstance(parsed, dict):
            for value in parsed.values():
                if isinstance(value, list):
                    parsed = value
                    break

        if not isinstance(parsed, list):
            raise ValueError("Invalid or truncated JSON array in response.")
        return parsed

    def _parse_response(self, raw_response: str) -> list:
        res_json = json.loads(raw_response)

        if isinstance(res_json, dict) and res_json.get("error") and not res_json.get("choices"):
            raise ValueError(f"API error: {res_json['error']}")

        try:
            ai_text = (res_json["choices"][0]["message"].get("content") or "").strip()
        except (KeyError, IndexError, TypeError, AttributeError):
            raise ValueError("Unexpected API response: " + raw_response[:500])

        if not ai_text:
            raise ValueError("Empty response from model.")

        for think_tag in ("</think>", "</thought>"):
            if think_tag in ai_text:
                ai_text = ai_text.split(think_tag)[-1].strip()

        return self._extract_json_array(ai_text)

    def _resolve_string_item(self, s: str, original_set: Set[str], num_mods: int) -> str:
        if s in original_set:
            return s
        stripped = _META_TAG_SUFFIX_RE.sub("", s).strip()
        if stripped in original_set:
            return stripped
        if s.isdigit() and 0 <= int(s) < num_mods:
            return self.mod_names[int(s)]
        if ":" in s:
            prefix_id, _, rest = s.partition(":")
            if prefix_id.strip().isdigit() and 0 <= int(prefix_id.strip()) < num_mods:
                return self.mod_names[int(prefix_id.strip())]
            rest_clean = _META_TAG_SUFFIX_RE.sub("", rest.strip()).strip()
            if rest_clean in original_set:
                return rest_clean
        if not self.is_plugin_mode and stripped.endswith(SEPARATOR_SUFFIX) and not self.keep_separators:
            return sanitize_separator(stripped)
        return ""

    def _normalize_result(self, sorted_list: List[Union[str, int]]) -> List[str]:
        original_set = set(self.mod_names)
        num_mods = len(self.mod_names)
        result: List[str] = []
        seen: Set[str] = set()

        for item in sorted_list:
            clean_item = ""
            if isinstance(item, int):
                if 0 <= item < num_mods:
                    clean_item = self.mod_names[item]
            elif isinstance(item, str):
                s = item.strip()
                if s:
                    clean_item = self._resolve_string_item(s, original_set, num_mods)

            if not clean_item or clean_item in seen:
                continue
            result.append(clean_item)
            seen.add(clean_item)

        for i, name in enumerate(self.mod_names):
            if name in seen:
                continue
            if not self.is_plugin_mode and name.endswith(SEPARATOR_SUFFIX) and not self.keep_separators:
                continue
            insert_at = 0
            for j in range(i - 1, -1, -1):
                prev = self.mod_names[j]
                if prev in seen:
                    insert_at = result.index(prev) + 1
                    break
            result.insert(insert_at, name)
            seen.add(name)

        return result

    def _prune_empty_separators(self, result: List[str]) -> List[str]:
        if self.is_plugin_mode:
            return [x for x in result if not x.endswith(SEPARATOR_SUFFIX)]
        original_set = set(self.mod_names)
        pruned: List[str] = []
        for i, name in enumerate(result):
            if name.endswith(SEPARATOR_SUFFIX) and name not in original_set:
                nxt = result[i + 1] if i + 1 < len(result) else None
                if nxt is None or nxt.endswith(SEPARATOR_SUFFIX):
                    continue
            pruned.append(name)
        return pruned

    def _enforce_locked_order(self, items: List[str], locked: List[str]) -> List[str]:
        locked_set = set(locked)
        present = set(items)
        ordered = [m for m in locked if m in present]
        if not ordered:
            return items

        new_items = list(items)
        if len(ordered) >= 2:
            slots = [i for i, item in enumerate(new_items) if item in locked_set]
            for slot, mod_name in zip(slots, ordered):
                new_items[slot] = mod_name

        orig_non_sep = [m for m in self.mod_names if not m.endswith(SEPARATOR_SUFFIX)]
        trailing_locked = []
        for m in reversed(orig_non_sep):
            if m in locked_set:
                trailing_locked.append(m)
            else:
                break
        if trailing_locked:
            trailing_locked.reverse()
            trail_set = set(trailing_locked)
            new_items = [x for x in new_items if x not in trail_set] + trailing_locked

        leading_locked = []
        for m in orig_non_sep:
            if m in locked_set and m not in set(trailing_locked):
                leading_locked.append(m)
            else:
                break
        if leading_locked:
            lead_set = set(leading_locked)
            new_items = leading_locked + [x for x in new_items if x not in lead_set]

        return new_items

    def run(self):
        try:
            self.progress_update.emit("Sending request...")

            sys_prompt = PLUGIN_SYSTEM_PROMPT if self.is_plugin_mode else SYSTEM_PROMPT
            user_content = build_user_prompt(
                self.mod_names,
                self.locked_mods,
                self.custom_rules,
                compact_mode=self.compact_mode,
                keep_separators=self.keep_separators,
                meta_map=self.meta_map,
                inspect_assets=self.inspect_assets,
                include_nexus_meta=self.include_nexus_meta,
                is_plugin_mode=self.is_plugin_mode,
                plugin_meta_map=self.plugin_meta_map,
                loot_group_ranks=self.loot_group_ranks,
                loot_plugin_rules=self.loot_plugin_rules
            )

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.1,
                "reasoning_effort": "high"
            }

            raw_response = self._request_with_fallbacks(payload)
            if self._aborted:
                return

            sorted_list = self._parse_response(raw_response)
            result = self._normalize_result(sorted_list)
            if self.locked_mods:
                result = self._enforce_locked_order(result, self.locked_mods)
            result = self._prune_empty_separators(result)
            if self.is_plugin_mode:
                result = enforce_plugin_constraints(
                    result,
                    self.plugin_meta_map,
                    self.locked_mods,
                    self.mod_names,
                    loot_group_ranks=self.loot_group_ranks,
                    loot_plugin_rules=self.loot_plugin_rules,
                    apply_group_sort=False
                )

            if not self._aborted:
                self.sorted_ready.emit(result)

        except ApiHttpError as e:
            if not self._aborted:
                self.failed.emit(str(e))
        except urllib.error.URLError as e:
            if not self._aborted:
                self.failed.emit(f"Connection error: {e.reason}")
        except Exception as e:
            if not self._aborted:
                self.failed.emit(str(e) or type(e).__name__)


class AlignDialog(QDialog):
    def __init__(self, organizer=None, parent=None):
        super().__init__(parent)
        self._organizer = organizer
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setWindowFlags(self.windowFlags() | WINDOW_MIN_MAX)
        self.resize(1240, 820)
        self.setStyleSheet(MINIMAL_STYLESHEET)

        self.settings = QSettings("MO2Community", APP_NAME)
        self._legacy_settings = QSettings("MO2Community", "AILeftPanelSorter")

        self.sort_mode = MODE_MODS
        self.profile_path = ""
        self.mods_path = ""
        self.game_data_path = ""
        self.modlist_path = ""
        self.plugins_path = ""
        self.loadorder_path = ""
        self.backup_path = ""
        self.plugins_backup_path = ""
        self.loadorder_backup_path = ""
        self.created_seps_path = ""

        self.original_lines: List[str] = []
        self.raw_mods_order: List[str] = []
        self.mod_prefixes: Dict[str, str] = {}
        self.mod_meta_map: Dict[str, Tuple[List[str], int, str]] = {}
        self.plugin_meta_map: Dict[str, Tuple[bool, bool, List[str], str]] = {}
        self.plugin_issues_map: Dict[str, str] = {}
        self.loot_group_ranks: Dict[str, int] = {}
        self.loot_plugin_rules: Dict[str, Tuple[str, List[str], List[str], List[str]]] = {}
        self.current_loot_repo = "skyrimse"
        self.current_masterlist_path = ""

        self.lead_foreign: List[str] = []
        self.trail_foreign: List[str] = []
        self.sortable_file_order: List[str] = []
        self.proposed_order: List[str] = []
        self.locked_mods_set: Set[str] = set()
        self.file_is_descending = True
        self.worker: Optional[AISortWorker] = None
        self.loot_worker: Optional[MasterlistDownloadWorker] = None
        self.request_timeout = DEFAULT_REQUEST_TIMEOUT
        self.compact_mode = False
        self.keep_separators = False
        self.inspect_assets = True
        self.include_nexus_meta = True
        self._is_populating = False
        self._api_keys: Dict[str, str] = {}
        self._active_preset = ""

        self._sortable_set: Set[str] = set()
        self._sortable_mod_count = 0
        self._sortable_sep_count = 0
        self._mods_json_cache = "[]"
        self._last_moved_set: Set[str] = set()

        self._setup_ui()
        self._load_saved_settings()
        self._init_paths()
        self._load_current_list()

    def _setting_val(self, key: str, default=None):
        val = self.settings.value(key, None)
        if val is None:
            val = self._legacy_settings.value(key, default)
        return val

    def _init_paths(self):
        if self._organizer is not None:
            try:
                self.profile_path = os.path.normpath(self._organizer.profilePath())
                self.mods_path = os.path.normpath(self._organizer.modsPath())
                _, _, g_data, _ = resolve_mo2_environment(self.profile_path)
                self.game_data_path = g_data
                self._sync_path_fields([], self.profile_path, self.mods_path)
                return
            except Exception:
                pass

        saved_prof = str(self._setting_val("standalone_profile_path", "") or "").strip()
        saved_mods = str(self._setting_val("standalone_mods_path", "") or "").strip()

        prof_dir, auto_mods, auto_game_data, prof_list = resolve_mo2_environment(saved_prof)
        if not prof_dir and saved_prof and os.path.isdir(saved_prof):
            prof_dir = saved_prof
        mods_dir = saved_mods if (saved_mods and os.path.isdir(saved_mods)) else auto_mods
        self.game_data_path = auto_game_data

        self._sync_path_fields(prof_list, prof_dir, mods_dir)

        if prof_dir and not os.path.isfile(os.path.join(prof_dir, "modlist.txt")):
            if os.path.isfile(os.path.join(prof_dir, "plugins.txt")) or self.game_data_path:
                self.mode_combo.blockSignals(True)
                self.mode_combo.setCurrentIndex(1)
                self.mode_combo.blockSignals(False)
                self.sort_mode = MODE_PLUGINS
                self.btn_dag_sort.setVisible(True)
                self.btn_loot_update.setVisible(True)
                self._rebuild_filter_combo_items()

    def _sync_path_fields(self, prof_list: List[str], prof_dir: str, mods_dir: str):
        self.profile_path = os.path.normpath(prof_dir) if prof_dir else ""
        self.mods_path = os.path.normpath(mods_dir) if mods_dir else ""
        self._update_derived_paths()

        self.profile_path_input.blockSignals(True)
        self.profile_path_input.setText(self.profile_path)
        self.profile_path_input.blockSignals(False)

        self.mods_path_input.blockSignals(True)
        self.mods_path_input.setText(self.mods_path or self.game_data_path)
        self.mods_path_input.blockSignals(False)

        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        if prof_list:
            for p in prof_list:
                self.profile_combo.addItem(p)
            curr_name = os.path.basename(self.profile_path)
            idx = self.profile_combo.findText(curr_name)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)
            self.profile_combo.setVisible(True)
        else:
            self.profile_combo.setVisible(False)
        self.profile_combo.blockSignals(False)

    def _update_derived_paths(self):
        if self.profile_path:
            self.modlist_path = os.path.join(self.profile_path, "modlist.txt")
            self.plugins_path = os.path.join(self.profile_path, "plugins.txt")
            self.loadorder_path = os.path.join(self.profile_path, "loadorder.txt")
            self.backup_path = os.path.join(self.profile_path, "modlist.txt.align_backup")
            self.plugins_backup_path = os.path.join(self.profile_path, "plugins.txt.align_backup")
            self.loadorder_backup_path = os.path.join(self.profile_path, "loadorder.txt.align_backup")
            self.created_seps_path = os.path.join(self.profile_path, "modlist.txt.align_separators.json")
        else:
            self.modlist_path = ""
            self.plugins_path = ""
            self.loadorder_path = ""
            self.backup_path = ""
            self.plugins_backup_path = ""
            self.loadorder_backup_path = ""
            self.created_seps_path = ""

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Standalone Path & Mode Bar
        path_bar = QHBoxLayout()
        path_bar.setSpacing(6)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Left Panel (Mods)",
            "Right Panel (Plugins / LOOT)"
        ])
        self.mode_combo.setMinimumWidth(175)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        path_bar.addWidget(self.mode_combo)

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(115)
        self.profile_combo.setVisible(False)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_combo_changed)
        path_bar.addWidget(self.profile_combo)

        self.profile_path_input = QLineEdit()
        self.profile_path_input.setPlaceholderText("MO2 Profile or Game AppData Path")
        self.profile_path_input.editingFinished.connect(self._on_profile_path_edited)
        path_bar.addWidget(self.profile_path_input, 3)

        self.btn_browse_profile = QPushButton("Browse")
        self.btn_browse_profile.clicked.connect(self._browse_profile_folder)
        path_bar.addWidget(self.btn_browse_profile)

        self.btn_detect = QPushButton("Detect")
        self.btn_detect.clicked.connect(self._show_detect_menu)
        path_bar.addWidget(self.btn_detect)

        self.mods_path_input = QLineEdit()
        self.mods_path_input.setPlaceholderText("Mods or Game Data Folder")
        self.mods_path_input.editingFinished.connect(self._on_mods_path_edited)
        path_bar.addWidget(self.mods_path_input, 2)

        self.btn_browse_mods = QPushButton("Data/Mods...")
        self.btn_browse_mods.clicked.connect(self._browse_mods_folder)
        path_bar.addWidget(self.btn_browse_mods)

        self.btn_reload = QPushButton("\u21bb")
        self.btn_reload.setFixedWidth(32)
        self.btn_reload.clicked.connect(self._load_current_list)
        path_bar.addWidget(self.btn_reload)

        layout.addLayout(path_bar)

        # AI Connection Bar
        conn_bar = QHBoxLayout()
        conn_bar.setSpacing(6)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(135)
        for name in PRESETS.keys():
            self.preset_combo.addItem(name)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        conn_bar.addWidget(self.preset_combo)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Model")
        self.model_input.setMinimumWidth(160)
        conn_bar.addWidget(self.model_input, 2)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Endpoint URL")
        conn_bar.addWidget(self.url_input, 3)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("API Key")
        self.key_input.setEchoMode(ECHO_PASSWORD)
        conn_bar.addWidget(self.key_input, 2)

        self.btn_toggle_key = QPushButton("Show")
        self.btn_toggle_key.setCheckable(True)
        self.btn_toggle_key.setFixedWidth(52)
        self.btn_toggle_key.toggled.connect(self._toggle_api_key_visibility)
        conn_bar.addWidget(self.btn_toggle_key)

        self.btn_advanced = QPushButton("Options")
        self.btn_advanced.clicked.connect(self._open_advanced_settings)
        conn_bar.addWidget(self.btn_advanced)

        layout.addLayout(conn_bar)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.btn_lock_sel = QPushButton(f"{ICON_LOCK} Lock")
        self.btn_lock_sel.clicked.connect(self._lock_selected)
        toolbar.addWidget(self.btn_lock_sel)

        self.btn_unlock_sel = QPushButton(f"{ICON_UNLOCK} Unlock")
        self.btn_unlock_sel.clicked.connect(self._unlock_selected)
        toolbar.addWidget(self.btn_unlock_sel)

        self.btn_unlock_all = QPushButton("Clear Locks")
        self.btn_unlock_all.clicked.connect(self._unlock_all)
        toolbar.addWidget(self.btn_unlock_all)

        self.btn_toggle_rules = QPushButton("Rules")
        self.btn_toggle_rules.setCheckable(True)
        self.btn_toggle_rules.toggled.connect(self._toggle_rules_panel)
        toolbar.addWidget(self.btn_toggle_rules)

        self.btn_presets = QPushButton("Presets")
        presets_menu = QMenu(self)
        act_import_preset = presets_menu.addAction("Import Preset (.json)...")
        act_export_preset = presets_menu.addAction("Export Preset (.json)...")
        act_import_preset.triggered.connect(self._import_preset)
        act_export_preset.triggered.connect(self._export_preset)
        self.btn_presets.setMenu(presets_menu)
        toolbar.addWidget(self.btn_presets)

        self.btn_dag_sort = QPushButton("DAG Sort")
        self.btn_dag_sort.setVisible(False)
        self.btn_dag_sort.clicked.connect(self._run_offline_dag_sort)
        toolbar.addWidget(self.btn_dag_sort)

        self.btn_loot_update = QPushButton("Update LOOT DB")
        self.btn_loot_update.setVisible(False)
        self.btn_loot_update.clicked.connect(self._update_loot_masterlist)
        toolbar.addWidget(self.btn_loot_update)

        self.btn_move_up = QPushButton("\u2191")
        self.btn_move_up.setFixedWidth(30)
        self.btn_move_up.setEnabled(False)
        self.btn_move_up.clicked.connect(lambda: self._nudge_proposed(-1))
        toolbar.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("\u2193")
        self.btn_move_down.setFixedWidth(30)
        self.btn_move_down.setEnabled(False)
        self.btn_move_down.clicked.connect(lambda: self._nudge_proposed(1))
        toolbar.addWidget(self.btn_move_down)

        toolbar.addStretch()

        self.filter_combo = QComboBox()
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        toolbar.addWidget(self.filter_combo)
        self._rebuild_filter_combo_items()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(240)
        self.search_input.textChanged.connect(self._apply_filter)
        toolbar.addWidget(self.search_input)

        layout.addLayout(toolbar)

        self.rules_input = QPlainTextEdit()
        self.rules_input.setPlaceholderText("Custom rules...")
        self.rules_input.setFixedHeight(72)
        self.rules_input.setVisible(False)
        self.rules_input.textChanged.connect(self._update_stats)
        layout.addWidget(self.rules_input)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Lock",
            "Current Order",
            "Meta / Diagnostics",
            "\u0394",
            "Proposed Order"
        ])
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(25)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, RESIZE_FIXED)
        header.setSectionResizeMode(1, RESIZE_STRETCH)
        header.setSectionResizeMode(2, RESIZE_FIXED)
        header.setSectionResizeMode(3, RESIZE_FIXED)
        header.setSectionResizeMode(4, RESIZE_STRETCH)
        self.table.setColumnWidth(0, 62)
        self.table.setColumnWidth(2, 245)
        self.table.setColumnWidth(3, 60)
        self.table.setSelectionBehavior(SELECT_ROWS)
        self.table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.table.setContextMenuPolicy(CUSTOM_CONTEXT_MENU)
        self.table.customContextMenuRequested.connect(self._show_table_context_menu)
        self.table.itemChanged.connect(self._on_table_item_changed)
        layout.addWidget(self.table, 1)

        QShortcut(QKeySequence("Alt+Up"), self, activated=lambda: self._nudge_proposed(-1))
        QShortcut(QKeySequence("Alt+Down"), self, activated=lambda: self._nudge_proposed(1))

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(8)

        self.status_label = QLabel("Ready")
        bottom_bar.addWidget(self.status_label, 1)

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #a1a1aa; font-weight: 600;")
        bottom_bar.addWidget(self.stats_label)

        self.btn_restore = QPushButton("Restore")
        self.btn_restore.setMinimumHeight(32)
        self.btn_restore.clicked.connect(self._restore_backup)
        bottom_bar.addWidget(self.btn_restore)

        self.btn_analyze = QPushButton("Analyze")
        self.btn_analyze.setObjectName("btnPrimary")
        self.btn_analyze.setMinimumHeight(32)
        self.btn_analyze.setMinimumWidth(120)
        self.btn_analyze.clicked.connect(self._on_analyze_or_cancel_clicked)
        bottom_bar.addWidget(self.btn_analyze)

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setObjectName("btnSuccess")
        self.btn_apply.setMinimumHeight(32)
        self.btn_apply.setMinimumWidth(120)
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self._apply_sorting)
        bottom_bar.addWidget(self.btn_apply)

        layout.addLayout(bottom_bar)

    def _rebuild_filter_combo_items(self):
        self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        if self.sort_mode == MODE_PLUGINS:
            self.filter_combo.addItems([
                "All",
                "Moved",
                "Locked",
                "Issues (!)",
                "LOOT Matched",
                "Masters (ESM)",
                "Light (ESL)",
                "Active Only",
                "Disabled Only"
            ])
        else:
            self.filter_combo.addItems([
                "All",
                "Moved",
                "Locked",
                "Separators",
                "Active Only",
                "Disabled Only",
                "Asset: SKSE",
                "Asset: Mesh / Tex",
                "Asset: Script",
                "Asset: Anim"
            ])
        self.filter_combo.blockSignals(False)

    def _on_mode_changed(self, idx: int):
        self._save_settings()
        self.sort_mode = MODE_PLUGINS if idx == 1 else MODE_MODS
        is_plug = (self.sort_mode == MODE_PLUGINS)
        self.btn_dag_sort.setVisible(is_plug)
        self.btn_loot_update.setVisible(is_plug)
        self._rebuild_filter_combo_items()
        self._reload_profile_locks()
        self._load_current_list()

    def _show_detect_menu(self):
        envs = discover_detected_environments()
        menu = QMenu(self)
        if not envs:
            act_none = menu.addAction("No standard installations found")
            act_none.setEnabled(False)
        else:
            for label, p_dir, m_dir in envs:
                act = menu.addAction(label)
                act.setData((p_dir, m_dir))

        pos = self.btn_detect.mapToGlobal(QPoint(0, self.btn_detect.height()))
        chosen = menu.exec(pos) if hasattr(menu, "exec") else menu.exec_(pos)
        if chosen and chosen.data():
            p_dir, m_dir = chosen.data()
            self._apply_selected_environment(p_dir, explicit_mods_or_data=m_dir)

    def _run_offline_dag_sort(self):
        if self.sort_mode != MODE_PLUGINS or not self.sortable_file_order:
            return
        panel_curr = self._to_panel(self.sortable_file_order)
        locked_in_order = [m for m in panel_curr if m in self.locked_mods_set]
        sorted_panel = enforce_plugin_constraints(
            panel_curr,
            self.plugin_meta_map,
            locked_in_order,
            panel_curr,
            loot_group_ranks=self.loot_group_ranks,
            loot_plugin_rules=self.loot_plugin_rules,
            apply_group_sort=True
        )
        self._on_ai_success(sorted_panel)
        moved = len(self._last_moved_set)
        loot_note = f" + LOOT ({len(self.loot_plugin_rules)} rules)" if self.loot_plugin_rules else ""
        self.status_label.setText(f"DAG Sort complete: {moved} plugin(s) reordered (MAST{loot_note})")

    def _update_loot_masterlist(self):
        if self.loot_worker is not None and self.loot_worker.isRunning():
            return
        repo = detect_loot_game_repo(self.raw_mods_order, self.profile_path, self.game_data_path)
        self.current_loot_repo = repo
        target_path = os.path.join(get_app_base_dir(), "loot_cache", repo, "masterlist.yaml")

        self.btn_loot_update.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.loot_worker = MasterlistDownloadWorker(repo, target_path)
        self.loot_worker.progress_update.connect(self._on_progress)
        self.loot_worker.finished_ok.connect(self._on_loot_download_ok)
        self.loot_worker.failed.connect(self._on_loot_download_error)
        _ACTIVE_WORKERS[:] = [w for w in _ACTIVE_WORKERS if w.isRunning()]
        _ACTIVE_WORKERS.append(self.loot_worker)
        self.loot_worker.start()

    def _on_loot_download_ok(self, saved_path: str, branch: str):
        self.btn_loot_update.setEnabled(True)
        if self.worker is None or not self.worker.isRunning():
            self.progress_bar.setVisible(False)
        self.current_masterlist_path = saved_path
        self._load_loot_rules_for_current_plugins()
        self._evaluate_plugin_diagnostics(self.raw_mods_order)
        self._rebuild_stats_cache()
        prop_panel = self._to_panel(self.proposed_order) if self.proposed_order else []
        self._populate_table(self._to_panel(self.raw_mods_order), prop_panel)
        self._update_stats()
        self.status_label.setText(
            f"LOOT Masterlist updated ({self.current_loot_repo}@{branch}): "
            f"{len(self.loot_plugin_rules)} plugins matched"
        )

    def _on_loot_download_error(self, err_msg: str):
        self.btn_loot_update.setEnabled(True)
        if self.worker is None or not self.worker.isRunning():
            self.progress_bar.setVisible(False)
        self.status_label.setText("LOOT Masterlist update failed")
        QMessageBox.warning(self, "LOOT Masterlist Error", err_msg)

    # ---------------------------------------------------- Path Bar Handlers
    def _browse_profile_folder(self):
        start_dir = self.profile_path or os.path.expanduser("~")
        chosen = QFileDialog.getExistingDirectory(
            self, "Select MO2 Folder, Profile Folder, or Game Folder", start_dir
        )
        if not chosen:
            return
        self._apply_selected_environment(chosen)

    def _browse_mods_folder(self):
        start_dir = self.mods_path or self.game_data_path or self.profile_path or os.path.expanduser("~")
        chosen = QFileDialog.getExistingDirectory(self, "Select MO2 Mods Folder or Game Data Folder", start_dir)
        if not chosen:
            return
        norm = os.path.normpath(chosen)
        if os.path.basename(norm).lower() == "data":
            self.game_data_path = norm
        else:
            self.mods_path = norm
        self.mods_path_input.setText(norm)
        self._save_settings()
        self._load_current_list()

    def _on_profile_path_edited(self):
        typed = self.profile_path_input.text().strip()
        if typed and os.path.normpath(typed) != self.profile_path:
            self._apply_selected_environment(typed)

    def _on_mods_path_edited(self):
        typed = self.mods_path_input.text().strip()
        norm = os.path.normpath(typed) if typed else ""
        if norm and os.path.isdir(norm):
            if os.path.basename(norm).lower() == "data":
                self.game_data_path = norm
            else:
                self.mods_path = norm
            self._save_settings()
            self._load_current_list()

    def _on_profile_combo_changed(self):
        prof_name = self.profile_combo.currentText().strip()
        if not prof_name or not self.profile_path:
            return
        parent_dir = os.path.dirname(self.profile_path)
        candidate = os.path.join(parent_dir, prof_name)
        if os.path.isdir(candidate) and os.path.normpath(candidate) != self.profile_path:
            self.profile_path = os.path.normpath(candidate)
            self._update_derived_paths()
            self.profile_path_input.blockSignals(True)
            self.profile_path_input.setText(self.profile_path)
            self.profile_path_input.blockSignals(False)
            self._reload_profile_locks()
            self._save_settings()
            self._load_current_list()

    def _apply_selected_environment(self, path_str: str, explicit_mods_or_data: str = ""):
        prof_dir, auto_mods, auto_game_data, prof_list = resolve_mo2_environment(path_str)
        if not prof_dir and os.path.isdir(path_str):
            prof_dir = path_str
        mods_dir = auto_mods if auto_mods else (explicit_mods_or_data if explicit_mods_or_data else self.mods_path)
        if auto_game_data:
            self.game_data_path = auto_game_data
        elif explicit_mods_or_data and os.path.basename(explicit_mods_or_data).lower() == "data":
            self.game_data_path = explicit_mods_or_data

        self._sync_path_fields(prof_list, prof_dir, mods_dir)

        if prof_dir and not os.path.isfile(os.path.join(prof_dir, "modlist.txt")):
            if os.path.isfile(os.path.join(prof_dir, "plugins.txt")) or self.game_data_path:
                self.mode_combo.blockSignals(True)
                self.mode_combo.setCurrentIndex(1)
                self.mode_combo.blockSignals(False)
                self.sort_mode = MODE_PLUGINS
                self.btn_dag_sort.setVisible(True)
                self.btn_loot_update.setVisible(True)
                self._rebuild_filter_combo_items()

        self._reload_profile_locks()
        self._save_settings()
        self._load_current_list()

    def _reload_profile_locks(self):
        saved_locked = self._setting_val(self._locked_settings_key(), None)
        if saved_locked is None and self.sort_mode == MODE_MODS:
            saved_locked = self._setting_val("locked_mods", [])
        self.locked_mods_set = set(self._to_str_list(saved_locked))

    # ---------------------------------------------------- UI Controls
    def _toggle_api_key_visibility(self, checked: bool):
        self.key_input.setEchoMode(ECHO_NORMAL if checked else ECHO_PASSWORD)
        self.btn_toggle_key.setText("Hide" if checked else "Show")

    def _toggle_rules_panel(self, checked: bool):
        self.rules_input.setVisible(checked)

    def _export_preset(self):
        base_dir = self.profile_path if os.path.isdir(self.profile_path) else os.path.expanduser("~")
        default_file = os.path.join(base_dir, "align_preset.json")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Align Preset", default_file, "JSON Files (*.json)"
        )
        if not file_path:
            return
        data = {
            "app": APP_NAME,
            "version": APP_VERSION,
            "mode": "plugins" if self.sort_mode == MODE_PLUGINS else "mods",
            "custom_rules": self.rules_input.toPlainText(),
            "locked_items": sorted(self.locked_mods_set),
            "options": {
                "compact_mode": self.compact_mode,
                "keep_separators": self.keep_separators,
                "inspect_assets": self.inspect_assets,
                "include_nexus_meta": self.include_nexus_meta
            }
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.status_label.setText(f"Preset exported: {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _import_preset(self):
        base_dir = self.profile_path if os.path.isdir(self.profile_path) else os.path.expanduser("~")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Align Preset", base_dir, "JSON Files (*.json)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Invalid preset format.")

            if "custom_rules" in data:
                rules_str = str(data.get("custom_rules") or "")
                self.rules_input.setPlainText(rules_str)
                if rules_str.strip():
                    self.btn_toggle_rules.setChecked(True)

            raw_locks = data.get("locked_items", data.get("locked_mods"))
            if isinstance(raw_locks, list):
                imported_locks = {str(x) for x in raw_locks if isinstance(x, str)}
                if self.sort_mode == MODE_MODS:
                    for m in self.sortable_file_order:
                        if self.mod_prefixes.get(m) == "*":
                            imported_locks.add(m)
                else:
                    for p in self.sortable_file_order:
                        if p.lower() in OFFICIAL_MASTERS_LOWER:
                            imported_locks.add(p)
                self.locked_mods_set = imported_locks

            opts = data.get("options")
            if isinstance(opts, dict):
                if "compact_mode" in opts:
                    self.compact_mode = bool(opts["compact_mode"])
                if "keep_separators" in opts:
                    self.keep_separators = bool(opts["keep_separators"])
                if "inspect_assets" in opts:
                    self.inspect_assets = bool(opts["inspect_assets"])
                if "include_nexus_meta" in opts:
                    self.include_nexus_meta = bool(opts["include_nexus_meta"])

            self._rebuild_stats_cache()
            prop_panel = self._to_panel(self.proposed_order) if self.proposed_order else []
            self._populate_table(self._to_panel(self.raw_mods_order), prop_panel)
            self._update_stats()
            self._save_settings()
            self.status_label.setText(f"Preset imported: {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    def _show_table_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        curr_item = self.table.item(row, 1)
        prop_item = self.table.item(row, 4)
        curr_name = curr_item.text().strip() if curr_item else ""
        prop_name = prop_item.text().strip() if prop_item else ""
        mod_name = curr_name or prop_name

        menu = QMenu(self)
        act_lock = menu.addAction(f"{ICON_LOCK} Lock")
        act_unlock = menu.addAction(f"{ICON_UNLOCK} Unlock")

        act_up = None
        act_down = None
        act_ins_sep = None
        act_ren_sep = None
        act_del_sep = None

        if self.proposed_order:
            menu.addSeparator()
            act_up = menu.addAction("Move Up in Proposed (Alt+Up)")
            act_down = menu.addAction("Move Down in Proposed (Alt+Down)")
            if self.sort_mode == MODE_MODS:
                act_ins_sep = menu.addAction("Insert Separator Above...")
                if prop_name.endswith(SEPARATOR_SUFFIX):
                    act_ren_sep = menu.addAction("Rename Separator...")
                    act_del_sep = menu.addAction("Delete Separator")

        act_rule_bottom = None
        act_rule_top = None
        act_copy = None

        if mod_name and not mod_name.endswith(SEPARATOR_SUFFIX):
            menu.addSeparator()
            act_rule_bottom = menu.addAction(f"Rule: Keep '{mod_name}' at Bottom")
            act_rule_top = menu.addAction(f"Rule: Keep '{mod_name}' at Top")
            act_copy = menu.addAction("Copy Name")

        global_pos = self.table.viewport().mapToGlobal(pos)
        chosen = menu.exec(global_pos) if hasattr(menu, "exec") else menu.exec_(global_pos)
        if not chosen:
            return

        if chosen == act_lock:
            self._lock_selected()
        elif chosen == act_unlock:
            self._unlock_selected()
        elif chosen == act_up:
            self._nudge_proposed(-1)
        elif chosen == act_down:
            self._nudge_proposed(1)
        elif chosen == act_ins_sep:
            self._insert_separator_at(row)
        elif chosen == act_ren_sep:
            self._rename_separator_at(row)
        elif chosen == act_del_sep:
            self._delete_separator_at(row)
        elif chosen == act_rule_bottom:
            self._append_custom_rule(f"- Keep '{mod_name}' at the very bottom (highest priority).")
        elif chosen == act_rule_top:
            self._append_custom_rule(f"- Keep '{mod_name}' at the very top (lowest priority).")
        elif chosen == act_copy:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(mod_name)

    def _append_custom_rule(self, rule_line: str):
        existing = self.rules_input.toPlainText().strip()
        if rule_line not in existing:
            updated = (existing + "\n" + rule_line).strip() if existing else rule_line
            self.rules_input.setPlainText(updated)
        if not self.btn_toggle_rules.isChecked():
            self.btn_toggle_rules.setChecked(True)

    def _nudge_proposed(self, direction: int):
        if not self.proposed_order:
            return
        rows = self._selected_visible_rows()
        if not rows:
            return
        row = rows[0]
        panel_prop = self._to_panel(self.proposed_order)
        target = row + direction
        if row < 0 or row >= len(panel_prop) or target < 0 or target >= len(panel_prop):
            return
        moved_item = panel_prop[row]
        panel_prop[row], panel_prop[target] = panel_prop[target], panel_prop[row]

        if self.sort_mode == MODE_PLUGINS:
            locked_in_order = [m for m in panel_prop if m in self.locked_mods_set]
            enforced = enforce_plugin_constraints(
                panel_prop,
                self.plugin_meta_map,
                locked_in_order,
                self.raw_mods_order,
                loot_group_ranks=self.loot_group_ranks,
                loot_plugin_rules=self.loot_plugin_rules,
                apply_group_sort=False
            )
            if enforced != panel_prop:
                self.status_label.setText(f"Master / LOOT constraint prevented moving '{moved_item}'")
                panel_prop = enforced

        self.proposed_order = self._from_panel(panel_prop)
        self._populate_table(self._to_panel(self.raw_mods_order), panel_prop)
        new_row = panel_prop.index(moved_item) if moved_item in panel_prop else target
        self.table.selectRow(new_row)

    def _insert_separator_at(self, row: int):
        if not self.proposed_order or self.sort_mode == MODE_PLUGINS:
            return
        text, ok = QInputDialog.getText(self, "New Separator", "Separator name:")
        if not ok or not text.strip():
            return
        sep_name = sanitize_separator(text.strip())
        panel_prop = self._to_panel(self.proposed_order)
        if sep_name in panel_prop:
            return
        idx = max(0, min(row, len(panel_prop)))
        panel_prop.insert(idx, sep_name)
        self.proposed_order = self._from_panel(panel_prop)
        self._populate_table(self._to_panel(self.raw_mods_order), panel_prop)

    def _rename_separator_at(self, row: int):
        panel_prop = self._to_panel(self.proposed_order)
        if row < 0 or row >= len(panel_prop):
            return
        old_name = panel_prop[row]
        if not old_name.endswith(SEPARATOR_SUFFIX):
            return
        base_old = old_name[:-len(SEPARATOR_SUFFIX)]
        text, ok = QInputDialog.getText(self, "Rename Separator", "New name:", text=base_old)
        if not ok or not text.strip():
            return
        new_name = sanitize_separator(text.strip())
        if new_name in panel_prop and new_name != old_name:
            return
        panel_prop[row] = new_name
        self.proposed_order = self._from_panel(panel_prop)
        self._populate_table(self._to_panel(self.raw_mods_order), panel_prop)

    def _delete_separator_at(self, row: int):
        panel_prop = self._to_panel(self.proposed_order)
        if row < 0 or row >= len(panel_prop):
            return
        if not panel_prop[row].endswith(SEPARATOR_SUFFIX):
            return
        panel_prop.pop(row)
        self.proposed_order = self._from_panel(panel_prop)
        self._populate_table(self._to_panel(self.raw_mods_order), panel_prop)

    def _on_preset_changed(self):
        new_preset = self.preset_combo.currentText()
        if self._active_preset:
            self._api_keys[self._active_preset] = self.key_input.text().strip()
        self._active_preset = new_preset

        data = PRESETS.get(new_preset, {})
        if new_preset != "Custom":
            self.url_input.setText(data.get("url", ""))
            self.model_input.setText(data.get("model", ""))
        self.key_input.setText(self._api_keys.get(new_preset, ""))

    def _locked_settings_key(self) -> str:
        prefix = "locked_plugins_json/" if self.sort_mode == MODE_PLUGINS else "locked_mods_json/"
        if not self.profile_path:
            return prefix + "default"
        profile_name = os.path.basename(os.path.normpath(self.profile_path)) or "default"
        return prefix + profile_name

    @staticmethod
    def _to_str_list(raw) -> List[str]:
        if raw is None:
            return []
        if isinstance(raw, (list, tuple)):
            return [str(x) for x in raw]
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return []
            try:
                data = json.loads(raw)
                if isinstance(data, list):
                    return [str(x) for x in data]
            except ValueError:
                pass
            return [raw]
        return []

    def _load_saved_settings(self):
        saved_preset = str(self._setting_val("preset", "Google Gemini"))
        idx = self.preset_combo.findText(saved_preset)
        if idx == -1:
            idx = 0
        preset_name = self.preset_combo.itemText(idx)

        raw_keys = self._setting_val("api_keys_json", "")
        try:
            loaded = json.loads(raw_keys) if raw_keys else {}
            self._api_keys = {str(k): str(v) for k, v in loaded.items()} if isinstance(loaded, dict) else {}
        except ValueError:
            self._api_keys = {}
        legacy_key = self._setting_val("key", "")
        if legacy_key and preset_name not in self._api_keys:
            self._api_keys[preset_name] = str(legacy_key)

        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentIndex(idx)
        self.preset_combo.blockSignals(False)
        self._active_preset = ""
        self._on_preset_changed()

        saved_url = self._setting_val("url", "")
        saved_model = self._setting_val("model", "")
        saved_rules = self._setting_val("custom_rules", "")
        if saved_url:
            self.url_input.setText(str(saved_url))
        if saved_model:
            self.model_input.setText(str(saved_model))
        if saved_rules:
            self.rules_input.setPlainText(str(saved_rules))
            if str(saved_rules).strip():
                self.btn_toggle_rules.setChecked(True)

        try:
            saved_timeout = int(self._setting_val("request_timeout", DEFAULT_REQUEST_TIMEOUT))
        except (TypeError, ValueError):
            saved_timeout = DEFAULT_REQUEST_TIMEOUT
        self.request_timeout = max(MIN_REQUEST_TIMEOUT, min(MAX_REQUEST_TIMEOUT, saved_timeout))

        raw_compact = self._setting_val("compact_mode", "false")
        self.compact_mode = str(raw_compact).lower() in ("true", "1", "yes")

        raw_keep_seps = self._setting_val("keep_separators", "false")
        self.keep_separators = str(raw_keep_seps).lower() in ("true", "1", "yes")

        raw_inspect = self._setting_val("inspect_assets", "true")
        self.inspect_assets = str(raw_inspect).lower() in ("true", "1", "yes")

        raw_nexus = self._setting_val("include_nexus_meta", "true")
        self.include_nexus_meta = str(raw_nexus).lower() in ("true", "1", "yes")

        self._reload_profile_locks()

    def _save_settings(self):
        if self._active_preset:
            self._api_keys[self._active_preset] = self.key_input.text().strip()
        self.settings.setValue("preset", self.preset_combo.currentText())
        self.settings.setValue("url", self.url_input.text().strip())
        self.settings.setValue("model", self.model_input.text().strip())
        self.settings.setValue("api_keys_json", json.dumps(self._api_keys, ensure_ascii=False))
        self.settings.remove("key")
        self.settings.setValue("custom_rules", self.rules_input.toPlainText())
        self.settings.setValue("request_timeout", int(self.request_timeout))
        self.settings.setValue("compact_mode", "true" if self.compact_mode else "false")
        self.settings.setValue("keep_separators", "true" if self.keep_separators else "false")
        self.settings.setValue("inspect_assets", "true" if self.inspect_assets else "false")
        self.settings.setValue("include_nexus_meta", "true" if self.include_nexus_meta else "false")
        if self._organizer is None:
            self.settings.setValue("standalone_profile_path", self.profile_path)
            self.settings.setValue("standalone_mods_path", self.mods_path or self.game_data_path)
        self.settings.setValue(
            self._locked_settings_key(),
            json.dumps(sorted(self.locked_mods_set), ensure_ascii=False)
        )

    def done(self, result):
        if self.worker is not None and self.worker.isRunning():
            self.worker.abort()
            try:
                self.worker.progress_update.disconnect()
                self.worker.sorted_ready.disconnect()
                self.worker.failed.disconnect()
            except Exception:
                pass
        try:
            self._save_settings()
        except Exception:
            pass
        super().done(result)

    def _to_panel(self, file_order: List[str]) -> List[str]:
        if self.sort_mode == MODE_PLUGINS:
            return list(file_order)
        return list(reversed(file_order)) if self.file_is_descending else list(file_order)

    def _from_panel(self, panel_order: List[str]) -> List[str]:
        if self.sort_mode == MODE_PLUGINS:
            return list(panel_order)
        return list(reversed(panel_order)) if self.file_is_descending else list(panel_order)

    def _detect_descending(self) -> bool:
        if self._organizer is not None:
            try:
                mod_list = self._organizer.modList()
                existing = set(mod_list.allMods())
                valid = [
                    m for m in self.raw_mods_order
                    if m in existing and self.mod_prefixes.get(m) != "*"
                ]
                if len(valid) >= 2:
                    return mod_list.priority(valid[0]) > mod_list.priority(valid[-1])
            except Exception:
                pass
        return True

    def _scan_all_mods_metadata(self):
        self.mod_meta_map = {}
        mods_dir = self.mods_path
        if not mods_dir or not os.path.isdir(mods_dir):
            for name in self.raw_mods_order:
                if self.mod_prefixes.get(name) == "*":
                    self.mod_meta_map[name] = (["DLC"], 0, "")
            return

        for name in self.raw_mods_order:
            if name.endswith(SEPARATOR_SUFFIX):
                continue
            if self.mod_prefixes.get(name) == "*":
                self.mod_meta_map[name] = (["DLC"], 0, "")
                continue
            folder = os.path.join(mods_dir, name)
            self.mod_meta_map[name] = inspect_mod_directory(folder)

    def _load_loot_rules_for_current_plugins(self):
        self.loot_group_ranks = {}
        self.loot_plugin_rules = {}
        if not self.raw_mods_order:
            return
        self.current_loot_repo = detect_loot_game_repo(
            self.raw_mods_order, self.profile_path, self.game_data_path
        )
        ml_path = find_existing_masterlist_path(self.current_loot_repo)
        self.current_masterlist_path = ml_path
        if not ml_path:
            return
        installed_lower = {p.lower() for p in self.raw_mods_order}
        self.loot_group_ranks, self.loot_plugin_rules = parse_loot_masterlist(ml_path, installed_lower)

    def _scan_all_plugins_metadata(self):
        self.plugin_meta_map = {}
        self.plugin_issues_map = {}
        plugin_locations: Dict[str, Tuple[str, str]] = {}

        data_dir = self.game_data_path
        if not data_dir and self.mods_path and os.path.basename(self.mods_path).lower() == "data":
            data_dir = self.mods_path

        if data_dir and os.path.isdir(data_dir):
            try:
                with os.scandir(data_dir) as it:
                    for entry in it:
                        if entry.is_file() and entry.name.lower().endswith((".esm", ".esp", ".esl")):
                            plugin_locations[entry.name.lower()] = (entry.path, "Game Data")
            except Exception:
                pass

        active_mods_asc: List[str] = []
        if self.modlist_path and os.path.isfile(self.modlist_path):
            try:
                with open(self.modlist_path, "r", encoding="utf-8-sig") as f:
                    lines = [ln.strip() for ln in f.read().splitlines() if ln.strip() and not ln.startswith("#")]
                for ln in reversed(lines):
                    if ln[0] == "+":
                        active_mods_asc.append(ln[1:])
            except Exception:
                pass

        if self.mods_path and os.path.isdir(self.mods_path) and self.mods_path != data_dir:
            scan_mod_names = active_mods_asc
            if not scan_mod_names:
                try:
                    scan_mod_names = [d.name for d in os.scandir(self.mods_path) if d.is_dir()]
                except Exception:
                    scan_mod_names = []

            for mod_name in scan_mod_names:
                mod_folder = os.path.join(self.mods_path, mod_name)
                if not os.path.isdir(mod_folder):
                    continue
                try:
                    with os.scandir(mod_folder) as it:
                        for entry in it:
                            if entry.is_file() and entry.name.lower().endswith((".esm", ".esp", ".esl")):
                                plugin_locations[entry.name.lower()] = (entry.path, mod_name)
                except Exception:
                    pass

            overwrite_dir = os.path.join(os.path.dirname(self.mods_path), "overwrite")
            if os.path.isdir(overwrite_dir):
                try:
                    with os.scandir(overwrite_dir) as it:
                        for entry in it:
                            if entry.is_file() and entry.name.lower().endswith((".esm", ".esp", ".esl")):
                                plugin_locations[entry.name.lower()] = (entry.path, "Overwrite")
                except Exception:
                    pass

        for plug_name in self.raw_mods_order:
            loc = plugin_locations.get(plug_name.lower())
            if loc:
                fpath, src_mod = loc
                is_esm, is_esl, masters = parse_tes4_header(fpath)
                self.plugin_meta_map[plug_name] = (is_esm, is_esl, masters, src_mod)
            else:
                lname = plug_name.lower()
                is_esm = lname.endswith((".esm", ".esl")) or lname in OFFICIAL_MASTERS_LOWER
                is_esl = lname.endswith(".esl")
                src = "Base / CC" if (lname in OFFICIAL_MASTERS_LOWER or lname.startswith("cc")) else ""
                self.plugin_meta_map[plug_name] = (is_esm, is_esl, [], src)

        self._load_loot_rules_for_current_plugins()
        self._evaluate_plugin_diagnostics(self.raw_mods_order)

    def _evaluate_plugin_diagnostics(self, order_list: List[str]):
        self.plugin_issues_map = {}
        idx_map = {p.lower(): i for i, p in enumerate(order_list)}
        active_lower = {
            p.lower() for p in order_list
            if self.mod_prefixes.get(p, "*") == "*"
        }

        for i, plug_name in enumerate(order_list):
            if self.mod_prefixes.get(plug_name, "*") != "*":
                continue
            if plug_name not in self.plugin_meta_map:
                continue
            pl = plug_name.lower()
            _, _, masters, _ = self.plugin_meta_map[plug_name]
            found_issue = False
            for m in masters:
                ml = m.lower()
                if ml not in idx_map and ml not in OFFICIAL_MASTERS_LOWER:
                    self.plugin_issues_map[plug_name] = f"!MISS: {m}"
                    found_issue = True
                    break
                if ml in idx_map and ml not in active_lower and ml not in OFFICIAL_MASTERS_LOWER:
                    self.plugin_issues_map[plug_name] = f"!OFF: {m}"
                    found_issue = True
                    break
                if ml in idx_map and idx_map[ml] > i:
                    self.plugin_issues_map[plug_name] = f"!ORDER: {m}"
                    found_issue = True
                    break

            if not found_issue and pl in self.loot_plugin_rules:
                _, l_after, l_req, l_inc = self.loot_plugin_rules[pl]
                for inc_p in l_inc:
                    if inc_p.lower() in active_lower:
                        self.plugin_issues_map[plug_name] = f"!INC: {inc_p}"
                        found_issue = True
                        break
                if not found_issue:
                    for req_p in l_req:
                        rl = req_p.lower()
                        if rl.endswith((".esp", ".esm", ".esl")) and rl not in idx_map and rl not in OFFICIAL_MASTERS_LOWER:
                            self.plugin_issues_map[plug_name] = f"!REQ: {req_p}"
                            found_issue = True
                            break
                if not found_issue:
                    for aft_p in l_after:
                        al = aft_p.lower()
                        if al in idx_map and idx_map[al] > i:
                            self.plugin_issues_map[plug_name] = f"!LOOT: after {aft_p}"
                            break

    def _format_table_meta_badge(self, name: str) -> str:
        if not name:
            return ""
        if self.sort_mode == MODE_PLUGINS:
            if name not in self.plugin_meta_map:
                return ""
            is_esm, is_esl, masters, src_mod = self.plugin_meta_map[name]
            parts = []
            issue = self.plugin_issues_map.get(name, "")
            if issue:
                parts.append(issue)
            flags = []
            if is_esm:
                flags.append("ESM")
            if is_esl:
                flags.append("ESL")
            if flags:
                parts.append("/".join(flags))
            if masters:
                parts.append(f"M:{len(masters)}")
            pl = name.lower()
            if pl in self.loot_plugin_rules and not issue:
                grp = self.loot_plugin_rules[pl][0]
                if grp and grp != "default":
                    parts.append(f"grp:{grp[:14]}")
                else:
                    parts.append("LOOT")
            elif src_mod and not issue:
                parts.append(src_mod[:18])
            return " | ".join(parts)

        if name.endswith(SEPARATOR_SUFFIX) or name not in self.mod_meta_map:
            return ""
        tags, nx_id, cat_name = self.mod_meta_map[name]
        parts = []
        if self.inspect_assets and tags:
            parts.append(" \u00b7 ".join(tags[:3]))
        if self.include_nexus_meta:
            if cat_name:
                parts.append(cat_name)
            elif nx_id > 0:
                parts.append(f"#{nx_id}")
        return " | ".join(parts)

    def _load_current_list(self):
        if self.sort_mode == MODE_PLUGINS:
            self._load_current_plugins()
        else:
            self._load_current_modlist()

    def _load_current_plugins(self):
        self.original_lines = []
        self.raw_mods_order = []
        self.mod_prefixes = {}
        self.plugin_meta_map = {}
        self.plugin_issues_map = {}
        self.loot_group_ranks = {}
        self.loot_plugin_rules = {}
        self.lead_foreign = []
        self.trail_foreign = []
        self.sortable_file_order = []
        self.proposed_order = []
        self.btn_apply.setEnabled(False)
        self.btn_move_up.setEnabled(False)
        self.btn_move_down.setEnabled(False)
        self._rebuild_stats_cache()

        has_plugins = bool(self.plugins_path and os.path.isfile(self.plugins_path))
        has_loadorder = bool(self.loadorder_path and os.path.isfile(self.loadorder_path))
        data_dir = self.game_data_path or (
            self.mods_path if os.path.basename(self.mods_path).lower() == "data" else ""
        )

        if not has_plugins and not has_loadorder and not (data_dir and os.path.isdir(data_dir)):
            self._populate_table([], [])
            self._update_stats()
            self.status_label.setText("Select MO2 Profile, Game AppData, or Game Data folder")
            return

        active_set: Set[str] = set()
        plugins_txt_order: List[str] = []

        if has_plugins:
            with open(self.plugins_path, "r", encoding="utf-8-sig") as f:
                for line in f.read().splitlines():
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    if s.startswith("*"):
                        pname = s[1:].strip()
                        if pname:
                            active_set.add(pname.lower())
                            plugins_txt_order.append(pname)
                    else:
                        plugins_txt_order.append(s)

        seen_lower: Set[str] = set()
        if has_loadorder:
            with open(self.loadorder_path, "r", encoding="utf-8-sig") as f:
                for line in f.read().splitlines():
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    pname = s[1:].strip() if s.startswith("*") else s
                    if pname and pname.lower() not in seen_lower:
                        self.raw_mods_order.append(pname)
                        seen_lower.add(pname.lower())

        for pname in plugins_txt_order:
            if pname.lower() not in seen_lower:
                self.raw_mods_order.append(pname)
                seen_lower.add(pname.lower())

        if data_dir and os.path.isdir(data_dir):
            try:
                disk_plugins = sorted(
                    entry.name for entry in os.scandir(data_dir)
                    if entry.is_file() and entry.name.lower().endswith((".esm", ".esp", ".esl"))
                )
                for dp in disk_plugins:
                    if dp.lower() not in seen_lower:
                        self.raw_mods_order.append(dp)
                        seen_lower.add(dp.lower())
            except Exception:
                pass

        for pname in self.raw_mods_order:
            pl = pname.lower()
            is_act = (pl in active_set) or (pl in OFFICIAL_MASTERS_LOWER) or pl.startswith("cc") or not has_plugins
            self.mod_prefixes[pname] = "*" if is_act else "-"

        self.file_is_descending = False
        self.sortable_file_order = list(self.raw_mods_order)

        for p in self.sortable_file_order:
            pl = p.lower()
            if pl in OFFICIAL_MASTERS_LOWER or pl.startswith("cc"):
                self.locked_mods_set.add(p)

        self._scan_all_plugins_metadata()
        self._rebuild_stats_cache()
        self._populate_table(self._to_panel(self.raw_mods_order), [])
        self._update_stats()
        prof_label = os.path.basename(self.profile_path) or "Data"
        issues_cnt = len(self.plugin_issues_map)
        loot_cnt = len(self.loot_plugin_rules)
        loot_msg = f" · LOOT DB: {loot_cnt} matched" if loot_cnt else " · No LOOT DB (Click 'Update LOOT DB')"
        issue_msg = f" · {issues_cnt} issue(s)" if issues_cnt else ""
        self.status_label.setText(f"Loaded Plugins: {prof_label}{loot_msg}{issue_msg}")

    def _load_current_modlist(self):
        self.original_lines = []
        self.raw_mods_order = []
        self.mod_prefixes = {}
        self.mod_meta_map = {}
        self.lead_foreign = []
        self.trail_foreign = []
        self.sortable_file_order = []
        self.proposed_order = []
        self.btn_apply.setEnabled(False)
        self.btn_move_up.setEnabled(False)
        self.btn_move_down.setEnabled(False)
        self._rebuild_stats_cache()

        if not self.modlist_path or not os.path.isfile(self.modlist_path):
            self._populate_table([], [])
            self._update_stats()
            self.status_label.setText("modlist.txt not found (Switch to Right Panel for non-MO2 setups)")
            return

        with open(self.modlist_path, "r", encoding="utf-8-sig") as f:
            self.original_lines = [line.strip() for line in f.read().splitlines()]

        for line in self.original_lines:
            if not line or line.startswith("#"):
                continue
            prefix = line[0]
            name = line[1:]
            if prefix not in "+-*" or not name:
                continue
            self.raw_mods_order.append(name)
            self.mod_prefixes[name] = prefix

        self.file_is_descending = self._detect_descending()

        names = self.raw_mods_order
        i = 0
        while i < len(names) and self.mod_prefixes[names[i]] == "*":
            i += 1
        j = len(names)
        while j > i and self.mod_prefixes[names[j - 1]] == "*":
            j -= 1
        self.lead_foreign = names[:i]
        self.trail_foreign = names[j:]
        self.sortable_file_order = names[i:j]

        for m in self.sortable_file_order:
            if self.mod_prefixes.get(m) == "*":
                self.locked_mods_set.add(m)

        self._scan_all_mods_metadata()
        self._rebuild_stats_cache()
        self._populate_table(self._to_panel(self.raw_mods_order), [])
        self._update_stats()
        prof_label = os.path.basename(self.profile_path) or "Profile"
        self.status_label.setText(f"Loaded Mods: {prof_label}")

    def _populate_table(self, current: List[str], proposed: List[str]):
        self._is_populating = True
        try:
            moved = compute_moved(current, proposed) if proposed else set()
            self._last_moved_set = moved
            current_set = set(current)

            curr_mod_rank: Dict[str, int] = {}
            for name in current:
                if not name.endswith(SEPARATOR_SUFFIX):
                    curr_mod_rank[name] = len(curr_mod_rank)

            prop_mod_rank: Dict[str, int] = {}
            for name in proposed:
                if not name.endswith(SEPARATOR_SUFFIX):
                    prop_mod_rank[name] = len(prop_mod_rank)

            max_rows = max(len(current), len(proposed))
            self.table.setRowCount(max_rows)

            color_separator = QColor(30, 58, 138, 110)
            color_new_separator = QColor(8, 145, 178, 130)
            color_modified = QColor(180, 83, 9, 110)
            color_locked = QColor(21, 128, 61, 110)
            color_issue = QColor(185, 28, 28, 125)
            color_text_bright = QColor(244, 244, 245)
            color_meta_text = QColor(161, 161, 170)
            color_issue_text = QColor(252, 165, 165)

            for i in range(max_rows):
                curr_text = current[i] if i < len(current) else ""
                prop_text = proposed[i] if i < len(proposed) else ""
                has_issue = (self.sort_mode == MODE_PLUGINS) and (curr_text in self.plugin_issues_map)

                lock_item = QTableWidgetItem()
                if curr_text and not curr_text.endswith(SEPARATOR_SUFFIX):
                    lock_item.setFlags(FLAG_ENABLED | FLAG_USER_CHECKABLE | FLAG_SELECTABLE)
                    is_locked = curr_text in self.locked_mods_set
                    lock_item.setCheckState(CHECKED if is_locked else UNCHECKED)
                else:
                    lock_item.setFlags(FLAG_ENABLED)
                lock_item.setTextAlignment(ALIGN_CENTER)
                self.table.setItem(i, 0, lock_item)

                item_curr = QTableWidgetItem(curr_text)
                item_curr.setFlags(FLAG_PLAIN)
                item_curr.setForeground(color_text_bright)
                if has_issue:
                    item_curr.setBackground(color_issue)
                elif curr_text.endswith(SEPARATOR_SUFFIX):
                    item_curr.setBackground(color_separator)
                elif curr_text in self.locked_mods_set:
                    item_curr.setBackground(color_locked)
                self.table.setItem(i, 1, item_curr)

                meta_item = QTableWidgetItem(self._format_table_meta_badge(curr_text))
                meta_item.setFlags(FLAG_PLAIN)
                meta_item.setForeground(color_issue_text if has_issue else color_meta_text)
                self.table.setItem(i, 2, meta_item)

                delta_item = QTableWidgetItem("")
                delta_item.setFlags(FLAG_PLAIN)
                delta_item.setTextAlignment(ALIGN_CENTER)
                if prop_text:
                    if prop_text.endswith(SEPARATOR_SUFFIX):
                        if prop_text not in current_set:
                            delta_item.setText("NEW")
                            delta_item.setForeground(QColor(56, 189, 248))
                        else:
                            delta_item.setText("SEP")
                            delta_item.setForeground(QColor(148, 163, 184))
                    elif prop_text in self.locked_mods_set:
                        delta_item.setText(ICON_LOCK)
                        delta_item.setForeground(QColor(74, 222, 128))
                    elif prop_text in moved:
                        old_r = curr_mod_rank.get(prop_text, 0)
                        new_r = prop_mod_rank.get(prop_text, 0)
                        diff = new_r - old_r
                        if diff > 0:
                            delta_item.setText(f"\u2193+{diff}")
                        elif diff < 0:
                            delta_item.setText(f"\u2191{diff}")
                        else:
                            delta_item.setText("\u2194")
                        delta_item.setForeground(QColor(251, 191, 36))
                    else:
                        delta_item.setText("\u00b7")
                        delta_item.setForeground(QColor(161, 161, 170))
                self.table.setItem(i, 3, delta_item)

                item_prop = QTableWidgetItem(prop_text)
                item_prop.setFlags(FLAG_PLAIN)
                item_prop.setForeground(color_text_bright)
                if prop_text.endswith(SEPARATOR_SUFFIX):
                    item_prop.setBackground(
                        color_new_separator if prop_text not in current_set else color_separator
                    )
                elif prop_text in self.locked_mods_set:
                    item_prop.setBackground(color_locked)
                elif prop_text in moved:
                    item_prop.setBackground(color_modified)
                self.table.setItem(i, 4, item_prop)
        finally:
            self._is_populating = False

        self._apply_filter()

    def _has_asset_tag(self, mod_name: str, target_tags: Set[str]) -> bool:
        if not mod_name or mod_name not in self.mod_meta_map:
            return False
        tags = self.mod_meta_map[mod_name][0]
        return any(t in target_tags for t in tags)

    def _apply_filter(self, *_args):
        query = self.search_input.text().strip().casefold()
        mode = self.filter_combo.currentIndex()

        self.table.setUpdatesEnabled(False)
        try:
            for row in range(self.table.rowCount()):
                curr_item = self.table.item(row, 1)
                meta_item = self.table.item(row, 2)
                prop_item = self.table.item(row, 4)
                curr_raw = curr_item.text() if curr_item else ""
                meta_raw = meta_item.text() if meta_item else ""
                prop_raw = prop_item.text() if prop_item else ""

                if query:
                    matches_text = (
                        (query in curr_raw.casefold())
                        or (query in prop_raw.casefold())
                        or (query in meta_raw.casefold())
                    )
                else:
                    matches_text = True

                matches_mode = True
                if self.sort_mode == MODE_PLUGINS:
                    if mode == 1:
                        matches_mode = (prop_raw in self._last_moved_set) or (curr_raw in self._last_moved_set)
                    elif mode == 2:
                        matches_mode = (curr_raw in self.locked_mods_set) or (prop_raw in self.locked_mods_set)
                    elif mode == 3:
                        matches_mode = (curr_raw in self.plugin_issues_map) or (prop_raw in self.plugin_issues_map)
                    elif mode == 4:
                        matches_mode = (curr_raw.lower() in self.loot_plugin_rules) or (
                            prop_raw.lower() in self.loot_plugin_rules
                        )
                    elif mode == 5:
                        m1 = self.plugin_meta_map.get(curr_raw, (False, False, [], ""))[0]
                        m2 = self.plugin_meta_map.get(prop_raw, (False, False, [], ""))[0]
                        matches_mode = m1 or m2
                    elif mode == 6:
                        l1 = self.plugin_meta_map.get(curr_raw, (False, False, [], ""))[1]
                        l2 = self.plugin_meta_map.get(prop_raw, (False, False, [], ""))[1]
                        matches_mode = l1 or l2
                    elif mode == 7:
                        p1 = self.mod_prefixes.get(curr_raw, "")
                        p2 = self.mod_prefixes.get(prop_raw, "")
                        matches_mode = (p1 == "*") or (p2 == "*")
                    elif mode == 8:
                        p1 = self.mod_prefixes.get(curr_raw, "")
                        p2 = self.mod_prefixes.get(prop_raw, "")
                        matches_mode = (p1 == "-") or (p2 == "-")
                else:
                    if mode == 1:
                        matches_mode = (prop_raw in self._last_moved_set) or (curr_raw in self._last_moved_set)
                    elif mode == 2:
                        matches_mode = (curr_raw in self.locked_mods_set) or (prop_raw in self.locked_mods_set)
                    elif mode == 3:
                        matches_mode = curr_raw.endswith(SEPARATOR_SUFFIX) or prop_raw.endswith(SEPARATOR_SUFFIX)
                    elif mode == 4:
                        p1 = self.mod_prefixes.get(curr_raw, "")
                        p2 = self.mod_prefixes.get(prop_raw, "")
                        matches_mode = (p1 in ("+", "*")) or (p2 in ("+", "*"))
                    elif mode == 5:
                        p1 = self.mod_prefixes.get(curr_raw, "")
                        p2 = self.mod_prefixes.get(prop_raw, "")
                        matches_mode = (p1 == "-" and not curr_raw.endswith(SEPARATOR_SUFFIX)) or (
                            p2 == "-" and not prop_raw.endswith(SEPARATOR_SUFFIX)
                        )
                    elif mode == 6:
                        matches_mode = self._has_asset_tag(curr_raw, {"SKSE", "SKSE-Cfg"}) or self._has_asset_tag(
                            prop_raw, {"SKSE", "SKSE-Cfg"}
                        )
                    elif mode == 7:
                        matches_mode = self._has_asset_tag(curr_raw, {"Mesh", "Tex"}) or self._has_asset_tag(
                            prop_raw, {"Mesh", "Tex"}
                        )
                    elif mode == 8:
                        matches_mode = self._has_asset_tag(curr_raw, {"Script"}) or self._has_asset_tag(
                            prop_raw, {"Script"}
                        )
                    elif mode == 9:
                        matches_mode = self._has_asset_tag(curr_raw, {"Anim"}) or self._has_asset_tag(
                            prop_raw, {"Anim"}
                        )

                self.table.setRowHidden(row, not (matches_text and matches_mode))
        finally:
            self.table.setUpdatesEnabled(True)

    def _selected_visible_rows(self) -> List[int]:
        rows = sorted(set(index.row() for index in self.table.selectedIndexes()))
        return [row for row in rows if not self.table.isRowHidden(row)]

    def _rebuild_stats_cache(self):
        entries = self.sortable_file_order
        panel_entries = self._to_panel(entries)
        self._sortable_set = set(entries)
        self._sortable_sep_count = sum(1 for n in entries if n.endswith(SEPARATOR_SUFFIX))
        self._sortable_mod_count = len(entries) - self._sortable_sep_count

        if self.sort_mode == MODE_PLUGINS:
            inst_lower = {n.lower() for n in panel_entries}
            annotated = [
                format_plugin_with_meta(
                    name,
                    self.plugin_meta_map,
                    self.loot_group_ranks,
                    self.loot_plugin_rules,
                    inst_lower
                )
                for name in panel_entries
            ]
            if self.compact_mode:
                payload_list = [f"{i}: {line}" for i, line in enumerate(annotated)]
            else:
                payload_list = annotated
        else:
            use_meta = bool(self.mod_meta_map and (self.inspect_assets or self.include_nexus_meta))
            if self.compact_mode:
                if use_meta:
                    payload_list = [
                        f"{i}: {format_mod_with_meta(name, self.mod_meta_map, self.inspect_assets, self.include_nexus_meta)}"
                        for i, name in enumerate(panel_entries)
                    ]
                else:
                    payload_list = [f"{i}: {name}" for i, name in enumerate(panel_entries)]
            else:
                if use_meta:
                    payload_list = [
                        format_mod_with_meta(name, self.mod_meta_map, self.inspect_assets, self.include_nexus_meta)
                        for name in panel_entries
                    ]
                else:
                    payload_list = panel_entries

        self._mods_json_cache = json.dumps(payload_list, ensure_ascii=False)

    def _update_stats(self, *_args):
        locked_sent = [m for m in self.locked_mods_set if m in self._sortable_set]

        tokens = 0
        if self._sortable_set:
            sys_prompt = PLUGIN_SYSTEM_PROMPT if self.sort_mode == MODE_PLUGINS else SYSTEM_PROMPT
            user_content = build_user_prompt(
                self.sortable_file_order,
                locked_sent,
                self.rules_input.toPlainText(),
                mods_json=self._mods_json_cache,
                compact_mode=self.compact_mode,
                keep_separators=self.keep_separators,
                is_plugin_mode=(self.sort_mode == MODE_PLUGINS)
            )
            chars = len(sys_prompt) + len(user_content)
            tokens = (chars + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN
            if tokens >= 100:
                tokens = int(round(tokens, -1))

        flags = []
        if self.compact_mode:
            flags.append("ID")
        if self.sort_mode == MODE_PLUGINS:
            if self.loot_plugin_rules:
                flags.append(f"LOOT:{len(self.loot_plugin_rules)}")
            else:
                flags.append("MAST")
            if self.plugin_issues_map:
                flags.append(f"!{len(self.plugin_issues_map)}")
        else:
            if self.keep_separators:
                flags.append("KeepSep")
            if self.inspect_assets:
                flags.append("Assets")
            if self.include_nexus_meta:
                flags.append("Nexus")
        flag_str = f"  [{', '.join(flags)}]" if flags else ""

        unit_label = "plugins" if self.sort_mode == MODE_PLUGINS else "mods"
        self.stats_label.setText(
            f"{self._sortable_mod_count:,} {unit_label}  \u00b7  "
            f"{len(locked_sent):,} locked  \u00b7  "
            f"~{tokens:,} tok{flag_str}"
        )

    def _on_table_item_changed(self, item: QTableWidgetItem):
        if self._is_populating or item.column() != 0:
            return
        curr_item = self.table.item(item.row(), 1)
        if not curr_item:
            return
        mod_name = curr_item.text().strip()
        if not mod_name or mod_name.endswith(SEPARATOR_SUFFIX):
            return

        self._is_populating = True
        try:
            has_issue = (self.sort_mode == MODE_PLUGINS) and (mod_name in self.plugin_issues_map)
            if item.checkState() == CHECKED:
                self.locked_mods_set.add(mod_name)
                if not has_issue:
                    curr_item.setBackground(QColor(21, 128, 61, 110))
            else:
                self.locked_mods_set.discard(mod_name)
                if not has_issue:
                    curr_item.setBackground(QColor(24, 24, 28))
        finally:
            self._is_populating = False

        self._update_stats()
        self._save_settings()

    def _lock_selected(self):
        for row in self._selected_visible_rows():
            item_lock = self.table.item(row, 0)
            curr_item = self.table.item(row, 1)
            if item_lock and curr_item:
                mod_name = curr_item.text().strip()
                if mod_name and not mod_name.endswith(SEPARATOR_SUFFIX):
                    item_lock.setCheckState(CHECKED)

    def _unlock_selected(self):
        for row in self._selected_visible_rows():
            item_lock = self.table.item(row, 0)
            if item_lock:
                item_lock.setCheckState(UNCHECKED)

    def _unlock_all(self):
        self._is_populating = True
        try:
            self.locked_mods_set.clear()
            if self.sort_mode == MODE_MODS:
                for m in self.sortable_file_order:
                    if self.mod_prefixes.get(m) == "*":
                        self.locked_mods_set.add(m)
            else:
                for p in self.sortable_file_order:
                    pl = p.lower()
                    if pl in OFFICIAL_MASTERS_LOWER or pl.startswith("cc"):
                        self.locked_mods_set.add(p)

            for row in range(self.table.rowCount()):
                item_lock = self.table.item(row, 0)
                curr_item = self.table.item(row, 1)
                mod_name = curr_item.text().strip() if curr_item else ""
                is_locked = mod_name in self.locked_mods_set
                has_issue = (self.sort_mode == MODE_PLUGINS) and (mod_name in self.plugin_issues_map)
                if item_lock and (item_lock.flags() & FLAG_USER_CHECKABLE):
                    item_lock.setCheckState(CHECKED if is_locked else UNCHECKED)
                if curr_item and not mod_name.endswith(SEPARATOR_SUFFIX) and not has_issue:
                    curr_item.setBackground(
                        QColor(21, 128, 61, 110) if is_locked else QColor(24, 24, 28)
                    )
        finally:
            self._is_populating = False
        self._update_stats()
        self._save_settings()

    def _set_running_ui(self, running: bool):
        if running:
            self.btn_analyze.setText("Cancel")
            self.btn_analyze.setObjectName("btnDanger")
            self.btn_apply.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
        else:
            self.btn_analyze.setText("Analyze")
            self.btn_analyze.setObjectName("btnPrimary")
            self.progress_bar.setVisible(False)
        self.btn_analyze.style().unpolish(self.btn_analyze)
        self.btn_analyze.style().polish(self.btn_analyze)

    def _on_analyze_or_cancel_clicked(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.abort()
            try:
                self.worker.progress_update.disconnect()
                self.worker.sorted_ready.disconnect()
                self.worker.failed.disconnect()
            except Exception:
                pass
            self._set_running_ui(False)
            self.status_label.setText("Cancelled")
            return
        self._start_ai_sorting()

    def _start_ai_sorting(self):
        api_url = self.url_input.text().strip()
        api_key = self.key_input.text().strip()
        model = self.model_input.text().strip()

        if not api_url or not model:
            QMessageBox.warning(self, "Configuration", "Specify URL and Model.")
            return

        mods_to_send = self._to_panel(self.sortable_file_order)
        if not mods_to_send:
            QMessageBox.warning(self, "Empty List", "No items loaded. Select a valid folder first.")
            return

        is_local = any(h in api_url for h in ("localhost", "127.0.0.1", "[::1]", "0.0.0.0"))
        if not api_key and not is_local:
            yes_btn = QMessageBox.StandardButton.Yes if IS_QT6 else QMessageBox.Yes
            no_btn = QMessageBox.StandardButton.No if IS_QT6 else QMessageBox.No
            reply = QMessageBox.question(
                self, "API Key",
                "API key is empty. Continue?",
                yes_btn | no_btn
            )
            if reply != yes_btn:
                return

        self._save_settings()

        locked_mods_in_order = [m for m in mods_to_send if m in self.locked_mods_set]
        custom_rules = self.rules_input.toPlainText().strip()

        self._set_running_ui(True)

        self.worker = AISortWorker(
            api_url=api_url,
            api_key=api_key,
            model=model,
            mod_names=mods_to_send,
            locked_mods=locked_mods_in_order,
            custom_rules=custom_rules,
            timeout=self.request_timeout,
            compact_mode=self.compact_mode,
            keep_separators=self.keep_separators,
            meta_map=self.mod_meta_map,
            inspect_assets=self.inspect_assets,
            include_nexus_meta=self.include_nexus_meta,
            is_plugin_mode=(self.sort_mode == MODE_PLUGINS),
            plugin_meta_map=self.plugin_meta_map,
            loot_group_ranks=self.loot_group_ranks,
            loot_plugin_rules=self.loot_plugin_rules
        )
        self.worker.progress_update.connect(self._on_progress)
        self.worker.sorted_ready.connect(self._on_ai_success)
        self.worker.failed.connect(self._on_ai_error)

        _ACTIVE_WORKERS[:] = [w for w in _ACTIVE_WORKERS if w.isRunning()]
        _ACTIVE_WORKERS.append(self.worker)
        self.worker.start()

    def _open_advanced_settings(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"{APP_NAME} — Options")
        dlg.setMinimumWidth(360)
        dlg.setStyleSheet(MINIMAL_STYLESHEET)
        lay = QVBoxLayout(dlg)

        row = QHBoxLayout()
        row.addWidget(QLabel("Timeout (s):"))
        spin = QSpinBox()
        spin.setRange(MIN_REQUEST_TIMEOUT, MAX_REQUEST_TIMEOUT)
        spin.setSingleStep(10)
        spin.setValue(self.request_timeout)
        row.addWidget(spin)
        lay.addLayout(row)

        compact_cb = QCheckBox("Compact ID Mode")
        compact_cb.setChecked(self.compact_mode)
        lay.addWidget(compact_cb)

        keep_seps_cb = QCheckBox("Keep Existing Separators Only (Left Panel)")
        keep_seps_cb.setChecked(self.keep_separators)
        lay.addWidget(keep_seps_cb)

        assets_cb = QCheckBox("Inspect Mod Assets (SKSE, Meshes, Textures, Scripts...)")
        assets_cb.setChecked(self.inspect_assets)
        lay.addWidget(assets_cb)

        nexus_cb = QCheckBox("Include Nexus ID & Category (meta.ini)")
        nexus_cb.setChecked(self.include_nexus_meta)
        lay.addWidget(nexus_cb)

        btn_row = QHBoxLayout()
        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(
            lambda _=False: (
                spin.setValue(DEFAULT_REQUEST_TIMEOUT),
                compact_cb.setChecked(False),
                keep_seps_cb.setChecked(False),
                assets_cb.setChecked(True),
                nexus_cb.setChecked(True)
            )
        )
        btn_row.addWidget(btn_reset)
        btn_row.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.setObjectName("btnPrimary")
        btn_ok.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_ok)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_cancel)
        lay.addLayout(btn_row)

        accepted = dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()
        if accepted:
            self.request_timeout = int(spin.value())
            self.compact_mode = bool(compact_cb.isChecked())
            self.keep_separators = bool(keep_seps_cb.isChecked())
            self.inspect_assets = bool(assets_cb.isChecked())
            self.include_nexus_meta = bool(nexus_cb.isChecked())
            self._rebuild_stats_cache()
            prop_panel = self._to_panel(self.proposed_order) if self.proposed_order else []
            self._populate_table(self._to_panel(self.raw_mods_order), prop_panel)
            self._update_stats()
            self._save_settings()

    def _on_progress(self, msg: str):
        self.status_label.setText(msg)

    def _on_ai_success(self, sorted_panel: List[str]):
        self._set_running_ui(False)

        sorted_file = self._from_panel(sorted_panel)
        self.proposed_order = self.lead_foreign + sorted_file + self.trail_foreign

        current_panel = self._to_panel(self.raw_mods_order)
        proposed_panel = self._to_panel(self.proposed_order)
        self._populate_table(current_panel, proposed_panel)

        moved = len(self._last_moved_set)
        if self.sort_mode == MODE_PLUGINS:
            self.status_label.setText(f"Done: {moved} plugin(s) moved (MAST, ESM & LOOT constraints verified)")
        else:
            cur_set, prop_set = set(current_panel), set(proposed_panel)
            new_seps = sum(1 for n in proposed_panel if n.endswith(SEPARATOR_SUFFIX) and n not in cur_set)
            removed_seps = sum(1 for n in current_panel if n.endswith(SEPARATOR_SUFFIX) and n not in prop_set)
            self.status_label.setText(
                f"Done: {moved} moved, +{new_seps} / -{removed_seps} separators"
            )
        self.btn_apply.setEnabled(True)
        self.btn_move_up.setEnabled(True)
        self.btn_move_down.setEnabled(True)

    def _on_ai_error(self, err_msg: str):
        self._set_running_ui(False)
        self.status_label.setText("Error")
        QMessageBox.critical(self, "Error", f"{err_msg}")

    def _refresh_mo2(self) -> bool:
        if self._organizer is None:
            return False
        try:
            self._organizer.refresh(False)
            return True
        except Exception:
            return False

    @staticmethod
    def _write_file_atomic(target_path: str, lines: List[str]):
        tmp_path = target_path + ".align_tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp_path, target_path)

    def _apply_sorting(self):
        if not self.proposed_order:
            return
        if self.sort_mode == MODE_PLUGINS:
            self._apply_plugin_sorting()
        else:
            self._apply_mod_sorting()

    def _apply_plugin_sorting(self):
        if not self.profile_path or not os.path.isdir(self.profile_path):
            return

        yes_btn = QMessageBox.StandardButton.Yes if IS_QT6 else QMessageBox.Yes
        no_btn = QMessageBox.StandardButton.No if IS_QT6 else QMessageBox.No

        prompt_msg = "Apply proposed plugin load order to plugins.txt and loadorder.txt?"
        if self._organizer is None:
            prompt_msg += "\n(If MO2/Vortex is open, refresh after applying)"

        reply = QMessageBox.question(self, "Apply Load Order", prompt_msg, yes_btn | no_btn)
        if reply != yes_btn:
            return

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            if os.path.isfile(self.plugins_path):
                shutil.copyfile(self.plugins_path, self.plugins_backup_path)
                shutil.copyfile(self.plugins_path, os.path.join(self.profile_path, f"plugins.txt.bak_{timestamp}"))
            if os.path.isfile(self.loadorder_path):
                shutil.copyfile(self.loadorder_path, self.loadorder_backup_path)
                shutil.copyfile(self.loadorder_path, os.path.join(self.profile_path, f"loadorder.txt.bak_{timestamp}"))

            loadorder_lines = [f"# This file was automatically sorted by {APP_NAME}"]
            plugins_lines = [f"# This file was automatically sorted by {APP_NAME}"]

            for item in self.proposed_order:
                loadorder_lines.append(item)
                is_active = self.mod_prefixes.get(item, "*") == "*"
                plugins_lines.append(f"*{item}" if is_active else item)

            self._write_file_atomic(self.loadorder_path, loadorder_lines)
            self._write_file_atomic(self.plugins_path, plugins_lines)

            if self._organizer is not None:
                self._refresh_mo2()
                self.accept()
            else:
                self._load_current_plugins()
                self.status_label.setText("Applied to plugins.txt & loadorder.txt")
        except Exception as e:
            QMessageBox.critical(self, "Write Error", f"{e}")

    def _apply_mod_sorting(self):
        if not self.modlist_path:
            return

        yes_btn = QMessageBox.StandardButton.Yes if IS_QT6 else QMessageBox.Yes
        no_btn = QMessageBox.StandardButton.No if IS_QT6 else QMessageBox.No

        prompt_msg = "Apply proposed order to modlist.txt?"
        if self._organizer is None:
            prompt_msg += "\n(If MO2 is currently open, press F5 in MO2 after applying)"

        reply = QMessageBox.question(self, "Apply", prompt_msg, yes_btn | no_btn)
        if reply != yes_btn:
            return

        try:
            shutil.copyfile(self.modlist_path, self.backup_path)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ts_backup = os.path.join(self.profile_path, f"modlist.txt.bak_{timestamp}")
            shutil.copyfile(self.modlist_path, ts_backup)

            mods_dir = self.mods_path
            created: List[str] = []

            new_lines = [f"# This file was automatically sorted by {APP_NAME}"]
            for item in self.proposed_order:
                if item.endswith(SEPARATOR_SUFFIX):
                    if mods_dir and os.path.isdir(mods_dir):
                        sep_folder = os.path.join(mods_dir, item)
                        if not os.path.exists(sep_folder):
                            os.makedirs(sep_folder, exist_ok=True)
                            with open(os.path.join(sep_folder, "meta.ini"), "w", encoding="utf-8") as meta:
                                meta.write(
                                    "[General]\nmodid=0\nversion=\nnewestVersion=\n"
                                    "category=0\ninstallationFile=\n"
                                )
                            created.append(item)
                    new_lines.append(f"-{item}")
                else:
                    prefix = self.mod_prefixes.get(item, "+")
                    new_lines.append(f"{prefix}{item}")

            self._write_file_atomic(self.modlist_path, new_lines)

            with open(self.created_seps_path, "w", encoding="utf-8") as f:
                json.dump({"created": created, "timestamp": timestamp}, f, ensure_ascii=False)

            if self._organizer is not None:
                self._refresh_mo2()
                self.accept()
            else:
                self._load_current_modlist()
                self.status_label.setText("Applied to modlist.txt (Press F5 in MO2)")

        except Exception as e:
            QMessageBox.critical(self, "Write Error", f"{e}")

    def _cleanup_created_separators(self) -> int:
        legacy_seps = os.path.join(self.profile_path, "modlist.txt.ai_separators.json") if self.profile_path else ""
        target_seps = self.created_seps_path if (self.created_seps_path and os.path.exists(self.created_seps_path)) else legacy_seps
        if not target_seps or not os.path.exists(target_seps):
            return 0
        if not self.mods_path or not os.path.isdir(self.mods_path):
            return 0
        removed = 0
        try:
            with open(target_seps, "r", encoding="utf-8") as f:
                names = json.load(f).get("created", [])
            mods_dir = os.path.normpath(self.mods_path)
            in_modlist = set(self.raw_mods_order)
            for name in names:
                if (not isinstance(name, str) or not name.endswith(SEPARATOR_SUFFIX)
                        or os.path.basename(name) != name or name in in_modlist):
                    continue
                folder = os.path.normpath(os.path.join(mods_dir, name))
                if os.path.dirname(folder) != mods_dir or not os.path.isdir(folder):
                    continue
                if set(os.listdir(folder)) <= {"meta.ini"}:
                    shutil.rmtree(folder, ignore_errors=True)
                    removed += 1
            os.remove(target_seps)
        except Exception:
            pass
        return removed

    def _restore_backup(self):
        if not self.profile_path or not os.path.isdir(self.profile_path):
            return

        if self.sort_mode == MODE_PLUGINS:
            candidates = []
            if os.path.exists(self.plugins_backup_path):
                candidates.append(("Latest (.align_backup)", self.plugins_backup_path, self.loadorder_backup_path))
            legacy_p = os.path.join(self.profile_path, "plugins.txt.ai_backup")
            legacy_lo = os.path.join(self.profile_path, "loadorder.txt.ai_backup")
            if os.path.exists(legacy_p):
                candidates.append(("Legacy (.ai_backup)", legacy_p, legacy_lo))
            try:
                for fname in sorted(os.listdir(self.profile_path), reverse=True):
                    if fname.startswith("plugins.txt.bak_"):
                        ts = fname[len("plugins.txt.bak_"):]
                        p_bak = os.path.join(self.profile_path, fname)
                        lo_bak = os.path.join(self.profile_path, f"loadorder.txt.bak_{ts}")
                        candidates.append((fname, p_bak, lo_bak))
            except Exception:
                pass

            if not candidates:
                QMessageBox.warning(self, "Restore", "No plugins backup found.")
                return

            chosen_p, chosen_lo = candidates[0][1], candidates[0][2]
            if len(candidates) > 1:
                labels = [c[0] for c in candidates]
                item, ok = QInputDialog.getItem(self, "Restore Plugins Backup", "Select backup:", labels, 0, False)
                if not ok:
                    return
                for label, p_path, lo_path in candidates:
                    if label == item:
                        chosen_p, chosen_lo = p_path, lo_path
                        break

            try:
                if os.path.isfile(chosen_p):
                    tmp_p = self.plugins_path + ".align_tmp"
                    shutil.copyfile(chosen_p, tmp_p)
                    os.replace(tmp_p, self.plugins_path)
                if chosen_lo and os.path.isfile(chosen_lo):
                    tmp_lo = self.loadorder_path + ".align_tmp"
                    shutil.copyfile(chosen_lo, tmp_lo)
                    os.replace(tmp_lo, self.loadorder_path)

                self._load_current_plugins()
                self._refresh_mo2()
                self.status_label.setText("Plugins backup restored")
            except Exception as e:
                QMessageBox.critical(self, "Restore Error", str(e))
            return

        candidates = []
        if os.path.exists(self.backup_path):
            candidates.append(("Latest (.align_backup)", self.backup_path))
        legacy_m = os.path.join(self.profile_path, "modlist.txt.ai_backup")
        if os.path.exists(legacy_m):
            candidates.append(("Legacy (.ai_backup)", legacy_m))
        try:
            for fname in sorted(os.listdir(self.profile_path), reverse=True):
                if fname.startswith("modlist.txt.bak_"):
                    full = os.path.join(self.profile_path, fname)
                    candidates.append((fname, full))
        except Exception:
            pass

        if not candidates:
            QMessageBox.warning(self, "Restore", "No backup found.")
            return

        chosen_path = candidates[0][1]
        if len(candidates) > 1:
            labels = [c[0] for c in candidates]
            item, ok = QInputDialog.getItem(self, "Restore Backup", "Select backup:", labels, 0, False)
            if not ok:
                return
            for label, path in candidates:
                if label == item:
                    chosen_path = path
                    break

        try:
            tmp_path = self.modlist_path + ".align_tmp"
            shutil.copyfile(chosen_path, tmp_path)
            os.replace(tmp_path, self.modlist_path)

            self._load_current_modlist()
            self._cleanup_created_separators()
            self._refresh_mo2()
            self.status_label.setText("Backup restored")
        except Exception as e:
            QMessageBox.critical(self, "Restore Error", str(e))


SorterDialog = AlignDialog


if HAS_MOBASE:
    class AlignPlugin(mobase.IPluginTool):
        def __init__(self):
            super().__init__()
            self._organizer = None
            self._parent_widget = None

        def init(self, organizer: mobase.IOrganizer) -> bool:
            self._organizer = organizer
            return True

        def setParentWidget(self, widget) -> None:
            self._parent_widget = widget

        def name(self) -> str:
            return APP_NAME

        def author(self) -> str:
            return "HiTenzOFF"

        def description(self) -> str:
            return "Align — Hybrid AI & LOOT Mod and Load Order Organizer"

        def version(self) -> mobase.VersionInfo:
            return mobase.VersionInfo(1, 4, 0, mobase.ReleaseType.FINAL)

        def isActive(self) -> bool:
            return True

        def requirements(self) -> list:
            return []

        def settings(self) -> List[mobase.PluginSetting]:
            return []

        def displayName(self) -> str:
            return APP_NAME

        def tooltip(self) -> str:
            return ""

        def icon(self) -> QIcon:
            return find_app_icon()

        def display(self) -> None:
            try:
                dialog = AlignDialog(self._organizer, self._parent_widget)
            except TypeError:
                dialog = AlignDialog(self._organizer)
            if hasattr(dialog, "exec"):
                dialog.exec()
            else:
                dialog.exec_()

    AILeftPanelSorter = AlignPlugin

    def createPlugin():
        return AlignPlugin()

    def createPlugins() -> list:
        return [AlignPlugin()]


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app_icon = find_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    win = AlignDialog(organizer=None)
    win.show()
    sys.exit(app.exec() if hasattr(app, "exec") else app.exec_())


if __name__ == "__main__":
    main()
