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
            ]
        )
        
        # Create context with realistic settings
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': random.randint(1366, 1920), 'height': random.randint(768, 1080)},
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'longitude': -74.0060, 'latitude': 40.7128},
            permissions=['geolocation'],
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
        await self.page.fill(selector, '')  # Clear first
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
        
        # Random birthday (18-35 years old)
        birth_year = random.randint(1989, 2005)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        # Random gender
        gender = random.choice(['male', 'female'])
        
        # Random strong password
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
            
            # Generate account data
            self.account_data = self.generate_account_data()
            
            logger.info("Navigating to Facebook signup page...")
            await self.page.goto('https://www.facebook.com/reg/', wait_until='domcontentloaded', timeout=30000)
            await self.random_delay(2, 4)
            
            # Fill first name
            logger.info("Filling first name...")
            await self.page.wait_for_selector('input[name="firstname"]', timeout=10000)
            await self.human_type('input[name="firstname"]', self.account_data['first_name'])
            await self.random_delay(0.5, 1.0)
            
            # Fill last name
            logger.info("Filling last name...")
            await self.human_type('input[name="lastname"]', self.account_data['last_name'])
            await self.random_delay(0.5, 1.0)
            
            # Fill password
            logger.info("Filling password...")
            await self.human_type('input[name="reg_passwd__"]', self.account_data['password'])
            await self.random_delay(0.5, 1.0)
            
            # Fill birthday
            logger.info("Filling birthday...")
            await self.page.select_option('select[name="birthday_day"]', str(self.account_data['birth_day']))
            await self.random_delay(0.3, 0.7)
            
            await self.page.select_option('select[name="birthday_month"]', str(self.account_data['birth_month']))
            await self.random_delay(0.3, 0.7)
            
            await self.page.select_option('select[name="birthday_year"]', str(self.account_data['birth_year']))
            await self.random_delay(0.5, 1.0)
            
            # Select gender
            logger.info("Selecting gender...")
            gender_value = '2' if self.account_data['gender'] == 'male' else '1'
            await self.page.click(f'input[type="radio"][value="{gender_value}"]')
            await self.random_delay(0.5, 1.0)
            
            logger.info("Initial fields filled successfully. Ready for phone number.")
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
            
            # Find and fill phone number input
            await self.page.wait_for_selector('input[name="reg_email__"]', timeout=10000)
            await self.human_type('input[name="reg_email__"]', phone)
            await self.random_delay(0.5, 1.0)
            
            # Check if confirmation field exists
            try:
                confirmation_field = await self.page.query_selector('input[name="reg_email_confirmation__"]')
                if confirmation_field:
                    logger.info("Filling phone confirmation field...")
                    await self.human_type('input[name="reg_email_confirmation__"]', phone)
                    await self.random_delay(0.5, 1.0)
            except Exception as e:
                logger.info(f"No confirmation field found or error: {e}")
            
            # Click Sign Up button
            logger.info("Clicking Sign Up button...")
            await self.page.click('button[name="websubmit"]')
            
            self.account_data['phone'] = phone
            await self.random_delay(3, 5)
            
            logger.info("Phone number submitted successfully. Waiting for OTP...")
            
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
            
            # Wait for OTP input field
            await self.page.wait_for_selector('input[name="code"]', timeout=20000)
            await self.random_delay(1, 2)
            
            # Enter OTP
            await self.human_type('input[name="code"]', otp)
            await self.random_delay(0.5, 1.0)
            
            # Click continue/confirm button
            await self.page.click('button[type="submit"]')
            await self.random_delay(3, 5)
            
            # Check if signup was successful
            current_url = self.page.url
            logger.info(f"Current URL after OTP: {current_url}")
            
            # Check for success indicators
            if 'facebook.com' in current_url and '/reg/' not in current_url:
                logger.info("✅ Account creation successful!")
                self.account_data['created_at'] = datetime.now().isoformat()
                self.account_data['status'] = 'success'
                self.account_data['profile_url'] = current_url
                return True
            else:
                # Check if we're still on verification page
                try:
                    error_element = await self.page.query_selector('[role="alert"]')
                    if error_element:
                        error_text = await error_element.inner_text()
                        logger.warning(f"Error message found: {error_text}")
                except:
                    pass
                
                logger.warning("Account creation may have failed or needs additional verification.")
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
    """
    Save account data to JSON file.
    
    Args:
        account_data: Account information to save
    """
    try:
        # Load existing accounts
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
        else:
            accounts = []
        
        # Add new account
        accounts.append(account_data)
        
        # Save to file
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
This bot helps you create Facebook accounts automatically using Playwright.
 **Commands:** • /start - Show this welcome message
