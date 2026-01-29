# NavyTraceback

<div align="center">
  <img src="https://raw.githubusercontent.com/YOUR_USERNAME/NavyTraceback/main/assets/full_logo.png" alt="NavyTraceback Banner" width="600" />
</div>

Python tracebacks are usually a mess of white text on a black background. **NavyTraceback** replaces them with a Windows XP-style Blue Screen of Death (BSOD) and automatically handles crash dumps so you don't lose your debug data.

## Why?
Standard stack traces are boring. This library makes crashes readable and gives you a `.txt` dump file on your desktop immediately which helps debugging way more than people might expect.

## Safe Mode

NavyTraceback includes a safe mode feature that won't clutter your terminal screen entirely, this
feature helps you look at your print statements you set-up for further debugging.

To enable this feature, type in the snippet below:

```python
import navytraceback

# Initiates safe mode upon starting a script
navytraceback.safe_mode(True)
```

## Installation

To install this library, type in the command below:

```bash
pip install navytraceback