"""
Facebook Account Creation Telegram Bot
Automates Facebook signup with manual phone number and OTP input.
"""

import os
import json
import logging
import random
import time
from typing import Dict, Any
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_PHONE, WAITING_OTP = range(2)

# File to store created accounts
ACCOUNTS_FILE = 'accounts.json'


class FacebookAccountCreator:
    """Handles Facebook account creation automation using Selenium."""
    
    def __init__(self, headless: bool = False):
        """
        Initialize the Facebook account creator.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.driver = None
        self.account_data: Dict[str, Any] = {}
        
    def setup_driver(self):
        """Set up undetected Chrome driver with anti-detection measures."""
        logger.info("Setting up Chrome driver...")
        
        options = uc.ChromeOptions()
        
        # Railway/production settings
        if self.headless:
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
        
        # Anti-detection settings
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--start-maximized')
        options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Random window size for better anti-detection
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        self.driver = uc.Chrome(options=options, version_main=120)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("Chrome driver setup complete")
    
    def human_type(self, element, text: str):
        """
        Type text with random human-like delays.
        
        Args:
            element: Selenium WebElement
            text: Text to type
        """
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def random_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """Add random delay to simulate human behavior."""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def generate_account_data(self) -> Dict[str, Any]:
        """Generate random account data."""
        first_names = ['John', 'Emma', 'Michael', 'Sarah', 'David', 'Lisa', 'Robert', 'Maria']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
        
        # Random birthday (18-35 years old)
        birth_year = random.randint(1989, 2005)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        # Random gender
        gender = random.choice(['male', 'female'])
        
        # Random password (strong)
        password = f"Fb{random.randint(100000, 999999)}!@#"
        
        return {
            'first_name': random.choice(first_names),
            'last_name': random.choice(last_names),
            'password': password,
            'birth_day': birth_day,
            'birth_month': birth_month,
            'birth_year': birth_year,
            'gender': gender,
        }
    
    async def start_signup(self) -> Dict[str, Any]:
        """
        Start Facebook signup process and fill initial fields.
        
        Returns:
            Account data dictionary
        """
        try:
            self.setup_driver()
            
            # Generate account data
            self.account_data = self.generate_account_data()
            
            logger.info("Navigating to Facebook signup page...")
            self.driver.get('https://www.facebook.com/reg/')
            self.random_delay(2, 4)
            
            # Fill first name
            logger.info("Filling first name...")
            first_name_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'firstname'))
            )
            self.human_type(first_name_input, self.account_data['first_name'])
            self.random_delay()
            
            # Fill last name
            logger.info("Filling last name...")
            last_name_input = self.driver.find_element(By.NAME, 'lastname')
            self.human_type(last_name_input, self.account_data['last_name'])
            self.random_delay()
            
            # Fill password
            logger.info("Filling password...")
            password_input = self.driver.find_element(By.NAME, 'reg_passwd__')
            self.human_type(password_input, self.account_data['password'])
            self.random_delay()
            
            # Fill birthday
            logger.info("Filling birthday...")
            day_select = Select(self.driver.find_element(By.NAME, 'birthday_day'))
            day_select.select_by_value(str(self.account_data['birth_day']))
            self.random_delay(0.3, 0.7)
            
            month_select = Select(self.driver.find_element(By.NAME, 'birthday_month'))
            month_select.select_by_value(str(self.account_data['birth_month']))
            self.random_delay(0.3, 0.7)
            
            year_select = Select(self.driver.find_element(By.NAME, 'birthday_year'))
            year_select.select_by_value(str(self.account_data['birth_year']))
            self.random_delay()
            
            # Select gender
            logger.info("Selecting gender...")
            if self.account_data['gender'] == 'male':
                gender_value = '2'
            else:
                gender_value = '1'
            
            gender_radio = self.driver.find_element(By.CSS_SELECTOR, f'input[type="radio"][value="{gender_value}"]')
            gender_radio.click()
            self.random_delay()
            
            logger.info("Initial fields filled. Ready for phone number.")
            return self.account_data
            
        except Exception as e:
            logger.error(f"Error during signup start: {e}")
            self.cleanup()
            raise
    
    def enter_phone_number(self, phone: str):
        """
        Enter phone number and submit.
        
        Args:
            phone: Phone number to enter
        """
        try:
            logger.info(f"Entering phone number: {phone}")
            
            # Find phone number input (can be email or phone)
            phone_input = self.driver.find_element(By.NAME, 'reg_email__')
            phone_input.clear()
            self.human_type(phone_input, phone)
            self.random_delay()
            
            # Confirm phone number (Facebook asks to re-enter)
            try:
                phone_confirm = self.driver.find_element(By.NAME, 'reg_email_confirmation__')
                phone_confirm.clear()
                self.human_type(phone_confirm, phone)
                self.random_delay()
            except NoSuchElementException:
                logger.info("Phone confirmation field not found, continuing...")
            
            # Click Sign Up button
            logger.info("Clicking Sign Up button...")
            signup_button = self.driver.find_element(By.NAME, 'websubmit')
            signup_button.click()
            
            self.account_data['phone'] = phone
            self.random_delay(3, 5)
            
            logger.info("Phone number submitted. Waiting for OTP...")
            
        except Exception as e:
            logger.error(f"Error entering phone number: {e}")
            raise
    
    def enter_otp(self, otp: str) -> bool:
        """
        Enter OTP code and complete signup.
        
        Args:
            otp: OTP code
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Entering OTP: {otp}")
            
            # Wait for OTP input field
            otp_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, 'code'))
            )
            self.human_type(otp_input, otp)
            self.random_delay()
            
            # Click continue/confirm button
            confirm_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            confirm_button.click()
            self.random_delay(3, 5)
            
            # Check if signup was successful
            # Usually redirects to home page or shows welcome message
            current_url = self.driver.current_url
            
            if 'facebook.com' in current_url and '/reg/' not in current_url:
                logger.info("Account creation successful!")
                self.account_data['created_at'] = datetime.now().isoformat()
                self.account_data['status'] = 'success'
                return True
            else:
                logger.warning("Account creation may have failed. Current URL: " + current_url)
                self.account_data['status'] = 'failed'
                return False
                
        except TimeoutException:
            logger.error("Timeout waiting for OTP field")
            self.account_data['status'] = 'timeout'
            return False
        except Exception as e:
            logger.error(f"Error entering OTP: {e}")
            self.account_data['status'] = 'error'
            return False
    
    def cleanup(self):
        """Close browser and clean up resources."""
        if self.driver:
            logger.info("Closing browser...")
            self.driver.quit()
            self.driver = None


