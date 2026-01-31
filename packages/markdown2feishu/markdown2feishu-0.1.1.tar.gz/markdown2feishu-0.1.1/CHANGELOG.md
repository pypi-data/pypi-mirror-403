# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-29

### Added

- Initial release
- Markdown to Feishu blocks converter using mistune
- Support for headings (H1-H6), paragraphs, lists, tables, code blocks
- Inline formatting: bold, italic, strikethrough, links, inline code
- FeishuClient for creating documents and sending webhooks
- Configuration via environment variables, TOML files, or code parameters
- CLI tool `feishu-md` for pushing files from command line