• /create - Start creating a new Facebook account
• /help - Get detailed help and instructions
• /cancel - Cancel current operation
 **Quick Start:** 1. Send /create to begin
2. Bot will auto-fill name, birthday, gender, password
3. You provide your phone number
4. You provide the OTP code from SMS
5. Done! Account is created and saved

⚠️ **Important:** Use responsibly and follow Facebook's Terms of Service.

Ready? Send /create to start! 🚀
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
📖 **Facebook Account Creator Bot - Detailed Help**  **How It Works:** 
1️⃣ **Start Account Creation**    • Send /create command
   • Bot opens Facebook signup page
   • Automatically fills: Name, Birthday, Gender, Password

2️⃣ **Provide Phone Number**    • Bot asks for your phone number
   • Format: +[country_code][number]
   • Example: +8801712345678 (Bangladesh)
   • Example: +12025551234 (USA)

3️⃣ **Enter OTP Code**    • Facebook sends SMS with verification code
   • Send that code to the bot
   • Bot enters it and completes signup

4️⃣ **Get Account Details**    • Bot sends you all account info
   • Password, phone, birthday, etc.
   • Also saved to accounts.json file
 **Tips for Success:** ✅ Use a real, active phone number
✅ Make sure you can receive SMS
✅ Enter OTP quickly (before it expires)
✅ Don't create too many accounts from same IP
 **Common Issues:** 
❌ **"Phone number already used"**    → That number has a Facebook account already
   → Try a different phone number

❌ **"Wrong OTP code"**    → Double-check the code from SMS
   → Make sure it hasn't expired (usually 10 min)
   → Start over with /create

❌ **"Bot not responding"**    → Check bot is running
   → Check internet connection
   → Try /cancel then /create again
 **Security Notes:** 🔒 Your account data is saved locally
🔒 Bot doesn't store your data on external servers
🔒 Keep your accounts.json file secure
 **Commands:** /start - Welcome message
/create - Create new account
/cancel - Cancel current operation
/help - This help message

Need more help? Contact the bot administrator.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /create command - start account creation."""
    
    # Check if there's already an ongoing creation
    if 'creator' in context.user_data:
        await update.message.reply_text(
            "⚠️ You already have an ongoing account creation.\n"
            "Please complete it or use /cancel first."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🚀 **Starting Facebook Account Creation...** \n\n"
        "⏳ Please wait while I:\n"
        "• Open Facebook signup page\n"
        "• Fill in random name and details\n"
        "• Prepare for your phone number\n\n"
        "This may take 10-20 seconds...",
        parse_mode='Markdown'
    )
    
    try:
        # Get headless setting from environment
        headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        
        # Initialize creator
        creator = FacebookAccountCreator(headless=headless)
        context.user_data['creator'] = creator
        
        # Start signup process
        account_data = await creator.start_signup()
        
        # Show generated info to user
        info_message = f"""
✅ **Basic Information Filled Successfully!**  **Generated Account Details:** ━━━━━━━━━━━━━━━━━━━━━━
👤 **Name:** {account_data['first_name']} {account_data['last_name']}
🎂 **Birthday:** {account_data['birth_day']}/{account_data['birth_month']}/{account_data['birth_year']}
⚧️ **Gender:** {account_data['gender'].capitalize()}
🔐 **Password:** `{account_data['password']}`
━━━━━━━━━━━━━━━━━━━━━━

📱 **Next Step: Phone Number** 
Please send your phone number in international format:
• Format: +[country_code][number]
• Example: `+8801712345678`
• Example: `+12025551234`

