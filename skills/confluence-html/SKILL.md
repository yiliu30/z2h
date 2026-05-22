---
name: confluence-html
description: Create rich, interactive HTML that survives Confluence's save sanitizer by using only inline styles, no external resources, and JavaScript for dynamic content. Use this skill when embedding HTML visualizations, interactive diagrams, or data displays into Confluence pages via the HTML macro. The main challenge is that Confluence strips CSS `<style>` blocks and `class=` attributes on save (though preview shows them). This skill ensures your HTML builds and stays beautiful after save.
license: MIT
---

# Confluence HTML Macro

You are creating HTML that will be embedded into Confluence via the `<ac:structured-macro ac:name="html">` macro. The challenge: **Confluence preview renders correctly, but on save the sanitizer strips `<style>` blocks and `class=` attributes, breaking the layout.**

The solution is counterintuitive — build like it's 2005: all styling via inline `style=""` attributes, no external resources, and JavaScript to apply dynamic styles.

## How Confluence's HTML Sanitizer Works

Preview is misleading. When you save:
- **Strips entirely**: `<style>` blocks, `<link>` tags, `@import`, external fonts
- **Strips attributes**: `class=`, all CSS custom properties (`var(--xxx)`)
- **Removes from DOM**: `<head>` (only `<body>` renders)
- **Blocks CSP**: external CDNs, Google Fonts, analytics
- **Preserves**: `<script>` blocks, inline `style=""` attributes, `style.*` from JS

This means your beautiful CSS architecture gets nuked on save, leaving only raw HTML and inline styles.

## Instructions

### 1. Ban All CSS Classes and Style Blocks

- Delete the `<style>` block entirely
- Remove all `class="xxx"` attributes
- Rewrite every styling decision as inline `style="property: value;"`

```html
<!-- ✗ DON'T: relies on .card class from <style> block -->
<div class="card">Content</div>

<!-- ✓ DO: inline everything -->
<div style="background: #fff; border: 1px solid #ccc; padding: 1rem; border-radius: 8px;">
  Content
</div>
```

### 2. Use Only System Fonts

No web font loading. Use:
- `'Courier New', monospace` (system mono)
- `Georgia, serif` (system serif)
- `Arial, -apple-system, sans-serif` (system sans)

```css
/* ✗ DON'T */
font-family: 'JetBrains Mono';
@import url('https://fonts.googleapis.com/...');

/* ✓ DO */
font-family: 'Courier New', monospace;
```

### 3. Use JavaScript for Dynamic Styles

JavaScript `<script>` blocks survive. Apply all dynamic styling via `element.style.*`:

```html
<!-- Apply responsive layout -->
<div id="grid"></div>
<script>
const grid = document.getElementById('grid');
grid.style.display = 'grid';
grid.style.gridTemplateColumns = 'repeat(32, 1fr)';
grid.style.gap = '1px';
grid.style.background = 'rgba(100, 100, 100, 0.1)';
</script>
```

### 4. Inline Hover Effects

CSS `:hover` requires a `<style>` block. Use `onmouseenter` / `onmouseleave`:

```html
<div id="box" style="background: #eee; padding: 1rem;"
  onmouseenter="this.style.background='#ddd'; this.style.transform='scale(1.02)'"
  onmouseleave="this.style.background='#eee'; this.style.transform='scale(1)'">
  Hover me
</div>
```

### 5. Flatten All Color References

Never use CSS custom properties (`var(--color)`). Use `#hex` or `rgba()` directly:

```html
<!-- ✗ DON'T -->
<span style="color: var(--primary-color);">Text</span>

<!-- ✓ DO -->
<span style="color: #0e8a7d;">Text</span>
```

### 6. Wrap in Confluence HTML Macro

```html
<ac:structured-macro ac:macro-id="unique-id" ac:name="html" ac:schema-version="1">
  <ac:plain-text-body><![CDATA[
<!-- your inline-styled HTML here -->
]]></ac:plain-text-body>
</ac:structured-macro>
```

## Examples

### Input
User wants to embed an interactive data grid visualization in Confluence showing token cache layout with custom colors.

### Expected Behavior

Before embedding — the local HTML renders beautifully with light mode colors, gradients, and a 64×32 grid of cells.

Steps:
1. **Audit the HTML**: search for `class="`, `<style>`, `<link>`, `var(--`. All must return 0 matches.
2. **Convert classes to inline**: For each `.grid-cell { background: ...; }`, add `style="background: ..."` to the element.
3. **Move CSS custom properties**: Replace `color: var(--primary)` → `color: #hex`
4. **Port animations/responsive logic to JS**: Move `@keyframes`, `@media`, `:hover` into `<script>` blocks using `element.style.*`.
5. **Test preview**: Open Confluence, paste via HTML macro, verify preview renders.
6. **Test save**: Save the page, reload. If layout persists, it's Confluence-safe.

## What NOT to Do

- **No `<style>` block** — will be stripped on save
- **No `class="xxx"`** — useless after save (style block gone)
- **No `@media` queries** — no style block to put them in
- **No CSS custom properties (`var(--xxx)`)** — sanitizer doesn't understand them
- **No external fonts** — CSP blocks them
- **No `::before` / `::after`** — require style block
- **No `@keyframes`** — require style block
- **No `<link>` tags** — all external resources blocked

## Pre-embed Checklist

Before pasting into Confluence, run these searches (should all return 0):
1. `grep -c 'class="' file.html` ✔️ must be 0
2. `grep -c '<style' file.html` ✔️ must be 0
3. `grep -c '<link' file.html` ✔️ must be 0
4. `grep -c 'var(--' file.html` ✔️ must be 0
5. Open file locally in a browser → visual check ✔️ passes
6. Test in Confluence preview → renders ✔️
7. Save page, reload → layout persists ✔️
