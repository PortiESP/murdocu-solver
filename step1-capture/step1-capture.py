from pathlib import Path

from playwright.sync_api import sync_playwright


PUZZLE_URL = "https://murdoku.com/play/puzzle-preppers-medium"
BOARD = ".grid-wrapper"

Path("output/characters").mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    # state.json skips the intro and enables the gender colors used by step2
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(storage_state="state.json", device_scale_factor=2)
    page = ctx.new_page()

    page.goto(PUZZLE_URL)
    page.wait_for_timeout(5000)  # The area names appear with a delay

    # Board, as shown
    page.locator(BOARD).screenshot(path="output/board.png", animations="disabled")
    # Hide the objects: board with area names
    hide_objects = page.add_style_tag(content=".grid-wrapper img { visibility: hidden !important; }")
    page.locator(BOARD).screenshot(path="output/board-only-names.png", animations="disabled")
    # Hide the names too: empty board
    page.add_style_tag(content=".mdk-anim > div:last-of-type { visibility: hidden !important; }")
    page.locator(BOARD).screenshot(path="output/board-only.png", animations="disabled")
    # Show the objects again: board with objects, without names
    hide_objects.evaluate("e => e.remove()")
    page.locator(BOARD).screenshot(path="output/board-no-names.png", animations="disabled")

    # Portrait cards (name + clue)
    for i, elem in enumerate(page.locator(".mrdPortraitGroup").all()):
        elem.screenshot(path=f"output/characters/{i}.png", animations="disabled")

    ctx.close()
