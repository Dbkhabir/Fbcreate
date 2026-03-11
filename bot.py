class FacebookAccountCreator:
    """Handles Facebook account creation automation using Playwright."""
    
    def __init__(self, headless: bool = True):
        """Initialize the Facebook account creator."""
        self.headless = headless
        self.browser: Browser = None
        self.page: Page = None
        self.playwright: Playwright = None
        self.account_data: Dict[str, Any] = {}
        
    async def setup_browser(self):
        """Set up Playwright browser with anti-detection measures."""
        logger.info("Setting up Playwright browser...")
        
        self.playwright = await async_playwright().start()
        
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
            ],
            timeout=60000
        )
        
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768},
            locale='en-US',
            timezone_id='America/New_York',
        )
        
        context.set_default_timeout(30000)
        
        self.page = await context.new_page()
        
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
        """Type text with human-like delays."""
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
        """Start Facebook signup process and fill initial fields."""
        try:
            await self.setup_browser()
            
            self.account_data = self.generate_account_data()
            
            logger.info("Navigating to Facebook signup page...")
            await self.page.goto('https://www.facebook.com/reg/', 
                                wait_until='domcontentloaded', 
                                timeout=60000)
            await self.random_delay(3, 5)
            
            logger.info("Waiting for form to be ready...")
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            
            logger.info("Filling first name...")
            await self.page.wait_for_selector('input[name="firstname"]', timeout=20000)
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
        """Enter phone number and submit."""
        try:
            logger.info(f"Entering phone number: {phone}")
            
            await self.page.wait_for_selector('input[name="reg_email__"]', timeout=20000)
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
        """Enter OTP code and complete signup."""
        try:
            logger.info(f"Entering OTP: {otp}")
            
            await self.page.wait_for_selector('input[name="code"]', timeout=30000)
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
