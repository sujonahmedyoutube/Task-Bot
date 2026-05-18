"""
Admin handlers for the Telegram Task & Reward Bot
"""

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import config
import utils
from database import Database

db = Database()

# States
AWAITING_TASK_TITLE = 10
AWAITING_TASK_DESC = 11
AWAITING_TASK_LINK = 12
AWAITING_TASK_REWARD = 13
AWAITING_GIFT_AMOUNT = 14
AWAITING_GIFT_LIMIT = 15
AWAITING_GIFT_EXPIRY = 16
AWAITING_BROADCAST = 17

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show admin panel"""
    user_id = update.effective_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await update.message.reply_text("❌ Unauthorized!", reply_markup=utils.get_main_keyboard(user_id))
        return config.MAIN_MENU
    
    await update.message.reply_text(
        "⚙️ *Admin Panel*",
        parse_mode='Markdown',
        reply_markup=utils.get_admin_keyboard()
    )
    return config.ADMIN_MENU

async def handle_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin menu"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        return config.MAIN_MENU
    
    if text == "➕ Add Task":
        return await start_add_task(update, context)
    elif text == "🗑 Remove Task":
        return await show_remove_task(update, context)
    elif text == "⏳ Pending Subs":
        return await show_pending_submissions(update, context)
    elif text == "💸 Manage Withdrawals":
        return await show_pending_withdrawals(update, context)
    elif text == "🎁 Create Gift":
        return await start_create_gift_code(update, context)
    elif text == "📢 Broadcast":
        return await start_broadcast(update, context)
    elif text == "📊 Analytics":
        return await show_analytics(update, context)
    elif text == "🏠 Back to Main":
        await update.message.reply_text("Main Menu", reply_markup=utils.get_main_keyboard(user_id))
        return config.MAIN_MENU
    
    return config.ADMIN_MENU

async def start_add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start add task"""
    await update.message.reply_text("Send task title:", reply_markup=utils.get_cancel_keyboard())
    return AWAITING_TASK_TITLE

async def add_task_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Add task title"""
    context.user_data['new_task'] = {'title': update.message.text}
    await update.message.reply_text("Send description:")
    return AWAITING_TASK_DESC

async def add_task_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Add task description"""
    context.user_data['new_task']['description'] = update.message.text
    await update.message.reply_text("Send link:")
    return AWAITING_TASK_LINK

async def add_task_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Add task link"""
    context.user_data['new_task']['link'] = update.message.text
    await update.message.reply_text("Send reward amount:")
    return AWAITING_TASK_REWARD

async def add_task_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Add task reward"""
    try:
        reward = float(update.message.text)
        context.user_data['new_task']['reward'] = reward
        
        task_id = await db.add_task(context.user_data['new_task'])
        await update.message.reply_text(f"✅ Task added! ID: {task_id}", reply_markup=utils.get_admin_keyboard())
    except:
        await update.message.reply_text("❌ Invalid amount!", reply_markup=utils.get_admin_keyboard())
    
    return config.ADMIN_MENU

async def show_remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show tasks to remove"""
    tasks = await db.get_active_tasks()
    
    if not tasks:
        await update.message.reply_text("No tasks!", reply_markup=utils.get_admin_keyboard())
        return config.ADMIN_MENU
    
    msg = "🗑 Select task number to remove:\n\n"
    for i, t in enumerate(tasks, 1):
        msg += f"{i}. {t['title']}\n"
    
    context.user_data['tasks_to_remove'] = tasks
    await update.message.reply_text(msg, reply_markup=utils.get_cancel_keyboard())
    return config.REMOVING_TASK

async def handle_remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle task removal"""
    try:
        num = int(update.message.text)
        tasks = context.user_data.get('tasks_to_remove', [])
        
        if 1 <= num <= len(tasks):
            await db.remove_task(tasks[num-1]['id'])
            await update.message.reply_text("✅ Task removed!", reply_markup=utils.get_admin_keyboard())
        else:
            await update.message.reply_text("Invalid number!", reply_markup=utils.get_admin_keyboard())
    except:
        await update.message.reply_text("Invalid!", reply_markup=utils.get_admin_keyboard())
    
    return config.ADMIN_MENU

