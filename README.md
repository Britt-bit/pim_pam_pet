# SpinAlert 🎡🔔🏆

A Kivy-based Android app with three features:
- **Alert Scheduler** — set a time window and number of random daily alerts
- **Spin Wheel** — spin for a random letter or color
- **Scoreboard** — add players and track scores with +/− buttons

---

## Running on your PC (for testing)

### 1. Install Python 3.10+
https://www.python.org/downloads/

### 2. Install Kivy
```bash
pip install kivy plyer
```

### 3. Run the app
```bash
cd pim_pam_pet
python main.py
```

---

## Building the Android APK

Buildozer is meant to run on **Linux**. On **macOS** or **Windows**, use **Docker** (simplest) or a Linux machine / WSL2.

### Option A — Docker (recommended on macOS and Windows)

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and start it.
2. In a terminal, from this project folder:
   ```bash
   ./build-android.sh
   ```
   The first build downloads the Android SDK/NDK and can take **20–40+ minutes** and several GB of disk. Later builds are faster. A cache is kept in `~/.buildozer` so you do not redownload everything every time.

3. The debug APK is under `bin/`, for example:
   ```text
   bin/spinalert-1.0-arm64-v8a-debug.apk
   ```
   (Exact name may include an ABI; any `*-debug.apk` in `bin/` is fine to install.)

If Docker says it cannot find the image, pull it once:
```bash
docker pull kivy/buildozer
```

**Apple Silicon (M1/M2/M3):** The script uses `linux/amd64` so the official image runs; the build may be slower than on Intel.

### Option B — Linux or WSL2 (native Buildozer)

1. **WSL2 (Windows):** In PowerShell (Admin): `wsl --install`, then open Ubuntu from the Start menu.
2. Install dependencies, then build:
   ```bash
   sudo apt update && sudo apt install -y \
       git zip unzip python3-pip \
       build-essential libssl-dev libffi-dev \
       libsqlite3-dev python3-dev \
       openjdk-17-jdk autoconf libtool \
       libltdl-dev libz-dev cmake
   pip3 install --user buildozer cython
   cd /path/to/pim_pam_pet
   buildozer android debug
   ```

### Install the APK on your phone

1. **Allow unknown apps** (wording varies by Android version):
   - **Settings → Apps → Special access → Install unknown apps** and allow your file manager, **or**
   - **Settings → Security →** enable installing from the source you use (e.g. USB, Drive, mail).
2. **Copy the APK** to the phone: USB, AirDrop to Files, Google Drive, email, etc.
3. Open the APK on the phone and tap **Install**.

**Optional — USB and ADB:** Enable **Developer options** and **USB debugging** on the phone, connect with USB, then on your computer (with `adb` installed):
```bash
adb install -r bin/*-debug.apk
```
Use the exact filename from your `bin/` folder.

---

## App structure

```
pim_pam_pet/
├── main.py           ← All app code (screens, wheel, scheduler, scores)
├── buildozer.spec    ← Android build config
├── build-android.sh  ← Docker one-liner to build the APK (macOS/Windows)
└── spinapp_data.json ← Auto-created on first run (saves your data)
```

---

## Features

### 🔔 Alert Scheduler
- Set start and end hour with sliders (e.g. 07:00 – 19:00)
- Set how many alerts per day (1–20)
- Tap **Start Scheduling** — alerts fire at random times in your window
- Runs in a background thread; survives screen changes

### 🎡 Spin Wheel
- Toggle between **Letters** (A–L on the wheel) and **Colors**
- Tap SPIN — wheel animates and lands on a random result
- Result displayed below the wheel

### 🏆 Scoreboard
- Type a name and tap **+ Add** to add a player
- Tap **+** / **−** to adjust scores (auto-saves)
- Players are sorted by score (highest first)
- Tap **✕** to remove a player

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: kivy` | Run `pip install kivy` |
| Buildozer fails on first run | Make sure Java 17 is installed: `java -version` |
| **"Buildozer is running as root"** | Do **not** use `sudo buildozer`. Run as your normal user. If you already used `sudo` once, fix cache ownership, then rebuild: `sudo chown -R "$USER:$USER" ~/.buildozer .buildozer` (from the project directory). If `~/.android` is root-owned, `sudo rm -rf ~/.android` and try again (it will be recreated for your user). The `warn_on_root = 0` in this project only skips the **prompt**; you should still avoid root so files are not owned by root. |
| Notifications don't work on PC | Normal — plyer notifications need Android |
| App crashes on phone | Run `buildozer android debug logcat` to see errors |

---

## Customizing

- **Add more letters to the wheel**: Edit `WHEEL_LETTERS` in `main.py`
- **Change wheel colors**: Edit `WHEEL_COLORS` list
- **Change app colors**: Edit the color constants at the top of `main.py` (BG, ACCENT, etc.)
