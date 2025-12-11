# 🎵 JD360 Audio Toolkit

A beginner-friendly tool for extracting and rebuilding audio for **Just Dance (Xbox 360)** `.wav.ckd` files.

This toolkit lets you:
- **Uncook** (`.wav.ckd` → `.wav`)
- **Recook** (edited `.wav` → new `.wav.ckd`)

Everything is interactive — drag files in, press a number, done.

No gatekeeping here.  
I developed this myself — no one else’s work was used.

---

# 📦 Installation Guide

Follow all steps carefully. Skipping anything will cause errors.

---

## 1️⃣ Install Python 3

Download:  
👉 https://www.python.org/downloads/

During installation:
- ✅ Check **“Add Python to PATH”**
- ✅ Finish setup

Verify:

```cmd
python --version
```

---

## 2️⃣ Install vgmstream-cli (for UNCOOKING)

Download:  
👉 https://vgmstream.org/downloads

Extract to a permanent folder, for example:  
`C:\Tools\vgmstream\`

Ensure this folder contains:
- `vgmstream-cli.exe`

### Add vgmstream to PATH

1. Open Start → search **Environment Variables**
2. Click **“Edit the system environment variables”**
3. Click **Environment Variables…**
4. Under **System variables**, select `Path` → **Edit**
5. Click **New** and add:  
   `C:\Tools\vgmstream\`
6. Click OK on all dialogs to save.

### Test in a new Command Prompt:

```cmd
vgmstream-cli
```

If you see usage text, it works.

---

## 3️⃣ Install XMA2 Encoder (for RECOOKING)

### A. Install the Xbox 360 SDK (Sorry can't provide, find it yourself)

After installation, go to:  
`C:\Program Files (x86)\Microsoft Xbox 360 SDK\bin\win32\`

You should find:
- `xma2encode.exe`

### B. Copy xma2encode.exe into System32

Copy:
- `xma2encode.exe`

To:
- `C:\Windows\System32\`

This allows you to run `xma2encode` from any folder.

### C. Verify

```cmd
xma2encode test.wav
```

If it creates a `.xma` file (or similar), you’re good.

---

# 🚀 Using JD360 Audio Toolkit

Place `jd360_tool.py` somewhere convenient (e.g. next to your CKD files), then run:

```cmd
python jd360_tool.py
```

You should see:

```
=== Just Dance 360 Audio Tool ===
1) Uncook .wav.ckd -> .wav
2) Recook (template .wav.ckd + edited .wav -> new .wav.ckd)
0) Exit
Select an option:
```

---

## 🥣 1) UNCOOK (CKD → WAV)

1. Press `1`
2. When prompted, drag your `.wav.ckd` file into the Command Prompt window and press Enter
3. A `.wav` file with the same name will appear next to the CKD

**Example:**  
`seven.wav.ckd` → `seven.wav`

---

## 🍳 2) RECOOK (WAV → CKD)

You need:
- The original game CKD (template), e.g. `seven.wav.ckd`
- Your edited WAV, exported as:
  - 48,000 Hz
  - PCM
  - Stereo (if the original was stereo)

### Steps:

1. Press `2`
2. Drag the original `.wav.ckd` and press Enter (template)
3. Drag your edited `.wav` and press Enter
4. Enter a name for the output CKD, e.g. `seven_mod.wav.ckd`

### The tool will:
- Call `xma2encode` to encode your WAV to XMA2
- Inject the new XMA2 data into the original CKD header
- Save the new CKD with your provided name

💡 Rename/replace the original file in your Just Dance game folder with the modded `.wav.ckd` (after backing up!).

---

# 🧠 How It Works (Short Version)

Just Dance Xbox 360 uses RAKI containers with XMA2 audio.

Each `.wav.ckd` has:
- A header (RAKI metadata, seek table, etc.)
- An audio section (XMA2 payload)

### The toolkit:
- Reads the header size from the CKD
- Finds the `"data"` chunk inside the header
- Updates the stored audio size
- Rebuilds a new CKD as:  
  `[original header] + [your new XMA2 audio]`

✅ Just Dance streams tracks from start to finish, so keeping the header + offsets intact is enough for stable playback.

---

# ⚠️ Important Notes

Your edited WAV **must be**:
- 48 kHz
- PCM
- Same number of channels as the original (usually stereo)

❌ Do not use MP3/AAC renamed to `.wav`  
🎚️ Avoid heavy clipping — leave headroom  
⏱️ Keep song length close to original for best behavior  
💾 Always back up all original `.wav.ckd` files before replacing

---

# 🛠 Troubleshooting

### ❓ `vgmstream-cli` is not recognized
- Check that `C:\Tools\vgmstream\` is in the **System PATH**
- Run a **new Command Prompt** and try:

```cmd
vgmstream-cli
```

---

### ❓ `xma2encode` is not recognized
- Confirm `xma2encode.exe` is in:  
  `C:\Windows\System32\`
- Run a **new Command Prompt** and try:

```cmd
xma2encode test.wav
```

---

### ❓ Recooked file is silent / broken
- Ensure edited file is **48 kHz PCM WAV**
- Try lowering volume slightly to avoid clipping
- Test with simpler CKD (e.g. intro/ambience)

---

### ❓ “Could not find encoded XMA file”
- Some SDKs output:
  - `file.xma`
  - `file_xma.wav`
  - `file_xma2.wav`

🔍 Check the folder after running `xma2encode` to see which file was created.

---

# 👤 Credits

Developed by **Spidey-JD** (your friendly neighborhood Just Dance modder 🕷️)  
No gatekeeping — I developed this myself, no one else’s work was used.

---

# ⭐ Support

If this toolkit helped you mod Just Dance on Xbox 360, consider **starring the repository**.  
Issues and pull requests are welcome!
