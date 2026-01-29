# fn-1.6 Add custom branding and theme styling

## Description

Add custom branding and theme styling to give Bond a distinct visual identity.

### Steps

1. **Define Bond color palette**
   - Choose primary color (suggestion: deep purple or forensic blue)
   - Choose accent color
   - Ensure WCAG 2.1 AA contrast compliance

2. **Create custom CSS** (`docs/stylesheets/extra.css`)
   - CSS custom properties for brand colors
   - Hero section styling (gradient text, etc)
   - Grid card styling for features
   - Code block customization

3. **Update mkdocs.yml**
   - Add `extra_css: [stylesheets/extra.css]`
   - Configure color palette for light/dark modes
   - Set logo/favicon if available

4. **Add theme features**
   - Navigation tabs
   - Search suggestions
   - Content tabs linking
   - Code copy button

### Reference

- Dataing CSS: `/Users/bordumb/workspace/repositories/dataing/docs/docs/stylesheets/extra.css`
- Material color guide: https://squidfunk.github.io/mkdocs-material/setup/changing-the-colors/

### Color Palette Suggestions

**Option A - Forensic Blue:**
- Primary: #1a237e (deep blue)
- Accent: #00bcd4 (cyan)

**Option B - Investigation Purple:**
- Primary: #4a148c (deep purple)
- Accent: #ff9800 (amber)

**Option C - Neutral Professional:**
- Primary: #263238 (blue-grey)
- Accent: #00c853 (green)
## Acceptance
- [ ] docs/stylesheets/extra.css exists with Bond brand colors
- [ ] Light mode color scheme is configured
- [ ] Dark mode color scheme is configured
- [ ] Hero section has custom styling (if applicable)
- [ ] Code blocks have consistent styling
- [ ] Navigation tabs and search work correctly
- [ ] Color contrast meets WCAG 2.1 AA guidelines
## Done summary
Added custom Bond branding with Forensic Blue theme (primary #1a237e, accent #00bcd4). Full light/dark mode support, hero gradients, styled cards/buttons/tables/code blocks. Build verified.
## Evidence
- Commits:
- Tests:
- PRs: