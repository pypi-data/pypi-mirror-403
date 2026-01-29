# Stocxer MCP - AI Trading Assistant

Connect your Stocxer trading account to AI assistants like Claude Desktop, Cursor, and Windsurf. Get instant access to your portfolio, positions, orders, and powerful market analysis through natural conversation.

## 🌟 Features

- 📊 **Portfolio Access** - View positions, orders, P&L in real-time
- 🧠 **Smart Analysis** - ICT concepts, Order Blocks, Fair Value Gaps
- 📈 **Stock Screener** - Technical analysis with BUY/SELL signals
- 💬 **Natural Language** - Just ask your AI assistant
- 🔐 **Secure** - No credentials stored locally, uses Stocxer backend

## 🚀 Quick Install

### One-Line Installation (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/fdscoop/stocxer-mcp/main/install.sh | bash
```

### Manual Installation

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/fdscoop/stocxer-mcp.git
   cd stocxer-mcp
   ```

2. **Run installer**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Restart Claude Desktop**
   - Completely quit (Cmd+Q on Mac)
   - Reopen Claude Desktop
   - Look for 🔌 icon at bottom

### pip Installation (Alternative)

```bash
pip install stocxer-mcp
```

Then configure manually or run `install.sh`.

## 🔐 Authentication

1. Visit **[https://stocxer.in](https://stocxer.in)**
2. Login with your Fyers credentials
3. MCP server automatically uses your authenticated session
4. No need to copy tokens or configure credentials

## 💬 Example Conversations

Once installed, ask Claude:

**Portfolio & Positions**
- *"What are my current positions?"*
- *"Show me today's P&L"*
- *"Do I have any NIFTY positions open?"*

**Market Analysis**
- *"Analyze NIFTY using ICT concepts"*
- *"What's the market trend for BANKNIFTY?"*
- *"Should I buy RELIANCE? Give me technical analysis"*

**Option Trading**
- *"What strike should I trade for NIFTY calls?"*
- *"Show me high OI strikes for BANKNIFTY"*
- *"What's the PCR for FINNIFTY?"*

**Advanced Queries**
- *"Based on my positions, should I hedge with options?"*
- *"Compare my open positions with current market signals"*
- *"What's the probability analysis for NIFTY today?"*

## 🔧 Supported AI Assistants

### ✅ Claude Desktop (Auto-configured)
Just run `install.sh` and restart Claude.

### ✅ Cursor IDE
Add to settings:
```json
{
  "mcp": {
    "servers": {
      "stocxer": {
        "command": "python3",
        "args": ["/path/to/stocxer_mcp/server.py"]
      }
    }
  }
}
```

### ✅ Windsurf
Same config as Cursor.

### ✅ Cline/Roo-Cline (VS Code)
Add to VS Code settings:
```json
{
  "cline.mcpServers": {
    "stocxer": {
      "command": "python3",
      "args": ["/path/to/stocxer_mcp/server.py"]
    }
  }
}
```

## 🛠️ Advanced Configuration

### Custom Backend URL

Create `.env` file in the stocxer-mcp directory:
```bash
STOCXER_API_URL=https://your-custom-backend.com
```

Default: `https://stocxer-ai.onrender.com`

### Development Mode

For local testing:
```bash
STOCXER_API_URL=http://localhost:8000
```

## 📖 Available Tools

- `get_positions` - Current open positions
- `get_orders` - Order history
- `get_portfolio_summary` - Complete portfolio overview
- `analyze_index` - Multi-timeframe ICT analysis for indices
- `analyze_stock` - Technical analysis for stocks
- `get_stock_quote` - Live stock prices
- `search_symbol` - Find stock symbols

## 🔒 Security & Privacy

- **No credentials stored** - MCP client is just a thin wrapper
- **All logic on backend** - Your trading algorithms stay private
- **Token-based auth** - Secure session management via Supabase
- **Read-only by design** - Cannot place orders (by design for safety)

## 🐛 Troubleshooting

**MCP server not showing in Claude?**
1. Check config: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json`
2. Verify Python path: `which python3`
3. Test server: `python3 stocxer_mcp/server.py`

**Authentication errors?**
1. Login at https://stocxer.in
2. Check if Fyers token is valid (check dashboard)
3. Token expires after ~24 hours - just re-login

**Connection errors?**
1. Check backend status: `curl https://stocxer-ai.onrender.com/health`
2. Verify internet connection
3. Check MCP logs in Claude

## 📝 License

MIT License - See LICENSE file

## 🤝 Support

- **Documentation**: [https://stocxer.in/docs](https://stocxer.in/docs)
- **Issues**: [GitHub Issues](https://github.com/fdscoop/stocxer-mcp/issues)
- **Website**: [https://stocxer.in](https://stocxer.in)

## ⚠️ Disclaimer

This software is for educational and research purposes. Trading involves risk. Past performance is not indicative of future results. Always do your own research before trading.

---

Made with ❤️ by Stocxer AI
