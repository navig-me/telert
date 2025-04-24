# Simple Methods for Creating a Demo GIF

If you're having trouble with Terminalizer, here are some simpler alternatives for creating a GIF of the telert demo:

## Option 1: Use a Screen Recording Tool + GIF Converter

1. Use a screen recording tool to record your terminal:
   - On macOS: QuickTime Player (File > New Screen Recording)
   - On Windows: Xbox Game Bar (Win+G) or OBS Studio
   - On Linux: SimpleScreenRecorder or OBS Studio

2. Run the demo simulation script:
   ```bash
   ./demo-simulation.sh
   ```

3. Convert the recording to GIF using an online converter or tool:
   - [ezgif.com](https://ezgif.com/video-to-gif)
   - [CloudConvert](https://cloudconvert.com/mp4-to-gif)
   - [GIPHY](https://giphy.com/create/gifmaker)

## Option 2: Use asciinema-player (Web-based)

1. Install asciinema:
   ```bash
   pip install asciinema
   ```

2. Record your terminal session:
   ```bash
   asciinema rec telert-demo.cast
   
   # Then run the demo inside the recording
   ./demo-simulation.sh
   
   # Stop recording with Ctrl+D
   ```

3. Upload to asciinema.org:
   ```bash
   asciinema upload telert-demo.cast
   ```

4. Get the embed code from asciinema.org and add it to your README using HTML.

## Option 3: Simple GIF Creation with Recordit

1. Download Recordit (macOS/Windows): http://recordit.co/

2. Start recording a portion of your screen containing the terminal

3. Run the demo script:
   ```bash
   ./demo-simulation.sh
   ```

4. Stop the recording when finished, and Recordit will automatically generate a GIF

5. Copy the GIF URL provided by Recordit and use it in your README:
   ```markdown
   ![telert demo](http://recordit.co/your-recording-id)
   ```

## Option 4: Use Peek (Linux)

1. Install Peek:
   ```bash
   # Ubuntu/Debian
   sudo apt install peek
   
   # Fedora
   sudo dnf install peek
   ```

2. Open Peek and select the terminal window area

3. Run the demo script and record with Peek:
   ```bash
   ./demo-simulation.sh
   ```

4. Save the recording as a GIF