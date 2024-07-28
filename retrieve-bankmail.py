#!/usr/bin/env python3

"""
Usage: retrieve-bankmail.py [OPTIONS]

Retrieve bankmail from Bankwest Online Banking
"""

import sys
import asyncio
import os
import logging
from logging import Logger
import argparse
import coloredlogs
import verboselogs
from getpass import getpass
from playwright.async_api import async_playwright, Page
from dotenv import load_dotenv

class BankMessage():
    """Class representing a Bankwest bank mail message"""
    id: str
    content: str
    datedate: str
    sender: str
    subject: str
    _logger: Logger

    def __init__(self, id: str, subject: str, sender: str, date: str, _logger: Logger):
        self.id = id
        self.subject = subject
        self.sender = sender
        self.date = date
        self._logger = _logger

    def set_content(self, message: str):
        """Set the content of the message"""
        self.content = message

    def log(self):
        """Log the message"""
        self._logger.info("ID: %s", self.id)
        self._logger.info("From: %s", self.sender)
        self._logger.info("Subject: %s", self.subject)
        self._logger.info("Date: %s", self.date)
        self._logger.info("Content: %s", self.content)


# Load environment variables from a .env file (if using dotenv)
load_dotenv()

coloredlogs.DEFAULT_LOG_FORMAT='%(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)-8s %(message)s'
# Make the log level more visible on my dark terminal background
coloredlogs.DEFAULT_FIELD_STYLES['levelname']['bright'] = True
coloredlogs.DEFAULT_LEVEL_STYLES['info']['color'] = 'cyan'

verboselogs.install()
logger = verboselogs.VerboseLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

LOG_LEVEL = 'INFO'

LOGIN_PAGE = 'https://ibs.bankwest.com.au/Session/PersonalLogin'
MAIL_PAGE = 'https://ibs.bankwest.com.au/SecureMailWeb/MailPage.aspx?app=cm'
MESSAGE_PAGE = 'https://ibs.bankwest.com.au/SecureMailWeb/ReadMailPage.aspx?msgid=%s&status=R'

parser = argparse.ArgumentParser(description='')
parser.add_argument('-v', '--verbose', action='store_true', help='verbose logging')
parser.add_argument('-d', '--debug', action='store_true', help='debug logging')
parser.add_argument('-s', '--show-browser', dest='show_browser', action='store_true', help='display the browser')
parser.add_argument('-l', '--limit', type=int, help='limit for the amount of mail returned')
parser.add_argument('-g', '--log-level', dest='log_level', type=str, help='manually set the log level')

args = parser.parse_args()

if args.debug:
    LOG_LEVEL='DEBUG'
elif args.verbose:
    LOG_LEVEL='VERBOSE'
elif args.log_level:
    args.log_level = args.log_level.lower()
    if args.log_level.upper() in ['INFO', 'DEBUG', 'VERBOSE', 'NOTICE', 'SPAM', 'WARNING']:
        LOG_LEVEL=args.log_level.upper()

coloredlogs.install(level=LOG_LEVEL, logger=logger)

logger.debug('settings log level to %s', LOG_LEVEL)

def get_credentials():
    # Get credentials from environment variables
    pan = os.getenv('PAN')
    password = os.getenv('PASSWORD')

    if not pan or not password:
        logger.warning('no credentials in environment')
        pan = input('Enter your Bankwest PAN: ')
        password = getpass('Enter your Bankwest online banking password: ')

    if not pan or not password:
        logger.critical('Unable to log into online banking without a PAN and password')
        sys.exit(1)

    return {
        'pan': pan,
        'password': password
    }

async def login(page: Page, pan: str, password: str):
    """Perform login to Bankwest Online Banking"""
    logger.verbose(f'loading {LOGIN_PAGE}')
    # Navigate to the login page
    await page.goto(LOGIN_PAGE)

    # Enter username
    await page.fill('input[name="PAN"]', pan)

    # Enter password
    await page.fill('input[name="Password"]', password)

    # Click the login button
    await page.click('button[name="button"]')

    # Wait for navigation to complete (adjust as necessary for your bank's site)
    logger.verbose('waiting for page to load')
    await page.wait_for_selector('.logoutButton')

async def go_to_mail_page(page: Page):
    """Navigate to the messages page"""
    logger.verbose('navigating to mail page')
    await page.goto(MAIL_PAGE)

    # Wait for messages to load
    logger.verbose('waiting for mail page %s to load', MAIL_PAGE)
    await page.wait_for_selector('#leftColumn')

async def get_message_content(message: BankMessage, page: Page) -> str:
    """Get the message content"""
    mail_link = MESSAGE_PAGE % (message.id)
    logger.verbose('loading message %s', message.id)
    await page.goto(mail_link)

    selector = 'span[id$="lblBody"]'

    # Wait for messages to load
    logger.verbose('waiting for message to load')
    await page.wait_for_selector(selector)

    message_body = await page.query_selector(selector)
    message_content = await message_body.inner_text()

    return message_content.replace('<br>', '\n')

async def login_and_scrape_bank_messages():
    """The main function that logs into BOB and grabs your bankmail messages"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not args.show_browser)
        context = await browser.new_context()
        page = await context.new_page()

        credentials = get_credentials()

        await login(page, credentials.get('pan'), credentials.get('password'))

        await go_to_mail_page(page)

        # Get the page content
        logger.verbose('getting page content')

        bank_messages = []

        # Scrape messages
        messages = await page.query_selector_all('.MasterTable_default > tbody > tr')
        if args.limit is not None:
            messages = messages[0:args.limit]

        logger.debug('retrieved %s messages', len(messages))

        for message in messages:
            subject_element = await message.query_selector('a > div')
            subject = await subject_element.inner_text()

            elements = await message.query_selector_all('td')
            date = await elements[2].inner_text()
            sender_element = await elements[4].query_selector('div')
            sender = await sender_element.inner_text()

            id_element = await message.query_selector('td > input')
            message_id = await id_element.get_attribute('value')

            bank_message = BankMessage(message_id, subject, sender, date, logger)

            bank_messages.append(bank_message)


        for message in bank_messages:
            message_content = await get_message_content(message, page)
            message.set_content(message_content)
            message.log()

        logger.info('finished getting mail')

        # Close browser
        await browser.close()

# Run the async function
asyncio.run(login_and_scrape_bank_messages())
