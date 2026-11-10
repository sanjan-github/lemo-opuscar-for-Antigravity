---
name: lemo-opuscar
description: >-
  Direct and produce a short film made entirely in code, in one of the styles
  of the Lemo-Opuscar library (e.g. Impasto Oil Painting, Watercolor
  Brush, Ukiyo-e, Satellite Briefing, Exploded Teardown).
  Use when the user asks for a video, film, short, promo, explainer or
  animation in a named style, including explainers built from real material
  such as satellite imagery, laser scans, CAD files or archive scans, and
  new films cut from real archive footage and documents; when they want a film
  about their own topic and haven't chosen a style (help them choose); when
  they want to change a style into their own, make their own style from a blank
  page, or use a style they saved; when they start the skill without saying what
  they want; or when they ask which film styles there are. Not for plain editing,
  trimming or converting the user's existing video files. Always default strictly
  to English unless another language is explicitly requested by the user.
---

# Lemo-Opuscar (Antigravity Edition)

The **Lemo-Opuscar** film library is installed directly in this plugin. Every film is created entirely from code: deterministic canvas/WebGL rendering, procedural sound synthesis, neural TTS, musical composition, and automated two-pass ffmpeg muxing.

> [!IMPORTANT]
> **Strict English-Only Policy:** Always use **English only** for all agent communication, user prompts, directing treatments, voiceover scripts, narration, on-screen text, subtitles, and code comments. Do NOT use or prompt for any other language unless the user explicitly requests another language in their prompt.

> [!NOTE]
> **Library Location ($LIB):** The library lives at the plugin root (e.g. `~/.gemini/config/plugins/lemo-opuscar` or repository root). All 66 styles, core tools, audio engines, guides, and fonts are already present locally. No cloning or remote download is required.

---

## 1. Antigravity Environment & Tool Mapping

Antigravity operates in Windows PowerShell with specific agent tools. Follow this mapping strictly:

| Legacy / Concept | Antigravity Tool & Syntax | Execution Rules |
| :--- | :--- | :--- |
| **Questions to User** | `ask_question` | Pass `questions: [{ question, options, is_multi_select }]`.<br>• Put the recommended choice first with `(Recommended)`.<br>• **Never** include an `"Other"` option (the UI adds it automatically).<br>• Do **not** use for simple yes/no questions (use chat).<br>• For style browsing (66 styles), list them in markdown chat to avoid truncation.<br>• All questions must be written in English. |
| **Shell Commands** | `run_command` | Shell is **PowerShell**. Each command runs in a new session (working directory does not persist).<br>• Run Node & Python directly from `$LIB`.<br>• Run shell scripts (`setup.sh`, `mux.sh`) via Git Bash (`& "$env:ProgramFiles\Git\bin\bash.exe"` or `setup.ps1`). |
| **Long Operations** | `run_command` with `WaitMsBeforeAsync: 500` | Dependency installs (`deps`), video frame rendering, and heavy audio synthesis should be backgrounded.<br>• **Reactive Wakeup:** Antigravity wakes you automatically when tasks finish. **Do not poll or loop `manage_task`!** |
| **File Operations** | `read_file`, `write_file`, `edit_file` | Use native tools instead of shell `cat`, `grep`, `sed`, or redirection (`>`). |
| **Static Visual Assets** | `invoke_subagent` (`TypeName: "image-generator"`) | Use only for generating logos, reference stills, or supporting graphic assets. |
| **Archive / Data Research** | `invoke_subagent` (`TypeName: "research"`) | Delegate deep historical research or data exploration to the read-only research subagent. |
| **Artifacts & Reviews** | `<appDataDir>\brain\<conversation-id>` | Save treatment docs, shot lists, and cue sheets in the project folder AND optionally as user-facing artifacts with `ArtifactMetadata`. |

---

## 2. Project Workspace & Storage

Always establish the project directory before writing files:

1. **Active Workspace:** If a workspace is active in Antigravity, create the film project inside:
   `<workspace>/<film-name>/`
2. **No Active Workspace:** If no workspace is active, create the film project inside the default Antigravity scratch area:
   `C:/Users/TestUser/.gemini/antigravity/scratch/<film-name>/`
   *(Remind the user they can open this folder as their active workspace).*
3. **Naming:** Use lowercase letters, digits, and hyphens (`[a-z0-9-]+`). Never use spaces, `#`, or `?`.

---

## 3. Setup & Dependencies

Dependency tiers are installed on-demand from the library root:

```powershell
# 1. Inspect installed tools and packages:
& "$LIB\skills\lemo-opuscar\scripts\setup.ps1"

# 2. Install Core Tier (Node packages + Playwright Chromium + Python venv):
# Run as background task (WaitMsBeforeAsync: 500)
& "$LIB\skills\lemo-opuscar\scripts\setup.ps1" deps

# 3. Add Voice or Music Tiers when required by the style ($LIB/TECHNIQUE.md §1):
& "$LIB\skills\lemo-opuscar\scripts\setup.ps1" deps voice
& "$LIB\skills\lemo-opuscar\scripts\setup.ps1" deps music
```

