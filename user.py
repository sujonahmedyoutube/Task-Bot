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
AWAITING_TASK_SUBMIT_SCREENSHOT = 2
AWAITING_TASK_SUBMIT_NOTE = 3
AWAITING_WITHDRAW_AMOUNT = 4
AWAITING_GIFT_CODE = 5

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    
    referrer_id = None
    if context.args and len(context.args) > 0:
        if context.args[0].startswith('ref_'):
            try:
                referrer_id = int(context.args[0].split('_')[1])
                if referrer_id == user_id:
                    referrer_id = None
            except:
                pass
    
    existing_user = await db.get_user(user_id)
    if not existing_user:
        await db.create_user(user_id, user.username, referrer_id)
        welcome_msg = f"🎉 Welcome {user.first_name}!\n\nComplete tasks to earn rewards!"
    else:
        welcome_msg = f"👋 Welcome back, {user.first_name}!"
    
    await update.message.reply_text(
        welcome_msg,
        reply_markup=utils.get_main_keyboard(user_id)
    )
    return config.MAIN_MENU

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle main menu"""
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
        await update.message.reply_text("🏠 Main Menu:", reply_markup=utils.get_main_keyboard(user_id))
        return config.MAIN_MENU
    else:
        await update.message.reply_text("❌ Please use buttons:", reply_markup=utils.get_main_keyboard(user_id))
        return config.MAIN_MENU

async def show_tasks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show tasks menu"""
    keyboard = [["📋 List Available Tasks"], [config.COMMON_BUTTONS["BACK_TO_MAIN"]]]
    await update.message.reply_text(
        f"{config.EMOJI['TASK']} *Tasks Menu*\n\nUse /submit_TASKID to submit tasks",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return config.TASKS_MENU

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """List tasks"""
    tasks = await db.get_active_tasks()
    
    if not tasks:
        await update.message.reply_text("No tasks available!")
        return config.TASKS_MENU
    
    for task in tasks:
        msg = f"📋 *{task['title']}*\n💰 Reward: {task['reward']} coins\n🔗 {task['link']}\n\nTo submit: `/submit_{task['id']}`"
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    return config.TASKS_MENU

async def submit_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /submit command"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("Usage: `/submit_TASKID`", parse_mode='Markdown')
        return config.MAIN_MENU
    
    task_id = context.args[0]
    task = await db.get_task(task_id)
    
    if not task or task.get('status') != 'active':
        await update.message.reply_text("Invalid task ID!")
        return config.MAIN_MENU
    
    context.user_data['submitting_task_id'] = task_id
    await update.message.reply_text("Send screenshot proof:", reply_markup=utils.get_cancel_keyboard())
    return AWAITING_TASK_SUBMIT_SCREENSHOT

async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive screenshot"""
    user_id = update.effective_user.id
    
    if not update.message.photo:
        await update.message.reply_text("Please send a photo!", reply_markup=utils.get_cancel_keyboard())
        return AWAITING_TASK_SUBMIT_SCREENSHOT
    
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    context.user_data['submission_screenshot'] = photo_file.file_path
    
    await update.message.reply_text("Add a note or send /skip:", reply_markup=utils.get_cancel_keyboard())
    return AWAITING_TASK_SUBMIT_NOTE

async def receive_submission_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive note"""
    user_id = update.effective_user.id
    note = update.message.text if update.message.text != '/skip' else None
    
    task_id = context.user_data.get('submitting_task_id')
    screenshot = context.user_data.get('submission_screenshot')
    
    success = await db.create_submission(user_id, task_id, screenshot, note)
    
    await update.message.reply_text(
        "✅ Submission sent!" if success else "❌ Failed!",
        reply_markup=utils.get_main_keyboard(user_id)
    )
    
    context.user_data.clear()
    return config.MAIN_MENU

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show balance"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    
    if not user:
        return config.MAIN_MENU
    
    msg = f"💰 *Balance*\nCurrent: {user['balance']:.2f} coins\nTotal Earned: {user.get('total_earned', 0):.2f}\nReferrals: {user.get('referrals', 0)}"
    
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=utils.get_back_keyboard())
    return config.VIEWING_BALANCE

async def show_withdraw_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show withdraw menu"""
    keyboard = [["💰 Request Withdraw"], ["🏠 Main Menu"]]
    await update.message.reply_text(
        f"💰 Minimum: {config.DEFAULT_MIN_WITHDRAWAL} coins",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return config.WITHDRAW_MENU

async def request_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Request withdrawal"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    
    if not user or user['balance'] < config.DEFAULT_MIN_WITHDRAWAL:
        await update.message.reply_text("Insufficient balance!", reply_markup=utils.get_main_keyboard(user_id))
        return config.MAIN_MENU
    
    await update.message.reply_text("Enter amount:", reply_markup=utils.get_cancel_keyboard())
    return AWAITING_WITHDRAW_AMOUNT

async def process_withdrawal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process withdrawal"""
    user_id = update.effective_user.id
    
    try:
        amount = float(update.message.text)
    except:
        await update.message.reply_text("Invalid amount!")
        return AWAITING_WITHDRAW_AMOUNT
    
    user = await db.get_user(user_id)
    
    if amount < config.DEFAULT_MIN_WITHDRAWAL or amount > user['balance']:
        await update.message.reply_text("Invalid amount!")
        return AWAITING_WITHDRAW_AMOUNT
    
    success = await db.create_withdrawal(user_id, amount)
    await update.message.reply_text(
        "✅ Request submitted!" if success else "❌ Failed!",
        reply_markup=utils.get_main_keyboard(user_id)
    )
    return config.MAIN_MENU

async def show_referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show referral menu"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    link = utils.create_referral_link(user_id)
    
    msg = f"👥 *Referral*\nLink: {link}\nReferrals: {user.get('referrals', 0)}\nEarned: {user.get('referrals', 0) * config.REFERRAL_BONUS} coins"
    
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=utils.get_back_keyboard())
    return config.REFERRAL_MENU

async def start_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start redeem"""
    await update.message.reply_text("Enter gift code:", reply_markup=utils.get_cancel_keyboard())
    return AWAITING_GIFT_CODE

async def process_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process redeem"""
    user_id = update.effective_user.id
    code = update.message.text.strip().upper()
    
    result = await db.redeem_gift_code(code, user_id)
    await update.message.reply_text(result['message'], reply_markup=utils.get_main_keyboard(user_id))
    return config.MAIN_MENU

async def show_leaderboard_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show leaderboard"""
    leaders = await db.get_leaderboard('balance', 10)
    
    msg = "🏆 *Top Earners*\n"
    for i, u in enumerate(leaders, 1):
        msg += f"{i}. {u['username']}: {u['balance']:.2f} coins\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=utils.get_back_keyboard())
    return config.VIEWING_LEADERBOARD

async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show support"""
    msg = f"🆘 *Support*\nContact: {config.SUPPORT_CONTACT}"
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=utils.get_back_keyboard())
    return config.MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel operation"""
    user_id = update.effective_user.id
    await update.message.reply_text("Cancelled.", reply_markup=utils.get_main_keyboard(user_id))
    context.user_data.clear()
    return config.MAIN_MENU
