# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-26

### Added

- Initial release
- `discord_ask` - Send questions and wait for user response
- `discord_notify` - Send notifications without waiting
- `discord_send_file` - Send files to Discord
- `discord_screenshot` - Take and send desktop screenshots
- `discord_embed` - Send rich embed messages
- Configurable reminder via `DISCORD_REMINDER` environment variable
- Camera emoji reaction for quick screenshots
- Image attachment support with base64 encoding for AI models
- Singleton Discord connection for persistent sessions

### Features

- Async architecture with discord.py
- Full MCP 1.0 compliance
- Optional Pillow dependency for screenshots
- Cross-platform support (Windows, macOS, Linux)