⚠️ Make sure:
✓ Number can receive SMS
✓ Number is not already used on Facebook
✓ You have access to this number now
        """
        await update.message.reply_text(info_message, parse_mode='Markdown')
        
        return WAITING_PHONE
        
    except Exception as e:
        logger.error(f"Error in create_command: {e}", exc_info=True)
        
        # Cleanup if error
        if 'creator' in context.user_data:
            try:
                await context.user_data['creator'].cleanup()
            except:
                pass
            del context.user_data['creator']
        
        await update.message.reply_text(
            f"❌ **Error Starting Account Creation** \n\n"
            f"Error: `{str(e)}`\n\n"
            f"Possible reasons:\n"
            f"• Browser failed to start\n"
            f"• Network connection issue\n"
            f"• Facebook page didn't load\n\n"
            f"Please try again with /create",
            parse_mode='Markdown'
        )
        return ConversationHandler.END


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input from user."""
    phone = update.message.text.strip()
    
    # Basic validation
    if not phone.startswith('+'):
        await update.message.reply_text(
            "❌ **Invalid Phone Number Format** \n\n"
            "Phone number must start with '+' and country code.\n\n"
            " **Examples:** \n"
            "• `+8801712345678` (Bangladesh)\n"
            "• `+12025551234` (USA)\n"
            "• `+447911123456` (UK)\n\n"
            "Please send a valid phone number:",
            parse_mode='Markdown'
        )
        return WAITING_PHONE
    
    # Remove spaces and check if rest is numeric
    phone_digits = phone[1:].replace(' ', '').replace('-', '')
    if not phone_digits.isdigit() or len(phone_digits) < 8:
        await update.message.reply_text(
            "❌ **Invalid Phone Number** \n\n"
            "Phone number format is incorrect.\n"
            "Please send a valid phone number with country code.\n\n"
            "Example: `+8801712345678`",
            parse_mode='Markdown'
        )
        return WAITING_PHONE
    
    await update.message.reply_text(
        f"📱 **Submitting Phone Number...** \n\n"
        f"Phone: `{phone}`\n"
        f"⏳ Please wait 5-10 seconds...",
        parse_mode='Markdown'
    )
    
    try:
        creator = context.user_data.get('creator')
        if not creator:
            await update.message.reply_text(
                "❌ Session expired. Please start over with /create"
            )
            return ConversationHandler.END
        
        # Enter phone number
        await creator.enter_phone_number(phone)
        
        await update.message.reply_text(
            "✅ **Phone Number Submitted Successfully!** \n\n"
            "📬 **Facebook is sending you an OTP code via SMS** \n\n"
            "⏰ The code should arrive within 1-2 minutes.\n\n"
            "📝 **When you receive the code:** \n"
            "• It will be 4-6 digits\n"
            "• Send it here immediately\n"
            "• Don't add any text, just the numbers\n\n"
            "Example: `123456`\n\n"
            "Waiting for your OTP code... ⏳",
            parse_mode='Markdown'
        )
        
        return WAITING_OTP
        
    except Exception as e:
        logger.error(f"Error entering phone: {e}", exc_info=True)
        
        error_msg = str(e).lower()
        
        if 'already' in error_msg or 'exists' in error_msg:
            reason = "This phone number is already registered on Facebook"
        elif 'invalid' in error_msg:
            reason = "Facebook rejected this phone number (invalid format or country)"
        elif 'timeout' in error_msg:
            reason = "Page took too long to respond"
        else:
            reason = "Unknown error occurred"
        
        await update.message.reply_text(
            f"❌ **Failed to Submit Phone Number** \n\n"
            f" **Reason:** {reason}\n\n"
            f" **Error Details:** `{str(e)}`\n\n"
            f" **What to do:** \n"
            f"• Try a different phone number\n"
            f"• Make sure number format is correct\n"
            f"• Check if number is already used on Facebook\n\n"
            f"Use /create to try again with a different number.",
            parse_mode='Markdown'
        )
        
        # Cleanup
        if creator:
            try:
                await creator.cleanup()
            except:
                pass
        
        if 'creator' in context.user_data:
            del context.user_data['creator']
        
        return ConversationHandler.END


