"""
Theme system for OpenCode TUI.

Supports 15+ built-in themes plus custom themes from ~/.config/opencode/themes/
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from opencode.config.paths import get_themes_dir


@dataclass
class SyntaxColors:
    """Syntax highlighting colors."""

    keyword: str = "#ff79c6"
    string: str = "#f1fa8c"
    number: str = "#bd93f9"
    comment: str = "#6272a4"
    function: str = "#50fa7b"
    variable: str = "#f8f8f2"
    type: str = "#8be9fd"
    operator: str = "#ff79c6"
    punctuation: str = "#f8f8f2"


@dataclass
class DiffColors:
    """Diff visualization colors."""

    added: str = "#50fa7b"
    added_bg: str = "#1a3d1a"
    removed: str = "#ff5555"
    removed_bg: str = "#3d1a1a"
    modified: str = "#f1fa8c"
    modified_bg: str = "#3d3d1a"


@dataclass
class Theme:
    """Complete theme definition."""

    name: str = "opencode"
    display_name: str = "OpenCode"
    mode: Literal["dark", "light"] = "dark"

    # Primary colors
    primary: str = "#bd93f9"
    secondary: str = "#6272a4"
    accent: str = "#ff79c6"

    # Status colors
    error: str = "#ff5555"
    warning: str = "#ffb86c"
    success: str = "#50fa7b"
    info: str = "#8be9fd"

    # Background layers
    background: str = "#282a36"
    background_panel: str = "#1e1f29"
    background_element: str = "#44475a"

    # Text colors
    text: str = "#f8f8f2"
    text_muted: str = "#6272a4"
    text_accent: str = "#bd93f9"

    # Border colors
    border: str = "#44475a"
    border_focus: str = "#bd93f9"

    # Selection
    selection: str = "#44475a"
    selection_text: str = "#f8f8f2"

    # Syntax highlighting
    syntax: SyntaxColors = field(default_factory=SyntaxColors)

    # Diff colors
    diff: DiffColors = field(default_factory=DiffColors)

    def to_dict(self) -> dict:
        """Convert theme to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "mode": self.mode,
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "error": self.error,
            "warning": self.warning,
            "success": self.success,
            "info": self.info,
            "background": self.background,
            "background_panel": self.background_panel,
            "background_element": self.background_element,
            "text": self.text,
            "text_muted": self.text_muted,
            "text_accent": self.text_accent,
            "border": self.border,
            "border_focus": self.border_focus,
            "selection": self.selection,
            "selection_text": self.selection_text,
            "syntax": {
                "keyword": self.syntax.keyword,
                "string": self.syntax.string,
                "number": self.syntax.number,
                "comment": self.syntax.comment,
                "function": self.syntax.function,
                "variable": self.syntax.variable,
                "type": self.syntax.type,
                "operator": self.syntax.operator,
                "punctuation": self.syntax.punctuation,
            },
            "diff": {
                "added": self.diff.added,
                "added_bg": self.diff.added_bg,
                "removed": self.diff.removed,
                "removed_bg": self.diff.removed_bg,
                "modified": self.diff.modified,
                "modified_bg": self.diff.modified_bg,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> Theme:
        """Create theme from dictionary."""
        syntax_data = data.get("syntax", {})
        diff_data = data.get("diff", {})

        return cls(
            name=data.get("name", "custom"),
            display_name=data.get("display_name", "Custom"),
            mode=data.get("mode", "dark"),
            primary=data.get("primary", "#bd93f9"),
            secondary=data.get("secondary", "#6272a4"),
            accent=data.get("accent", "#ff79c6"),
            error=data.get("error", "#ff5555"),
            warning=data.get("warning", "#ffb86c"),
            success=data.get("success", "#50fa7b"),
            info=data.get("info", "#8be9fd"),
            background=data.get("background", "#282a36"),
            background_panel=data.get("background_panel", "#1e1f29"),
            background_element=data.get("background_element", "#44475a"),
            text=data.get("text", "#f8f8f2"),
            text_muted=data.get("text_muted", "#6272a4"),
            text_accent=data.get("text_accent", "#bd93f9"),
            border=data.get("border", "#44475a"),
            border_focus=data.get("border_focus", "#bd93f9"),
            selection=data.get("selection", "#44475a"),
            selection_text=data.get("selection_text", "#f8f8f2"),
            syntax=SyntaxColors(
                keyword=syntax_data.get("keyword", "#ff79c6"),
                string=syntax_data.get("string", "#f1fa8c"),
                number=syntax_data.get("number", "#bd93f9"),
                comment=syntax_data.get("comment", "#6272a4"),
                function=syntax_data.get("function", "#50fa7b"),
                variable=syntax_data.get("variable", "#f8f8f2"),
                type=syntax_data.get("type", "#8be9fd"),
                operator=syntax_data.get("operator", "#ff79c6"),
                punctuation=syntax_data.get("punctuation", "#f8f8f2"),
            ),
            diff=DiffColors(
                added=diff_data.get("added", "#50fa7b"),
                added_bg=diff_data.get("added_bg", "#1a3d1a"),
                removed=diff_data.get("removed", "#ff5555"),
                removed_bg=diff_data.get("removed_bg", "#3d1a1a"),
                modified=diff_data.get("modified", "#f1fa8c"),
                modified_bg=diff_data.get("modified_bg", "#3d3d1a"),
            ),
        )


# Built-in themes
BUILTIN_THEMES: dict[str, Theme] = {
    "opencode": Theme(),
    "dracula": Theme(
        name="dracula",
        display_name="Dracula",
        mode="dark",
        primary="#bd93f9",
        secondary="#6272a4",
        accent="#ff79c6",
        error="#ff5555",
        warning="#ffb86c",
        success="#50fa7b",
        info="#8be9fd",
        background="#282a36",
        background_panel="#1e1f29",
        background_element="#44475a",
        text="#f8f8f2",
        text_muted="#6272a4",
        text_accent="#bd93f9",
    ),
    "tokyonight": Theme(
        name="tokyonight",
        display_name="Tokyo Night",
        mode="dark",
        primary="#7aa2f7",
        secondary="#565f89",
        accent="#bb9af7",
        error="#f7768e",
        warning="#e0af68",
        success="#9ece6a",
        info="#7dcfff",
        background="#1a1b26",
        background_panel="#16161e",
        background_element="#24283b",
        text="#c0caf5",
        text_muted="#565f89",
        text_accent="#7aa2f7",
    ),
    "catppuccin": Theme(
        name="catppuccin",
        display_name="Catppuccin Mocha",
        mode="dark",
        primary="#cba6f7",
        secondary="#6c7086",
        accent="#f5c2e7",
        error="#f38ba8",
        warning="#fab387",
        success="#a6e3a1",
        info="#89dceb",
        background="#1e1e2e",
        background_panel="#181825",
        background_element="#313244",
        text="#cdd6f4",
        text_muted="#6c7086",
        text_accent="#cba6f7",
    ),
    "nord": Theme(
        name="nord",
        display_name="Nord",
        mode="dark",
        primary="#88c0d0",
        secondary="#4c566a",
        accent="#81a1c1",
        error="#bf616a",
        warning="#ebcb8b",
        success="#a3be8c",
        info="#88c0d0",
        background="#2e3440",
        background_panel="#242933",
        background_element="#3b4252",
        text="#eceff4",
        text_muted="#4c566a",
        text_accent="#88c0d0",
    ),
    "monokai": Theme(
        name="monokai",
        display_name="Monokai Pro",
        mode="dark",
        primary="#a9dc76",
        secondary="#727072",
        accent="#ff6188",
        error="#ff6188",
        warning="#ffd866",
        success="#a9dc76",
        info="#78dce8",
        background="#2d2a2e",
        background_panel="#221f22",
        background_element="#403e41",
        text="#fcfcfa",
        text_muted="#727072",
        text_accent="#a9dc76",
    ),
    "gruvbox": Theme(
        name="gruvbox",
        display_name="Gruvbox Dark",
        mode="dark",
        primary="#fabd2f",
        secondary="#665c54",
        accent="#fe8019",
        error="#fb4934",
        warning="#fabd2f",
        success="#b8bb26",
        info="#83a598",
        background="#282828",
        background_panel="#1d2021",
        background_element="#3c3836",
        text="#ebdbb2",
        text_muted="#665c54",
        text_accent="#fabd2f",
    ),
    "solarized": Theme(
        name="solarized",
        display_name="Solarized Dark",
        mode="dark",
        primary="#268bd2",
        secondary="#586e75",
        accent="#2aa198",
        error="#dc322f",
        warning="#b58900",
        success="#859900",
        info="#2aa198",
        background="#002b36",
        background_panel="#001e26",
        background_element="#073642",
        text="#839496",
        text_muted="#586e75",
        text_accent="#268bd2",
    ),
    "onedark": Theme(
        name="onedark",
        display_name="One Dark Pro",
        mode="dark",
        primary="#61afef",
        secondary="#5c6370",
        accent="#c678dd",
        error="#e06c75",
        warning="#e5c07b",
        success="#98c379",
        info="#56b6c2",
        background="#282c34",
        background_panel="#21252b",
        background_element="#2c313a",
        text="#abb2bf",
        text_muted="#5c6370",
        text_accent="#61afef",
    ),
    "ayu": Theme(
        name="ayu",
        display_name="Ayu Dark",
        mode="dark",
        primary="#ffcc66",
        secondary="#5c6773",
        accent="#f29e74",
        error="#f07178",
        warning="#ffcc66",
        success="#bae67e",
        info="#5ccfe6",
        background="#0a0e14",
        background_panel="#050709",
        background_element="#1d2530",
        text="#b3b1ad",
        text_muted="#5c6773",
        text_accent="#ffcc66",
    ),
    "vesper": Theme(
        name="vesper",
        display_name="Vesper",
        mode="dark",
        primary="#ffc799",
        secondary="#575279",
        accent="#d7827e",
        error="#eb6f92",
        warning="#f6c177",
        success="#9ccfd8",
        info="#c4a7e7",
        background="#101010",
        background_panel="#080808",
        background_element="#1a1a1a",
        text="#ffffff",
        text_muted="#575279",
        text_accent="#ffc799",
    ),
    "nightowl": Theme(
        name="nightowl",
        display_name="Night Owl",
        mode="dark",
        primary="#82aaff",
        secondary="#637777",
        accent="#c792ea",
        error="#ef5350",
        warning="#ffcb6b",
        success="#c3e88d",
        info="#89ddff",
        background="#011627",
        background_panel="#001122",
        background_element="#0b2942",
        text="#d6deeb",
        text_muted="#637777",
        text_accent="#82aaff",
    ),
    # Light themes
    "solarized_light": Theme(
        name="solarized_light",
        display_name="Solarized Light",
        mode="light",
        primary="#268bd2",
        secondary="#93a1a1",
        accent="#2aa198",
        error="#dc322f",
        warning="#b58900",
        success="#859900",
        info="#2aa198",
        background="#fdf6e3",
        background_panel="#eee8d5",
        background_element="#eee8d5",
        text="#657b83",
        text_muted="#93a1a1",
        text_accent="#268bd2",
    ),
    "github_light": Theme(
        name="github_light",
        display_name="GitHub Light",
        mode="light",
        primary="#0969da",
        secondary="#57606a",
        accent="#8250df",
        error="#cf222e",
        warning="#bf8700",
        success="#1a7f37",
        info="#0969da",
        background="#ffffff",
        background_panel="#f6f8fa",
        background_element="#f3f4f6",
        text="#24292f",
        text_muted="#57606a",
        text_accent="#0969da",
    ),
}


class ThemeManager:
    """Manages theme loading and switching."""

    def __init__(self) -> None:
        self._current: Theme = BUILTIN_THEMES["opencode"]
        self._custom_themes: dict[str, Theme] = {}
        self._load_custom_themes()

    def _load_custom_themes(self) -> None:
        """Load custom themes from user directory."""
        themes_dir = get_themes_dir()
        for theme_file in themes_dir.glob("*.json"):
            try:
                data = json.loads(theme_file.read_text())
                theme = Theme.from_dict(data)
                self._custom_themes[theme.name] = theme
            except (json.JSONDecodeError, OSError):
                continue

    @property
    def current(self) -> Theme:
        """Get current theme."""
        return self._current

    def set_theme(self, name: str) -> bool:
        """Set the current theme by name."""
        if name in BUILTIN_THEMES:
            self._current = BUILTIN_THEMES[name]
            return True
        if name in self._custom_themes:
            self._current = self._custom_themes[name]
            return True
        return False

    def list_themes(self) -> list[Theme]:
        """List all available themes."""
        all_themes = list(BUILTIN_THEMES.values()) + list(self._custom_themes.values())
        return sorted(all_themes, key=lambda t: t.display_name)

    def get_theme(self, name: str) -> Theme | None:
        """Get a theme by name."""
        if name in BUILTIN_THEMES:
            return BUILTIN_THEMES[name]
        return self._custom_themes.get(name)

    def save_custom_theme(self, theme: Theme) -> None:
        """Save a custom theme to user directory."""
        themes_dir = get_themes_dir()
        theme_file = themes_dir / f"{theme.name}.json"
        theme_file.write_text(json.dumps(theme.to_dict(), indent=2))
        self._custom_themes[theme.name] = theme


# Global theme manager
_theme_manager: ThemeManager | None = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def get_current_theme() -> Theme:
    """Get the current theme."""
    return get_theme_manager().current
