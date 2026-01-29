# DevOs – Developer Operating System CLI

**Tagline:** One command-line interface to manage your entire development workflow.

## 🚀 Overview

DevOs is a comprehensive CLI tool designed to streamline your development workflow. From project initialization to deployment, DevOs provides a unified interface for common development tasks, AI integration, environment management, and productivity tracking.

## ✨ Features

- **🏗️ Project Management**: Quick project bootstrapping with multiple templates
- **🤖 AI Integration**: Built-in support for OpenAI and Groq AI providers
- **📊 Work Tracking**: Automatic time tracking and productivity reports
- **🔧 Environment Management**: Secure environment variable handling
- **📦 Release Automation**: Simplified versioning and deployment
- **📝 Documentation**: Auto-generated project documentation
- **🎯 Dashboard**: Interactive productivity dashboard
- **⚡ Quick Commands**: Fast access to common development tasks

## 🛠️ Installation

### From PyPI (Recommended)
```bash
pip install devos
```

### From Source
```bash
git clone https://github.com/johndansu/DevOs_Cli.git
cd DevOs_Cli
pip install -e ".[dev]"
```

## 🎯 Quick Start

```bash
# Initialize a new project
devos init python-api

# Start tracking your work session
devos track start

# Configure AI provider
devos ai config --provider groq --api-key your-groq-key

# Set environment variables
devos env set DATABASE_URL postgresql://...

# Generate weekly productivity report
devos report weekly

# Ship a new version
devos ship minor

# Start interactive dashboard
devos dashboard
```

## 📋 Core Commands

### Project Management
- `devos init <template>` - Initialize new project with templates
- `devos project <action>` - Project-specific operations
- `devos quick <task>` - Quick access to common tasks

### AI Integration
- `devos ai chat` - Interactive AI chat interface
- `devos ai config` - Configure AI providers and settings
- `devos groq chat` - Groq-specific AI chat
- `devos groq enhanced` - Enhanced Groq interactions

### Work Tracking
- `devos track start/stop` - Start/stop work sessions
- `devos history` - View work history
- `devos report <type>` - Generate productivity reports

### Environment Management
- `devos env set <key>` - Set environment variables
- `devos env list` - List all environment variables
- `devos env export` - Export environment configuration

### Release & Deployment
- `devos ship <version>` - Automated version bumping and release
- `devos deploy <target>` - Deploy to various platforms

### Documentation
- `devos docs generate` - Auto-generate project documentation
- `devos docs serve` - Serve documentation locally

### Dashboard
- `devos dashboard` - Interactive productivity dashboard
- `devos interactive` - Interactive mode for complex operations

## 🎨 Available Templates

- `python-api` - Python REST API with FastAPI
- `react-app` - React application with TypeScript
- `node-service` - Node.js microservice
- `python-cli` - Python CLI tool
- `static-site` - Static website generator

## ⚙️ Configuration

Configuration is stored in `~/.devos/config.yml`:

```yaml
# Default settings
default_language: python
default_template: python-api

# AI Configuration
ai:
  default_provider: groq
  groq:
    model: "llama-3.1-70b-versatile"
  openai:
    model: "gpt-4"

# Work Tracking
tracking:
  auto_git: true
  auto_commit: true
  session_timeout: 3600

# Reports
reports:
  week_start: monday
  include_git_stats: true
  include_ai_usage: true

# Environment
environment:
  encryption_key_file: ~/.devos/key
  backup_enabled: true
```

## 🔧 Development Setup

```bash
# Clone the repository
git clone https://github.com/johndansu/DevOs_Cli.git
cd DevOs_Cli

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
isort src/

# Run linting
flake8 src/
mypy src/

# Build package
python -m build
```

## 📊 Project Structure

```
DevOs/
├── src/devos/           # Main CLI source code
│   ├── commands/        # Command implementations
│   ├── core/           # Core functionality
│   │   └── ai/         # AI integration modules
│   └── cli.py          # Main CLI entry point
├── landing-page/       # Web dashboard (Next.js)
├── pyproject.toml      # Project configuration
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** - For GPT API integration
- **Groq** - For high-performance AI inference
- **Click** - For the CLI framework
- **Rich** - For beautiful terminal output
- **Next.js** - For the web dashboard

## 📞 Support

- 📧 Email: support@devos.dev
- 🐛 Issues: [GitHub Issues](https://github.com/johndansu/DevOs_Cli/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/johndansu/DevOs_Cli/discussions)

---

**Made with ❤️ by [John Dansu](https://github.com/johndansu)**
