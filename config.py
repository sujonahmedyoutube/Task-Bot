"""
Configuration file for the Telegram Task & Reward Bot
"""

import os

# Bot Configuration - আপনার টোকেন দেওয়া আছে
BOT_TOKEN = "8691371811:AAH1EWuhbIImkl-2x-yOWlPikkP1NjEAeUg"

# Bot Username (for referral links)
BOT_USERNAME = "NeroxaTasks_Bot"

# Firebase Configuration
FIREBASE_DB_URL = "https://telegram-bot-e6095-default-rtdb.firebaseio.com/"

# Firebase Credentials File Name
FIREBASE_CREDENTIALS_FILE = "telegram-bot-e6095-firebase-adminsdk-fbsvc-c4bce032f0.json"

# Admin Configuration - আপনার এডমিন আইডি দেওয়া আছে
ADMIN_USER_IDS = [8502686983]

# Referral System
REFERRAL_BONUS = 5.0

# Withdrawal Settings
DEFAULT_MIN_WITHDRAWAL = 10.0
WITHDRAWAL_ENABLED = True
WITHDRAW_START_TIME = "00:00"
WITHDRAW_END_TIME = "23:59"

# Task Settings
MAX_PENDING_SUBMISSIONS = 5

# Emoji Constants
EMOJI = {
    "TASK": "📋",
    "WITHDRAW": "💰",
    "BALANCE": "🧾",
    "REFER": "👥",
    "REDEEM": "🎁",
    "SUPPORT": "🆘",
    "LEADERBOARD": "🏆",
    "BACK": "🔙",
    "HOME": "🏠",
    "CHECK": "✅",
    "CROSS": "❌",
    "PENDING": "⏳",
    "APPROVED": "✅",
    "REJECTED": "❌",
    "CHANNEL": "📢",
    "USER": "👤",
    "STATS": "📊",
    "GIFT": "🎀",
    "MEGAPHONE": "📢",
    "LOCK": "🔒",
    "UNLOCK": "🔓",
    "ADMIN": "⚙️",
    "YES": "✅",
    "NO": "❌",
    "CANCEL": "🚫"
}

# Main Menu Buttons (Reply Keyboard)
MAIN_MENU_BUTTONS = [
    [f"{EMOJI['TASK']} Tasks", f"{EMOJI['WITHDRAW']} Withdraw"],
    [f"{EMOJI['BALANCE']} Balance", f"{EMOJI['REFER']} Refer"],
    [f"{EMOJI['REDEEM']} Redeem", f"{EMOJI['LEADERBOARD']} Leaderboard"],
    [f"{EMOJI['SUPPORT']} Support"]
]

# Admin Menu Buttons (Reply Keyboard)
ADMIN_MENU_BUTTONS = [
    ["➕ Add Task", "🗑 Remove Task"],
    ["⏳ Pending Subs", "💸 Manage Withdrawals"],
    ["🎁 Create Gift", "📢 Broadcast"],
    ["👥 Manage Users", "🔗 Force Join"],
    ["📊 Analytics", "🏠 Back to Main"]
]

# Common Buttons
COMMON_BUTTONS = {
    "BACK_TO_MAIN": "🏠 Main Menu",
    "CANCEL": f"{EMOJI['CANCEL']} Cancel"
}

# Support Information
SUPPORT_CONTACT = "@NeroxaSupport"

# Session States
MAIN_MENU = 0
TASKS_MENU = 1
WITHDRAW_MENU = 2
REFERRAL_MENU = 3
ADMIN_MENU = 4
VIEWING_TASKS = 5
REQUESTING_WITHDRAW = 6
REDEEMING_CODE = 7
VIEWING_LEADERBOARD = 8
VIEWING_BALANCE = 9
ADDING_TASK = 10
REMOVING_TASK = 11
PENDING_SUBMISSIONS = 12
MANAGING_WITHDRAWALS = 13
CREATING_GIFT_CODE = 14
BROADCASTING = 15
MANAGING_USERS = 16
FORCE_JOIN_MENU = 17
VIEWING_ANALYTICS = 18
