# Text-based Financial Indices Hub — GitHub Pages edition

This is a static conversion of the original Dash/Python app. The deployed site does **not** need Flask, Dash, Gunicorn, EC2, or any always-on Python server.

## Deploy to GitHub Pages

1. Create a GitHub repository (for example `financial-indices`).
2. Upload **the contents of this folder** to the repository root.
3. In GitHub, open **Settings → Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**.
5. Select branch `main` and folder `/ (root)`, then save.
6. The site will be available at `https://<username>.github.io/<repository>/`.

All application paths are relative, so a project Pages URL works without editing `index.html`.

## Local preview

Because browsers block `fetch()` from `file://`, do not double-click `index.html` for testing. Run a tiny local HTTP server instead:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/`.

## Structure

- `index.html` — static page and explanatory content
- `js/app.js` — tabs, dropdowns, sliders, Plotly rendering
- `data/` — normalized JSON generated from the original CSV outputs
- `vendor/plotly.min.js` — local Plotly.js, so charts do not depend on a Plotly CDN
- `assets/styles.css` — responsive dashboard styling
- `tools/build_data.py` — data conversion script used to turn the original `out/*.csv` files into browser-friendly JSON
- `.nojekyll` — tells GitHub Pages to serve the files directly

## Updating data later

The website itself needs no Python server. If the source CSV outputs are updated, regenerate the JSON data as a build/update step and commit the changed `data/` files. The included `tools/build_data.py` can regenerate the normalized data from a local copy of the original project. For example:

```bash
python tools/build_data.py --src ../original-project
```

The folder supplied to `--src` must contain the original `out/` CSV files.

## Notes

- Interactive hover, zoom, pan, range slider, dropdowns, legend toggling, the BC-factor table, and treemap depth control are browser-side.
- MathJax is loaded from jsDelivr for equation rendering. The graphs themselves use the bundled local Plotly.js file.
- The data in the supplied original source ends around 2022/2023; this conversion preserves that supplied data rather than inventing newer observations.
