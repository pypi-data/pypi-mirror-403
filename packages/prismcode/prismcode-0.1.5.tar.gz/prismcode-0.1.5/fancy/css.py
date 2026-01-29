"""CSS generation for Prism TUI - minimalist transparent design."""

def generate_css(theme: dict) -> str:
    """Generate minimalist CSS. No backgrounds = terminal transparency with ansi_color=True."""

    # Get theme colors with defaults
    accent = theme.get("accent_color", "cyan")
    dim = theme.get("dim_color", "dim")
    tool = theme.get("tool_color", "cyan")
    text = theme.get("text_color", "white")

    return f"""
Screen {{
    layers: base menu;
}}

#main {{
    width: 100%;
    height: 100%;
    layer: base;
}}

#chat-scroll {{
    width: 100%;
    height: 1fr;
    scrollbar-size: 1 1;
    padding: 0;
    margin: 0;
}}

#chat-content {{
    padding: 0;
    margin: 0;
}}

/* Legacy input styles - kept for backward compatibility */
#input-row {{
    width: 100%;
    height: auto;
    min-height: 1;
    padding: 0;
}}

#prompt {{
    width: 2;
    height: 1;
    content-align: right middle;
}}

#input {{
    width: 1fr;
    height: auto;
    min-height: 1;
    max-height: 10;
    border: none;
    scrollbar-size: 0 1;
    padding: 0;
}}

#input:focus {{
    border: none;
}}

/* Legacy autocomplete - replaced by CommandMenu */
#autocomplete {{
    width: 100%;
    max-height: 8;
    padding: 0 1;
    display: none;
}}

#autocomplete.show {{
    display: block;
}}

#status {{
    width: 100%;
    height: 1;
    padding: 0;
}}

/* Focus bar styles */
FocusBar {{
    width: 100%;
    height: auto;
    min-height: 1;
    padding: 0;
}}

FocusBar.hidden {{
    display: none;
}}

FocusBar #focus-content {{
    width: 100%;
    height: auto;
    padding: 0;
}}

/* New CommandInputBar styles */
CommandInputBar {{
    dock: bottom;
    height: auto;
    width: 100%;
    layers: base menu;
}}

CommandInputBar #input-container {{
    width: 100%;
    height: auto;
    min-height: 1;
    layer: base;
}}

CommandInputBar #prompt {{
    width: 2;
    height: 1;
    content-align: right middle;
}}

CommandInputBar #cmd-input {{
    width: 1fr;
    height: 1;
    min-height: 1;
    border: none;
    padding: 0;
}}

CommandInputBar #cmd-input:focus {{
    border: none;
}}

/* CommandMenu styles */
CommandMenu {{
    height: auto;
    max-height: 12;
    width: 100%;
    display: none;
    layer: menu;
    padding: 0;
    margin: 0;
}}

CommandMenu.visible {{
    display: block;
}}

CommandMenu OptionList {{
    height: auto;
    max-height: 10;
    border: none;
    padding: 0 1;
    scrollbar-size: 1 1;
}}

CommandMenu OptionList:focus {{
    border: none;
}}

CommandMenu OptionList > .option-list--option-highlighted {{
    background: {accent};
}}

CommandMenu OptionList > .option-list--option-hover {{
    background: {dim};
}}

CommandMenu .settings-panel {{
    display: none;
    height: auto;
    max-height: 10;
    padding: 0 1;
}}

CommandMenu .settings-panel.visible {{
    display: block;
}}
"""
