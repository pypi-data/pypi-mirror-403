# AI Accounting CLI (Clerk)

> Talk to your books like you're texting a friend 💬

A delightfully simple command-line tool that lets you manage your business finances using plain English. No accounting jargon required.

## What is this?

Instead of clicking through menus and filling out forms, just tell the AI what you want:

```
"Show me my expenses for last month"
"Create an invoice for John Smith, $1,500 for consulting"
"What's my bank balance?"
"Import transactions from @transactions.csv"
```

The AI understands what you mean, handles all the accounting details, and gives you back exactly what you need - whether that's a quick answer, a beautiful chart, or a professional PDF report.

## Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install faxter-clerk

# Or install from source
cd ai_account/cli
pip install -e .
```

### First Run

```bash
# Just run it - you'll be guided through setup
clerk

# Or run as a Python module
python -m faxter_clerk
```

The first time you run it, you'll:
1. Enter your email address
2. Receive a 6-digit code via email
3. Enter the code (that's it - no password needed!)
4. Optionally save your credentials for next time

### Your First Query

```
You: hello
Assistant: 👋 Hi! I'm your AI accounting assistant...

You: show my bank accounts
Assistant:
# Bank Accounts
- **GTB Checking** - ₦235,000
- **Savings Account** - ₦1,250,000
...

You: create an invoice for ABC Corp, $5000 for consulting
Assistant: ✅ Invoice created! ...
```

## What Can It Do?

### 📊 Financial Queries
Ask questions in plain English:
- "What were my top expenses in Q4?"
- "Show me profit and loss for last month"
- "What's the balance on my checking account?"
- "List all unpaid invoices"

### ⚡ Actions & Transactions
Tell it what to do:
- "Create an invoice for Jane Doe, $2,000 for design work"
- "Record a ₦50,000 payment to rent"
- "Purchase 10 laptops at $800 each"
- "Pay the ABC Corp invoice"

### 📈 Reports & Exports
Get professional outputs:
- "Generate balance sheet as PDF"
- "Create comprehensive financial report"
- "Export my transactions to Excel"
- "Show me cash flow as a bar chart"

### 📎 File Processing
Upload and process files:
- "Import transactions from @bank-statement.csv"
- "Extract data from @invoice.pdf"
- "Process receipts @receipt1.jpg @receipt2.jpg"

## Real Examples

### Viewing Transactions
```
You: show my transactions for last week
```

### Creating Invoices
```
You: create invoice for Acme Corp
      $15,000 for website development
      due in 30 days
```

### Uploading Files
```
You: import @transactions.csv
📎 Auto-attaching 1 file(s):
  ✓ transactions.csv (45.2KB)Assistant: ✅ Imported 5 transactions

You: generate balance sheet as PDF
📄 Files generated:
  - balance-sheet-2024-01.pdf
    URL: https://ai.faxter.com/files/balance-sheet-2024-01.pdf
```

### Getting Help
```
You: help
# Shows all available commands

You: what can you do?
# Shows examples and capabilities
```

## CLI Commands

Type these special commands in the interactive mode:

| Command | What it does |
|---------|--------------|
| `help` | Show available commands and examples |
| `files` | List files in current directory |
| `capabilities` | Show all available operations |
| `clear` | Clear the screen |
| `new` | Start a new conversation |
| `exit` | Quit (or use `quit`, `q`) |

## File Upload Methods

### Method 1: @ Syntax (Recommended)

Just mention files with `@` - they'll be auto-attached!

```
You: import @transactions.csv
You: analyze @data.xlsx and @report.pdf
You: process @~/Documents/bank-statement.xlsx
```

### Method 2: Upload Command

```
You: upload transactions.csv
💬 Enter your message about these files:
You: Import these transactions
```

### Method 3: Command Line

```bash
clerk --message "import these" --files transactions.csv
```

## Advanced Usage

### Single Query Mode

```bash
# Quick one-off queries without interactive mode
clerk --message "show my balance"
clerk --message "create invoice for John, $500"
```

### Local Development

```bash
# Connect to local development server
clerk --api-url http://localhost:8000
```

### Performance Metrics

```bash
# See how long queries take and AI token usage
clerk --show-metadata
```

### Managing Credentials

```bash
# Force new login
clerk --login

