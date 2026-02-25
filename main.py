import argparse
import asyncio
from playwright.async_api import async_playwright

def get_unique_name(base_name, index, max_length=15):
    if index == 0:
        return base_name[:max_length]
    
    # Expanded list of "invisible" or non-printing characters
    # Includes standard ZW characters + Hangul fillers + Braille blank
    chars = [
        '\u200B', '\u200C', '\u200D', '\uFEFF', 
        '\u200E', '\u200F', '\u2060', '\u2800', 
        '\u3164', '\u115F', '\u1160', '\u17B4',
        '\u17B5', '\u180E', '\u202F'
    ]
    
    zw_str = ""
    v = index
    base = len(chars)
    
    # Create a unique sequence of characters for this index
    while v > 0:
        zw_str += chars[v % base]
        v //= base
    
    # If the sequence is empty (shouldn't happen for index > 0), use the first char
    if not zw_str:
        zw_str = chars[0]
        
    # Interleave and truncate
    # Blooket limit is 15.
    res = ""
    name_part = base_name[:max(1, max_length - len(zw_str))]
    
    # Place invisible chars at the start/middle to avoid simple trailing space stripping
    if len(name_part) > 1:
        res = name_part[0] + zw_str + name_part[1:]
    else:
        res = name_part + zw_str
        
    return res[:max_length]

async def automate_window(browser, code, base_name, index, headless=True):
    # Use a real-looking user agent and viewport
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={'width': 1280, 'height': 720}
    )
    
    # Simple stealth: hide the navigator.webdriver flag
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    page = await context.new_page()
    
    try:
        print(f"Window {str(index).zfill(2)}: Navigating to Blooket...")
        # Use commit instead of networkidle for faster/more robust loads
        await page.goto('https://play.blooket.com/play', wait_until="load", timeout=60000)
        
        # 1. Game ID Input
        game_id_input = page.locator('input[placeholder="Game ID"], input.Form_idInput__MPydi').first
        await game_id_input.wait_for(state="visible", timeout=20000)
        await game_id_input.fill(code)
        
        # Click the submit button or press Enter
        await page.keyboard.press("Enter")
        
        # 2. Nickname Input
        # Wait for the nickname input to appear
        nickname_input = page.locator('input[placeholder="Nickname"], input[type="text"]:visible').first
        try:
            await nickname_input.wait_for(state="visible", timeout=15000)
        except:
            # If not visible, maybe Enter didn't work, try clicking the button
            submit_button = page.locator('button[aria-label="Submit"], button.FormSubmitButton_submitButton__MK2LJ').first
            if await submit_button.is_visible():
                await submit_button.click()
            await nickname_input.wait_for(state="visible", timeout=10000)
            
        unique_name = get_unique_name(base_name, index)
        await nickname_input.fill(unique_name)
        await page.keyboard.press("Enter")
        
        # Wait for potential error messages or successful join
        # Successful join usually shows a 'Waiting for Host' message or similar
        # Failure usually shows 'That name is already taken' or similar
        
        # We'll wait a bit and check if we are in
        await page.wait_for_timeout(2000)
        
        # Check for error message
        error_msg = page.locator('div[class*="error"], div[class*="Error"]').first
        if await error_msg.is_visible() and await error_msg.text_content():
            text = await error_msg.text_content()
            print(f"Window {str(index).zfill(2)} error: {text}")
            if "name" in text.lower():
                # Try one more time with a slightly different name if it's a name error
                await nickname_input.fill(unique_name + str(index))
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)

        # Assign a specific key based on index (1, 2, 3, or 4)
        target_key = str((index % 4) + 1)
        
        # Inject spam script that only presses ONE key
        spam_script = f"""
        (function() {{
            const keyToSimulate = "{target_key}";
            const pressKey = () => {{
                window.dispatchEvent(new KeyboardEvent('keydown', {{
                    key: keyToSimulate,
                    code: `Digit${{keyToSimulate}}`,
                    bubbles: true
                }}));
            }};
            
            // 1. Fallback ultra-rapide (1ms au lieu de 50ms)
            const intervalId = setInterval(pressKey, 1);
            
            // 2. MutationObserver pour réagir instantanément à l'apparition des questions (0ms de latence structurelle)
            const observer = new MutationObserver(() => {{
                pressKey();
            }});
            
            // On observe tous les changements sur la page (ajout de boutons, changement d'écrans)
            if (document.body) {{
                observer.observe(document.body, {{
                    childList: true,
                    subtree: true,
                    attributes: true
                }});
            }} else {{
                // Cas d'edge-case (body pas encore chargé) on attend le DOM
                document.addEventListener('DOMContentLoaded', () => {{
                    observer.observe(document.body, {{
                        childList: true,
                        subtree: true,
                        attributes: true
                    }});
                }});
            }}
            
            window.stopEmulation = () => {{
                clearInterval(intervalId);
                observer.disconnect();
            }};
        }})();
        """
        await page.evaluate(spam_script)
        print(f"Window {str(index).zfill(2)} setup complete: {repr(unique_name)} (spaming '{target_key}')")
        
    except Exception as e:
        print(f"Window {index} failed: {e}")
        if headless:
            path = f"error_window_{index}.png"
            await page.screenshot(path=path)
            print(f"Saved error screenshot to {path}")
        raise e


async def run_bot(code, name, count, headless=True):
    print(f"Starting {count} windows for game {code} with base name '{name}' (headless={headless})...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        tasks = []
        for i in range(count):
            tasks.append(automate_window(browser, code, name, i, headless=headless))
            if i < count - 1:
                await asyncio.sleep(0.5) # Small stagger
            
        await asyncio.gather(*tasks)
        print("All windows setup completed. The script is now spamming keys.")
        print("Keeping browser open. Press Ctrl+C in terminal to exit.")
        while True:
            await asyncio.sleep(3600)

def main():
    parser = argparse.ArgumentParser(description="Blooket Bot - Multi-window spammer")
    parser.add_argument("code", help="The Blooket Game ID / Code")
    parser.add_argument("name", help="The base nickname to use")
    parser.add_argument("--count", "-c", type=int, default=4, help="Number of windows to open (default: 4)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()
    
    try:
        asyncio.run(run_bot(args.code, args.name, args.count, args.headless))
    except KeyboardInterrupt:
        print("\nExiting bot...")

if __name__ == "__main__":
    main()
