# AI DZ CHECK

## Overview
A Progressive Web Application (PWA) — the "First Algerian Tool for Detecting Misleading Content." It detects AI-generated images, videos, and audio using metadata analysis and multiple AI detection engine simulations.

## Tech Stack
- **Frontend**: Pure HTML5, CSS3, Vanilla JavaScript (ES6+) — no build system
- **PWA**: Service Worker (`sw.js`) + Web App Manifest (`manifest.json`)
- **External Libraries (CDN)**: Font Awesome, Google Fonts (Inter), Exifr, jsPDF
- **Languages**: English, Arabic, French (built into `script.js`)

## Project Structure
```
index.html       - Main entry point and UI
script.js        - All application logic and translations (~3500 lines)
style.css        - Styling including dark theme and particle animations
sw.js            - Service worker for PWA offline caching
manifest.json    - Web app manifest for PWA installation
icon-*.png       - App icons
```

## Running the App
- **Workflow**: "Start application" — serves static files via `npx serve -s . -l 5000`
- **Port**: 5000

## Deployment to GitHub + Vercel
- **GitHub repo**: https://github.com/Nadirinfograph23/ai-dzcheck
- **Vercel site**: https://ai-dzcheck.vercel.app/
- **IMPORTANT**: After every code change, push to GitHub using the GitHub API (the token is stored as `GITHUB_TOKEN` secret). Vercel auto-deploys from the `main` branch.
- **Push method**: Use the GitHub API via code_execution (create blobs → create tree → create commit → update ref). Direct `git push` does NOT work due to environment limitations.

## Key Bug Fixed
- `analyzeMetadata()` in script.js was missing the `async` keyword, causing a SyntaxError that prevented ALL JavaScript from loading — breaking the language button, PWA bar, and file analysis.

## Features Added (with NEW badge)
- Image detection cards: FauxLens, Deepfake Detection IO, AI DeepFake Detector, AI Detect Lab, Hive Moderation, Sightengine, Is It AI
- Video detection cards: ScreenApp Video Detection, OverChat Video Detection
- Audio detection cards: Deepfake Voice Detection, Free AI Detector, AI Voice Detector, AI Video Detector (Audio), ScreenApp AI Audio
- Social media reverse search (dork section) with blinking NEW badge
- All new cards have blinking `badge-new` icon in both analysis steps and results sections
