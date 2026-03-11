"""
Facebook Account Creation Telegram Bot - Mobile Optimized Version
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

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

WAITING_PHONE, WAITING_OTP = range(2)
ACCOUNTS_FILE = 'accounts.json'

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Facebook Bot Running!"

@flask_app.route('/health')
def health():
    return {"status": "ok"}

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


class FacebookAccountCreator:
    """Facebook account creator with mobile site."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Browser = None
        self.page: Page = None
        self.playwright: Playwright = None
        self.account_data: Dict[str, Any] = {}
        
    async def setup_browser(self):
        """Setup browser optimized for mobile."""
        logger.info("🔧 Setting up browser...")
        
        try:
            self.playwright = await async_playwright().start()
            
            # Mobile browser settings
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-gpu',
                    '--no-zygote',
                    '--single-process',
                ],
                timeout=90000
            )
            
            # Mobile device context
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                viewport={'width': 375, 'height': 667},
                device_scale_factor=2,
                is_mobile=True,
                has_touch=True,
                locale='en-US',
            )
            
            context.set_default_timeout(45000)
            context.set_default_navigation_timeout(90000)
            
            self.page = await context.new_page()
            
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            logger.info("✅ Browser ready")
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            raise
    
    async def human_type(self, selector: str, text: str):
        """Type like human."""
        try:
            await self.page.fill(selector, text)
        except:
            # Fallback to slow typing
            for char in text:
                await self.page.type(selector, char, delay=random.randint(50, 100))
            
    async def random_delay(self, min_sec: float = 0.3, max_sec: float = 1.0):
        """Random delay."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))
    
    def generate_account_data(self) -> Dict[str, Any]:
        """Generate account data."""
        first_names = ['Alex', 'Sam', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery']
        last_names = ['Smith', 'Brown', 'Wilson', 'Lee', 'Chen', 'Kim', 'Patel', 'Garcia']
        
        birth_year = random.randint(1990, 2003)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        gender = random.choice(['male', 'female'])
        password = f"Pass{random.randint(10000, 99999)}!@"
        
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
        """Start signup with mobile site."""
        try:
            await self.setup_browser()
            self.account_data = self.generate_account_data()
            
            logger.info("📱 Opening Facebook mobile signup...")
            
            # Use mobile site - much faster!
            await self.page.goto(
                'https://m.facebook.com/reg/',
                wait_until='load',
                timeout=90000
            )
            
            logger.info("⏳ Waiting for page...")
            await asyncio.sleep(5)
            
            # Try different selectors for mobile
            selectors_to_try = [
                ('input[name="firstname"]', 'name firstname'),
                ('input#firstname', 'id firstname'),
                ('input[placeholder*="First"]', 'placeholder First'),
            ]
            
            first_name_input = None
            for selector, desc in selectors_to_try:
                try:
                    logger.info(f"🔍 Trying selector: {desc}")
                    first_name_input = await self.page.wait_for_selector(
                        selector, 
                        timeout=15000,
                        state='visible'
                    )
                    if first_name_input:
                        logger.info(f"✅ Found input with: {desc}")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ {desc} not found: {e}")
                    continue
            
            if not first_name_input:
                raise Exception("Could not find first name input")
            
            logger.info("✍️ Filling first name...")
            await self.human_type('input[name="firstname"]', self.account_data['first_name'])
            await self.random_delay()
            
            logger.info("✍️ Filling last name...")
            await self.human_type('input[name="lastname"]', self.account_data['last_name'])
            await self.random_delay()
            
            # Birthday
            logger.info("📅 Setting birthday...")
            try:
                await self.page.select_option('select[name="birthday_day"]', str(self.account_data['birth_day']))
                await self.random_delay(0.2, 0.5)
                await self.page.select_option('select[name="birthday_month"]', str(self.account_data['birth_month']))
                await self.random_delay(0.2, 0.5)
                await self.page.select_option('select[name="birthday_year"]', str(self.account_data['birth_year']))
                await self.random_delay()
            except Exception as e:
                logger.warning(f"Birthday fields issue: {e}")
            
            # Gender
            logger.info("⚧️ Setting gender...")
            try:
                gender_value = '2' if self.account_data['gender'] == 'male' else '1'
                await self.page.click(f'input[value="{gender_value}"]')
                await self.random_delay()
            except Exception as e:
                logger.warning(f"Gender field issue: {e}")
            
            # Password (might be later)
            logger.info("🔐 Looking for password field...")
            try:
                password_selectors = [
                    'input[name="reg_passwd__"]',
                    'input[type="password"]',
                    'input[name="password"]'
                ]
                
                for sel in password_selectors:
                    try:
                        pwd_field = await self.page.query_selector(sel)
                        if pwd_field:
                            await self.human_type(sel, self.account_data['password'])
                            logger.info("✅ Password filled")
                            break
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Password field not found yet: {e}")
            
            await self.random_delay(1, 2)
            
            logger.info("✅ Basic info filled!")
            return self.account_data
            
        except Exception as e:
            logger.error(f"❌ Signup error: {e}")
            
            # Take screenshot for debugging
            try:
                await self.page.screenshot(path='error_screenshot.png')
                logger.info("📸 Screenshot saved")
            except:
                pass
            
            await self.cleanup()
            raise
    
    async def enter_phone_number(self, phone: str):
        """Enter phone number."""
        try:
            logger.info(f"📱 Entering phone: {phone}")
            
            # Wait a bit for page to be ready
            await asyncio.sleep(2)
            
            # Try multiple selectors
            phone_selectors = [
                'input[name="reg_email__"]',
                'input[name="email"]',
                'input[type="tel"]',
                'input[placeholder*="phone"]',
                'input[placeholder*="Mobile"]',
            ]
            
            phone_entered = False
            for selector in phone_selectors:
                try:
                    field = await self.page.query_selector(selector)
                    if field:
                        await self.human_type(selector, phone)
                        logger.info(f"✅ Phone entered via {selector}")
                        phone_entered = True
                        break
                except:
                    continue
            
            if not phone_entered:
                raise Exception("Could not find phone input field")
            
            await self.random_delay(1, 2)
            
            # Try confirmation field
            try:
                confirm_field = await self.page.query_selector('input[name="reg_email_confirmation__"]')
                if confirm_field:
                    await self.human_type('input[name="reg_email_confirmation__"]', phone)
                    logger.info("✅ Phone confirmation filled")
            except:
                pass
            
            # Click submit
            logger.info("👆 Clicking submit...")
            
            submit_selectors = [
                'button[name="websubmit"]',
                'button[type="submit"]',
                'button:has-text("Sign Up")',
                'button:has-text("Next")',
            ]
            
            for selector in submit_selectors:
                try:
                    await self.page.click(selector, timeout=5000)
                    logger.info(f"✅ Clicked: {selector}")
                    break
                except:
                    continue
            
            self.account_data['phone'] = phone
            await asyncio.sleep(5)
            
            logger.info("✅ Phone submitted")
            
        except Exception as e:
            logger.error(f"❌ Phone entry error: {e}")
            raise
    
    async def enter_otp(self, otp: str) -> bool:
        """Enter OTP."""
        try:
            logger.info(f"🔐 Entering OTP: {otp}")
            
            await asyncio.sleep(2)
            
            # OTP field selectors
            otp_selectors = [
                'input[name="code"]',
                'input[name="confirmation_code"]',
                'input[type="text"][maxlength="6"]',
                'input[placeholder*="code"]',
            ]
            
            otp_entered = False
            for selector in otp_selectors:
                try:
                    field = await self.page.wait_for_selector(selector, timeout=15000)
                    if field:
                        await self.human_type(selector, otp)
                        logger.info(f"✅ OTP entered via {selector}")
                        otp_entered = True
                        break
                except:
                    continue
            
            if not otp_entered:
                raise Exception("Could not find OTP input field")
            
            await self.random_delay(1, 2)
            
            # Submit OTP
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Continue")',
                'button:has-text("Confirm")',
                'button:has-text("Next")',
            ]
            
            for selector in submit_selectors:
                try:
                    await self.page.click(selector, timeout=5000)
                    logger.info(f"✅ Clicked: {selector}")
                    break
                except:
                    continue
            
            await asyncio.sleep(5)
            
            # Check success
            current_url = self.page.url
            logger.info(f"📍 Current URL: {current_url}")
            
            if 'facebook.com' in current_url and '/reg/' not in current_url and '/checkpoint' not in current_url:
                logger.info("✅ Account created!")
                self.account_data['created_at'] = datetime.now().isoformat()
                self.account_data['status'] = 'success'
                return True
            else:
                logger.warning(f"⚠️ Uncertain status, URL: {current_url}")
                self.account_data['status'] = 'uncertain'
                return False
                
        except Exception as e:
            logger.error(f"❌ OTP error: {e}")
            self.account_data['status'] = 'error'
            return False
    
    async def cleanup(self):
        """Cleanup."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("🧹 Cleanup done")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


