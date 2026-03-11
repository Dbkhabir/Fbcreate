"""
Facebook Account Creation Telegram Bot - Playwright Version
Automates Facebook signup with manual phone number and OTP input.
"""

import os
import json
import logging
import random
import asyncio
from typing import Dict, Any
from datetime import datetime
from threading import Thread

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

from playwright.async_api import async_playwright, Browser, Page, Playwright
from flask import Flask

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

# Flask app for Railway (keeps the service alive)
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Facebook Account Creator Bot is running!"

@flask_app.route('/health')
def health():
    return {"status": "healthy", "bot": "active"}

def run_flask():
    """Run Flask server in background."""
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


class FacebookAccountCreator:
    """Handles Facebook account creation automation using Playwright."""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the Facebook account creator.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.browser: Browser = None
        self.page: Page = None
        self.playwright: Playwright = None
        self.account_data: Dict[str, Any] = {}
        
    async def setup_browser(self):
        """Set up Playwright browser with anti-detection measures."""
        logger.info("Setting up Playwright browser...")
        
        self.playwright = await async_playwright().start()
        
        # Launch browser with anti-detection settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-gpu',
                '--no-zygote',
            ]
        )
        
        # Create context with realistic settings
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': random.randint(1366, 1920), 'height': random.randint(768, 1080)},
            locale='en-US',
            timezone_id='America/New_York',
        )
        
        self.page = await context.new_page()
        
        # Remove webdriver detection
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            window.navigator.chrome = {
                runtime: {},
            };
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        logger.info("Playwright browser setup complete")
    
    async def human_type(self, selector: str, text: str):
        """
        Type text with human-like delays.
        
        Args:
            selector: CSS selector for the input element
            text: Text to type
        """
        await self.page.fill(selector, '')
        for char in text:
            await self.page.type(selector, char, delay=random.randint(50, 150))
            
    async def random_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """Add random delay to simulate human behavior."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))
    
    def generate_account_data(self) -> Dict[str, Any]:
        """Generate random account data."""
        first_names = ['John', 'Emma', 'Michael', 'Sarah', 'David', 'Lisa', 'Robert', 'Maria', 
                      'James', 'Emily', 'William', 'Olivia', 'Daniel', 'Sophia', 'Matthew', 'Ava']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                     'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas']
        
        birth_year = random.randint(1989, 2005)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        gender = random.choice(['male', 'female'])
        
        password = f"Fb{random.randint(100000, 999999)}!@{random.choice(['#', '$', '%'])}"
        
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
            await self.setup_browser()
            
            self.account_data = self.generate_account_data()
            
            logger.info("Navigating to Facebook signup page...")
            await self.page.goto('https://www.facebook.com/reg/', wait_until='domcontentloaded', timeout=30000)
            await self.random_delay(2, 4)
            
            logger.info("Filling first name...")
            await self.page.wait_for_selector('input[name="firstname"]', timeout=10000)
            await self.human_type('input[name="firstname"]', self.account_data['first_name'])
            await self.random_delay(0.5, 1.0)
            
            logger.info("Filling last name...")
            await self.human_type('input[name="lastname"]', self.account_data['last_name'])
            await self.random_delay(0.5, 1.0)
            
            logger.info("Filling password...")
            await self.human_type('input[name="reg_passwd__"]', self.account_data['password'])
            await self.random_delay(0.5, 1.0)
            
            logger.info("Filling birthday...")
            await self.page.select_option('select[name="birthday_day"]', str(self.account_data['birth_day']))
            await self.random_delay(0.3, 0.7)
            
            await self.page.select_option('select[name="birthday_month"]', str(self.account_data['birth_month']))
            await self.random_delay(0.3, 0.7)
            
            await self.page.select_option('select[name="birthday_year"]', str(self.account_data['birth_year']))
            await self.random_delay(0.5, 1.0)
            
            logger.info("Selecting gender...")
            gender_value = '2' if self.account_data['gender'] == 'male' else '1'
            await self.page.click(f'input[type="radio"][value="{gender_value}"]')
            await self.random_delay(0.5, 1.0)
            
            logger.info("Initial fields filled successfully.")
            return self.account_data
            
        except Exception as e:
            logger.error(f"Error during signup start: {e}")
            await self.cleanup()
            raise
    
    async def enter_phone_number(self, phone: str):
        """
        Enter phone number and submit.
        
        Args:
            phone: Phone number to enter
        """
        try:
            logger.info(f"Entering phone number: {phone}")
            
            await self.page.wait_for_selector('input[name="reg_email__"]', timeout=10000)
            await self.human_type('input[name="reg_email__"]', phone)
            await self.random_delay(0.5, 1.0)
            
            try:
                confirmation_field = await self.page.query_selector('input[name="reg_email_confirmation__"]')
                if confirmation_field:
                    logger.info("Filling phone confirmation field...")
                    await self.human_type('input[name="reg_email_confirmation__"]', phone)
                    await self.random_delay(0.5, 1.0)
            except Exception as e:
                logger.info(f"No confirmation field: {e}")
            
            logger.info("Clicking Sign Up button...")
            await self.page.click('button[name="websubmit"]')
            
            self.account_data['phone'] = phone
            await self.random_delay(3, 5)
            
            logger.info("Phone number submitted successfully.")
            
        except Exception as e:
            logger.error(f"Error entering phone number: {e}")
            raise
    
    async def enter_otp(self, otp: str) -> bool:
        """
        Enter OTP code and complete signup.
        
        Args:
            otp: OTP code
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Entering OTP: {otp}")
            
            await self.page.wait_for_selector('input[name="code"]', timeout=20000)
            await self.random_delay(1, 2)
            
            await self.human_type('input[name="code"]', otp)
            await self.random_delay(0.5, 1.0)
            
            await self.page.click('button[type="submit"]')
            await self.random_delay(3, 5)
            
            current_url = self.page.url
            logger.info(f"Current URL after OTP: {current_url}")
            
            if 'facebook.com' in current_url and '/reg/' not in current_url:
                logger.info("✅ Account creation successful!")
                self.account_data['created_at'] = datetime.now().isoformat()
                self.account_data['status'] = 'success'
                self.account_data['profile_url'] = current_url
                return True
            else:
                logger.warning("Account creation may have failed.")
                self.account_data['status'] = 'uncertain'
                self.account_data['final_url'] = current_url
                return False
                
        except Exception as e:
            logger.error(f"Error entering OTP: {e}")
            self.account_data['status'] = 'error'
            self.account_data['error'] = str(e)
            return False
    
    async def cleanup(self):
        """Close browser and clean up resources."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                logger.info("Closing browser...")
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def save_account(account_data: Dict[str, Any]):
    """Save account data to JSON file."""
    try:
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
        else:
            accounts = []
        
        accounts.append(account_data)
        
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Account saved to {ACCOUNTS_FILE}")
        
    except Exception as e:
        logger.error(f"Error saving account: {e}")


# ============================================
# TELEGRAM BOT HANDLERS
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome_message = """
👋 **Welcome to Facebook Account Creator Bot!** 
This bot helps you create Facebook accounts automatically.
 **Commands:** • /start - Show this message