def save_account(account_data: Dict[str, Any]):
    """
    Save account data to JSON file.
    
    Args:
        account_data: Account information to save
    """
    try:
        # Load existing accounts
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r') as f:
                accounts = json.load(f)
        else:
            accounts = []
        
        # Add new account
        accounts.append(account_data)
        
        # Save to file
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(accounts, f, indent=2)
        
        logger.info(f"Account saved to {ACCOUNTS_FILE}")
        
    except Exception as e:
        logger.error(f"Error saving account: {e}")


# Telegram Bot Handlers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome_message = """
👋 **Welcome to Facebook Account Creator Bot!** 
This bot helps you create Facebook accounts automatically.
 **Commands:** /start - Show this message
/create - Start creating a new Facebook account
/help - Get help
 **How it works:** 1. Use /create to start
2. Bot will fill basic info automatically
3. You provide phone number when asked
4. You provide OTP code when asked
5. Account is created and saved!

⚠️ **Note:** Use responsibly and follow Facebook's Terms of Service.
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """ **Facebook Account Creator Bot - Help**  **Steps to create an account:** 
1️⃣ Send /create command
2️⃣ Bot will start filling the signup form automatically
3️⃣ When asked, send your phone number (e.g., +8801712345678)
4️⃣ Facebook will send you an OTP code
5️⃣ Send the OTP code to the bot
6️⃣ Done! Your account is created
 **Troubleshooting:** - If phone number is already used, try another
- If OTP is wrong, the process will fail - start over with /create
- Each account is saved to accounts.json file
 **Commands:** /start - Welcome message
/create - Create new account
/cancel - Cancel current operation
/help - This help message
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /create command - start account creation."""
    await update.message.reply_text(
        "🚀 Starting Facebook account creation...\n"
        "Please wait while I fill the basic information..."
    )
    
    try:
        # Initialize creator
        creator = FacebookAccountCreator(headless=os.getenv('HEADLESS', 'false').lower() == 'true')
        context.user_data['creator'] = creator
        
        # Start signup process
        account_data = await creator.start_signup()
        
        # Show generated info
        info_message = f"""
✅ **Basic information filled:**  **Name:** {account_data['first_name']} {account_data['last_name']} **Birthday:** {account_data['birth_day']}/{account_data['birth_month']}/{account_data['birth_year']} **Gender:** {account_data['gender'].capitalize()} **Password:** `{account_data['password']}`

📱 **Now, please send your phone number** (with country code, e.g., +8801712345678)
        """
        await update.message.reply_text(info_message, parse_mode='Markdown')
        
        return WAITING_PHONE
        
    except Exception as e:
        logger.error(f"Error in create_command: {e}")
        await update.message.reply_text(
            f"❌ Error starting account creation: {str(e)}\n"
            "Please try again with /create"
        )
        return ConversationHandler.END


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input."""
    phone = update.message.text.strip()
    
    # Basic validation
    if not phone.startswith('+') and not phone.isdigit():
        await update.message.reply_text(
            "❌ Invalid phone number format.\n"
            "Please send a valid phone number (e.g., +8801712345678)"
        )
        return WAITING_PHONE
    
    await update.message.reply_text(
        f"📱 Entering phone number: {phone}\n"
        "Please wait..."
    )
    
    try:
        creator = context.user_data['creator']
        creator.enter_phone_number(phone)
        
        await update.message.reply_text(
            "✅ Phone number submitted!\n\n"
            "📬 Facebook will send you an OTP code via SMS.\n"
            " **Please send the OTP code when you receive it.** "
        )
        
        return WAITING_OTP
        
    except Exception as e:
        logger.error(f"Error entering phone: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n\n"
            "Possible reasons:\n"
            "- Phone number already registered\n"
            "- Invalid phone format\n"
            "- Facebook detected unusual activity\n\n"
            "Use /create to try again with a different number."
        )
        
        creator = context.user_data.get('creator')
        if creator:
            creator.cleanup()
        
        return ConversationHandler.END


async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle OTP input."""
    otp = update.message.text.strip()
    
    # Basic validation
    if not otp.isdigit() or len(otp) < 4:
        await update.message.reply_text(
            "❌ Invalid OTP format.\n"
            "Please send the numeric code you received (e.g., 123456)"
        )
        return WAITING_OTP
    
    await update.message.reply_text(
        f"🔐 Verifying OTP: {otp}\n"
        "Please wait..."
    )
    
    try:
        creator = context.user_data['creator']
        success = creator.enter_otp(otp)
        
        if success:
            # Save account
            save_account(creator.account_data)
            
            success_message = f"""
🎉 **Account created successfully!**  **Account Details:**  **Name:** {creator.account_data['first_name']} {creator.account_data['last_name']} **Phone:** {creator.account_data['phone']} **Password:** `{creator.account_data['password']}` **Birthday:** {creator.account_data['birth_day']}/{creator.account_data['birth_month']}/{creator.account_data['birth_year']}

✅ Account saved to accounts.json

Use /create to create another account.
            """
            await update.message.reply_text(success_message, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "❌ Account creation failed.\n"
                "Possible reasons:\n"
                "- Wrong OTP code\n"
                "- OTP expired\n"
                "- Facebook detected unusual activity\n\n"
                "Use /create to try again."
            )
        
        creator.cleanup()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error entering OTP: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n\n"
            "Use /create to try again."
        )
        
        creator = context.user_data.get('creator')
        if creator:
            creator.cleanup()
        
        return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    creator = context.user_data.get('creator')
    if creator:
        creator.cleanup()
    
    await update.message.reply_text(
        "❌ Operation cancelled.\n"
        "Use /create to start a new account creation."
    )
    
    return ConversationHandler.END


def main():
    """Main function to run the bot."""
    # Get token from environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('create', create_command)],
        states={
            WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
            WAITING_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otp)],
        },
        fallbacks=[CommandHandler('cancel', cancel_command)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(conv_handler)
    
    # Start bot
    logger.info("Bot started! Use Ctrl+C to stop.")
    
    # Use polling (easier for testing)
    # For production on Railway, consider using webhook
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()