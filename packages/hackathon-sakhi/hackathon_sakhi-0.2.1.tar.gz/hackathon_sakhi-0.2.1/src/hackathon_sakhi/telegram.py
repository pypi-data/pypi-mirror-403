#!/usr/bin/env python3
"""
Telegram MCP Server for Hackathon Sakhi.

Sends alerts and messages via Telegram bot.

Environment Variables:
    TELEGRAM_BOT_TOKEN: Your Telegram bot token (required)
    TELEGRAM_CHAT_ID: Default chat ID to send messages (required)
    LOG_LEVEL: Logging level (optional, default: INFO)
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


@dataclass
class TelegramMessage:
    """Data class for Telegram message."""
    text: str
    chat_id: str
    parse_mode: str = "HTML"


class TelegramServiceInterface(ABC):
    """Abstract interface for Telegram services."""
    
    @abstractmethod
    def send_message(self, message: TelegramMessage) -> bool:
        """Send message via Telegram."""
        pass


class TelegramBotService(TelegramServiceInterface):
    """Telegram Bot API implementation."""
    
    def __init__(self, bot_token: str, default_chat_id: str):
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def send_message(self, message: TelegramMessage) -> bool:
        """Send message via Telegram Bot API."""
        try:
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                "chat_id": message.chat_id or self.default_chat_id,
                "text": message.text,
                "parse_mode": message.parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Message sent successfully to chat {message.chat_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Telegram message: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending message: {str(e)}")
            return False


class TelegramMCPServer:
    """MCP Server for Telegram messaging."""
    
    def __init__(self, telegram_service: TelegramServiceInterface):
        self.telegram_service = telegram_service
        self.mcp = FastMCP("hackathon-telegram-actions")
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.mcp.tool()
        def send_hackathon_telegram_message(message: str) -> str:
            """
            Send a Telegram message using a bot.
            Use this for sending alerts, notifications, or safety messages.
            
            Args:
                message: Message to send on Telegram
                
            Returns:
                A confirmation message
            """
            self.logger.info(f"Tool called: send_telegram_message")
            
            telegram_msg = TelegramMessage(text=message, chat_id="")
            success = self.telegram_service.send_message(telegram_msg)
            
            if success:
                return "Telegram message sent successfully ✅"
            else:
                return "Failed to send Telegram message ❌"
    
    def run(self):
        """Start the MCP server."""
        self.logger.info("Starting Telegram MCP Server...")
        self.mcp.run(transport="stdio")


def setup_logging(log_level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def main():
    """Main entry point for the Telegram MCP server."""
    try:
        # Load environment variables
        load_dotenv()
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not bot_token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN not found. "
                "Please set it: export TELEGRAM_BOT_TOKEN=your_token"
            )
        
        if not chat_id:
            raise ValueError(
                "TELEGRAM_CHAT_ID not found. "
                "Please set it: export TELEGRAM_CHAT_ID=your_chat_id"
            )
        
        log_level = os.getenv("LOG_LEVEL", "INFO")
        setup_logging(log_level)
        
        # Initialize services
        telegram_service = TelegramBotService(bot_token, chat_id)
        server = TelegramMCPServer(telegram_service)
        
        # Start server
        server.run()
        
    except Exception as e:
        logging.error(f"Failed to start Telegram server: {str(e)}")
        raise


if __name__ == "__main__":
    main()
