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
script.js        - All application logic and translations
style.css        - Styling including dark theme and particle animations
sw.js            - Service worker for PWA offline caching
manifest.json    - Web app manifest for PWA installation
icon-*.png       - App icons
```

## Running the App
- **Workflow**: "Start application" — serves static files via `python3 -m http.server 5000 --bind 0.0.0.0`
- **Port**: 5000

## Deployment
- **Type**: Static site deployment
- **Public Dir**: `.` (project root)