• /create - Create new Facebook account
• /help - Get help
• /cancel - Cancel operation
 **Quick Start:** 1. Send /create
2. Bot fills name, birthday, password
3. You provide phone number
4. You provide OTP code
5. Done!

⚠️ Use responsibly!

Ready? Send /create 🚀
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
📖 **Help - Facebook Account Creator**  **Steps:** 1️⃣ /create - Start
2️⃣ Bot fills form automatically
3️⃣ Send phone: +8801712345678
4️⃣ Facebook sends OTP via SMS
5️⃣ Send OTP: 123456
6️⃣ Account created!
 **Tips:** ✅ Use valid phone number
✅ Number must receive SMS
✅ Enter OTP quickly
 **Troubleshooting:** ❌ Phone already used → Try different number
❌ Wrong OTP → Check SMS again
❌ Bot stuck → Use /cancel then /create
 **Commands:** /start, /create, /cancel, /help
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /create command."""
    
    if 'creator' in context.user_data:
        await update.message.reply_text(
            "⚠️ Already creating an account.\n"
            "Use /cancel first."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🚀 **Starting Account Creation...** \n\n"
        "⏳ Please wait 10-20 seconds...",
        parse_mode='Markdown'
    )
    
    try:
        headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        
        creator = FacebookAccountCreator(headless=headless)
        context.user_data['creator'] = creator
        
        account_data = await creator.start_signup()
        
        info_message = f"""
✅ **Basic Info Filled!**  **Details:** ━━━━━━━━━━━━━━━━━━━━
👤 **Name:** {account_data['first_name']} {account_data['last_name']}
🎂 **Birthday:** {account_data['birth_day']}/{account_data['birth_month']}/{account_data['birth_year']}
⚧️ **Gender:** {account_data['gender'].capitalize()}
🔐 **Password:** `{account_data['password']}`
━━━━━━━━━━━━━━━━━━━━

📱 **Next: Send your phone number** 
Format: `+8801712345678`

