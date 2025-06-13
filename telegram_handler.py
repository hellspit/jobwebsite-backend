from telethon import TelegramClient, events
import os
from dotenv import load_dotenv
import asyncio
from message_parser import process_job_message
from database import db_handler
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_bot.log'),
        logging.StreamHandler()
    ]
)

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
GROUP_USERNAME = "@jobs_and_internships_updates"

class TelegramHandler:
    def __init__(self):
        self.client = TelegramClient('session_name', API_ID, API_HASH)
        self.last_processed_id = None
        self.is_processing = False

    async def process_job_posting(self, message_text: str, message_id: int) -> bool:
        """
        Process a job posting using the message parser and store in database
        """
        try:
            logging.info(f"Processing message ID: {message_id}")
            success = await process_job_message(message_text)
            if success:
                logging.info(f"Successfully processed and stored message ID: {message_id}")
            else:
                logging.info(f"Message ID {message_id} was not relevant or processing failed")
            return success
        except Exception as e:
            logging.error(f"Error processing job posting {message_id}: {e}")
            return False

    async def process_historical_messages(self, entity):
        """
        Process the last 25 messages from the group
        """
        if self.is_processing:
            logging.info("Already processing messages, skipping historical processing")
            return

        self.is_processing = True
        try:
            messages = await self.client.get_messages(entity, limit=25)
            logging.info(f"Found {len(messages)} historical messages to process")
            
            for message in reversed(messages):  # Process oldest first
                if message.text:
                    await self.process_job_posting(message.text, message.id)
            
            if messages:
                self.last_processed_id = messages[0].id
                logging.info(f"Last processed message ID: {self.last_processed_id}")
            
        except Exception as e:
            logging.error(f"Error processing historical messages: {e}")
        finally:
            self.is_processing = False

    async def start(self):
        try:
            await self.client.start(phone=PHONE)
            logging.info("Telegram client started successfully")
            
            entity = await self.client.get_entity(GROUP_USERNAME)
            logging.info(f"Connected to group: {entity.title}")
            
            # Process historical messages first
            await self.process_historical_messages(entity)
            
            # Set up event handler for new messages
            @self.client.on(events.NewMessage(chats=entity))
            async def handle_new_message(event):
                try:
                    if event.message.id > self.last_processed_id:
                        logging.info(f"New message received: {event.message.id}")
                        if event.message.text:
                            await self.process_job_posting(event.message.text, event.message.id)
                        self.last_processed_id = event.message.id
                except Exception as e:
                    logging.error(f"Error handling new message {event.message.id}: {e}")
            
            logging.info("Monitoring for new messages...")
            await self.client.run_until_disconnected()
            
        except ValueError as e:
            logging.error(f"Could not find the group. Please check the format:")
            logging.error("1. For public groups: Use @groupname (e.g., @mygroup)")
            logging.error("2. For private groups: Use the group ID (e.g., -1001234567890)")
            logging.error(f"Current value: {GROUP_USERNAME}")
        except Exception as e:
            logging.error(f"Error in start method: {str(e)}")
        finally:
            await self.client.disconnect()
            logging.info("Telegram client disconnected")

# Create a singleton instance
telegram_handler = TelegramHandler()

async def start_telegram_client():
    while True:
        try:
            await telegram_handler.start()
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            logging.info("Restarting in 30 seconds...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    logging.info("Starting Telegram bot...")
    asyncio.run(start_telegram_client()) 