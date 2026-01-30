# EntelligenceAI CLI

AI-powered code review assistant that helps you catch bugs, improve code quality, and follow best practices - all from your terminal.

[![PyPI version](https://badge.fury.io/py/entelligence-cli.svg)](https://pypi.org/project/entelligence-cli/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🚀 Installation

```bash
pip install entelligence-cli
```

## 📝 Quick Start

### 1. Get Your API Key

Sign up and get your API key: [app.entelligence.ai/settings?tab=api](https://app.entelligence.ai/settings?tab=api)

### 2. Authenticate

```bash
entelligence auth login
```

Paste your API key when prompted.

### 3. Review Your Code

```bash
entelligence review
```

That's it! The CLI will analyze your uncommitted changes (or committed changes if none) and provide intelligent feedback.

## 📖 Usage

### Authentication Commands

```bash
# Log in with your API key
entelligence auth login

# Check authentication status
entelligence auth status

# Log out
entelligence auth logout
```

### Review Commands

```bash
# Review current changes (default: uncommitted, falls back to committed)
entelligence review

# Review only committed changes vs base branch
entelligence review --committed-only

# Review against a specific branch
entelligence review --base-branch develop

# Set review priority
entelligence review --priority high

# Verbose output mode
entelligence review --mode verbose

# Plain text output
entelligence review --plain

# Debug mode
entelligence review --debug
```

### Common Workflows

**Before Committing:**
```bash
git add .
entelligence review
git commit -m "Your message"
```

**Before Creating PR:**
```bash
git checkout -b feature/my-feature
# ... make changes ...
entelligence review --priority high
git push origin feature/my-feature
```


## 🔧 Configuration

### Config File

Configuration is stored at `~/.entelligence/config.json` with secure permissions (read/write for owner only).

### Environment Variables

For non-interactive use, you can set:

- `ENTELLIGENCE_API_KEY` - Your API key (alternative to `entelligence auth login`)

## 💡 Benefits

### For Individual Developers
- Catch bugs before they reach code review
- Learn best practices through AI suggestions
- Save time on code reviews
- Improve code quality consistently

### For Teams
- Maintain consistent code standards
- Reduce code review time
- Improve code quality across the team

## 🆘 Troubleshooting

### Authentication Failed

```bash
# Check your authentication status
entelligence auth status

# If invalid, re-authenticate
entelligence auth logout
entelligence auth login
```

Ensure your API key is valid at [app.entelligence.ai/settings?tab=api](https://app.entelligence.ai/settings?tab=api)

### Connection Timeout

- Check your internet connection
- Try again with `--debug` flag for more information

### No Changes Detected

```bash
# Check what changes are available
git status

# Review only committed changes if you have commits on your branch
entelligence review --committed-only

# Or review against a different base branch
entelligence review --base-branch develop
```

## 📚 Resources

- **Website**: [entelligence.ai](https://entelligence.ai)
- **Documentation**: [docs.entelligence.ai](https://docs.entelligence.ai)
- **Support**: [info@entelligence.ai](mailto:info@entelligence.ai)

## 📄 License

Proprietary - Copyright © 2026 EntelligenceAI. All rights reserved.

## ❓ FAQ

**Q: Is my code stored on your servers?**
A: No, code is only analyzed transiently and not permanently stored.

**Q: Does this work with private repositories?**
A: Yes, all code remains private and secure.

**Q: What languages are supported?**
A: Python, JavaScript, TypeScript, Java, Go, Rust, C++, Ruby, PHP, Swift, Kotlin, and more.

**Q: Can I review specific files only?**
A: Currently reviews are based on Git changes. File-specific reviews coming soon.

---

Made with ❤️ by [EntelligenceAI](https://entelligence.ai)
