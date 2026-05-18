"""
Admin handlers for the Telegram Task & Reward Bot
"""

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import config
import utils
from database import Database

db = Database()

# Admin conversation states
AWAITING_TASK_TITLE = 10
AWAITING_TASK_DESC = 11
AWAITING_TASK_LINK = 12
AWAITING_TASK_REWARD = 13
AWAITING_GIFT_AMOUNT = 14
AWAITING_GIFT_LIMIT = 15
AWAITING_GIFT_EXPIRY = 16
AWAITING_BROADCAST = 17
AWAITING_USER_ID = 18
AWAITING_USER_ACTION = 19
AWAITING_USER_AMOUNT = 20

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Create admin menu keyboard"""
    keyboard = config.ADMIN_MENU_BUTTONS
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Create keyboard with cancel button"""
    keyboard = [[config.COMMON_BUTTONS["CANCEL"]]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show admin panel"""
    user_id = update.effective_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await update.message.reply_text(
            "❌ You are not authorized to access this panel!",
            reply_markup=utils.get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    await update.message.reply_text(
        f"{config.EMOJI['ADMIN']} *Admin Panel*\n\n"
        f"Welcome, Admin!\n\n"
        f"Select an option from the menu below:",
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )
    
    return config.ADMIN_MENU

async def handle_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin menu button presses"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await update.message.reply_text(
            "❌ You are not authorized!",
            reply_markup=utils.get_main_keyboard(user_id)
        )
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
    
    elif text == "👥 Manage Users":
        await update.message.reply_text(
            "👥 *User Management*\n\n"
            "Commands:\n"
            "• `/ban @username` - Ban a user\n"
            "• `/unban @username` - Unban a user\n"
            "• `/addbalance @username amount` - Add balance\n"
            "• `/removebalance @username amount` - Remove balance\n"
            "• `/userinfo @username` - Get user info",
            parse_mode='Markdown',
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    elif text == "🔗 Force Join":
        return await show_force_join_menu(update, context)
    
    elif text == "📊 Analytics":
        return await show_analytics(update, context)
    
    elif text == "🏠 Back to Main":
        await update.message.reply_text(
            "🏠 Returning to Main Menu...",
            reply_markup=utils.get_main_keyboard(user_id)
        )
        return config.MAIN_MENU
    
    else:
        await update.message.reply_text(
            "❌ Unknown command. Please use the buttons below:",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU

async def start_add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start add task process"""
    await update.message.reply_text(
        "➕ *Add New Task*\n\n"
        "Please send the task title:\n\n"
        "Send /cancel to cancel.",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_TASK_TITLE

async def add_task_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle task title"""
    title = update.message.text
    
    if title == '/cancel':
        await update.message.reply_text(
            "❌ Task creation cancelled.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    context.user_data['new_task'] = {'title': title}
    
    await update.message.reply_text(
        "📝 Send task description:\n\n"
        "Send /cancel to cancel.",
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_TASK_DESC

async def add_task_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle task description"""
    description = update.message.text
    
    if description == '/cancel':
        await update.message.reply_text(
            "❌ Task creation cancelled.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    context.user_data['new_task']['description'] = description
    
    await update.message.reply_text(
        "🔗 Send task link (URL):\n\n"
        "Make sure the link is valid.\n\n"
        "Send /cancel to cancel.",
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_TASK_LINK

async def add_task_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle task link"""
    link = update.message.text
    
    if link == '/cancel':
        await update.message.reply_text(
            "❌ Task creation cancelled.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    if not link.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "❌ Invalid URL! Please send a valid link starting with http:// or https://\n\n"
            "Send /cancel to cancel.",
            reply_markup=get_cancel_keyboard()
        )
        return AWAITING_TASK_LINK
    
    context.user_data['new_task']['link'] = link
    
    await update.message.reply_text(
        "💰 Send task reward amount (in coins):\n\n"
        "Example: 10, 25, 50\n\n"
        "Send /cancel to cancel.",
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_TASK_REWARD

async def add_task_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle task reward"""
    reward_text = update.message.text
    
    if reward_text == '/cancel':
        await update.message.reply_text(
            "❌ Task creation cancelled.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    try:
        reward = float(reward_text)
        if reward <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount! Please send a valid positive number.\n\n"
            "Example: 10, 25, 50\n\n"
            "Send /cancel to cancel.",
            reply_markup=get_cancel_keyboard()
        )
        return AWAITING_TASK_REWARD
    
    context.user_data['new_task']['reward'] = reward
    
    # Create task
    task_data = {
        'title': context.user_data['new_task']['title'],
        'description': context.user_data['new_task']['description'],
        'link': context.user_data['new_task']['link'],
        'reward': context.user_data['new_task']['reward']
    }
    
    try:
        task_id = await db.add_task(task_data)
        
        await update.message.reply_text(
            f"✅ *Task Added Successfully!*\n\n"
            f"📋 Title: {task_data['title']}\n"
            f"💰 Reward: {task_data['reward']} coins\n"
            f"🆔 Task ID: `{task_id}`\n\n"
            f"Users can now see and complete this task.",
            parse_mode='Markdown',
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error adding task: {str(e)}\n\n"
            f"Please try again.",
            reply_markup=get_admin_keyboard()
        )
    
    context.user_data.pop('new_task', None)
    return config.ADMIN_MENU

async def show_remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show tasks list for removal"""
    tasks = await db.get_active_tasks()
    
    if not tasks:
        await update.message.reply_text(
            "❌ No active tasks to remove.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    context.user_data['tasks_to_remove'] = tasks
    
    message = "🗑 *Remove Task*\n\n"
    message += "Select a task to remove by sending its number:\n\n"
    
    for i, task in enumerate(tasks, 1):
        message += f"{i}. {task['title'][:30]} - {task['reward']} coins\n"
    
    message += f"\nSend /cancel to cancel."
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    
    return config.REMOVING_TASK

async def handle_remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle task removal selection"""
    text = update.message.text
    
    if text == '/cancel':
        await update.message.reply_text(
            "❌ Task removal cancelled.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    tasks = context.user_data.get('tasks_to_remove', [])
    
    try:
        task_num = int(text)
        if 1 <= task_num <= len(tasks):
            task = tasks[task_num - 1]
            success = await db.remove_task(task['id'])
            
            if success:
                await update.message.reply_text(
                    f"✅ Task '{task['title']}' removed successfully!",
                    reply_markup=get_admin_keyboard()
                )
            else:
                await update.message.reply_text(
                    f"❌ Failed to remove task!",
                    reply_markup=get_admin_keyboard()
                )
        else:
            await update.message.reply_text(
                f"❌ Invalid selection! Please send a number between 1 and {len(tasks)}",
                reply_markup=get_cancel_keyboard()
            )
            return config.REMOVING_TASK
    except ValueError:
        await update.message.reply_text(
            "❌ Please send a valid number!",
            reply_markup=get_cancel_keyboard()
        )
        return config.REMOVING_TASK
    
    context.user_data.pop('tasks_to_remove', None)
    return config.ADMIN_MENU

async def show_pending_submissions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show pending submissions"""
    submissions = await db.get_pending_submissions()
    
    if not submissions:
        await update.message.reply_text(
            "✅ No pending submissions!",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    context.user_data['pending_subs'] = submissions
    context.user_data['pending_index'] = 0
    
    return await show_submission(update, context, 0)

async def show_submission(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int) -> int:
    """Show a specific submission"""
    submissions = context.user_data.get('pending_subs', [])
    
    if index < 0 or index >= len(submissions):
        await update.message.reply_text(
            "✅ No more submissions.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    sub = submissions[index]
    
    message = f"⏳ *Pending Submission #{index + 1}/{len(submissions)}*\n\n"
    message += f"👤 User: @{sub['username']}\n"
    message += f"📋 Task: {sub['task_title']}\n"
    message += f"💰 Reward: {sub['task_reward']} coins\n"
    message += f"📝 Note: {sub.get('note', 'No note')}\n"
    message += f"🖼️ Screenshot: {sub['screenshot_url']}\n\n"
    message += f"Commands:\n"
    message += f"• `/approve_{sub['id']}` - Approve this submission\n"
    message += f"• `/reject_{sub['id']}` - Reject this submission\n"
    message += f"• `/next` - View next submission\n"
    message += f"• `/prev` - View previous submission\n"
    message += f"• `/done` - Exit"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([
            ["✅ Approve", "❌ Reject"],
            ["⬅️ Previous", "➡️ Next", "🏁 Done"]
        ], resize_keyboard=True)
    )
    
    return config.PENDING_SUBMISSIONS

async def handle_pending_submissions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pending submissions navigation and actions"""
    text = update.message.text
    submissions = context.user_data.get('pending_subs', [])
    current_index = context.user_data.get('pending_index', 0)
    
    if text == "✅ Approve":
        if submissions:
            sub = submissions[current_index]
            success = await db.approve_submission(sub['id'])
            
            if success:
                await update.message.reply_text(f"✅ Submission approved! Reward added.")
                submissions.pop(current_index)
                context.user_data['pending_subs'] = submissions
                
                if current_index >= len(submissions):
                    current_index = len(submissions) - 1
                context.user_data['pending_index'] = current_index
                
                if not submissions:
                    await update.message.reply_text(
                        "✅ No more pending submissions!",
                        reply_markup=get_admin_keyboard()
                    )
                    return config.ADMIN_MENU
                
                return await show_submission(update, context, current_index)
            else:
                await update.message.reply_text("❌ Failed to approve submission!")
    
    elif text == "❌ Reject":
        if submissions:
            sub = submissions[current_index]
            success = await db.reject_submission(sub['id'], "Task not completed properly")
            
            if success:
                await update.message.reply_text(f"❌ Submission rejected!")
                submissions.pop(current_index)
                context.user_data['pending_subs'] = submissions
                
                if current_index >= len(submissions):
                    current_index = len(submissions) - 1
                context.user_data['pending_index'] = current_index
                
                if not submissions:
                    await update.message.reply_text(
                        "✅ No more pending submissions!",
                        reply_markup=get_admin_keyboard()
                    )
                    return config.ADMIN_MENU
                
                return await show_submission(update, context, current_index)
            else:
                await update.message.reply_text("❌ Failed to reject submission!")
    
    elif text == "➡️ Next":
        if current_index + 1 < len(submissions):
            current_index += 1
            context.user_data['pending_index'] = current_index
            return await show_submission(update, context, current_index)
        else:
            await update.message.reply_text("📌 This is the last submission!")
    
    elif text == "⬅️ Previous":
        if current_index - 1 >= 0:
            current_index -= 1
            context.user_data['pending_index'] = current_index
            return await show_submission(update, context, current_index)
        else:
            await update.message.reply_text("📌 This is the first submission!")
    
    elif text == "🏁 Done":
        await update.message.reply_text(
            "✅ Exited submission review.",
            reply_markup=get_admin_keyboard()
        )
        context.user_data.pop('pending_subs', None)
        context.user_data.pop('pending_index', None)
        return config.ADMIN_MENU
    
    return config.PENDING_SUBMISSIONS

async def show_pending_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show pending withdrawals"""
    withdrawals = await db.get_pending_withdrawals()
    
    if not withdrawals:
        await update.message.reply_text(
            "✅ No pending withdrawals!",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    context.user_data['pending_withdrawals'] = withdrawals
    context.user_data['withdraw_index'] = 0
    
    return await show_withdrawal(update, context, 0)

async def show_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int) -> int:
    """Show a specific withdrawal"""
    withdrawals = context.user_data.get('pending_withdrawals', [])
    
    if index < 0 or index >= len(withdrawals):
        await update.message.reply_text(
            "✅ No more withdrawals.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    w = withdrawals[index]
    
    message = f"💸 *Pending Withdrawal #{index + 1}/{len(withdrawals)}*\n\n"
    message += f"👤 User: @{w['username']}\n"
    message += f"💰 Amount: {w['amount']} coins\n"
    message += f"📅 Requested: {w.get('created_at', 'Unknown')}\n\n"
    message += f"Commands:\n"
    message += f"• `/approve_withdraw_{w['id']}` - Approve this withdrawal\n"
    message += f"• `/reject_withdraw_{w['id']}` - Reject this withdrawal\n"
    message += f"• `/next` - View next withdrawal\n"
    message += f"• `/prev` - View previous withdrawal\n"
    message += f"• `/done` - Exit"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([
            ["✅ Approve", "❌ Reject"],
            ["⬅️ Previous", "➡️ Next", "🏁 Done"]
        ], resize_keyboard=True)
    )
    
    return config.MANAGING_WITHDRAWALS

async def handle_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle withdrawals navigation and actions"""
    text = update.message.text
    withdrawals = context.user_data.get('pending_withdrawals', [])
    current_index = context.user_data.get('withdraw_index', 0)
    
    if text == "✅ Approve":
        if withdrawals:
            w = withdrawals[current_index]
            success = await db.process_withdrawal(w['id'], 'approved')
            
            if success:
                await update.message.reply_text(f"✅ Withdrawal approved!")
                withdrawals.pop(current_index)
                context.user_data['pending_withdrawals'] = withdrawals
                
                if current_index >= len(withdrawals):
                    current_index = len(withdrawals) - 1
                context.user_data['withdraw_index'] = current_index
                
                if not withdrawals:
                    await update.message.reply_text(
                        "✅ No more pending withdrawals!",
                        reply_markup=get_admin_keyboard()
                    )
                    return config.ADMIN_MENU
                
                return await show_withdrawal(update, context, current_index)
            else:
                await update.message.reply_text("❌ Failed to approve withdrawal!")
    
    elif text == "❌ Reject":
        if withdrawals:
            w = withdrawals[current_index]
            success = await db.process_withdrawal(w['id'], 'rejected', "Request rejected")
            
            if success:
                await update.message.reply_text(f"❌ Withdrawal rejected!")
                withdrawals.pop(current_index)
                context.user_data['pending_withdrawals'] = withdrawals
                
                if current_index >= len(withdrawals):
                    current_index = len(withdrawals) - 1
                context.user_data['withdraw_index'] = current_index
                
                if not withdrawals:
                    await update.message.reply_text(
                        "✅ No more pending withdrawals!",
                        reply_markup=get_admin_keyboard()
                    )
                    return config.ADMIN_MENU
                
                return await show_withdrawal(update, context, current_index)
            else:
                await update.message.reply_text("❌ Failed to reject withdrawal!")
    
    elif text == "➡️ Next":
        if current_index + 1 < len(withdrawals):
            current_index += 1
            context.user_data['withdraw_index'] = current_index
            return await show_withdrawal(update, context, current_index)
        else:
            await update.message.reply_text("📌 This is the last withdrawal!")
    
    elif text == "⬅️ Previous":
        if current_index - 1 >= 0:
            current_index -= 1
            context.user_data['withdraw_index'] = current_index
            return await show_withdrawal(update, context, current_index)
        else:
            await update.message.reply_text("📌 This is the first withdrawal!")
    
    elif text == "🏁 Done":
        await update.message.reply_text(
            "✅ Exited withdrawal review.",
            reply_markup=get_admin_keyboard()
        )
        context.user_data.pop('pending_withdrawals', None)
        context.user_data.pop('withdraw_index', None)
        return config.ADMIN_MENU
    
    return config.MANAGING_WITHDRAWALS

async def start_create_gift_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start gift code creation"""
    await update.message.reply_text(
        "🎁 *Create Gift Code*\n\n"
        "Enter the reward amount (in coins):\n\n"
        "Example: 10, 25, 50, 100\n\n"
        "Send /cancel to cancel.",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_GIFT_AMOUNT

async def create_gift_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle gift code amount"""
    amount_text = update.message.text
    
    if amount_text == '/cancel':
        await update.message.reply_text(
            "❌ Gift code creation cancelled.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount! Please send a valid positive number.\n\n"
            "Send /cancel to cancel.",
            reply_markup=get_cancel_keyboard()
        )
        return AWAITING_GIFT_AMOUNT
    
    context.user_data['gift_code'] = {'amount': amount}
    
    await update.message.reply_text(
        "Enter usage limit:\n\n"
        "• -1 for unlimited uses\n"
        "• 0 for one-time use\n"
        "• Any positive number for multiple uses\n\n"
        "Example: -1, 0, 10, 100\n\n"
        "Send /cancel to cancel.",
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_GIFT_LIMIT

async def create_gift_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle gift code usage limit"""
    limit_text = update.message.text
    
    if limit_text == '/cancel':
        await update.message.reply_text(
            "❌ Gift code creation cancelled.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    try:
        limit = int(limit_text)
        if limit < -1:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid limit! Please enter -1, 0, or a positive number.\n\n"
            "Send /cancel to cancel.",
            reply_markup=get_cancel_keyboard()
        )
        return AWAITING_GIFT_LIMIT
    
    context.user_data['gift_code']['usage_limit'] = limit
    
    await update.message.reply_text(
        "Enter expiry days:\n\n"
        "• 0 for no expiry\n"
        "• Any positive number for days until expiry\n\n"
        "Example: 0, 7, 30, 365\n\n"
        "Send /cancel to cancel.",
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_GIFT_EXPIRY

async def create_gift_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle gift code expiry"""
    expiry_text = update.message.text
    
    if expiry_text == '/cancel':
        await update.message.reply_text(
            "❌ Gift code creation cancelled.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    try:
        expiry_days = int(expiry_text)
        if expiry_days < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid expiry! Please enter 0 or a positive number.\n\n"
            "Send /cancel to cancel.",
            reply_markup=get_cancel_keyboard()
        )
        return AWAITING_GIFT_EXPIRY
    
    # Generate random code
    import random
    import string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    # Create gift code
    success = await db.create_gift_code(
        code,
        context.user_data['gift_code']['amount'],
        context.user_data['gift_code']['usage_limit'],
        expiry_days if expiry_days > 0 else None
    )
    
    if success:
        expiry_msg = f"{expiry_days} days" if expiry_days > 0 else "No expiry"
        usage_msg = "Unlimited" if context.user_data['gift_code']['usage_limit'] == -1 else str(context.user_data['gift_code']['usage_limit'])
        
        await update.message.reply_text(
            f"✅ *Gift Code Created Successfully!*\n\n"
            f"🎁 Code: `{code}`\n"
            f"💰 Amount: {context.user_data['gift_code']['amount']} coins\n"
            f"🔄 Usage Limit: {usage_msg}\n"
            f"📅 Expiry: {expiry_msg}\n\n"
            f"Share this code with users to redeem!",
            parse_mode='Markdown',
            reply_markup=get_admin_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Failed to create gift code!",
            reply_markup=get_admin_keyboard()
        )
    
    context.user_data.pop('gift_code', None)
    return config.ADMIN_MENU

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start broadcast message"""
    await update.message.reply_text(
        "📢 *Broadcast Message*\n\n"
        "Send the message you want to broadcast to all users.\n\n"
        "You can use Markdown formatting.\n\n"
        "Send /cancel to cancel.",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    
    return AWAITING_BROADCAST

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send broadcast message to all users"""
    message_text = update.message.text
    
    if message_text == '/cancel':
        await update.message.reply_text(
            "❌ Broadcast cancelled.",
            reply_markup=get_admin_keyboard()
        )
        return config.ADMIN_MENU
    
    # Get all users from database
    import json
    users = db.db.child('users').get()
    
    success_count = 0
    fail_count = 0
    
    if users:
        for user_id, user_data in users.items():
            if user_data.get('banned', False):
                continue
            try:
                await update.message.bot.send_message(
                    chat_id=int(user_id),
                    text=f"📢 *Broadcast Message*\n\n{message_text}",
                    parse_mode='Markdown'
                )
                success_count += 1
            except Exception as e:
                fail_count += 1
                print(f"Failed to send to {user_id}: {e}")
    
    await update.message.reply_text(
        f"✅ Broadcast completed!\n\n"
        f"✓ Sent to: {success_count} users\n"
        f"✗ Failed: {fail_count} users\n\n"
        f"Message: {message_text[:100]}...",
        reply_markup=get_admin_keyboard()
    )
    
    return config.ADMIN_MENU

async def show_force_join_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show force join management menu"""
    channels = await db.get_force_join_channels()
    
    message = "🔗 *Force Join Channels Management*\n\n"
    message += "Users must join these channels to use the bot.\n\n"
    
    if channels:
        message += "*Current Channels:*\n"
        for channel in channels:
            message += f"• @{channel}\n"
    else:
        message += "No channels configured.\n\n"
    
    message += "\n*Commands:*\n"
    message += "• `/addchannel @username` - Add a channel\n"
    message += "• `/removechannel @username` - Remove a channel\n"
    message += "• `/listchannels` - List all channels"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([
            ["🏠 Back to Admin"]
        ], resize_keyboard=True)
    )
    
    return config.FORCE_JOIN_MENU

async def show_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show bot analytics"""
    analytics = await db.get_analytics()
    
    message = f"📊 *Bot Analytics*\n\n"
    message += f"👥 *Users:*\n"
    message += f"┌─────────────────────────┐\n"
    message += f"│ Total Users:       {analytics['total_users']:>8}\n"
    message += f"│ Active Users (7d): {analytics['active_users']:>8}\n"
    message += f"└─────────────────────────┘\n\n"
    
    message += f"💰 *Earnings:*\n"
    message += f"┌─────────────────────────┐\n"
    message += f"│ Total Earned:     {analytics['total_earnings']:>10.2f}\n"
    message += f"│ Total Withdrawn:  {analytics['total_withdrawn']:>10.2f}\n"
    message += f"│ Platform Balance: {(analytics['total_earnings'] - analytics['total_withdrawn']):>10.2f}\n"
    message += f"└─────────────────────────┘\n\n"
    
    message += f"⏳ *Pending:*\n"
    message += f"┌─────────────────────────┐\n"
    message += f"│ Pending Withdrawals:{analytics['pending_withdrawals']:>8}\n"
    message += f"│ Pending Submissions:{analytics['pending_submissions']:>8}\n"
    message += f"└─────────────────────────┘"
    
    keyboard = [
        ["🔄 Refresh", "🏠 Back to Admin"]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return config.VIEWING_ANALYTICS