def save_account(account_data: Dict[str, Any]):
    """Save account."""
    try:
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
        else:
            accounts = []
        
        accounts.append(account_data)
        
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved to {ACCOUNTS_FILE}")
        
    except Exception as e:
        logger.error(f"Save error: {e}")


# Telegram handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Facebook Account Creator**\n\n"
        "Commands:\n"
        "• /create - Create account\n"
        "• /cancel - Cancel\n\n"
        "Ready? Send /create 🚀",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **Help**\n\n"
        "1. /create\n"
        "2. Send phone: +8801712345678\n"
        "3. Send OTP: 123456\n"
        "4. Done! ✅",
        parse_mode='Markdown'
    )


async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'creator' in context.user_data:
        await update.message.reply_text("⚠️ Already creating. Use /cancel first")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🚀 **Starting...**\n\n"
        "⏳ This may take 30-60 seconds\n"
        "Please be patient...",
        parse_mode='Markdown'
    )
    
    try:
        headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        creator = FacebookAccountCreator(headless=headless)
        context.user_data['creator'] = creator
        
        account_data = await creator.start_signup()
        
        info_msg = f"""
✅ **Info Filled!**

👤 Name: {account_data['first_name']} {account_data['last_name']}
🎂 DOB: {account_data['birth_day']}/{account_data['birth_month']}/{account_data['birth_year']}
🔐 Pass: `{account_data['password']}`

📱 **Send phone number now**
Format: `+8801712345678`
        """
        await update.message.reply_text(info_msg, parse_mode='Markdown')
        
        return WAITING_PHONE
        
    except Exception as e:
        logger.error(f"Create error: {e}", exc_info=True)
        
        if 'creator' in context.user_data:
            try:
                await context.user_data['creator'].cleanup()
            except:
                pass
            del context.user_data['creator']
        
        error_msg = str(e)
        if 'timeout' in error_msg.lower():
            error_msg = "Facebook page took too long to load. Server might be slow. Try again."
        
        await update.message.reply_text(
            f"❌ **Error**\n\n{error_msg}\n\nTry /create again",
            parse_mode='Markdown'
        )
        return ConversationHandler.END


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    
    if not phone.startswith('+') or len(phone) < 10:
        await update.message.reply_text("❌ Invalid. Example: `+8801712345678`", parse_mode='Markdown')
        return WAITING_PHONE
    
    await update.message.reply_text(f"📱 Submitting `{phone}`...", parse_mode='Markdown')
    
    try:
        creator = context.user_data.get('creator')
        if not creator:
            await update.message.reply_text("❌ Session expired. /create")
            return ConversationHandler.END
        
        await creator.enter_phone_number(phone)
        
        await update.message.reply_text(
            "✅ **Phone Submitted!**\n\n"
            "📬 Check SMS for OTP\n"
            "Send the code here",
            parse_mode='Markdown'
        )
        
        return WAITING_OTP
        
    except Exception as e:
        logger.error(f"Phone error: {e}")
        await update.message.reply_text(f"❌ {str(e)}\n\nTry /create", parse_mode='Markdown')
        
        if creator:
            try:
                await creator.cleanup()
            except:
                pass
        if 'creator' in context.user_data:
            del context.user_data['creator']
        
        return ConversationHandler.END


