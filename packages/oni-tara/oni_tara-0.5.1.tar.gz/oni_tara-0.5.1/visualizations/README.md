# ONI Visualization Suite

> Interactive educational web applications for the ONI Framework

## Overview

This prototype suite demonstrates 5 interactive web applications designed to make neural interface security concepts accessible to general audiences. Each application transforms complex ONI Framework concepts into engaging, hands-on learning experiences.

## Applications

| # | Application | Purpose | Key Features |
|---|-------------|---------|--------------|
| 01 | **Coherence Metric Playground** | Visualize signal trustworthiness math | Real-time calculation, waveform comparison, attack presets |
| 02 | **ONI Layer Explorer** | Navigate the 14-layer model | Layer details, attack surfaces, defense mechanisms |
| 03 | **Neural Kill Chain Visualizer** | Watch attacks propagate | 5 attack types, animated timeline, defense highlights |
| 04 | **NSAM Checkpoint Simulator** | Gamified signal analysis | 5 checkpoints, score tracking, multiple scenarios |
| 05 | **Scale-Frequency Navigator** | Explore temporal scales | 6 time scales, frequency bands, security context |

## Quick Start

### Option A: Download and Run (Easiest)

1. **Download the project**
   - Click the green **"Code"** button at the top of this page
   - Select **"Download ZIP"**
   - Save the file to your computer (e.g., your Downloads folder)

2. **Unzip the folder**
   - **Windows:** Right-click the ZIP file → "Extract All"
   - **Mac:** Double-click the ZIP file

3. **Find the visualizations**
   - Open the unzipped folder
   - Navigate to: `MAIN` → `tara-neural-security-platform` → `visualizations`

4. **Launch the app**
   - Double-click `index.html`
   - Your web browser will open with the application launcher
   - Click any card to explore that visualization

### Option B: For Developers

```bash
git clone https://github.com/qikevinl/ONI.git
cd ONI/MAIN/tara-neural-security-platform/visualizations
open index.html    # Mac
start index.html   # Windows
```

### Option C: Via TARA UI

```bash
pip install oni-tara[ui]
tara ui
# Navigate to "Interactive" section in sidebar
```

No build step required - pure HTML/CSS/JS

## File Structure

```
visualizations/
├── index.html                          # Master index & design system
├── README.md                           # This file
├── 01-coherence-metric-playground.html
├── 02-oni-layer-explorer.html
├── 03-neural-killchain-visualizer.html
├── 04-nsam-checkpoint-simulator.html
└── 05-scale-frequency-navigator.html
```

## Design System

### Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| ONI Blue | `#00d4ff` | Primary actions, highlights |
| ONI Purple | `#8b5cf6` | Interface layers (L8-10) |
| ONI Pink | `#ec4899` | Cognitive layers (L11-14) |
| ONI Green | `#10b981` | Success, secure states |
| ONI Yellow | `#f59e0b` | Warnings, caution |
| ONI Red | `#ef4444` | Danger, attacks |

### Domain Colors

- **OSI Layers (1-7)**: Blue gradient (`#3b82f6`)
- **Interface Layers (8-10)**: Purple gradient (`#8b5cf6`)
- **Cognitive Layers (11-14)**: Pink gradient (`#ec4899`)

## Technical Specifications

### Current Implementation

- **Framework**: Vanilla JavaScript (no dependencies)
- **Visualization**: HTML5 Canvas API, SVG
- **Animation**: CSS transitions, `requestAnimationFrame`
- **Styling**: CSS Custom Properties (variables)

### Production Recommendations

| Aspect | Recommendation |
|--------|----------------|
| Framework | SvelteKit or Next.js |
| Visualization | D3.js + Three.js |
| Animation | Framer Motion / GSAP |
| Hosting | Vercel/Netlify |
| Bundling | Vite |

### Performance Targets

- 60fps animation
- <100KB per app (gzipped)
- <3s time to interactive
- Works offline after first load

## Accessibility

All prototypes follow WCAG 2.1 AA guidelines:

- [x] Sufficient color contrast
- [x] Keyboard navigable
- [x] Focus indicators
- [ ] Screen reader labels (TODO: full ARIA implementation)
- [ ] Reduced motion support (TODO: `prefers-reduced-motion`)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development Roadmap

### Phase 1: Foundation (Current)
- [x] Core prototypes
- [x] Design system
- [x] Basic interactivity

### Phase 2: Enhancement
- [ ] Mobile optimization
- [ ] Touch gestures
- [ ] Offline support (Service Worker)
- [ ] Analytics integration

### Phase 3: Production
- [ ] Component library extraction
- [ ] API for dynamic data
- [ ] Embedding widget
- [ ] Internationalization

### Phase 4: Advanced
- [ ] 3D visualization mode
- [ ] VR/AR adaptation
- [ ] Real-time collaboration
- [ ] LMS integration

## Integration Points

### Embedding in Publications

Each app can be embedded via iframe:

```html
<iframe
  src="./visualizations/01-coherence-metric-playground.html"
  width="100%"
  height="600"
  frameborder="0">
</iframe>
```

### Web Component (Future)

```html
<script src="visualizations.js"></script>
<oni-coherence-playground theme="dark"></oni-coherence-playground>
```

## Contributing

These prototypes are part of the ONI Framework research project. Contributions welcome:

1. Report bugs via GitHub Issues
2. Suggest features via Discussions
3. Submit PRs for enhancements

## License

Apache License 2.0 - See [LICENSE](../../LICENSE)

---

*Part of the ONI Framework | Neural Interface Security Research*
*Prototypes v1.0 | January 2026*
