import argparse
import asyncio
from playwright.async_api import async_playwright

def get_unique_name(base_name, index, max_length=15):
    if index == 0:
        return base_name[:max_length]
    
    # 4 types of zero-width characters to avoid detection
    chars = ['\u200B', '\u200C', '\u200D', '\uFEFF']
    
    zw_str = ""
    v = index - 1
    # Convert index to a base-4 string of zero-width characters
    # We do index - 1 so index 1 maps to 0 ('\u200B')
    if v == 0:
        zw_str = chars[0]
    else:
        while v > 0:
            zw_str += chars[v % 4]
            v //= 4
            
    # Blooket max name is 15. Make sure we don't exceed it.
    visual_len = max(1, max_length - len(zw_str))
    truncated_base = base_name[:visual_len]
    
    # Interleave the zero-width chars between the first few chars of the name
    res = ""
    if truncated_base:
        res += truncated_base[0]
    
    for i in range(len(zw_str)):
        res += zw_str[i]
        if i + 1 < len(truncated_base):
            res += truncated_base[i+1]
            
    if len(zw_str) + 1 < len(truncated_base):
        res += "".join(truncated_base[len(zw_str)+1:])
        
    # Append the rest of zw_str if it's longer than the base name
    if len(zw_str) >= len(truncated_base):
        res += zw_str[len(truncated_base)-1:]
        
    return res

async def automate_window(browser, code, base_name, index):
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto('https://play.blooket.com/play')
    
    # Wait for the game code input - using exact Blooket class and 'tel' type
    game_id_input = page.locator('input.Form_idInput__MPydi, input[type="tel"]:visible, input[placeholder*="ID"]').first
    await game_id_input.wait_for(state="visible", timeout=10000)
    await game_id_input.fill(code)
    await page.keyboard.press("Enter")
    
    # Wait for the nickname input. 
    # Blooket nickname input usually has a class like Form_nameInput or similar
    nickname_input = page.locator('input[placeholder*="Name"]:visible, input[class*="nameInput"]:visible, input[type="text"]:visible').first
    await nickname_input.wait_for(state="visible", timeout=10000)
    
    unique_name = get_unique_name(base_name, index)
    await nickname_input.fill(unique_name)
    await page.keyboard.press("Enter")
    
    # Wait for joining room
    await page.wait_for_timeout(3000)
    
    spam_script = """
    (function() {
        const targetElement = window;
        const keys = ['1', '2', '3', '4'];
        let keyIndex = 0;

        const pressKey = () => {
            const keyToSimulate = keys[keyIndex];
            keyIndex = (keyIndex + 1) % keys.length;
            const event = new KeyboardEvent('keydown', {
                key: keyToSimulate,
                code: `Digit${keyToSimulate}`,
                bubbles: true,
                cancelable: true
            });
            
            targetElement.dispatchEvent(event);
        };

        const intervalId = setInterval(pressKey, 0);

        console.log(`Emulating keys 1 to 4 at maximum speed. Run 'stopEmulation()' to quit.`);

        window.stopEmulation = () => {
            clearInterval(intervalId);
            console.log("Emulation stopped.");
        };
    })();
    """
    await page.evaluate(spam_script)
    print(f"Window {str(index).zfill(2)} setup complete with name: {repr(unique_name)}")


async def run_bot(code, name, count):
    print(f"Starting {count} windows for game {code} with base name '{name}'...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        tasks = []
        for i in range(count):
            tasks.append(automate_window(browser, code, name, i))
            
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
    args = parser.parse_args()
    
    try:
        asyncio.run(run_bot(args.code, args.name, args.count))
    except KeyboardInterrupt:
        print("\nExiting bot...")

if __name__ == "__main__":
    main()