> [!IMPORTANT]
> **System Tools:** Node 20+, ffmpeg 7+, and Python 3.11+ must be installed on the host system. If missing, inform the user during the one round of questions. Do not attempt to install system software yourself.

---

## 4. Running Pipeline Tools in PowerShell

Set `$LIB` (plugin root or active clone) and execute tools from PowerShell as follows:

### Stills Rendering
```powershell
Set-Location $LIB
node core/render/still.mjs "<project-folder>" 1.5 3.0 --out "<project-folder>/stills"
```

### Video Frame Rendering
```powershell
Set-Location $LIB
node core/render/video.mjs "<project-folder>" --fps 24 --out "<project-folder>/out/video.mp4"
```

### Audio Synthesis & Procedural SFX
```powershell
& "$LIB/.venv/Scripts/python.exe" "<project-folder>/mix.py"
```

### Audio/Video Muxing
```powershell
& "$env:ProgramFiles\Git\bin\bash.exe" "$LIB/core/render/mux.sh" "<project-folder>/out/video.mp4" "<project-folder>/out/mix.wav" "<project-folder>/<name>.mp4" 24
```

---

## 5. Directing Workflow (The Run)

### Step 1: Start & Style Selection
- **Language Default:** Always use English. Do not prompt the user for a language choice; converse, plan, and produce exclusively in English unless the user explicitly requests another language in their prompt.
- **Saved Styles:** Check if `~/lemo-my-styles/README.md` exists. If the user refers to a saved style, inspect it first.
- **No Request Yet (Skill invoked with no prompt):** Offer the ways in with a single question using `ask_question`:
  ```json
  {
    "questions": [
      {
        "question": "How would you like to start with Lemo-Opuscar?",
        "options": [
          "(Recommended) Make a film in a library style",
          "Change an existing library style and save as custom",
          "Create a new custom style from scratch",
          "Browse available styles"
        ],
        "is_multi_select": false
      }
    ]
  }
  ```
- **Choosing a Style:**
  - If a style is specified (e.g. `impasto`, `watercolor`, `satellite-briefing`), load its rules from [`$LIB/styles/<slug>/STYLE.md`](../../styles/).
  - If no style is specified, suggest 2–3 styles suited to their topic, provide the web gallery link (`https://lemomo-ai.github.io/lemo-opuscar/`), and display the category directory in English.

<details>
<summary><b>Click to expand the 66 Library Film Styles</b></summary>

- **Edit & Documentary** (8): Caption News (`caption-news`), 1920s Newsreel (`newsreel-1920s`), Live Countdown Split-screen (`live-countdown`), Time-lapse Symphony (`timelapse-symphony`), Visual Investigation (`visual-investigation`), Constructivist Montage (`constructivist-montage`), Sports Telestrator (`sports-telestrator`), Broadcast News Package (`broadcast-news`)
- **Evidence Films** (8): Satellite Briefing (`satellite-briefing`), Engineering Briefing Board (`engineering-board`), LiDAR Survey (`lidar-survey`), Projection on White Model (`white-model`), Data Physicalization (`data-physicalization`), Exploded Teardown (`exploded-teardown`), Microscope Story (`microscope-story`), Archive Light Table (`archive-light-table`)
- **Hand-drawn & Painting** (8): Crayon Picture Book (`crayon-picture-book`), Watercolor Brush (`watercolor`), Chinese Ink Wash (`chinese-ink`), Impasto Oil Painting (`impasto`), One-line Drawing (`one-line`), Whiteboard Explainer (`whiteboard-explainer`), Urban Sketch · Pen & Wash (`urban-sketch`), Chalkboard (`chalkboard`)
- **East Asian Traditions** (4): Shadow Puppetry (`shadow-puppetry`), Ukiyo-e (`ukiyo-e`), Red Paper-cut (`red-paper-cut`), Paper-cut Lightbox (`paper-lightbox`)
- **Print & Printmaking** (6): Risograph Print (`risograph`), Halftone Dossier (`halftone-dossier`), Woodcut Print (`woodcut`), Copperplate Engraving (`copperplate`), Silkscreen Travel Poster (`silkscreen-poster`), Printed Long Take (`printed-long-take`)
- **Graphic & Type** (7): Swiss Motion Graphics (`swiss-motion`), 60s Spy Title Sequence (`spy-title-60s`), Art Deco (`art-deco`), Blueprint / Technical Drawing (`blueprint`), Stained Glass (`stained-glass`), Pictogram Motion (`pictogram-motion`), ASCII / CRT Terminal (`ascii-crt`)
- **Information & Keynote** (8): Data Storytelling (`data-storytelling`), Isometric Infographic (`isometric-infographic`), Dark Tech Keynote (`dark-tech-keynote`), Living Screencast (`living-screencast`), Sci-Fi Hologram HUD (`hologram-hud`), Transit Map (`transit-map`), Isometric Picture Book (`isometric-picture-book`), Circuit Board (`circuit-board`)
- **Cartoon & Anime** (4): 1930s Rubber Hose Cartoon (`rubber-hose`), 80s Cel Anime (`cel-anime-80s`), Sci-Fi Sitcom Toon (`sci-fi-sitcom`), Mid-century Cartoon (`mid-century-cartoon`)
- **Games** (4): 16-bit Pixel RPG (`pixel-rpg-16bit`), HD-2D (`hd-2d`), Microgame Frenzy (`microgame-frenzy`), Game Show Flat (`game-show-flat`)
- **Cinema & Eras** (2): 1920s Silent Film (`silent-film-1920s`), Liminal Found Footage (`liminal-footage`)
- **Materials & 3D** (7): Brick Toy (`brick-toy`), Paper Pop-up Book (`paper-popup`), Tilt-Shift Miniature (`tilt-shift`), Low-poly Isometric Island (`low-poly-isometric`), Glass Product Render (`glass-product`), Memphis Diorama (`memphis-diorama`), Desktop Flythrough (`desktop-flythrough`)

