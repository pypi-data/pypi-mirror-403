# Hush

**Local-first data scrubbing for macOS**

Hush is a native macOS application that detects and anonymizes sensitive information in screenshots, images, and spreadsheets—completely offline. No data or telemetry leaves your machine.

## Features

- **100% Local**: No data ever leaves your machine; no telemetry or "phone home"
- **Native macOS App**: SwiftUI frontend with Python detection backend, animated menu bar icon
- **Hardware Accelerated**: Apple Vision Framework for OCR
- **Smart Detection**: PII (names, emails, phones, SSNs) and technical secrets (API keys, tokens)
- **Interactive Review**: Unified interface with Review/Add/Remove modes for precise control
- **Visual Editing**: Zoom, pan, and fine-tune detections with hover states and undo/redo
- **Custom Areas**: Add or remove detection areas manually with click-to-select interface
- **PDF Support**: Secure rasterized redaction with white background preview

## Tech Stack

| Layer | Technology |
|-------|------------|
| **UI** | Swift 5, SwiftUI, AppKit (macOS) |
| **Build** | Swift Package Manager (`Hush.swiftpm`) |
| **Backend** | Python 3.10+ (embedded via PythonKit or subprocess) |
| **OCR** | Apple Vision Framework (via Python `vision` / native) |
| **PII Detection** | [Presidio](https://github.com/microsoft/presidio) (regex + optional NLP), custom recognizers |
| **Config** | JSON in `~/.hush/` (thresholds, adjustments) |

## Open-Source Detection Engine

The **core detection engine and PII logic are open-source** so security-conscious users can verify that:

- Processing stays **fully local** (no cloud, no telemetry)
- Detection patterns and thresholds are **auditable and tunable**

### Where the logic lives

| Component | Path | Description |
|-----------|------|-------------|
| **PII detector** | `src/detectors/pii_detector.py` | Presidio-based detector; custom regex recognizers for AWS keys, Stripe keys, etc. |
| **Detection config** | `src/detection_config.py` | Confidence thresholds per entity type (PERSON, EMAIL_ADDRESS, PHONE_NUMBER, AWS_ACCESS_KEY, etc.) and persistence |
| **OCR** | `src/ocr/` | Vision-based OCR pipeline for images |
| **Anonymizers** | `src/anonymizers/` | Image redaction and spreadsheet anonymization |
| **Orchestration** | `src/ui/file_router.py`, `src/scrub_image.py`, `src/scrub_spreadsheet.py` | File routing and scrub workflows |

Entity types and default thresholds are defined in `src/detection_config.py`; custom recognizers (e.g. API key patterns) are in `src/detectors/pii_detector.py`. You can audit and extend these without touching the Swift UI.

## Supported Files

| Type | Formats | Method |
|------|---------|--------|
| Images | PNG, JPEG, HEIC | Black bar redaction |
| PDFs | PDF (any page count) | Rasterized redaction (secure, destroys text layer) |

## Quick Start

```bash
# Install dependencies
brew install poppler  # Required for PDF processing

# Set up Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg   # optional, for NLP-based PII

# Build and run
cd Hush.swiftpm && swift build && cd ..
./run.sh
```

## Architecture

```
SwiftUI Frontend (Hush.swiftpm/)
  ├── Views/            ReviewView (unified interface), DropZoneView, PreferencesView
  ├── Services/         MenuBarIconAnimator (animated icon), PythonBridge (IPC)
  └── Models/           AppState (shared state management)
        │ PythonKit or subprocess (JSON-RPC)
Python Backend (src/)
  ├── ocr/              Vision-based OCR
  ├── detectors/        Presidio PII detection (open-source logic)
  ├── detection_config  Thresholds and persistence
  └── anonymizers/      Image/spreadsheet processing
```

### UI Highlights

- **Animated Menu Bar Icon**: Blinking eyes that look around (synchronized across menu bar, dock, and drop zone)
- **Unified Review/Edit Interface**: Single window with tabbed modes (no separate Edit window)
- **Yellow Action Buttons**: Distinctive #FAD900 buttons with hover states (#E6C700)
- **Collapsible Detection Groups**: Expand/collapse similar detections, view confidence scores
- **Preferences**: Adjust confidence thresholds per entity type (Name, Email, Phone, etc.)

## Usage

1. Click **Hush** in menu bar → **Drop Zone**
2. Drag image or PDF onto drop zone
3. Click **Continue** to analyze
4. **Review** detections in unified interface with three modes:
   - **Review**: Preview red censor blocks on your file
   - **Add**: Click unflagged text areas to add custom detections
   - **Remove**: Click detected areas to remove false positives
5. Use **zoom controls** to inspect details, **undo** to revert changes
6. Click **Save Image/PDF** to export anonymized file

### Interactive Controls

- **Zoom**: Use `+` and `-` buttons or scroll wheel to zoom in/out
- **Pan**: Click and drag to move around zoomed preview
- **Recenter**: Click center button to reset view
- **Undo**: Revert last change (add/remove detection)
- **Checkbox Groups**: Toggle entire groups of similar detections

## Development

```bash
./run.sh              # Run app with Python environment
./scripts/build.sh    # Build for distribution

# Swift-only rebuild
cd Hush.swiftpm && swift build
```

### Recent Improvements

- Unified Review and Edit windows into single tabbed interface
- Animated menu bar icon with blinking eyes (SVG + PNG variants)
- Interactive Add/Remove modes with hover states and undo
- Yellow button styling with consistent hover colors
- White background for PDF preview (transparent PNG support)
- Removed training/model features (streamlined to detection thresholds)
- 1px separator border between list and preview
- Synchronized icon animations across menu bar, dock, and drop zone

## License

Core detection engine and PII logic: **MIT License** (see [LICENSE](LICENSE)). This encourages community trust, auditing, and contributions to detection patterns. Third-party dependencies (e.g. Presidio, spaCy) have their own licenses.
