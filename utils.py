"""
Utility functions for the Telegram Task & Reward Bot
"""

from telegram import ReplyKeyboardMarkup
import config

def get_main_keyboard(user_id: int = None) -> ReplyKeyboardMarkup:
    """Create main menu reply keyboard"""
    keyboard = config.MAIN_MENU_BUTTONS.copy()
    
    # Add admin button if user is admin
    if user_id and user_id in config.ADMIN_USER_IDS:
        keyboard.append([f"{config.EMOJI['ADMIN']} Admin Panel"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Create keyboard with back button only"""
    keyboard = [[config.COMMON_BUTTONS["BACK_TO_MAIN"]]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Create keyboard with cancel button"""
    keyboard = [[config.COMMON_BUTTONS["CANCEL"]]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Create admin menu keyboard"""
    keyboard = config.ADMIN_MENU_BUTTONS
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def format_balance(amount: float) -> str:
    """Format balance for display"""
    return f"💰 {amount:.2f} Coins"

def format_number(num: int) -> str:
    """Format large numbers with commas"""
    return f"{num:,}"

def validate_amount(amount: str) -> float:
    """Validate and convert amount string to float"""
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return None
        return amount_float
    except ValueError:
        return None

def is_admin(user_id: int) -> bool:
    """Check if user is an admin"""
    return user_id in config.ADMIN_USER_IDS

def create_referral_link(user_id: int) -> str:
    """Create referral link for a user"""
    return f"https://t.me/{config.BOT_USERNAME}?start=ref_{user_id}"
