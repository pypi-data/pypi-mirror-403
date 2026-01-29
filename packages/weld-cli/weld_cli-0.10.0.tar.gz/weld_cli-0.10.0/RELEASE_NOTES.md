### Added
- Telegram bot support is now included by default (no longer requires `telegram` extra)
- Telegram bot extended prompt detection for y/n confirmations, default prompts ([Y/n], [y/N]), Continue?/Proceed?/Apply? questions, and arrow-key menus
- Universal `/weld <command>` for running any weld subcommand via Telegram
- Document upload handling with automatic save to `.weld/telegram/uploads/`
- Reply-to-document auto-injection of uploaded file path in commands
- Output file detection with Download button for created files
- Project sync method for Telegram bot to synchronize config projects with database on startup
- Telegram bot: runs table pruning to limit stored runs per user
- Telegram user management commands: `weld telegram user add/remove/list`
- Auto-prompt to install weld globally during `weld telegram init`
- `--skip-hooks` flag for `weld commit` to bypass pre-commit hooks (useful for Telegram bot or CI)
- Interactive prompt support in Telegram bot with inline keyboard buttons for command options
- `weld telegram whoami` command to show bot identity and authentication status
- `weld telegram doctor` command to validate Telegram bot setup and environment
- `weld telegram projects add` command to register projects for Telegram bot access
- `weld telegram projects remove` command to unregister projects
- `weld telegram projects list` command to show registered projects
- `weld telegram` command group for remote bot interaction
- Telegram bot commands: /doctor, /plan, /interview, /implement, /commit for remote weld execution
- Telegram bot `/status` command to view current run, queue, and recent history
- Telegram bot `/cancel` command to abort active runs and clear pending queue
- `/use` command for Telegram bot to switch between configured projects
- Rate-limited message editor for Telegram with exponential backoff retry
- Telegram message formatting utilities with proper Unicode chunking support
- Per-chat FIFO queue system for Telegram bot to ensure ordered run processing
- Async command runner for Telegram bot with streaming output and timeout handling
- `TelegramFileError` and `TelegramRunError` exception classes for more specific error handling in Telegram bot
- File path validation for Telegram bot `/fetch` and `/push` commands with path traversal protection
- SQLite state persistence for Telegram bot with user contexts, projects, and command run tracking
- Telegram bot configuration with user authentication and project registration
- Initial Telegram bot integration module structure

### Changed
- `weld plan` default output now saves to same directory as input file with `_PLAN.md` suffix
  - Example: `weld plan /path/to/SPEC.md` → `/path/to/SPEC_PLAN.md`
  - Previously saved to `.weld/plan/{filename}-{timestamp}.md`
- `weld implement --autopilot` now respects `--no-review` flag (previously ignored)
- `weld implement --autopilot` now displays all active options (autopilot, auto-commit, no-review)
- Telegram support is now included in standard installation (no longer requires `weld[telegram]` extra)

### Fixed
- Telegram bot status output now shows error messages instead of truncating them
- Telegram bot now shows clear feedback after selecting prompt options ("Command continuing...")
- Telegram bot prompt message is updated with final result when command completes
- Telegram bot now persists `started_at` timestamp when run transitions from pending to running
