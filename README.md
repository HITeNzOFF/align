# Align (v1.4.0 Beta)
> **Hybrid AI & LOOT Load Order Optimizer and Mod Manager Organizer**

Align is a standalone desktop application and Mod Organizer 2 plugin designed to automatically organize both the **Left Panel (resource overwrite order / separators)** and the **Right Panel (plugin load order)** for Skyrim SE/VR, Fallout 4, and Starfield.

---

## ⚡ Key Features

- **Hybrid LOOT + AI Sorting:** Uses official LOOT `masterlist.yaml` rules, group hierarchies, and binary `TES4` header analysis (`MAST` dependencies) alongside LLM categorization for unlisted or custom mods.
- **Dual-Panel Architecture:**
  - **Left Panel (Mods):** Automatically groups mods, handles loose file overwrites, and generates MO2-compatible separators (`_separator`).
  - **Right Panel (Plugins):** Validates master file dependencies, detects missing/disabled masters, and prevents invalid load orders.
- **Offline DAG Sort:** Instant topological sorting based on master dependencies and official LOOT groups without making API calls.
- **Multi-Manager Support:** Works out-of-the-box with **Mod Organizer 2**, **Vortex**, and direct game **Data** folders.
- **Safety First:** Automated snapshot backups (`.align_backup`) and atomic file writes.

---

## 🚀 Download & Quick Start

1. Go to the **[Releases](https://github.com/HITeNzOFF/align/releases)** page and download `Align.exe`.
2. Launch `Align.exe`.
3. Click **Browse** (or **Detect**) to select your Mod Organizer 2 profile or game folder.
4. Use **DAG Sort** for instant offline sorting or provide an API key (Gemini, OpenAI, DeepSeek, OpenRouter, Ollama) for AI analysis.

---

## 📜 License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
