"""
User handlers for the Telegram Task & Reward Bot
"""

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import config
import utils
from database import Database

db = Database()

# Conversation states
AWAITING_TASK_SELECTION = 1
AWAITING_TASK_SUBMIT_SCREENSHOT = 2
AWAITING_TASK_SUBMIT_NOTE = 3
AWAITING_WITHDRAW_AMOUNT = 4
AWAITING_GIFT_CODE = 5
AWAITING_LEADERBOARD_TYPE = 6

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    
    # Check for referral code
    referrer_id = None
    if context.args and len(context.args) > 0:
        if context.args[0].startswith('ref_'):
            try:
                referrer_id = int(context.args[0].split('_')[1])
                if referrer_id == user_id:
                    referrer_id = None
            except:
                pass
    
    # Get or create user
    existing_user = await db.get_user(user_id)
    if not existing_user:
        await db.create_user(user_id, user.username, referrer_id)
        welcome_msg = f"🎉 Welcome {user.first_name}!\n\nComplete tasks to earn rewards!\n\nUse the buttons below to navigate:"
    else:
        welcome_msg = f"👋 Welcome back, {user.first_name}!\n\nWhat would you like to do today?"
    
    await update.message.reply_text(
        welcome_msg,
        reply_markup=get_main_keyboard(user_id)
    )
    
    return config.MAIN_MENU

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle main menu button presses"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == f"{config.EMOJI['TASK']} Tasks":
        return await show_tasks_menu(update, context)
    
    elif text == f"{config.EMOJI['WITHDRAW']} Withdraw":
        return await show_withdraw_menu(update, context)
    
    elif text == f"{config.EMOJI['BALANCE']} Balance":
        return await show_balance(update, context)
    
    elif text == f"{config.EMOJI['REFER']} Refer":
        return await show_referral_menu(update, context)
    
    elif text == f"{config.EMOJI['REDEEM']} Redeem":
        return await start_redeem(update, context)
    
    elif text == f"{config.EMOJI['LEADERBOARD']} Leaderboard":
        return await show_leaderboard_menu(update, context)
    
    elif text == f"{config.EMOJI['SUPPORT']} Support":
        return await show_support(update, context)
    
    elif text == f"{config.EMOJI['ADMIN']} Admin Panel" and user_id in config.ADMIN_USER_IDS:
        from admin import show_admin_menu
        return await show_admin_menu(update, context)
    
    elif text == config.COMMON_BUTTONS["BACK_TO_MAIN"]:
        await update.message.reply_text(
            "🏠 Main Menu:",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    else:
        await update.message.reply_text(
            "❌ Unknown command. Please use the buttons below:",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU

async def show_tasks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show tasks menu"""
    keyboard = [
        ["📋 List Available Tasks"],
        [config.COMMON_BUTTONS["BACK_TO_MAIN"]]
    ]
    
    await update.message.reply_text(
        f"{config.EMOJI['TASK']} *Tasks Menu*\n\n"
        f"📌 Click 'List Available Tasks' to see all tasks\n\n"
        f"💡 Complete tasks and earn rewards!\n\n"
        f"📝 To submit a task:\n"
        f"Type: `/submit_TASKID`\n"
        f"Example: `/submit_abc123`\n\n"
        f"Then send a screenshot as proof.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return config.TASKS_MENU

async def handle_tasks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle tasks menu button presses"""
    text = update.message.text
    
    if text == "📋 List Available Tasks":
        return await list_tasks(update, context)
    
    elif text == config.COMMON_BUTTONS["BACK_TO_MAIN"]:
        await update.message.reply_text(
            "🏠 Main Menu:",
            reply_markup=get_main_keyboard(update.effective_user.id)
        )
        return config.MAIN_MENU
    
    else:
        await update.message.reply_text(
            "❌ Please use the buttons below:",
            reply_markup=ReplyKeyboardMarkup([
                ["📋 List Available Tasks"],
                [config.COMMON_BUTTONS["BACK_TO_MAIN"]]
            ], resize_keyboard=True)
        )
        return config.TASKS_MENU

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """List all available tasks"""
    tasks = await db.get_active_tasks()
    
    if not tasks:
        await update.message.reply_text(
            "📭 No tasks available at the moment.\n\nPlease check back later!",
            reply_markup=ReplyKeyboardMarkup([
                ["🔄 Refresh"],
                [config.COMMON_BUTTONS["BACK_TO_MAIN"]]
            ], resize_keyboard=True)
        )
        return config.TASKS_MENU
    
    # Store tasks in context
    context.user_data['available_tasks'] = tasks
    
    # Send each task
    for i, task in enumerate(tasks, 1):
        message = f"📋 *Task #{i}*\n\n"
        message += f"*{task['title']}*\n\n"
        message += f"📝 *Description:*\n{task['description']}\n\n"
        message += f"💰 *Reward:* {task['reward']} Coins\n\n"
        message += f"🔗 *Link:* {task['link']}\n\n"
        message += f"📝 *To Submit:*\n"
        message += f"Send: `/submit_{task['id']}`\n"
        message += f"Then send your screenshot proof."
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown'
        )
    
    keyboard = [
        ["🔄 Refresh"],
        [config.COMMON_BUTTONS["BACK_TO_MAIN"]]
    ]
    
    await update.message.reply_text(
        "✅ Use `/submit_TASKID` to submit a task completion.\n"
        "Example: `/submit_abc123`\n\n"
        "Make sure to attach a screenshot with your submission!",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return config.TASKS_MENU

async def submit_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /submit command - starts task submission process"""
    user_id = update.effective_user.id
    
    # Check if command has task_id
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Please specify task ID.\n"
            "Usage: `/submit_TASKID`\n"
            "Example: `/submit_abc123`",
            parse_mode='Markdown'
        )
        return config.MAIN_MENU
    
    task_id = context.args[0]
    
    # Verify task exists
    task = await db.get_task(task_id)
    if not task or task.get('status') != 'active':
        await update.message.reply_text(
            "❌ Invalid task ID or task is no longer available.",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    # Store task_id in context
    context.user_data['submitting_task_id'] = task_id
    context.user_data['submitting_task_reward'] = task['reward']
    
    await update.message.reply_text(
        f"📸 *Submit Task: {task['title']}*\n\n"
        f"💰 Reward: {task['reward']} Coins\n\n"
        f"Please send a screenshot proving you completed the task.\n\n"
        f"Send /cancel to cancel.",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_TASK_SUBMIT_SCREENSHOT

async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive screenshot from user"""
    user_id = update.effective_user.id
    
    if not update.message.photo:
        await update.message.reply_text(
            "❌ Please send a valid photo as proof.\n\n"
            "Send /cancel to cancel.",
            reply_markup=get_cancel_keyboard()
        )
        return AWAITING_TASK_SUBMIT_SCREENSHOT
    
    # Get the largest photo
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    photo_url = photo_file.file_path
    
    context.user_data['submission_screenshot'] = photo_url
    
    await update.message.reply_text(
        "📝 Please add a note (optional) or send /skip to skip:\n\n"
        "Send /cancel to cancel.",
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_TASK_SUBMIT_NOTE

async def receive_submission_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive note for submission"""
    user_id = update.effective_user.id
    note = update.message.text
    
    if note == '/cancel':
        await update.message.reply_text(
            "❌ Task submission cancelled.",
            reply_markup=get_main_keyboard(user_id)
        )
        context.user_data.pop('submitting_task_id', None)
        context.user_data.pop('submission_screenshot', None)
        return config.MAIN_MENU
    
    if note == '/skip':
        note = None
    
    task_id = context.user_data.get('submitting_task_id')
    screenshot_url = context.user_data.get('submission_screenshot')
    
    # Create submission
    success = await db.create_submission(user_id, task_id, screenshot_url, note)
    
    if success:
        await update.message.reply_text(
            "✅ Task submission sent!\n\n"
            "Admin will review it and add rewards upon approval.\n\n"
            "You will be notified when your submission is processed.",
            reply_markup=get_main_keyboard(user_id)
        )
    else:
        await update.message.reply_text(
            "❌ Failed to submit task. Please try again.",
            reply_markup=get_main_keyboard(user_id)
        )
    
    # Clear context
    context.user_data.pop('submitting_task_id', None)
    context.user_data.pop('submission_screenshot', None)
    
    return config.MAIN_MENU

async def skip_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip adding note to submission"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    task_id = context.user_data.get('submitting_task_id')
    screenshot_url = context.user_data.get('submission_screenshot')
    
    success = await db.create_submission(user_id, task_id, screenshot_url, None)
    
    if success:
        await query.edit_message_text(
            "✅ Task submission sent!\n\n"
            "Admin will review it and add rewards upon approval.",
            reply_markup=get_main_keyboard(user_id)
        )
    else:
        await query.edit_message_text(
            "❌ Failed to submit task. Please try again.",
            reply_markup=get_main_keyboard(user_id)
        )
    
    context.user_data.pop('submitting_task_id', None)
    context.user_data.pop('submission_screenshot', None)
    
    return config.MAIN_MENU

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user balance"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ User not found!")
        return config.MAIN_MENU
    
    referral_earnings = user.get('referrals', 0) * config.REFERRAL_BONUS
    
    message = f"💰 *Your Balance*\n\n"
    message += f"┌───────────────────┐\n"
    message += f"│ Current Balance:  {user['balance']:.2f} Coins\n"
    message += f"├───────────────────┤\n"
    message += f"│ Total Earned:     {user.get('total_earned', 0):.2f} Coins\n"
    message += f"│ Total Withdrawn:  {user.get('total_withdrawn', 0):.2f} Coins\n"
    message += f"│ Referral Bonus:   {referral_earnings:.2f} Coins\n"
    message += f"├───────────────────┤\n"
    message += f"│ Total Referrals:  {user.get('referrals', 0)}\n"
    message += f"└───────────────────┘\n\n"
    
    if user['balance'] >= config.DEFAULT_MIN_WITHDRAWAL:
        message += f"✅ You can withdraw! (Min: {config.DEFAULT_MIN_WITHDRAWAL} Coins)"
    else:
        needed = config.DEFAULT_MIN_WITHDRAWAL - user['balance']
        message += f"⚠️ Need {needed:.2f} more coins to withdraw"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([
            ["💸 Request Withdraw", "🏠 Main Menu"]
        ], resize_keyboard=True)
    )
    
    return config.VIEWING_BALANCE

async def show_withdraw_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show withdrawal menu"""
    keyboard = [
        ["💰 Request Withdraw", "📜 Withdraw History"],
        ["🏠 Main Menu"]
    ]
    
    await update.message.reply_text(
        f"{config.EMOJI['WITHDRAW']} *Withdrawal Menu*\n\n"
        f"💰 Minimum Withdrawal: {config.DEFAULT_MIN_WITHDRAWAL} Coins\n\n"
        f"📌 Withdrawals are processed within 24-48 hours.\n\n"
        f"Select an option below:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return config.WITHDRAW_MENU

async def handle_withdraw_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle withdrawal menu button presses"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "💰 Request Withdraw":
        return await request_withdrawal(update, context)
    
    elif text == "📜 Withdraw History":
        await update.message.reply_text(
            "📜 *Withdrawal History*\n\n"
            "Your withdrawal requests will appear here.\n\n"
            "Feature coming soon!",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([
                ["🏠 Main Menu"]
            ], resize_keyboard=True)
        )
        return config.WITHDRAW_MENU
    
    elif text == "🏠 Main Menu":
        await update.message.reply_text(
            "🏠 Main Menu:",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    else:
        await update.message.reply_text(
            "❌ Please use the buttons below:",
            reply_markup=ReplyKeyboardMarkup([
                ["💰 Request Withdraw", "📜 Withdraw History"],
                ["🏠 Main Menu"]
            ], resize_keyboard=True)
        )
        return config.WITHDRAW_MENU

async def request_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start withdrawal request"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ User not found!")
        return config.MAIN_MENU
    
    # Check if withdrawals are enabled
    if not config.WITHDRAWAL_ENABLED:
        await update.message.reply_text(
            "❌ Withdrawals are currently disabled.\n\n"
            f"Withdrawal hours: {config.WITHDRAW_START_TIME} - {config.WITHDRAW_END_TIME}",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    # Check minimum amount
    if user['balance'] < config.DEFAULT_MIN_WITHDRAWAL:
        needed = config.DEFAULT_MIN_WITHDRAWAL - user['balance']
        await update.message.reply_text(
            f"❌ Insufficient balance!\n\n"
            f"Minimum withdrawal: {config.DEFAULT_MIN_WITHDRAWAL} Coins\n"
            f"You need {needed:.2f} more coins.\n\n"
            f"Complete more tasks to reach the minimum!",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    await update.message.reply_text(
        f"💰 *Request Withdrawal*\n\n"
        f"💰 Your Balance: {user['balance']:.2f} Coins\n"
        f"💰 Minimum: {config.DEFAULT_MIN_WITHDRAWAL} Coins\n\n"
        f"Please send the amount you want to withdraw:\n\n"
        f"Send /cancel to cancel.",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_WITHDRAW_AMOUNT

async def process_withdrawal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process withdrawal amount"""
    user_id = update.effective_user.id
    amount_text = update.message.text
    
    if amount_text == '/cancel':
        await update.message.reply_text(
            "❌ Withdrawal cancelled.",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            f"❌ Invalid amount! Please enter a valid number.\n\n"
            f"Minimum: {config.DEFAULT_MIN_WITHDRAWAL} Coins\n\n"
            f"Send /cancel to cancel.",
            reply_markup=get_cancel_keyboard()
        )
        return AWAITING_WITHDRAW_AMOUNT
    
    user = await db.get_user(user_id)
    
    if not user or user['balance'] < amount:
        await update.message.reply_text(
            f"❌ Insufficient balance!\n\n"
            f"Your balance: {user['balance'] if user else 0:.2f} Coins\n"
            f"Requested: {amount:.2f} Coins\n\n"
            "Please request a smaller amount.",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    if amount < config.DEFAULT_MIN_WITHDRAWAL:
        await update.message.reply_text(
            f"❌ Amount is below minimum!\n\n"
            f"Minimum withdrawal: {config.DEFAULT_MIN_WITHDRAWAL} Coins\n"
            f"Requested: {amount:.2f} Coins",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    # Create withdrawal request
    success = await db.create_withdrawal(user_id, amount)
    
    if success:
        await update.message.reply_text(
            f"✅ Withdrawal request of {amount:.2f} Coins submitted!\n\n"
            f"📌 Your request will be processed within 24-48 hours.\n"
            f"📌 You will be notified when it's approved/rejected.\n\n"
            f"Thank you for using our bot!",
            reply_markup=get_main_keyboard(user_id)
        )
    else:
        await update.message.reply_text(
            "❌ Failed to submit withdrawal request. Please try again.",
            reply_markup=get_main_keyboard(user_id)
        )
    
    return config.MAIN_MENU

async def show_referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show referral menu"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    
    referral_link = utils.create_referral_link(user_id)
    
    message = f"👥 *Referral Program*\n\n"
    message += f"🎁 Invite friends and earn {config.REFERRAL_BONUS} Coins for each referral!\n\n"
    message += f"📊 *Your Stats:*\n"
    message += f"┌─────────────────────┐\n"
    message += f"│ Total Referrals:    {user.get('referrals', 0)}\n"
    message += f"│ Earnings from Ref:  {user.get('referrals', 0) * config.REFERRAL_BONUS:.2f} Coins\n"
    message += f"└─────────────────────┘\n\n"
    message += f"🔗 *Your Referral Link:*\n"
    message += f"`{referral_link}`\n\n"
    message += f"📤 Share this link with your friends!\n"
    message += f"💰 You earn {config.REFERRAL_BONUS} Coins for each friend who joins!\n\n"
    message += f"💡 *How it works:*\n"
    message += f"1. Share your unique link with friends\n"
    message += f"2. Friend joins using your link\n"
    message += f"3. You automatically get {config.REFERRAL_BONUS} Coins!\n"
    message += f"4. Your friend also gets started!"
    
    keyboard = [
        ["📤 Share Link", "📊 Referral Stats"],
        ["🏠 Main Menu"]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return config.REFERRAL_MENU

async def handle_referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle referral menu button presses"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "📤 Share Link":
        user = await db.get_user(user_id)
        referral_link = utils.create_referral_link(user_id)
        
        await update.message.reply_text(
            f"📤 *Share Your Referral Link*\n\n"
            f"Send this link to your friends:\n\n"
            f"`{referral_link}`\n\n"
            f"💰 You earn {config.REFERRAL_BONUS} Coins for each friend who joins!",
            parse_mode='Markdown'
        )
        return config.REFERRAL_MENU
    
    elif text == "📊 Referral Stats":
        user = await db.get_user(user_id)
        
        message = f"📊 *Your Referral Statistics*\n\n"
        message += f"👥 Total Referrals: {user.get('referrals', 0)}\n"
        message += f"💰 Earnings: {user.get('referrals', 0) * config.REFERRAL_BONUS:.2f} Coins\n\n"
        message += f"🎯 Keep sharing to earn more!"
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown'
        )
        return config.REFERRAL_MENU
    
    elif text == "🏠 Main Menu":
        await update.message.reply_text(
            "🏠 Main Menu:",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    else:
        await update.message.reply_text(
            "❌ Please use the buttons below:",
            reply_markup=ReplyKeyboardMarkup([
                ["📤 Share Link", "📊 Referral Stats"],
                ["🏠 Main Menu"]
            ], resize_keyboard=True)
        )
        return config.REFERRAL_MENU

async def start_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start gift code redemption"""
    await update.message.reply_text(
        f"{config.EMOJI['GIFT']} *Redeem Gift Code*\n\n"
        f"Please enter your gift code:\n\n"
        f"Send /cancel to cancel.",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_GIFT_CODE

async def process_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process gift code redemption"""
    user_id = update.effective_user.id
    code = update.message.text.strip().upper()
    
    if code == '/cancel':
        await update.message.reply_text(
            "❌ Redemption cancelled.",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    result = await db.redeem_gift_code(code, user_id)
    
    if result['success']:
        await update.message.reply_text(
            f"✅ {result['message']}\n\n"
            f"Your balance has been updated!",
            reply_markup=get_main_keyboard(user_id)
        )
    else:
        await update.message.reply_text(
            f"❌ {result['message']}\n\n"
            f"Please check the code and try again.",
            reply_markup=get_main_keyboard(user_id)
        )
    
    return config.MAIN_MENU

async def show_leaderboard_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show leaderboard menu"""
    keyboard = [
        ["💰 Top Earners", "👥 Top Referrers"],
        ["🏠 Main Menu"]
    ]
    
    await update.message.reply_text(
        f"{config.EMOJI['LEADERBOARD']} *Leaderboard Menu*\n\n"
        f"Select the type of leaderboard you want to view:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return config.VIEWING_LEADERBOARD

async def handle_leaderboard_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle leaderboard menu button presses"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "💰 Top Earners":
        return await show_top_earners(update, context)
    
    elif text == "👥 Top Referrers":
        return await show_top_referrers(update, context)
    
    elif text == "🏠 Main Menu":
        await update.message.reply_text(
            "🏠 Main Menu:",
            reply_markup=get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    else:
        await update.message.reply_text(
            "❌ Please use the buttons below:"
        )
        return config.VIEWING_LEADERBOARD

async def show_top_earners(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show top earners leaderboard"""
    leaderboard = await db.get_leaderboard('balance', 10)
    
    message = f"💰 *Top 10 Earners (Balance)*\n\n"
    message += "┌────┬─────────────────┬──────────┐\n"
    message += "│ #  │ User            │ Balance  │\n"
    message += "├────┼─────────────────┼──────────┤\n"
    
    for i, user in enumerate(leaderboard, 1):
        username = user['username'][:15] if user['username'] else f"User_{i}"
        message += f"│ {i:<2} │ {username:<15} │ {user['balance']:>8.2f} │\n"
    
    message += "└────┴─────────────────┴──────────┘"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([
            ["🔄 Refresh", "👥 Top Referrers"],
            ["🏠 Main Menu"]
        ], resize_keyboard=True)
    )
    
    return config.VIEWING_LEADERBOARD

async def show_top_referrers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show top referrers leaderboard"""
    leaderboard = await db.get_leaderboard('referrals', 10)
    
    message = f"👥 *Top 10 Referrers*\n\n"
    message += "┌────┬─────────────────┬────────────┐\n"
    message += "│ #  │ User            │ Referrals  │\n"
    message += "├────┼─────────────────┼────────────┤\n"
    
    for i, user in enumerate(leaderboard, 1):
        username = user['username'][:15] if user['username'] else f"User_{i}"
        message += f"│ {i:<2} │ {username:<15} │ {user['referrals']:>10} │\n"
    
    message += "└────┴─────────────────┴────────────┘"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([
            ["🔄 Refresh", "💰 Top Earners"],
            ["🏠 Main Menu"]
        ], resize_keyboard=True)
    )
    
    return config.VIEWING_LEADERBOARD

async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show support information"""
    message = f"🆘 *Support Center*\n\n"
    message += f"📌 *FAQ*\n"
    message += f"• *How to earn coins?* - Complete tasks from the Tasks menu\n"
    message += f"• *When do I get rewards?* - After admin approval of your submission\n"
    message += f"• *How to withdraw?* - Go to Withdraw menu when you have minimum balance\n"
    message += f"• *Referral bonus?* - {config.REFERRAL_BONUS} Coins per referral\n"
    message += f"• *Minimum withdrawal?* - {config.DEFAULT_MIN_WITHDRAWAL} Coins\n\n"
    
    message += f"📞 *Contact Support*\n"
    message += f"For any issues or questions, please contact:\n"
    message += f"{config.SUPPORT_CONTACT}\n\n"
    
    message += f"💡 *Tips*\n"
    message += f"• Complete tasks regularly to increase your balance\n"
    message += f"• Share your referral link to earn passive income\n"
    message += f"• Check the leaderboard to see top earners\n\n"
    
    message += f"Thank you for using @{config.BOT_USERNAME}! 🎉"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=get_back_keyboard()
    )
    
    return config.MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation"""
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        "❌ Operation cancelled.",
        reply_markup=get_main_keyboard(user_id)
    )
    
    context.user_data.clear()
    return config.MAIN_MENU
