"""
Facebook Account Creation Telegram Bot - Debug Version
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

from playwright.async_api import async_playwright, Browser, Page, Playwright, TimeoutError as PlaywrightTimeout
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
    return "✅ Bot Running!"

@flask_app.route('/health')
def health():
    return {"status": "ok"}

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


class FacebookAccountCreator:
    """Facebook account creator with extensive debugging."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Browser = None
        self.page: Page = None
        self.playwright: Playwright = None
        self.account_data: Dict[str, Any] = {}
        self.debug_info = []
        
    def log_debug(self, message: str):
        """Log debug info."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        self.debug_info.append(log_msg)
        logger.info(log_msg)
        
    async def setup_browser(self):
        """Setup browser with debug logging."""
        try:
            self.log_debug("🔧 Starting Playwright...")
            self.playwright = await async_playwright().start()
            self.log_debug("✅ Playwright started")
            
            self.log_debug("🌐 Launching Chromium...")
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process',
                    '--no-zygote',
                ],
                timeout=120000  # 2 minutes
            )
            self.log_debug("✅ Browser launched")
            
            self.log_debug("📱 Creating browser context...")
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                viewport={'width': 412, 'height': 915},
                device_scale_factor=2.625,
                is_mobile=True,
                locale='en-US',
            )
            self.log_debug("✅ Context created")
            
            context.set_default_timeout(60000)
            context.set_default_navigation_timeout(120000)
            
            self.log_debug("📄 Creating new page...")
            self.page = await context.new_page()
            self.log_debug("✅ Page created")
            
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)
            
            self.log_debug("✅ Browser setup complete!")
            
        except Exception as e:
            self.log_debug(f"❌ Browser setup FAILED: {str(e)}")
            raise
    
    def generate_account_data(self) -> Dict[str, Any]:
        """Generate account data."""
        first_names = ['Alex', 'Sam', 'Jordan', 'Taylor', 'Morgan', 'Casey']
        last_names = ['Smith', 'Brown', 'Wilson', 'Lee', 'Chen', 'Kim']
        
        birth_year = random.randint(1992, 2002)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        gender = random.choice(['male', 'female'])
        password = f"Fb{random.randint(100000, 999999)}!@"
        
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
        """Start signup with detailed logging."""
        try:
            self.log_debug("=" * 50)
            self.log_debug("STARTING FACEBOOK SIGNUP PROCESS")
            self.log_debug("=" * 50)
            
            await self.setup_browser()
            
            self.account_data = self.generate_account_data()
            self.log_debug(f"Generated: {self.account_data['first_name']} {self.account_data['last_name']}")
            
            # Try multiple Facebook URLs
            urls_to_try = [
                'https://mbasic.facebook.com/reg/',
                'https://m.facebook.com/reg/',
                'https://touch.facebook.com/reg/',
            ]
            
            page_loaded = False
            loaded_url = None
            
            for url in urls_to_try:
                try:
                    self.log_debug(f"🌐 Trying URL: {url}")
                    
                    response = await self.page.goto(
                        url,
                        wait_until='domcontentloaded',
                        timeout=120000
                    )
                    
                    status = response.status if response else 'No response'
                    self.log_debug(f"Response status: {status}")
                    
                    if response and response.ok:
                        self.log_debug(f"✅ Page loaded: {url}")
                        page_loaded = True
                        loaded_url = url
                        break
                    else:
                        self.log_debug(f"⚠️ Failed: {url} (status: {status})")
                        
                except PlaywrightTimeout:
                    self.log_debug(f"⏱️ Timeout on: {url}")
                    continue
                except Exception as e:
                    self.log_debug(f"❌ Error on {url}: {str(e)}")
                    continue
            
            if not page_loaded:
                raise Exception("All Facebook URLs failed to load")
            
            self.log_debug("⏳ Waiting for page to settle...")
            await asyncio.sleep(5)
            
            # Take screenshot
            try:
                await self.page.screenshot(path='fb_page.png')
                self.log_debug("📸 Screenshot saved: fb_page.png")
            except:
                pass
            
            # Get page content for debugging
            try:
                page_title = await self.page.title()
                self.log_debug(f"Page title: {page_title}")
                
                current_url = self.page.url
                self.log_debug(f"Current URL: {current_url}")
            except:
                pass
            
            # Try to find ANY input field
            self.log_debug("🔍 Looking for input fields...")
            
            all_inputs = await self.page.query_selector_all('input')
            self.log_debug(f"Found {len(all_inputs)} input fields")
            
            # Log all input names
            for i, inp in enumerate(all_inputs[:10]):  # First 10 only
                try:
                    name = await inp.get_attribute('name')
                    inp_type = await inp.get_attribute('type')
                    placeholder = await inp.get_attribute('placeholder')
                    self.log_debug(f"Input {i}: name={name}, type={inp_type}, placeholder={placeholder}")
                except:
                    pass
            
            # Now try to fill the form
            self.log_debug("📝 Attempting to fill form...")
            
            # Try different firstname selectors
            firstname_filled = False
            firstname_selectors = [
                'input[name="firstname"]',
                'input[name="reg_firstname__"]',
                '#firstname',
                'input[placeholder*="First"]',
            ]
            
            for selector in firstname_selectors:
                try:
                    self.log_debug(f"Trying firstname selector: {selector}")
                    await self.page.wait_for_selector(selector, timeout=10000, state='visible')
                    await self.page.fill(selector, self.account_data['first_name'])
                    self.log_debug(f"✅ First name filled with: {selector}")
                    firstname_filled = True
                    break
                except Exception as e:
                    self.log_debug(f"⚠️ Failed {selector}: {str(e)}")
                    continue
            
            if not firstname_filled:
                raise Exception("Could not fill first name field")
            
            await asyncio.sleep(0.5)
            
            # Lastname
            self.log_debug("Filling last name...")
            lastname_selectors = [
                'input[name="lastname"]',
                'input[name="reg_lastname__"]',
                '#lastname',
            ]
            
            for selector in lastname_selectors:
                try:
                    await self.page.fill(selector, self.account_data['last_name'])
                    self.log_debug(f"✅ Last name filled")
                    break
                except:
                    continue
            
            await asyncio.sleep(0.5)
            
            # Birthday
            self.log_debug("Setting birthday...")
            try:
                await self.page.select_option('select[name="birthday_day"]', str(self.account_data['birth_day']))
                await asyncio.sleep(0.3)
                await self.page.select_option('select[name="birthday_month"]', str(self.account_data['birth_month']))
                await asyncio.sleep(0.3)
                await self.page.select_option('select[name="birthday_year"]', str(self.account_data['birth_year']))
                self.log_debug("✅ Birthday set")
            except Exception as e:
                self.log_debug(f"⚠️ Birthday error: {e}")
            
            await asyncio.sleep(0.5)
            
            # Gender
            self.log_debug("Setting gender...")
            try:
                gender_value = '2' if self.account_data['gender'] == 'male' else '1'
                await self.page.click(f'input[value="{gender_value}"]')
                self.log_debug("✅ Gender set")
            except Exception as e:
                self.log_debug(f"⚠️ Gender error: {e}")
            
            await asyncio.sleep(0.5)
            
            # Password
            self.log_debug("Setting password...")
            password_selectors = [
                'input[name="reg_passwd__"]',
                'input[name="password"]',
                'input[type="password"]',
            ]
            
            for selector in password_selectors:
                try:
                    await self.page.fill(selector, self.account_data['password'])
                    self.log_debug(f"✅ Password filled")
                    break
                except:
                    continue
            
            self.log_debug("=" * 50)
            self.log_debug("✅ FORM FILLED SUCCESSFULLY!")
            self.log_debug("=" * 50)
            
            return self.account_data
            
        except Exception as e:
            self.log_debug(f"❌ CRITICAL ERROR: {str(e)}")
            
            # Save debug info
            try:
                with open('debug_log.txt', 'w') as f:
                    f.write('\n'.join(self.debug_info))
                self.log_debug("💾 Debug log saved to debug_log.txt")
            except:
                pass
            
            await self.cleanup()
            raise
    
    async def enter_phone_number(self, phone: str):
        """Enter phone with logging."""
        try:
            self.log_debug(f"📱 Entering phone: {phone}")
            
            await asyncio.sleep(2)
            
            phone_selectors = [
                'input[name="reg_email__"]',
                'input[name="email"]',
                'input[type="tel"]',
            ]
            
            for selector in phone_selectors:
                try:
                    await self.page.fill(selector, phone)
                    self.log_debug(f"✅ Phone entered: {selector}")
                    break
                except:
                    continue
            
            await asyncio.sleep(1)
            
            # Submit
            submit_selectors = [
                'button[name="websubmit"]',
                'button[type="submit"]',
                'input[type="submit"]',
            ]
            
            for selector in submit_selectors:
                try:
                    await self.page.click(selector)
                    self.log_debug(f"✅ Clicked submit")
                    break
                except:
                    continue
            
            self.account_data['phone'] = phone
            await asyncio.sleep(5)
            
            self.log_debug("✅ Phone submission complete")
            
        except Exception as e:
            self.log_debug(f"❌ Phone error: {e}")
            raise
    
    async def enter_otp(self, otp: str) -> bool:
        """Enter OTP with logging."""
        try:
            self.log_debug(f"🔐 Entering OTP: {otp}")
            
            await asyncio.sleep(2)
            
            otp_selectors = [
                'input[name="code"]',
                'input[name="confirmation_code"]',
            ]
            
            for selector in otp_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=20000)
                    await self.page.fill(selector, otp)
                    self.log_debug(f"✅ OTP entered")
                    break
                except:
                    continue
            
            await asyncio.sleep(1)
            
            # Submit
            await self.page.click('button[type="submit"]')
            await asyncio.sleep(5)
            
            current_url = self.page.url
            self.log_debug(f"Final URL: {current_url}")
            
            if '/reg/' not in current_url:
                self.log_debug("✅ SUCCESS!")
                self.account_data['status'] = 'success'
                return True
            else:
                self.log_debug("⚠️ Uncertain")
                return False
                
        except Exception as e:
            self.log_debug(f"❌ OTP error: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup with logging."""
        try:
            self.log_debug("🧹 Cleaning up...")
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.log_debug("✅ Cleanup complete")
        except Exception as e:
            self.log_debug(f"Cleanup error: {e}")
    
    def get_debug_log(self) -> str:
        """Get debug log as string."""
        return '\n'.join(self.debug_info)


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
        
        logger.info(f"💾 Saved")
        
    except Exception as e:
        logger.error(f"Save error: {e}")