async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    
    if not otp.isdigit() or len(otp) < 4:
        await update.message.reply_text("❌ Invalid OTP. Send numbers only")
        return WAITING_OTP
    
    await update.message.reply_text(f"🔐 Verifying `{otp}`...", parse_mode='Markdown')
    
    try:
        creator = context.user_data.get('creator')
        if not creator:
            await update.message.reply_text("❌ Session expired. /create")
            return ConversationHandler.END
        
        success = await creator.enter_otp(otp)
        
        if success:
            save_account(creator.account_data)
            
            msg = f"""
🎉 **SUCCESS!**

👤 {creator.account_data['first_name']} {creator.account_data['last_name']}
📱 `{creator.account_data['phone']}`
🔐 `{creator.account_data['password']}`

✅ Saved!

/create for another
            """
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "❌ **Failed**\n\n"
                "Wrong OTP or FB issue\n"
                "Try /create again",
                parse_mode='Markdown'
            )
        
        await creator.cleanup()
        if 'creator' in context.user_data:
            del context.user_data['creator']
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"OTP error: {e}")
        await update.message.reply_text(f"❌ {str(e)}", parse_mode='Markdown')
        
        if creator:
            try:
                await creator.cleanup()
            except:
                pass
        if 'creator' in context.user_data:
            del context.user_data['creator']
        
        return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    creator = context.user_data.get('creator')
    
    if creator:
        await update.message.reply_text("⏳ Cancelling...")
        try:
            await creator.cleanup()
        except:
            pass
        del context.user_data['creator']
        await update.message.reply_text("❌ Cancelled")
    else:
        await update.message.reply_text("Nothing to cancel")
    
    return ConversationHandler.END


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}", exc_info=context.error)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ Error occurred. Try /create")
    except:
        pass


def main():
    # Flask background
    Thread(target=run_flask, daemon=True).start()
    logger.info(f"🌐 Flask on port {os.getenv('PORT', '8080')}")
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ No token!")
        return
    
    if not os.path.exists('.env'):
        os.environ['HEADLESS'] = 'true'
    
    logger.info("🤖 Starting bot...")
    
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
    
    logger.info("✅ Bot ready!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
