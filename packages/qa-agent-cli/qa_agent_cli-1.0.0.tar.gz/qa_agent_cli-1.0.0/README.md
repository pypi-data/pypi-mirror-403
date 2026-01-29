
# QA Agent CLI

AI-powered code quality analysis tool for local repositories.

## Features

- 🔍 Scan local codebases for bugs, security vulnerabilities, and maintainability issues
- 🤖 AI-powered analysis using Google Gemini
- 📊 Quality score calculation
- 📄 Export reports as JSON or PDF
- 🎯 Risk explanations with "What can go wrong?" analysis

## Installation

```bash
# 1. Clone or download this folder
cd qa-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Gemini API key
export GEMINI_API_KEY="your-api-key-here"
# On Windows: set GEMINI_API_KEY=your-api-key-here
```

## Usage

### Basic Scan
```bash
python qa_agent.py scan ./path/to/your/repo
```

### With Options
```bash
# Export JSON report
python qa_agent.py scan ./repo --output report.json

# Export PDF report
python qa_agent.py scan ./repo --pdf report.pdf

# Scan specific file types only
python qa_agent.py scan ./repo --extensions py,js,ts

# Set quality threshold (exit code 1 if below)
python qa_agent.py scan ./repo --threshold 70

# Verbose output
python qa_agent.py scan ./repo --verbose
```

### CI/CD Integration
```bash
# Use as quality gate (fails if score < threshold)
python qa_agent.py scan ./repo --threshold 80 --output report.json
echo $?  # 0 = passed, 1 = failed
```

## Get Your API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a new API key
3. Set it as environment variable: `export GEMINI_API_KEY="your-key"`

## Supported File Types

- Python: `.py`
- JavaScript: `.js`, `.jsx`
- TypeScript: `.ts`, `.tsx`
- Config files: `.json`, `.yaml`, `.yml`, `.env`
- Web: `.html`, `.css`

## Output Example

```
╔══════════════════════════════════════════════════════════════╗
║                    QA AGENT SCAN REPORT                       ║
╠══════════════════════════════════════════════════════════════╣
║  Repository: ./my-project                                     ║
║  Files Scanned: 24                                            ║
║  Quality Score: 73/100                                        ║
╠══════════════════════════════════════════════════════════════╣
║  Issues Found: 8                                              ║
║    🔴 High: 2  |  🟡 Medium: 4  |  🟢 Low: 2                  ║
╚══════════════════════════════════════════════════════════════╝
```

## License

MIT