</details>

---

### Step 2: One-Round Brief (No endless interrogation)
Ask everything needed in **one single round in English**, using `ask_question` for structured selections and chat for custom briefs:
1. Necessary story facts, names, or brand rules.
2. User's own materials: voiceover recordings, logos, photos, custom datasets.
3. Language of the film: Always English by default. Only inquire if the user's initial prompt explicitly requested a multilingual or foreign-language film.
4. Storyboard review preference:
   ```json
   {
     "questions": [
       {
         "question": "Would you like to review a detailed storyboard before production begins?",
         "options": ["(Recommended) No, proceed directly with full production", "Yes, generate and show storyboard first"],
         "is_multi_select": false
       }
     ]
   }
   ```
5. Any missing system prerequisites identified by `setup.ps1`.

*Once the user replies, proceed immediately. Do not come back with more rounds of questions.*

---

### Step 3: Treatment (`TREATMENT.md`)
Write `TREATMENT.md` inside the project folder in English before writing drawing code.
Follow [`DIRECTOR.md`](../../DIRECTOR.md):
- **3 Candidate Structures** & Chosen Rationale
- **Logline & Emotional Arc** (Setup → Turn → Ending)
- **Benchmark References** (What to learn vs What NOT to copy)
- **Complete Shot List** (Framing, camera movement, timing, narrative reason)
- **Beat Sheet & Cue Map** (Second-by-second action, musical tempo, sync points)
- **Sound Design Specification** (Foley bed, musical theme, audio cues)

---

### Step 4: Visual Proof & Stills
1. Write the initial rendering engine (`index.html`) implementing:
   ```javascript
   window.DUR = 45.0;              // Total duration in seconds
   window.render = (t) => { ... }; // Pure function of time t
   window.READY = true;            // Flag when assets/fonts are loaded
   ```
2. Render style frames at key timestamps:
   ```powershell
   node core/render/still.mjs "<project-folder>" 2.0 15.0 30.0 --out "<project-folder>/stills"
   ```
3. Show the stills inline in chat:
   `![Styleframe 1](file:///<project-folder>/stills/t_2.00.jpg)`

---

### Step 5: Storyboard Gate (Only if Requested)
- If the user explicitly opted in to review the storyboard, present the shot sequence and **stop turn** to wait for approval.
- Otherwise, **continue directly to production** without interrupting the user.

---

### Step 6: Full Production Pipeline
1. **Voice Tier:** Generate English voiceover via `say.py` (e.g. Kokoro offline or `en-US-AvaNeural`/`en-US-AndrewNeural`) and check word alignment with `faster-whisper`.
2. **Music & SFX Tier:** Synthesize the soundtrack and procedural foley cues via `mix.py`.
3. **Picture Rendering:** Export video stream frame-by-frame via `core/render/video.mjs`:
   ```powershell
   node core/render/video.mjs "<project-folder>" --fps 24 --out "<project-folder>/out/video.mp4"
   ```
4. **Muxing & Audio Mastering:** Run `core/render/mux.sh` via Git Bash to apply two-pass `loudnorm` (−14 LUFS, true peak ≤ −1 dB):
   ```powershell
   & "$env:ProgramFiles\Git\bin\bash.exe" "$LIB/core/render/mux.sh" "<project-folder>/out/video.mp4" "<project-folder>/out/mix.wav" "<project-folder>/<name>.mp4" 24
   ```

---

### Step 7: Self-Verification & Delivery
Verify against [`DIRECTOR.md` §11](../../DIRECTOR.md):
- [ ] Finished video exists and is non-empty (`<project-folder>/<name>.mp4`).
- [ ] Audio meets −14 LUFS (no clipping, English subtitles in sync).
- [ ] Visual style strictly obeys the invariants in `styles/<slug>/STYLE.md`.
- [ ] Standalone English subtitles exported as `.srt`.

Deliver by providing clickable links to the files:
- 🎬 **Final Film:** [`<name>.mp4`](file:///<project-folder>/<name>.mp4)
- 📝 **Treatment Document:** [`TREATMENT.md`](file:///<project-folder>/TREATMENT.md)
- 🖼️ **Stills & Storyboard:** [`stills/`](file:///<project-folder>/stills/)
- 📄 **Subtitles:** [`subtitles.srt`](file:///<project-folder>/subtitles.srt)
