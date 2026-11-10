# Lemo-Opuscar for Antigravity

> [!IMPORTANT]
> ### 🌟 Shoutout & Full Attribution to LemoLab
> **The original project, film styles, and creative concepts belong entirely to [LemoLab](https://github.com/lemomo-ai) ([lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)).**
> We do **not** claim credit for the invention or creation of these film styles, procedural engines, or the original directing methodologies. All 66 film styles, audio physical modeling, and deterministic code-rendering techniques are the original work of **LemoLab**.
>
> **What this repository is:**
> This repository is a dedicated rewrite and adaptation re-architected specifically for the **Antigravity** environment. We have re-engineered the workflow into a native **Antigravity Plugin** and skill, adding native PowerShell scripts (`setup.ps1`), Antigravity `ask_question` interactive brief dialogs, asynchronous execution with reactive task wakeups, and tailored agent guidelines.

---

## Overview
**Lemo-Opuscar for Antigravity** is a code-first filmmaking studio and autonomous directing workflow packaged as a native **Antigravity Plugin**. It enables Antigravity AI agents to direct, write, score, render, and mix complete short films deterministically using code—WebGL/Canvas rendering, procedural audio synthesis, neural text-to-speech, and automated FFmpeg mastering—without relying on generative video diffusion models. Re-architected for Windows and PowerShell environments, it integrates natively with Antigravity's agent tools, interactive UI prompts, and asynchronous background execution.

## Features
- **Deterministic Code-Rendered Filmmaking:** Produces complete, high-fidelity short films frame-by-frame via HTML5 Canvas, WebGL (Three.js), and headless Chromium rendering (`core/render/`).
- **66 Distinct Cinematic & Graphic Styles:** Includes all 66 production-ready visual styles created by LemoLab across 10 genres:
  - *Edit & Documentary* (Caption News, 1920s Newsreel, Visual Investigation, Time-lapse Symphony...)
  - *Evidence Films* (Satellite Briefing, LiDAR Survey, Exploded Teardown, Engineering Board...)
  - *Hand-drawn & Painting* (Impasto Oil Painting, Watercolor Brush, Chinese Ink Wash, Chalkboard...)
  - *East Asian Traditions* (Ukiyo-e, Shadow Puppetry, Red Paper-cut, Paper-cut Lightbox)
  - *Print & Printmaking* (Risograph Print, Halftone Dossier, Woodcut, Copperplate Engraving...)
  - *Graphic & Type* (Swiss Motion Graphics, 60s Spy Title Sequence, Blueprint, ASCII/CRT...)
  - *Information & Keynote* (Data Storytelling, Hologram HUD, Dark Tech Keynote, Screencast...)
  - *Cartoon & Anime* (Rubber Hose, 80s Cel Anime, Mid-century Cartoon...)
  - *Games* (16-bit Pixel RPG, HD-2D, Microgame Frenzy, Game Show Flat)
  - *Materials & 3D* (Brick Toy, Tilt-Shift Miniature, Low-poly Isometric Island, Glass Product...)
- **Antigravity Plugin Architecture:**
  - **Native Plugin Manifest (`plugin.json`):** Packaged at the repository root for seamless discovery, loading, and management in Antigravity.
  - **Antigravity Skill Definition (`skills/lemo-opuscar/SKILL.md`):** Complete workflow instructions teaching the agent how to direct films in Antigravity.
  - **Interactive Questions (`ask_question`):** Streamlined single-round brief capture directly within Antigravity UI with recommended options and structured inputs.
  - **Asynchronous Execution & Reactive Wakeups:** Frame rendering (`video.mjs`) and dependency installations run asynchronously as background tasks (`WaitMsBeforeAsync: 500`) with automatic wakeups, eliminating polling loops.
  - **Windows & PowerShell First:** Native PowerShell integration via `setup.ps1` helper and proper Git Bash shims for FFmpeg muxing, avoiding MSYS/bash path mangling issues.
  - **Subagent Delegation:** Built-in hooks to delegate research to the read-only `research` subagent and reference assets to `image-generator`.
  - **Strict English Default Policy:** Conversation, treatments, voiceover scripts, cue maps, and subtitles default strictly to English for consistent agent workflows.
- **Three-Tier Modular Dependency System:**
  - *Core Tier:* Node 20+, Playwright headless shell, and Python virtual environment for rendering.
  - *Voice Tier:* Offline neural TTS (Kokoro ONNX) and speech alignment verification (faster-whisper).
  - *Music & SFX Tier:* Algorithmic audio synthesis, physical modeling (`pluck.py`), and procedural foley cues (`sfx.py`).
- **Full Directing Pipeline (`DIRECTOR.md` & `TECHNIQUE.md`):** Complete automated workflow covering Treatment design (`TREATMENT.md`), beat sheet mapping, visual proof styleframes, camera choreographies, and loudness-compliant (−14 LUFS) multi-pass muxing.

## Installation & Usage

### Prerequisites
Ensure the following tools are installed on your host system:
- **Node.js:** v20+ (`npm` included)
- **FFmpeg:** v7+ (with `libmp3lame` and `loudnorm` filter enabled, on system `PATH`)
- **Python:** v3.11+ (or `uv`)
- **Git for Windows:** With Git Bash (`bash.exe`) installed

### Installing the Antigravity Plugin

#### Option 1: Global Plugin Installation (Recommended)
Clone this repository directly into your Antigravity plugins directory:
```powershell
git clone https://github.com/sanjan-github/lemo-opuscar-for-Antigravity.git "$env:USERPROFILE\.gemini\config\plugins\lemo-opuscar"
```
Antigravity automatically detects `plugin.json` and mounts the `lemo-opuscar` skill globally across all your projects.

#### Option 2: Active Project Customization
Clone or copy this repository into your active Antigravity workspace or link it under `.agents/`:
```powershell
git clone https://github.com/sanjan-github/lemo-opuscar-for-Antigravity.git
```

### Initializing Environment & Dependencies
Inspect prerequisites and install the core rendering dependencies via PowerShell:
```powershell
# Check prerequisites and installed tiers
& "skills\lemo-opuscar\scripts\setup.ps1"

# Install Core dependencies (Playwright headless shell + Python core venv)
& "skills\lemo-opuscar\scripts\setup.ps1" deps

# Optional: Add Voice and Music tiers when required
& "skills\lemo-opuscar\scripts\setup.ps1" deps voice
& "skills\lemo-opuscar\scripts\setup.ps1" deps music
```

### Directing a Film with Antigravity
With the plugin active in Antigravity, prompt your agent naturally:
- *"Direct a 30-second short film in an oil painting style about deep-sea exploration."*
- *"Create a satellite briefing explainer film analyzing the terrain of Olympus Mons."*
- *"Make an architectural blueprint animation breaking down modern skyscraper engineering."*
- *"Show me all available film styles in the Lemo-Opuscar library."*

The Antigravity agent will automatically invoke the `lemo-opuscar` skill, conduct a structured 1-round brief, draft `TREATMENT.md`, render preview styleframes, synthesize voice and score, and output a mastered MP4 film.

## Acknowledgments
This project is an adaptation and rewrite of [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar), originally created by **LemoLab**. It has been re-architected from the ground up for Antigravity.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
