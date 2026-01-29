# ChronosX

Minimal macOS menubar chronometer with lap history.

![macOS](https://img.shields.io/badge/platform-macOS-lightgrey) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-MIT-green)

## Install

### Via pip

```bash
pip install chronosx
chronosx
```

### As macOS App (clickable icon)

```bash
git clone https://github.com/albou/chronosx.git
cd chronosx
./scripts/build_app.sh
cp -r dist/ChronosX.app /Applications/
open /Applications/ChronosX.app
```

## Usage

| Action | Result |
|--------|--------|
| **Click** | Start/stop timer |
| **Right-click** | Open laps popup |
| **Double-click title** | Edit lap title |
| **Clear** | Delete all laps |
| **Exit** | Quit app |

### Display

- `●` — Idle
- `MM:SS.m` — Running (minutes:seconds.tenths)

## Data

Laps stored in `~/.chronosx_laps.json`

## Requirements

- macOS 10.14+
- Python 3.9+

## License

MIT