⚠️ Number must receive SMS!
        """
        await update.message.reply_text(info_message, parse_mode='Markdown')
        
        return WAITING_PHONE
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        
        if 'creator' in context.user_data:
            try:
                await context.user_data['creator'].cleanup()
            except:
                pass
            del context.user_data['creator']
        
        await update.message.reply_text(
            f"❌ **Error** \n\n`{str(e)}`\n\nTry /create again",
            parse_mode='Markdown'
        )
        return ConversationHandler.END


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input."""
    phone = update.message.text.strip()
    
    if not phone.startswith('+'):
        await update.message.reply_text(
            "❌ **Invalid Format** \n\n"
            "Must start with '+'\n"
            "Example: `+8801712345678`",
            parse_mode='Markdown'
        )
        return WAITING_PHONE
    
    phone_digits = phone[1:].replace(' ', '').replace('-', '')
    if not phone_digits.isdigit() or len(phone_digits) < 8:
        await update.message.reply_text(
            "❌ Invalid phone number.\n"
            "Example: `+8801712345678`",
            parse_mode='Markdown'
        )
        return WAITING_PHONE
    
    await update.message.reply_text(
        f"📱 Submitting: `{phone}`\n⏳ Wait...",
        parse_mode='Markdown'
    )
    
    try:
        creator = context.user_data.get('creator')
        if not creator:
            await update.message.reply_text("❌ Session expired. Use /create")
            return ConversationHandler.END
        
        await creator.enter_phone_number(phone)
        
        await update.message.reply_text(
            "✅ **Phone Submitted!** \n\n"
            "📬 Facebook is sending OTP via SMS\n\n"
            "⏰ Should arrive in 1-2 minutes\n\n"
            "📝 Send the code when received\n"
            "Example: `123456`",
            parse_mode='Markdown'
        )
        
        return WAITING_OTP
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        
        await update.message.reply_text(
            f"❌ **Failed** \n\n`{str(e)}`\n\n"
            f"Try different number with /create",
            parse_mode='Markdown'
        )
        
        if creator:
            try:
                await creator.cleanup()
            except:
                pass
        
        if 'creator' in context.user_data:
            del context.user_data['creator']
        
        return ConversationHandler.END


async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle OTP input."""
    otp = update.message.text.strip()
    
    if not otp.isdigit():
        await update.message.reply_text(
            "❌ OTP must be numbers only.\nExample: `123456`",
            parse_mode='Markdown'
        )
        return WAITING_OTP
    
    if len(otp) < 4 or len(otp) > 8:
        await update.message.reply_text(
            "❌ OTP usually 4-6 digits.\nCheck and resend.",
        )
        return WAITING_OTP
    
    await update.message.reply_text(
        f"🔐 Verifying: `{otp}`\n⏳ Wait...",
        parse_mode='Markdown'
    )
    
    try:
        creator = context.user_data.get('creator')
        if not creator:
            await update.message.reply_text("❌ Session expired. Use /create")
            return ConversationHandler.END
        
        success = await creator.enter_otp(otp)
        
        if success:
            save_account(creator.account_data)
            
            success_message = f"""
🎉 **ACCOUNT CREATED!** 🎉
 **Your Facebook Account:** ━━━━━━━━━━━━━━━━━━━━
👤 **Name:** {creator.account_data['first_name']} {creator.account_data['last_name']}
📱 **Phone:** `{creator.account_data['phone']}`
🔐 **Password:** `{creator.account_data['password']}`
🎂 **Birthday:** {creator.account_data['birth_day']}/{creator.account_data['birth_month']}/{creator.account_data['birth_year']}
⚧️ **Gender:** {creator.account_data['gender'].capitalize()}
━━━━━━━━━━━━━━━━━━━━

✅ Saved to accounts.json
 **Create another?** Send /create
            """
            await update.message.reply_text(success_message, parse_mode='Markdown')
            
        else:
            await update.message.reply_text(
                "❌ **Failed** \n\n"
                "Reasons:\n"
                "• Wrong OTP\n"
                "• OTP expired\n"
                "• FB detected bot\n\n"
                "Use /create to try again",
                parse_mode='Markdown'
            )
        
        await creator.cleanup()
        
        if 'creator' in context.user_data:
            del context.user_data['creator']
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        
        await update.message.reply_text(
            f"❌ **Error** \n\n`{str(e)}`\n\nUse /create",
            parse_mode='Markdown'
        )
        
        creator = context.user_data.get('creator')
        if creator:
            try:
                await creator.cleanup()
            except:
                pass
        
        if 'creator' in context.user_data:
            del context.user_data['creator']
        
        return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    
    creator = context.user_data.get('creator')
    
    if creator:
        await update.message.reply_text("⏳ Cancelling...")
        
        try:
            await creator.cleanup()
        except Exception as e:
            logger.error(f"Cancel cleanup error: {e}")
        
        del context.user_data['creator']
        
        await update.message.reply_text(
            "❌ **Cancelled** \n\nUse /create to start new",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("ℹ️ Nothing to cancel.\n\nUse /create")
    
    return ConversationHandler.END


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Unexpected error.\nTry /create again."
            )
    except:
        pass


def main():
    """Main function."""
    
    # Start Flask in background
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 Flask server started on port " + os.getenv('PORT', '8080'))
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
        return
    
    if not os.path.exists('.env'):
        os.environ['HEADLESS'] = 'true'
    
    logger.info("🤖 Initializing Bot...")
    
    application = Application.builder().token(token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('create', create_command)],
        states={
            WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
            WAITING_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otp)],
        },
        fallbacks=[CommandHandler('cancel', cancel_command)],
        allow_reentry=True,
    )
    
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("✅ Bot started!")
    logger.info("🚀 Ready to create accounts!")
    logger.info("Press Ctrl+C to stop")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
