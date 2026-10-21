import json

from playwright.sync_api import sync_playwright

PUZZLE_URL = "https://murdoku.com/play/puzzle-preppers-medium"

with open("../step3-modelate/output/solution.json", "r") as f:
    solution = json.load(f)

N = len(solution)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(storage_state="../step1-capture/state.json", device_scale_factor=2)
    page = ctx.new_page()

    page.goto(PUZZLE_URL)
    page.wait_for_timeout(5000)  # The area names appear with a delay

    bbox = page.locator(".grid-wrapper").bounding_box()
    if bbox is None:
        raise ValueError("Board not found on the page")

    cell_W = bbox["width"] / N
    cell_H = bbox["height"] / N

    def get_center_pixel(i, j):
        return (bbox["x"] + (j + 0.5) * cell_W, bbox["y"] + (i + 0.5) * cell_H)

    # solution.json keeps the order of clues.json, which is the order of the portraits on the page
    for index, (i, j) in enumerate(solution.values()):
        page.locator(".mrdPortraitGroup").nth(index).click()

        x, y = get_center_pixel(i, j)
        page.mouse.move(x, y)
        # Long press on the target cell
        page.mouse.down()
        page.wait_for_timeout(1000)
        page.mouse.up()

    input("Solution placed. Press Enter to close the browser...")
