# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- `uv run streamlit run aiyt/main.py` - Run the Streamlit app directly
- `aiyt` - Run via entry point (after installation)
- `uvx aiyt` - Run with uvx without installation
- `uv tool install aiyt` - Install locally as a tool

### Development Tools
- `ruff check` - Run linting (configured in pyproject.toml)
- `ruff format` - Format code
- `pytest` - Run tests (dev dependency)

### Package Management
- `uv sync` - Sync dependencies
- `uv add <package>` - Add new dependency
- `uv add --dev <package>` - Add development dependency

## Architecture

This is a Python Streamlit application for transcribing, chatting with, and summarizing YouTube videos using Google's Gemini AI.

### Core Components

**Entry Point**: `aiyt/launcher.py`
- Simple Click-based CLI that launches the Streamlit app
- Main entry point defined in pyproject.toml as `aiyt = "aiyt.launcher:main"`

**Main Application**: `aiyt/main.py`
- Sets up the Streamlit app with CSS styling
- Handles API key input and YouTube URL validation
- Routes to either caption extraction or audio transcription based on availability

**UI Components**: `aiyt/ui.py`
- `app_header()` - Renders the main header with icon and description
- `input_ui()` - Handles API key, model selection, and YouTube URL input
- `caption_ui()` - Interface for extracting existing captions (srt, txt, ai formatted)
- `transcribe_ui()` - Interface for transcribing audio when captions aren't available
- `chat_ui()` - Chat interface for interacting with transcripts
- `divider()` - Simple divider component

**Core Utilities**: `aiyt/utils.py`
- `add_punctuation()` - Uses Gemini to add punctuation to raw transcripts
- `download_audio_from_yt()` - Downloads lowest quality audio stream to buffer
- `upload_audio_to_gemini()` - Uploads audio to Gemini cloud storage
- `transcribe()` - Transcribes audio using Gemini API
- `consolidate_messages()` - Consolidates consecutive chat messages from same role

### Key Dependencies
- `streamlit` - Web UI framework
- `pytubefix` - YouTube video/audio downloading
- `google-genai` - Google Gemini AI client
- `click` - CLI framework for launcher
- `watchdog` - File system monitoring
- `ruff` - Linting and formatting
- `tomlkit` - TOML file processing

### Data Flow
1. User inputs Gemini API key, model selection, and YouTube URL via `input_ui()`
2. App validates URL and creates YouTube object
3. If captions exist → extract via `caption_ui()` and optionally format with AI
4. If no captions → download audio via `transcribe_ui()` → upload to Gemini → transcribe
5. Display results in Streamlit text area
6. Enable chat interface via `chat_ui()` for transcript interaction

### Configuration
- Ruff linting configured in pyproject.toml with specific ignores for E203, E402, E501, E712, F401, F811
- Project metadata and dependencies managed via pyproject.toml
- CSS styling loaded from `aiyt/style.css`
- Metadata stored in `aiyt/__init__.py`