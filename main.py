import argparse
import asyncio
from playwright.async_api import async_playwright
from dataclasses import dataclass
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich import box

console = Console()

@dataclass
class BotState:
    index: int
    name: str = "Initializing..."
    status: str = "Starting..."
    spam_key: str = "-"
    score: str = "0"

# Global state for all active bots
bots: list[BotState] = []

def get_unique_name(base_name, index, max_length=15):
    if index == 0:
        return base_name[:max_length]
    
    # Expanded list of "invisible" or non-printing characters
    chars = [
        '\u200B', '\u200C', '\u200D', '\uFEFF', 
        '\u200E', '\u200F', '\u2060', '\u2800', 
        '\u3164', '\u115F', '\u1160', '\u17B4',
        '\u17B5', '\u180E', '\u202F'
    ]
    
    zw_str = ""
    v = index
    base = len(chars)
    
    while v > 0:
        zw_str += chars[v % base]
        v //= base
    
    if not zw_str:
        zw_str = chars[0]
        
    res = ""
    name_part = base_name[:max(1, max_length - len(zw_str))]
    
    if len(name_part) > 1:
        res = name_part[0] + zw_str + name_part[1:]
    else:
        res = name_part + zw_str
        
    return res[:max_length]

def log_bot(index, msg):
    pass

async def update_bot_state_loop(page, index):
    """
    Background task that continuously tries to scrape the score, questions and answers
    without relying heavily on specific class names, using common patterns instead.
    """
    scrape_script = """
    () => {
        let score = "?";
        
        try {
            // Attempt to find score/coins/gold
            const scoreCandidates = document.querySelectorAll('div[class*="score"], div[class*="stat"], div[class*="balance"], div[class*="cash"], p[class*="money"]');
            for (let el of scoreCandidates) {
                if (el.innerText && /[0-9]/.test(el.innerText) && el.innerText.length < 15) {
                    score = el.innerText.trim();
                    break;
                }
            }
        } catch (e) {
            // Ignore extraction errors quietly on the frontend
        }
        
        return {score: score};
    }
    """
    
    while True:
        try:
            data = await page.evaluate(scrape_script)
            
            if data['score'] != "?":
                new_score = data['score'].replace('\n', ' ')
                
                if bots[index].score != new_score and bots[index].score != "0":
                    log_bot(index, f"Score changed to {new_score}")
                elif bots[index].score == "0" and new_score != "0":
                    log_bot(index, f"First points! Score: {new_score}")
                    
                bots[index].score = new_score
                
        except Exception:
            # Page might be navigating, closed, or evaluate failed context. 
            pass
            
        await asyncio.sleep(1) # Refresh state roughly every second