# Telegram handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Facebook Bot (Debug Mode)** \n\n"
        "/create - Start\n"
        "/cancel - Cancel\n\n"
        "This version shows detailed logs.",
        parse_mode='Markdown'
    )


async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'creator' in context.user_data:
        await update.message.reply_text("⚠️ Already running. /cancel first")
        return ConversationHandler.END
    
    status_msg = await update.message.reply_text(
        "🚀 **Starting...** \n\n"
        "⏳ This takes 1-2 minutes\n"
        "I'll send updates...",
        parse_mode='Markdown'
    )
    
    try:
        headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        creator = FacebookAccountCreator(headless=headless)
        context.user_data['creator'] = creator
        
        # Send progress updates
        await status_msg.edit_text("⏳ Setting up browser...")
        await asyncio.sleep(1)
        
        await status_msg.edit_text("⏳ Opening Facebook...")
        
        account_data = await creator.start_signup()
        
        # Send debug log
        debug_log = creator.get_debug_log()
        
        # Split if too long
        if len(debug_log) > 3000:
            debug_log = debug_log[-3000:]
        
        await update.message.reply_text(
            f"```\n{debug_log}\n```",
            parse_mode='Markdown'
        )
        
        info_msg = f"""
✅ **Form Filled!** 
👤 {account_data['first_name']} {account_data['last_name']}
🎂 {account_data['birth_day']}/{account_data['birth_month']}/{account_data['birth_year']}
🔐 `{account_data['password']}`

📱 **Send phone now:** Example: `+8801712345678`
        """
        await update.message.reply_text(info_msg, parse_mode='Markdown')
        
        return WAITING_PHONE
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        
        # Send debug log
        if 'creator' in context.user_data:
            try:
                debug_log = context.user_data['creator'].get_debug_log()
                if debug_log:
                    await update.message.reply_text(f"```\n{debug_log[-2000:]}\n```", parse_mode='Markdown')
            except:
                pass
            
            try:
                await context.user_data['creator'].cleanup()
            except:
                pass
            del context.user_data['creator']
        
        await update.message.reply_text(
            f"❌ **Error** \n\n`{str(e)}`\n\nCheck logs above for details",
            parse_mode='Markdown'
        )
        return ConversationHandler.END


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    
    if not phone.startswith('+'):
        await update.message.reply_text("❌ Must start with +")
        return WAITING_PHONE
    
    await update.message.reply_text(f"📱 Submitting {phone}...")
    
    try:
        creator = context.user_data.get('creator')
        if not creator:
            await update.message.reply_text("❌ Session expired")
            return ConversationHandler.END
        
        await creator.enter_phone_number(phone)
        
        # Send debug log
        debug_log = creator.get_debug_log()
        await update.message.reply_text(f"```\n{debug_log[-1000:]}\n```", parse_mode='Markdown')
        
        await update.message.reply_text(
            "✅ **Phone sent!** \n\n"
            "📬 Check SMS\n"
            "Send OTP code",
            parse_mode='Markdown'
        )
        
        return WAITING_OTP
        
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")
        
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
    
    if not otp.isdigit():
        await update.message.reply_text("❌ Numbers only")
        return WAITING_OTP
    
    await update.message.reply_text(f"🔐 Verifying {otp}...")
    
    try:
        creator = context.user_data.get('creator')
        if not creator:
            await update.message.reply_text("❌ Session expired")
            return ConversationHandler.END
        
        success = await creator.enter_otp(otp)
        
        # Send debug log
        debug_log = creator.get_debug_log()
        await update.message.reply_text(f"```\n{debug_log[-1000:]}\n```", parse_mode='Markdown')
        
        if success:
            save_account(creator.account_data)
            
            msg = f"""
🎉 **SUCCESS!** 
👤 {creator.account_data['first_name']} {creator.account_data['last_name']}
📱 `{creator.account_data['phone']}`
🔐 `{creator.account_data['password']}`

✅ Saved!
            """
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Failed or uncertain")
        
        await creator.cleanup()
        if 'creator' in context.user_data:
            del context.user_data['creator']
        
        return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")
        
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


def main():
    Thread(target=run_flask, daemon=True).start()
    logger.info(f"🌐 Flask on port {os.getenv('PORT', '8080')}")
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ No token!")
        return
    
    if not os.path.exists('.env'):
        os.environ['HEADLESS'] = 'true'
    
    logger.info("🤖 Starting bot (DEBUG MODE)...")
    
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
    application.add_handler(conv_handler)
    application.add_handler(error_handler)
    
    logger.info("✅ Bot ready (debug mode)!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