async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle OTP code input from user."""
    otp = update.message.text.strip()
    
    # Basic validation
    if not otp.isdigit():
        await update.message.reply_text(
            "❌ **Invalid OTP Format** \n\n"
            "OTP must contain only numbers.\n"
            "Please send just the numeric code.\n\n"
            "Example: `123456`",
            parse_mode='Markdown'
        )
        return WAITING_OTP
    
    if len(otp) < 4 or len(otp) > 8:
        await update.message.reply_text(
            "❌ **Invalid OTP Length** \n\n"
            "OTP is usually 4-6 digits.\n"
            "Please check and send the correct code.\n\n"
            "Example: `123456`",
            parse_mode='Markdown'
        )
        return WAITING_OTP
    
    await update.message.reply_text(
        f"🔐 **Verifying OTP Code...** \n\n"
        f"Code: `{otp}`\n"
        f"⏳ Please wait 5-10 seconds...",
        parse_mode='Markdown'
    )
    
    try:
        creator = context.user_data.get('creator')
        if not creator:
            await update.message.reply_text(
                "❌ Session expired. Please start over with /create"
            )
            return ConversationHandler.END
        
        # Enter OTP and check result
        success = await creator.enter_otp(otp)
        
        if success:
            # Save account to file
            save_account(creator.account_data)
            
            # Send success message with full details
            success_message = f"""
🎉 **ACCOUNT CREATED SUCCESSFULLY!** 🎉
 **Your New Facebook Account:** ━━━━━━━━━━━━━━━━━━━━━━
👤 **Name:** {creator.account_data['first_name']} {creator.account_data['last_name']}
📱 **Phone:** `{creator.account_data['phone']}`
🔐 **Password:** `{creator.account_data['password']}`
🎂 **Birthday:** {creator.account_data['birth_day']}/{creator.account_data['birth_month']}/{creator.account_data['birth_year']}
⚧️ **Gender:** {creator.account_data['gender'].capitalize()}
📅 **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━

✅ **Account saved to:** `accounts.json`

🔒 **Security Reminder:** • Change password after first login
• Enable two-factor authentication
• Keep credentials safe
 **To create another account:** Send /create command again

Enjoy your new Facebook account! 🚀
            """
            await update.message.reply_text(success_message, parse_mode='Markdown')
            
        else:
            # Failed but no exception - likely wrong OTP or other FB error
            await update.message.reply_text(
                "❌ **Account Creation Failed** \n\n"
                " **Possible Reasons:** \n"
                "• Wrong OTP code\n"
                "• OTP expired (usually valid for 10 minutes)\n"
                "• Facebook detected suspicious activity\n"
                "• Additional verification required\n\n"
                " **What to do:** \n"
                "• Use /create to try again\n"
                "• Try with a different phone number\n"
                "• Consider using a VPN if blocked\n\n"
                "Use /create to try again.",
                parse_mode='Markdown'
            )
        
        # Cleanup browser
        await creator.cleanup()
        
        # Remove creator from context
        if 'creator' in context.user_data:
            del context.user_data['creator']
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error entering OTP: {e}", exc_info=True)
        
        await update.message.reply_text(
            f"❌ **Error During Verification** \n\n"
            f" **Error:** `{str(e)}`\n\n"
            f" **Possible reasons:** \n"
            f"• Network connection lost\n"
            f"• Facebook page crashed\n"
            f"• Browser error\n\n"
            f"Use /create to try again.",
            parse_mode='Markdown'
        )
        
        # Cleanup
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
    """Handle /cancel command - cancel ongoing operation."""
    
    creator = context.user_data.get('creator')
    
    if creator:
        await update.message.reply_text(
            "⏳ Cancelling and cleaning up...",
        )
        
        try:
            await creator.cleanup()
        except Exception as e:
            logger.error(f"Error during cancel cleanup: {e}")
        
        del context.user_data['creator']
        
        await update.message.reply_text(
            "❌ **Operation Cancelled** \n\n"
            "Browser closed and session cleared.\n\n"
            "Use /create to start a new account creation.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "ℹ️ No ongoing operation to cancel.\n\n"
            "Use /create to start creating an account.",
        )
    
    return ConversationHandler.END


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred.\n"
                "Please try again with /create or contact support."
            )
    except:
        pass


def main():
    """Main function to run the bot."""
    
    # Get token from environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables!")
        logger.error("Please create a .env file with your bot token.")
        return
    
    logger.info("🤖 Initializing Telegram Bot...")
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Create conversation handler for account creation flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('create', create_command)],
        states={
            WAITING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)
            ],
            WAITING_OTP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otp)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_command)],
        allow_reentry=True,
    )
    
    # Add command handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(conv_handler)
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("✅ Bot started successfully!")
    logger.info("🚀 Ready to create Facebook accounts!")
    logger.info("Press Ctrl+C to stop
