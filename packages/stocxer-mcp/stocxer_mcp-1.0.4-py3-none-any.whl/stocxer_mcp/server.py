#!/usr/bin/env python3
"""
Stocxer MCP Server
Model Context Protocol server for Stocxer AI Trading Platform
Allows AI assistants (Claude, Cursor, etc.) to access your trading context
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import logging

from dotenv import load_dotenv
load_dotenv()

# MCP SDK imports
try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
except ImportError:
    print("ERROR: MCP SDK not installed. Run: pip install mcp")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stocxer-mcp")

# Initialize server
server = Server("stocxer-mcp")

# Backend API URL - configurable via environment variable
API_BASE_URL = os.getenv("STOCXER_API_URL", "https://stocxer-ai.onrender.com")

def get_browser_token():
    """Automatically detect auth token from browser storage"""
    import platform
    from pathlib import Path
    
    system = platform.system()
    token = None
    
    # Try to read from Chrome/Edge localStorage
    if system == "Darwin":  # macOS
        chrome_path = Path.home() / "Library/Application Support/Google/Chrome/Default/Local Storage/leveldb"
        edge_path = Path.home() / "Library/Application Support/Microsoft Edge/Default/Local Storage/leveldb"
    elif system == "Windows":
        chrome_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data/Default/Local Storage/leveldb"
        edge_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/User Data/Default/Local Storage/leveldb"
    else:  # Linux
        chrome_path = Path.home() / ".config/google-chrome/Default/Local Storage/leveldb"
        edge_path = Path.home() / ".config/microsoft-edge/Default/Local Storage/leveldb"
    
    # Try to extract token from browser storage
    for storage_path in [chrome_path, edge_path]:
        if storage_path.exists():
            try:
                for file in storage_path.glob("*.log"):
                    content = file.read_text(errors="ignore")
                    if "sb-access-token" in content and "stocxer.in" in content:
                        # Extract token (simplified - actual parsing would be more complex)
                        start = content.find("sb-access-token") + 20
                        end = content.find('"', start + 50)
                        if start > 0 and end > start:
                            token = content[start:end]
                            if token.startswith("eyJ"):
                                return token
            except:
                pass
    
    return None

# User authentication token - try env var first, then auto-detect from browser
AUTH_TOKEN = os.getenv("STOCXER_AUTH_TOKEN", "") or get_browser_token() or ""
logger.info(f"🌐 Using API: {API_BASE_URL}")
if not AUTH_TOKEN:
    logger.warning("⚠️  No auth token found. Please login at stocxer.in in your browser, or set STOCXER_AUTH_TOKEN env var.")
else:
    logger.info("✅ Auth token loaded")


# ============================================
# RESOURCES (Read-only data exposed to AI)
# ============================================

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available trading resources"""
    return [
        Resource(
            uri="stocxer://portfolio/summary",
            name="Portfolio Summary",
            description="Overall portfolio value, P&L, and holdings",
            mimeType="application/json",
        ),
        Resource(
            uri="stocxer://positions/current",
            name="Current Positions",
            description="All open positions with live P&L",
            mimeType="application/json",
        ),
        Resource(
            uri="stocxer://orders/today",
            name="Today's Orders",
            description="All orders placed today",
            mimeType="application/json",
        ),
        Resource(
            uri="stocxer://market/indices",
            name="Market Indices",
            description="NIFTY, BANKNIFTY, SENSEX live values",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource via API"""
    import httpx
    try:
        resource_map = {
            "stocxer://portfolio/summary": "/api/portfolio/summary",
            "stocxer://positions/current": "/api/portfolio/positions",
            "stocxer://orders/today": "/api/portfolio/orders",
            "stocxer://market/indices": "/api/market/indices",
        }
        
        endpoint = resource_map.get(uri)
        if not endpoint:
            return json.dumps({"error": "Unknown resource URI"})
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}{endpoint}", timeout=30.0)
            if response.status_code == 200:
                return response.text
            else:
                return json.dumps({"error": f"API returned {response.status_code}"})
    
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        return json.dumps({"error": str(e)})


# ============================================
# TOOLS (Actions AI can perform)
# ============================================

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available trading tools"""
    return [
        Tool(
            name="get_positions",
            description="Get all current open positions with live P&L, entry prices, and quantities",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_orders",
            description="Get all orders (pending, executed, cancelled) with status and details",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_portfolio_summary",
            description="Get complete portfolio summary including funds, margin, P&L, and holdings value",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="analyze_index",
            description="Advanced multi-timeframe ICT analysis with Order Blocks, Fair Value Gaps, liquidity zones, and ML predictions. Returns actionable trading signals with specific option strikes, entry/exit prices, targets, stop loss, best timing, and confidence scores.",
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {
                        "type": "string",
                        "description": "Index to analyze (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX, BANKEX)",
                    }
                },
                "required": ["index"],
            },
        ),
        Tool(
            name="analyze_stock",
            description="Analyze individual stocks using technical indicators (RSI, EMA, VWAP, momentum). Returns BUY/SELL/HOLD signals with confidence, targets, stop loss, and reasoning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., 'SBIN', 'TCS', 'RELIANCE')",
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_stock_quote",
            description="Get live quote for a specific stock/index symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., 'SBIN', 'TCS', 'RELIANCE', 'NIFTY')",
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="search_symbol",
            description="Search for stocks/indices by name or symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (company name or symbol)",
                    }
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution via API calls"""
    import httpx
    
    # Prepare auth headers
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    try:
        if name == "get_positions":
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/api/portfolio/positions", headers=headers, timeout=30.0)
                return [TextContent(type="text", text=response.text)]
        
        elif name == "get_orders":
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/api/portfolio/orders", headers=headers, timeout=30.0)
                return [TextContent(type="text", text=response.text)]
        
        elif name == "get_portfolio_summary":
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/api/portfolio/summary", headers=headers, timeout=30.0)
                return [TextContent(type="text", text=response.text)]
        
        elif name == "analyze_index":
            index = arguments.get("index", "NIFTY")
            symbol_map = {
                "NIFTY": "NSE:NIFTY50-INDEX",
                "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
                "FINNIFTY": "NSE:FINNIFTY-INDEX",
                "MIDCPNIFTY": "NSE:MIDCPNIFTY-INDEX",
                "SENSEX": "BSE:SENSEX-INDEX",
                "BANKEX": "BSE:BANKEX-INDEX"
            }
            symbol = symbol_map.get(index.upper(), "NSE:NIFTY50-INDEX")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/signals/{symbol}/actionable",
                    timeout=120.0
                )
                return [TextContent(type="text", text=response.text)]
        
        elif name == "analyze_stock":
            symbol = arguments.get("symbol", "")
            if not symbol:
                return [TextContent(type="text", text=json.dumps({"error": "Symbol required"}))]
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/screener/stock/{symbol}",
                    timeout=60.0
                )
                return [TextContent(type="text", text=response.text)]
        
        elif name == "get_stock_quote":
            symbol = arguments.get("symbol", "")
            if not symbol:
                return [TextContent(type="text", text=json.dumps({"error": "Symbol required"}))]
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/api/market/quote/{symbol}",
                    timeout=30.0
                )
                return [TextContent(type="text", text=response.text)]
        
        elif name == "search_symbol":
            query = arguments.get("query", "")
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/api/market/search?q={query}",
                    timeout=30.0
                )
                return [TextContent(type="text", text=response.text)]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"})
            )]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]


async def main():
    """Main server entry point"""
    logger.info("🚀 Starting Stocxer MCP Server...")
    logger.info(f"📡 Connected to: {API_BASE_URL}")
    logger.info("ℹ️  Authenticate at https://stocxer.in to enable all features")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("✅ MCP Server running on stdio")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="stocxer-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())


def cli():
    """CLI entry point for console script"""
    asyncio.run(main())
