# BlooketINT Spammer

A high-performance Blooket bot written in Python using Playwright that manages multiple browser windows to join games and spam keys. 
Features a **Rich CLI Dashboard** to monitor the swarm in real-time.

## 🚀 Features

- **Multi-Window Swarm Dashboard**: Live terminal UI built with `rich` that tracks your bots' statuses, spammed keys, and current score/points in real-time.
- **Unique Ghost Names**: Bypasses duplicate name detection by interleaving 4 different types of zero-width (invisible) characters into your base nickname.
- **Zero-Latency Reaction (MutationObserver)**: Injects a high-speed Javascript loop that uses a `MutationObserver` combined with a 1ms fallback interval to react instantly (0ms latency structure) as soon as Blooket questions appear on screen.
- **Smart Keys Division**: The bots are automatically assigned different keys (`1`, `2`, `3`, `4`) to ensure one of them always hits the correct answer first.
- **Headless Mode by Default**: Runs entirely in the background without launching visible browser windows (unless specified).

## 📦 Installation

This project uses `uv` for lightning-fast dependency management.

1. **Install uv** (if you haven't):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Setup Dependencies**:
   ```bash
   uv sync
   uv run playwright install
   ```

## 🎮 Usage

Run the script from your terminal providing the Game ID, your chosen base name, and the number of windows you want to open.

```bash
uv run main.py <GAME_CODE> "<NAME>" [-c NUMBER] [--show]
```

### Arguments

*   `code` : **(Required)** The Blooket Game ID / Code you wish to join.
*   `name` : **(Required)** The base nickname to use. The script will automatically scramble it with invisible characters for the bots.
*   `-c`, `--count` : *(Optional)* Number of bot windows to open. Defaults to **4** (perfect for covering all 4 answers).
*   `--show` : *(Optional)* By default, the bots run invisibly in the background (`headless = True`). Use this flag to actually open and render the Chromium windows.

### Examples

**Standard 4-bot setup (runs hidden, perfect for covering keys 1 to 4):**
```bash
uv run main.py 123456 "PlayerOne"
```

**8-window setup for maximum impact (with visible browsers):**
```bash
uv run main.py 123456 "GhostBot" -c 8 --show
```

## 🛠️ How it Works

1. **Automation**: Uses Playwright to launch Chromium instances (`headless` by default) and navigate to `play.blooket.com`.
2. **Naming Logic**: 
   - Window 1 gets the raw name.
   - Window 2+ uses a combination of `\u200B`, `\u200C`, `\u200D`, and `\uFEFF` to create a "unique" string on the server side that looks identical to the human eye.
3. **Zero-Latency Play**: Once joined, the bot injects a `MutationObserver` script. It watches the DOM (HTML) for any changes (like an answer button appearing) and dispatches the assigned `KeyboardEvent` signal (`1`, `2`, `3`, or `4`) instantly.
4. **Live Board**: A concurrent asynchronous loop constantly polls the DOM for the `score`/`balance` of each bot and feeds it back to the Python terminal dashboard.

## 🛑 Stopping

- To kill all bots and exit cleanly, simply press `Ctrl+C` in your terminal. The `rich` Alternate Screen Buffer will close and return your clean terminal state.

---
*Disclaimer: This is for educational/testing purposes only.*
