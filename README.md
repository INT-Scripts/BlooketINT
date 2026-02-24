# BlooketINT Spammer

A high-performance Blooket bot written in Python using Playwright that manages multiple browser windows to join games and spam keys.

## 🚀 Features

- **Multi-Window Support**: Open as many windows/tabs as you want simultaneously.
- **Unique Ghost Names**: Bypasses duplicate name detection by interleaving 4 different types of zero-width (invisible) characters into your base nickname.
- **Visual Length Bypassing**: Uses base-4 encoding for invisible characters to ensure names stay under Blooket's 15-character limit even with hundreds of bots.
- **Turbo Spam**: Injects a high-speed Javascript loop that spams keys `1`, `2`, `3`, and `4` at a 0ms interval.

## 📦 Installation

This project uses `uv` for lightning-fast dependency management.

1. **Install uv** (if you haven't):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Setup Dependencies**:
   ```bash
   uv add playwright
   uv run playwright install
   ```

## 🎮 Usage

Run the script from your terminal providing the Game ID, your chosen base name, and the number of windows you want to open.

```bash
uv run main.py <GAME_CODE> "<NAME>" --count <NUMBER>
```

### Examples

**Standard 4-window setup:**
```bash
uv run main.py 123456 "PlayerOne"
```

**8-window setup for maximum impact:**
```bash
uv run main.py 123456 "GhostBot" -c 8
```

## 🛠️ How it Works

1. **Automation**: Uses Playwright to launch a Chromium instance and navigate to `play.blooket.com`.
2. **Naming Logic**: 
   - Window 1 gets the raw name.
   - Window 2+ uses a combination of `\u200B`, `\u200C`, `\u200D`, and `\uFEFF` to create a "unique" string on the server side that looks identical to the human eye.
3. **The Script**: Once joined, it injects an `Interval` that dispatches `KeyboardEvent` signals for keys 1-4, allowing the bot to automatically select answers or perform actions mapped to those keys.

## 🛑 Stopping

- To stop the spam script in a specific browser console, run: `stopEmulation()`
- To kill all bots, simply press `Ctrl+C` in your terminal.

---
*Disclaimer: This is for educational/testing purposes only.*
