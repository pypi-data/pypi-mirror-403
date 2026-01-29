# GemCLI - Consumer Gemini AI for Code Completions, System Automation, and Image Generation

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built with Rich](https://img.shields.io/badge/Built%20with-Rich-green.svg)](https://github.com/Textualize/rich)

A professional Python command-line interface that leverages Google's consumer Gemini AI for unlimited code completions, autonomous file operations, system automation, and AI image generation - all directly from your terminal.

GemCLI provides a high-fidelity terminal experience with real-time markdown rendering, customizable themes, and browser-based authentication.

---

**PRIVACY & SECURITY**  
This is a CLIENT-SIDE application with NO SERVER component. Your data remains on YOUR machine. All processing is local. Session tokens never leave your system.

---

## Key Features

* **Modern Terminal Interface**: Built with Rich library for beautiful, responsive command-line experience
* **Four Operating Modes**: Chat, Semi-Agent (AI Coding Assistant), Agent (Autonomous), and Image Generation
* **Browser Cookie Authentication**: Automatic session extraction from Chrome, Edge, or Firefox - no API key needed
* **File Operations**: Read, edit, search, and create files through AI commands in Agent/Semi-Agent modes
* **System Command Execution**: Control system operations - open applications, adjust brightness/volume, launch file explorer, manage media playback
* **Git Integration**: Automatic commit, push, and AI-generated commit messages for version control
* **Diff Viewer**: Preview code changes before applying with VS Code or terminal-based diff view
* **Six Theme Profiles**: Customize with Cyan, Pink, Gold, Green, Purple, or White color schemes
* **Asynchronous Architecture**: Non-blocking API communication built on asyncio
* **Complete Privacy**: Client-side only - your session tokens never leave your local machine

---

## Modes & Capabilities

GemCLI offers four distinct operating modes, each tailored for specific use cases:

| Mode | Ask/Response | Read Files | Edit Files | Workspace Search | Autonomous | System Cmds |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Chat** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Semi-Agent** | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ |
| **Agent** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Image Gen** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |

### Mode Descriptions

#### Chat Mode
Basic conversational AI interface. Ask questions, receive answers, and engage in natural conversations with Gemini.

#### Semi-Agent Mode (AI Coding Assistant)
Enhanced mode where you specify files to work with. Gemini can:
- Read files you specify
- Suggest code modifications
- Apply changes with your approval
- Show diffs before committing
- Integrate with git workflow
- Execute system commands:
  - Open/close applications (Chrome, Notepad, Calculator, etc.)
  - Adjust brightness and volume
  - Launch file explorer
  - Control media playback
  - System shutdown (when explicitly requested)

#### Agent Mode (Autonomous)
Fully autonomous coding assistant. Gemini can:
- Search your entire workspace for relevant files
- Read any files it determines necessary
- Make coordinated changes across multiple files
- Work independently without file specifications
- Handle complex multi-file refactoring
- Execute system commands:
  - Open/close applications
  - Adjust brightness and volume
  - Launch file explorer
  - Control media playback
  - System shutdown (when explicitly requested)

#### Image Generation Mode
Create AI-generated images from text descriptions with customizable save locations.

---

## Getting Started

### Prerequisites

* Python 3.8 or higher installed on your system
* Active Gemini account - Must be logged into gemini.google.com in Chrome, Edge, or Firefox
* Internet connection for API communication

### Installation

#### Option 1: Install from PyPI (Quick Start)

Standard pip installation:
```bash
pip install gemcli
```

After installation, use one of these commands to start:
```bash
# If PATH is configured:
gemcli

# If gemcli command not found (use this if above fails):
python -m gemini_cli
```

#### Option 2: Install with pipx (Recommended - Automatic PATH Setup)

pipx automatically handles PATH configuration so `gemcli` works immediately:

```bash
# Install pipx if you don't have it
pip install pipx
pipx ensurepath

# Install GemCLI
pipx install gemcli
```

Close and reopen your terminal, then start GemCLI:
```bash
gemcli
```

#### Option 3: Install from Source

1. Clone the repository and navigate to directory:
   ```bash
   git clone https://github.com/89P13/GemCLI.git
   cd GemCLI
   ```

2. Set up a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # Activate on Windows:
   venv\Scripts\activate
   
   # Activate on macOS/Linux:
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run GemCLI:
   ```bash
   python gemini_cli.py
   
   # OR install locally and use the gemcli command:
   pip install -e .
   gemcli
   ```

### First-Time Setup

When you launch GemCLI for the first time:

1. **Automatic Authentication**: GemCLI will automatically detect and extract your Gemini session from your browser (Chrome, Edge, or Firefox). Ensure you are logged into gemini.google.com in one of these browsers.

2. **Mode Selection**: You will be presented with a menu to select your operating mode:
   - Chat - Basic conversational AI
   - Semi-Agent - AI coding assistant with file operations
   - Agent - Autonomous coding assistant
   - Image Generation - Create AI images

3. **Ready to Use**: Start typing your queries or commands. GemCLI will respond with formatted output directly in your terminal.

---

## Usage Guide

### Starting GemCLI

Launch the application:
```bash
gemcli
```

### Available Commands

| Command | Description |
|:---|:---|
| `/help` | Display help with mode capabilities and commands |
| `/exit` or `/quit` | Safely exit the current mode |
| `/clear` | Clear the terminal screen |
| `/mode` | Switch between operating modes |
| `/status` | Show git repository status (Semi-Agent/Agent modes) |
| `/commit` | Commit changes with AI-generated message (Semi-Agent/Agent modes) |
| `/push` | Push commits to remote repository (Semi-Agent/Agent modes) |

### File Path Autocomplete

In Semi-Agent and Agent modes, type `/` to trigger workspace file path autocomplete. Example:
```
You: Read /gemini_cli.py
```

---

## Settings

Access via main menu **Settings** option:

### Theme Customization
Choose from 6 professional color schemes:
- Cyan
- Pink
- Gold
- Green
- Purple
- White

### Git Integration
Configure automatic version control:
- Enable/Disable: Toggle git integration on or off
- Commit Mode: Choose immediate or on-exit commit behavior
- Auto Push: Automatically push commits after committing
- Branch Prompts: Configure branch creation and selection prompts
### Diff Viewer
Preview code changes before applying:
- VS Code: Open diffs in VS Code editor
- System Default: Use system default diff tool
- Terminal Only: Display diffs directly in terminal

### Image Generation
Configure image output settings:
- Save Path: Specify directory for generated images
- Filename Pattern: Customize image naming convention

---

## Project Structure

```text
CliTool/
├── gemini_cli.py      # Core application logic and UI
├── requirements.txt   # Python package dependencies
├── README.md          # Main documentation
├── QUICKSTART.md      # Quick reference guide
├── GIT_INTEGRATION.md # Git workflow documentation
└── INSTALL.md         # Detailed installation instructions
```

---

## Example Workflows

### Coding with Semi-Agent Mode
```
You: Read /src/app.py
Gemini: [Reads and analyzes file content]
You: Add error handling to the main function
Gemini: [Suggests changes with diff preview]
You: [Review and approve changes]
Gemini: [Applies modifications to file]
```

### Autonomous Agent Mode
```
You: Refactor the authentication system to use JWT tokens
Gemini: [Searches workspace for relevant files]
Gemini: [Reads necessary files and plans changes]
Gemini: [Makes coordinated modifications across multiple files]
Gemini: [Displays summary of all changes made]
```

### System Commands (Agent/Semi-Agent Mode)
```
You: lower the brightness
Gemini: Setting brightness to 30%
        [Executes system command]
        Command executed successfully

You: open chrome
Gemini: Opening Chrome browser
        [Executes system command]
        Command executed successfully

You: increase volume
Gemini: Increasing system volume
        [Executes system command]
        Command executed successfully
```

**Available System Commands:**
- Open/close applications (Chrome, Notepad, Calculator, File Explorer, etc.)
- Adjust brightness and volume levels
- Control media playback
- System shutdown (when explicitly requested)

For detailed system command documentation, refer to SYSTEM_COMMANDS.md

### Image Generation
```
You: Create a futuristic cyberpunk cityscape at night
Gemini: [Generates image and saves to configured directory]
```

---

## Troubleshooting

**Command Not Found: 'gemcli' is not recognized**

If `gemcli` shows an error after pip installation, you have three options:

**Quick Fix (No configuration needed):**
```bash
python -m gemini_cli
```

**Permanent Fix (Recommended):**
```bash
# Uninstall current installation
pip uninstall gemcli

# Reinstall with pipx (handles PATH automatically)
pip install pipx
pipx ensurepath
pipx install gemcli
```
Close and reopen terminal, then `gemcli` will work.

**Manual PATH Setup:**
Add Python's Scripts directory (usually `C:\Users\YourName\AppData\Local\Programs\Python\Python3X\Scripts\`) to your system PATH via System Properties > Environment Variables, then restart terminal

**Authentication Issues**

* Browser Lock: Ensure your browser is closed if the application cannot access the cookie database
* Login Status: Verify your session is active by visiting gemini.google.com
* Permissions: On Windows, try running your terminal as Administrator

**File Operations**

* Use absolute or relative paths from your current directory
* Type `/` to trigger autocomplete in Agent/Semi-Agent modes
* Review git status before making extensive changes

---

## License & Disclaimer

License: Distributed under the MIT License. See LICENSE file for details.

Disclaimer: This is an unofficial tool for educational and personal use. It utilizes a web-based API wrapper and may be subject to changes based on Google platform updates. Use responsibly and in accordance with Google's Terms of Service.

---

Made by 89P13

---