# Clear saved credentials
clerk --logout
```

## Features

### 🔐 Secure Authentication
- **Passwordless** - Just email + OTP code
- **Auto-save** - Remember your login
- **Auto-refresh** - Tokens refresh automatically

### ⚡ Real-Time Progress
- See live updates as the AI works
- Progress messages replace each other (clean!)
- Works like Slack typing indicators

### 🎨 Beautiful Output
- Markdown rendering with **bold**, *italic*, `code`
- Tables, lists, headers
- Charts and visualizations
- Professional PDF reports

### 📎 Smart File Handling
- Drag and drop file paths
- Auto-detect file types
- Support for CSV, Excel, PDF, images
- 10MB file size limit

### 💡 Intelligent Suggestions
- Get follow-up suggestions after each query
- Context-aware recommendations
- Learn what's possible

## Installation Details

### Minimum Requirements
```bash
pip install requests
```

### Recommended Setup
```bash
pip install requests rich sseclient-py
```

- **rich** - Beautiful markdown rendering and formatting
- **sseclient-py** - Real-time progress updates via Server-Sent Events

### What You Get

**With basic install (requests only):**
- ✅ Full functionality
- ✅ File uploads
- ✅ All commands
- ⚠️ Basic text formatting (ANSI codes)
- ⚠️ No real-time progress

**With recommended setup:**
- ✅ Everything above, plus:
- ✅ Beautiful markdown rendering
- ✅ Real-time progress updates
- ✅ Better tables and formatting

## Configuration

### API URL
```bash
# Default: Production (https://ai.faxter.com)
clerk

# Local development
clerk --api-url http://localhost:8000

# Custom server
clerk --api-url https://your-server.com
```

### Credentials Storage
Credentials are saved to `~/.accounting_cli/credentials.json` with secure file permissions (`0600`).

## Troubleshooting

### "Could not connect to server"
```bash
# Check your internet connection
ping ai.faxter.com

# Try specifying the URL explicitly
clerk --api-url https://ai.faxter.com
```

### "Authentication failed"
```bash
# Clear saved credentials and try again
clerk --logout
clerk --login
```

### "File not found"
```bash
# Use the 'files' command to see available files
You: files

# Or use absolute paths
You: import @/full/path/to/file.csv
```

### SSE/Progress not working
```bash
# Install the SSE client
pip install sseclient-py

# Restart the CLI
clerk
```

## Tips & Tricks

### 1. Use Arrow Keys
- ↑/↓ to navigate command history
- Your previous queries are saved

### 2. Be Natural
Don't overthink it - just ask naturally:
- ✅ "What did I spend on food last month?"
- ✅ "Create invoice for Sarah, $1000"
- ❌ Don't need: "Execute query SELECT * FROM transactions..."

### 3. Attach Files Easily
- Use `@filename` for files in current directory
- Use `@~/path` for home directory
- Use `files` command to see what's available

### 4. Start Fresh
Use `new` command to start a new conversation if context gets confusing

### 5. Explore Capabilities
Type `capabilities` to see everything the system can do

## What Makes This Special?

### No Accounting Knowledge Required
You don't need to know debits from credits. Just describe what happened in plain English:
- "I paid $500 for rent"
- "Customer paid their invoice"
- "Bought 10 laptops"

The AI handles all the accounting rules automatically.

### Conversational
It remembers context within a session:
```
You: show my checking account
Assistant: GTB Checking - ₦235,000

You: what about savings?
Assistant: Savings Account - ₦1,250,000
```

### Multi-Format Output
Get data however you need it:
- Quick text answers
- Beautiful charts and graphs
- Professional PDF reports
- Excel spreadsheets for further analysis

## Support & Feedback

- 🐛 Found a bug? Open an issue on GitHub
- 💡 Have a suggestion? We'd love to hear it!
- 📧 Need help? Check the docs or ask in the CLI with `help`

## License

MIT License - see [LICENSE](LICENSE) file for details

## Credits

Built with ❤️ using:
- FastAPI for the backend
- OpenAI GPT-4 for AI capabilities
- Rich for beautiful terminal formatting
- Server-Sent Events for real-time updates
