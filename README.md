# Murdoku solver

Proof of concept that solves a [Murdoku](https://murdoku.com) puzzle end to end: it captures the board from the web, parses it with computer vision and OCR, turns the clues into constraints with an LLM, solves them with CP-SAT and plays the solution back in the browser.

Each step is a standalone script that reads the previous step's output. Run every script from its own folder.

| Step | Script | Output |
|------|--------|--------|
| 1. Capture | `step1-capture/step1-capture.py` | Board screenshots (with/without objects and names) and the portrait cards |
| 2. Clues | `step2-parse/step2-ocr-characters.py` | `clues.json`: name, clue and gender of each person (OCR) |
| 3. Walls | `step2-parse/step3-board-tiles.py` | `walls.json`: walls detected from the gridline thickness |
| 4.1 Areas | `step2-parse/step4.1-areas.py` | `areas-ids.json`: areas found with a flood fill bounded by the walls |
| 4.2 Area names | `step2-parse/step4.2-areas-names.py` | `areas-names.json`, `areas.json`: area names (OCR) |
| 5. Objects | `step2-parse/step5-objects.py` | `objects.json`: objects found with template matching against `step2-parse/objects/` |
| 6. Model | `step3-modelate/step6-model.py` | `solution.json`: clues -> constraints (Gemini) -> CP-SAT model |
| 7. Play | `step4-solution/step7-play.py` | Places every person on the board in the browser |

`step2-parse/script-objects-screenshots.py` is a helper to create the object templates by clicking on the board.

The `video/` folder contains the resources and the Remotion project of the explainer video.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) must be installed. If it is not on `PATH`, set `TESSERACT_CMD` to the executable.
- Step 6 needs a Gemini API key in `step3-modelate/.env`: `GEMINI_API_KEY=...`. Responses are cached in `step3-modelate/output/ai_cache/`, so a repeated run with the same input does not call the API.