async def automate_window(browser, code, base_name, index, headless=True):
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={'width': 1280, 'height': 720}
    )
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page = await context.new_page()
    
    unique_name = get_unique_name(base_name, index)
    target_key = str((index % 4) + 1)
    
    bots[index].name = repr(unique_name)[1:-1] # Remove formatting quotes
    bots[index].spam_key = target_key
    bots[index].status = "Navigating..."
    
    try:
        log_bot(index, "Going to blooket.com/play")
        await page.goto('https://play.blooket.com/play', wait_until="load", timeout=60000)
        
        bots[index].status = "Joining Game..."
        log_bot(index, "Entering Game ID")
        game_id_input = page.locator('input[placeholder="Game ID"], input.Form_idInput__MPydi').first
        await game_id_input.wait_for(state="visible", timeout=20000)
        await game_id_input.fill(code)
        await page.keyboard.press("Enter")
        
        log_bot(index, "Entering Nickname")
        nickname_input = page.locator('input[placeholder="Nickname"], input[type="text"]:visible').first
        try:
            await nickname_input.wait_for(state="visible", timeout=15000)
        except:
            submit_button = page.locator('button[aria-label="Submit"], button.FormSubmitButton_submitButton__MK2LJ').first
            if await submit_button.is_visible():
                await submit_button.click()
            await nickname_input.wait_for(state="visible", timeout=10000)
            
        await nickname_input.fill(unique_name)
        await page.keyboard.press("Enter")
        
        await page.wait_for_timeout(2000)
        error_msg = page.locator('div[class*="error"], div[class*="Error"]').first
        if await error_msg.is_visible() and await error_msg.text_content():
            text = await error_msg.text_content()
            log_bot(index, f"Join Error: {text}")
            if "name" in text.lower():
                await nickname_input.fill(unique_name + str(index + 1))
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)

        bots[index].status = "Playing"
        log_bot(index, "Ready! Waiting for points/stats...")
        
        # Inject spam script that only presses ONE key and reacts instantly to mutations
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
            
            // Fallback ultra-rapide (1ms au lieu de 50ms)
            const intervalId = setInterval(pressKey, 1);
            
            // MutationObserver pour réagir instantanément à l'apparition des questions (0ms de latence structurelle)
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
        
        # Start state scraper loop
        asyncio.create_task(update_bot_state_loop(page, index))
        
        # Keep window alive forever asynchronously
        while True:
            await asyncio.sleep(3600)
            
    except Exception as e:
        bots[index].status = "Error"
        log_bot(index, f"Crashed: {str(e)[:40]}")
        if headless:
            path = f"error_window_{index}.png"
            await page.screenshot(path=path)
        raise e

def generate_table() -> Table:
    table = Table(box=box.ROUNDED, expand=True, title="[bold blue]🚀 Blooket Bot Swarm Dashboard[/bold blue]")
    table.add_column("ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Status", style="bold green")
    table.add_column("Key", justify="center", style="yellow")
    table.add_column("Score / Stats", justify="right", style="bold white")

    for bot in bots:
        # Style status conditionally
        status_color = "green"
        if bot.status == "Error":
            status_color = "red"
        elif bot.status != "Playing":
            status_color = "yellow"
            
        table.add_row(
            str(bot.index).zfill(2),
            bot.name,
            f"[{status_color}]{bot.status}[/{status_color}]",
            bot.spam_key,
            f"[bold yellow]{bot.score}[/bold yellow]"
        )
    return table

async def run_bot(code, name, count, headless=True):
    # Initialize the global bots list
    for i in range(count):
        bots.append(BotState(index=i))
        
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            # Arguments for performance and stability
            args=["--disable-web-security", "--disable-features=IsolateOrigins,site-per-process"]
        )
        tasks = []
        for i in range(count):
            tasks.append(asyncio.create_task(automate_window(browser, code, name, i, headless=headless)))
            if i < count - 1:
                await asyncio.sleep(0.5) # Stagger to avoid rate limits
                
        await asyncio.gather(*tasks)

async def rich_ui_loop():
    """
    Renders and updates the rich Live application table continuously.
    """
    with Live(generate_table(), refresh_per_second=4, console=console, screen=True) as live:
        while True:
            await asyncio.sleep(0.25) # 4 updates per second roughly
            live.update(generate_table())

async def main_async(code, name, count, headless):
    try:
        # Run the UI loop concurrently with the playwright bot runner
        await asyncio.gather(
            run_bot(code, name, count, headless),
            rich_ui_loop()
        )
    except asyncio.CancelledError:
        pass

def main():
    parser = argparse.ArgumentParser(description="Blooket Bot - Multi-window spammer")
    parser.add_argument("code", help="The Blooket Game ID / Code")
    parser.add_argument("name", help="The base nickname to use")
    parser.add_argument("--count", "-c", type=int, default=4, help="Number of windows to open (default: 4)")
    parser.add_argument("--show", action="store_false", dest="headless", help="Show browser windows (default is headless mode)")
    args = parser.parse_args()
    
    try:
        asyncio.run(main_async(args.code, args.name, args.count, args.headless))
    except KeyboardInterrupt:
        console.print("[bold red]\nExiting gracefully...[/bold red]")

if __name__ == "__main__":
    main()