async def show_pending_submissions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show pending submissions"""
    subs = await db.get_pending_submissions()
    
    if not subs:
        await update.message.reply_text("No pending submissions!", reply_markup=utils.get_admin_keyboard())
        return config.ADMIN_MENU
    
    context.user_data['pending_subs'] = subs
    context.user_data['pending_index'] = 0
    
    return await show_submission(update, context, 0)

async def show_submission(update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int) -> int:
    """Show single submission"""
    subs = context.user_data.get('pending_subs', [])
    sub = subs[idx]
    
    msg = f"👤 @{sub['username']}\n📋 {sub['task_title']}\n💰 {sub['task_reward']} coins\n"
    msg += f"Commands:\n/approve_{sub['id']}\n/reject_{sub['id']}\n/next\n/prev\n/done"
    
    keyboard = [["✅ Approve", "❌ Reject"], ["⬅️ Prev", "➡️ Next", "🏁 Done"]]
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return config.PENDING_SUBMISSIONS

async def show_pending_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show pending withdrawals"""
    withdrawals = await db.get_pending_withdrawals()
    
    if not withdrawals:
        await update.message.reply_text("No pending withdrawals!", reply_markup=utils.get_admin_keyboard())
        return config.ADMIN_MENU
    
    context.user_data['pending_withdrawals'] = withdrawals
    context.user_data['withdraw_index'] = 0
    
    return await show_withdrawal(update, context, 0)

async def show_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int) -> int:
    """Show single withdrawal"""
    withdrawals = context.user_data.get('pending_withdrawals', [])
    w = withdrawals[idx]
    
    msg = f"👤 @{w['username']}\n💰 {w['amount']} coins\n"
    msg += f"Commands:\n/approve_withdraw_{w['id']}\n/reject_withdraw_{w['id']}\n/next\n/prev\n/done"
    
    keyboard = [["✅ Approve", "❌ Reject"], ["⬅️ Prev", "➡️ Next", "🏁 Done"]]
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return config.MANAGING_WITHDRAWALS

async def start_create_gift_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start create gift code"""
    await update.message.reply_text("Enter amount:", reply_markup=utils.get_cancel_keyboard())
    return AWAITING_GIFT_AMOUNT

async def create_gift_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Create gift amount"""
    try:
        amount = float(update.message.text)
        context.user_data['gift'] = {'amount': amount}
        await update.message.reply_text("Usage limit (-1=unlimited, 0=once):")
        return AWAITING_GIFT_LIMIT
    except:
        await update.message.reply_text("Invalid!")
        return AWAITING_GIFT_AMOUNT

async def create_gift_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Create gift limit"""
    try:
        limit = int(update.message.text)
        context.user_data['gift']['limit'] = limit
        await update.message.reply_text("Expiry days (0=no expiry):")
        return AWAITING_GIFT_EXPIRY
    except:
        await update.message.reply_text("Invalid!")
        return AWAITING_GIFT_LIMIT

async def create_gift_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Create gift expiry"""
    try:
        expiry = int(update.message.text)
        import random, string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        await db.create_gift_code(code, context.user_data['gift']['amount'], 
                                  context.user_data['gift']['limit'], expiry if expiry > 0 else None)
        
        await update.message.reply_text(f"✅ Gift code: `{code}`", parse_mode='Markdown', 
                                       reply_markup=utils.get_admin_keyboard())
    except:
        await update.message.reply_text("Invalid!", reply_markup=utils.get_admin_keyboard())
    
    return config.ADMIN_MENU

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start broadcast"""
    await update.message.reply_text("Send message to broadcast:", reply_markup=utils.get_cancel_keyboard())
    return AWAITING_BROADCAST

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send broadcast"""
    msg = update.message.text
    
    # Get all users
    users = db.db.child('users').get()
    count = 0
    
    if users:
        for user_id in users.keys():
            try:
                await update.message.bot.send_message(chat_id=int(user_id), text=f"📢 {msg}")
                count += 1
            except:
                pass
    
    await update.message.reply_text(f"✅ Broadcast sent to {count} users", reply_markup=utils.get_admin_keyboard())
    return config.ADMIN_MENU

async def show_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show analytics"""
    analytics = await db.get_analytics()
    
    msg = f"📊 *Analytics*\n"
    msg += f"👥 Users: {analytics['total_users']}\n"
    msg += f"📈 Active: {analytics['active_users']}\n"
    msg += f"💰 Total Earned: {analytics['total_earnings']:.2f}\n"
    msg += f"💸 Withdrawn: {analytics['total_withdrawn']:.2f}\n"
    msg += f"⏳ Pending Withdrawals: {analytics['pending_withdrawals']}\n"
    msg += f"📋 Pending Subs: {analytics['pending_submissions']}"
    
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=utils.get_admin_keyboard())
    return config.VIEWING_ANALYTICS
