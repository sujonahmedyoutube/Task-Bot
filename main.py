"""
Main entry point for the Telegram Task & Reward Bot
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
import config
from database import Database
import user
import admin
import utils

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import conversation states
from user import (
    MAIN_MENU, TASKS_MENU, WITHDRAW_MENU, REFERRAL_MENU, ADMIN_MENU,
    VIEWING_LEADERBOARD, VIEWING_BALANCE, REMOVING_TASK,
    PENDING_SUBMISSIONS, MANAGING_WITHDRAWALS, VIEWING_ANALYTICS,
    AWAITING_TASK_SUBMIT_SCREENSHOT, AWAITING_TASK_SUBMIT_NOTE,
    AWAITING_WITHDRAW_AMOUNT, AWAITING_GIFT_CODE
)

from admin import (
    AWAITING_TASK_TITLE, AWAITING_TASK_DESC, AWAITING_TASK_LINK,
    AWAITING_TASK_REWARD, AWAITING_GIFT_AMOUNT, AWAITING_GIFT_LIMIT,
    AWAITING_GIFT_EXPIRY, AWAITING_BROADCAST, FORCE_JOIN_MENU
)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_chat:
        await update.effective_chat.send_message(
            "❌ An error occurred. Please try again later."
        )

async def post_init(application: Application) -> None:
    """Initialize database and other components after bot starts"""
    logger.info("🤖 Bot is starting up...")
    
    # Initialize database
    try:
        db = Database()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all text messages"""
    if not update.message or not update.message.text:
        return
    
    # Skip commands
    if update.message.text.startswith('/'):
        return
    
    # Get current state
    state = context.user_data.get('state', MAIN_MENU)
    
    # Route to appropriate handler based on state
    if state == MAIN_MENU:
        new_state = await user.handle_main_menu(update, context)
        context.user_data['state'] = new_state
    elif state == TASKS_MENU:
        new_state = await user.handle_tasks_menu(update, context)
        context.user_data['state'] = new_state
    elif state == WITHDRAW_MENU:
        new_state = await user.handle_withdraw_menu(update, context)
        context.user_data['state'] = new_state
    elif state == REFERRAL_MENU:
        new_state = await user.handle_referral_menu(update, context)
        context.user_data['state'] = new_state
    elif state == ADMIN_MENU:
        new_state = await admin.handle_admin_menu(update, context)
        context.user_data['state'] = new_state
    elif state == VIEWING_LEADERBOARD:
        new_state = await user.handle_leaderboard_menu(update, context)
        context.user_data['state'] = new_state
    elif state == VIEWING_BALANCE:
        new_state = await user.show_balance(update, context)
        context.user_data['state'] = new_state
    elif state == REMOVING_TASK:
        new_state = await admin.handle_remove_task(update, context)
        context.user_data['state'] = new_state
    elif state == PENDING_SUBMISSIONS:
        new_state = await admin.handle_pending_submissions(update, context)
        context.user_data['state'] = new_state
    elif state == MANAGING_WITHDRAWALS:
        new_state = await admin.handle_withdrawals(update, context)
        context.user_data['state'] = new_state
    elif state == VIEWING_ANALYTICS:
        new_state = await admin.show_analytics(update, context)
        context.user_data['state'] = new_state
    else:
        # Default to main menu handler
        new_state = await user.handle_main_menu(update, context)
        context.user_data['state'] = new_state

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle commands that don't have dedicated handlers"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    
    # Handle approve/reject commands
    if text.startswith('/approve_'):
        submission_id = text.split('_')[1]
        success = await admin.db.approve_submission(submission_id)
        if success:
            await update.message.reply_text(f"✅ Submission {submission_id} approved!")
        else:
            await update.message.reply_text(f"❌ Failed to approve submission!")
    
    elif text.startswith('/reject_'):
        submission_id = text.split('_')[1]
        success = await admin.db.reject_submission(submission_id, "Task not completed properly")
        if success:
            await update.message.reply_text(f"❌ Submission {submission_id} rejected!")
        else:
            await update.message.reply_text(f"❌ Failed to reject submission!")
    
    elif text.startswith('/approve_withdraw_'):
        withdrawal_id = text.split('_')[2]
        success = await admin.db.process_withdrawal(withdrawal_id, 'approved')
        if success:
            await update.message.reply_text(f"✅ Withdrawal {withdrawal_id} approved!")
        else:
            await update.message.reply_text(f"❌ Failed to approve withdrawal!")
    
    elif text.startswith('/reject_withdraw_'):
        withdrawal_id = text.split('_')[2]
        success = await admin.db.process_withdrawal(withdrawal_id, 'rejected', "Request rejected")
        if success:
            await update.message.reply_text(f"❌ Withdrawal {withdrawal_id} rejected!")
        else:
            await update.message.reply_text(f"❌ Failed to reject withdrawal!")
    
    elif text == '/next':
        # This will be handled by the state handlers
        pass
    
    elif text == '/prev':
        pass
    
    elif text == '/done':
        pass

def main() -> None:
    """Start the bot"""
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()
    
    # --- Conversation Handlers ---
    
    # Task submission conversation
    task_submission_conv = ConversationHandler(
        entry_points=[CommandHandler('submit', user.submit_task_command)],
        states={
            AWAITING_TASK_SUBMIT_SCREENSHOT: [
                MessageHandler(filters.PHOTO, user.receive_screenshot),
                CommandHandler('cancel', user.cancel)
            ],
            AWAITING_TASK_SUBMIT_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, user.receive_submission_note),
                CommandHandler('skip', user.skip_note),
                CommandHandler('cancel', user.cancel)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', user.cancel),
            MessageHandler(filters.ALL, user.cancel)
        ],
        name="task_submission",
        persistent=False
    )
    
    # Withdrawal conversation
    withdrawal_conv = ConversationHandler(
        entry_points=[CommandHandler('withdraw', user.request_withdrawal)],
        states={
            AWAITING_WITHDRAW_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, user.process_withdrawal_amount),
                CommandHandler('cancel', user.cancel)
            ]
        },
        fallbacks=[CommandHandler('cancel', user.cancel)],
        name="withdrawal",
        persistent=False
    )
    
    # Redeem conversation
    redeem_conv = ConversationHandler(
        entry_points=[CommandHandler('redeem', user.start_redeem)],
        states={
            AWAITING_GIFT_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, user.process_redeem),
                CommandHandler('cancel', user.cancel)
            ]
        },
        fallbacks=[CommandHandler('cancel', user.cancel)],
        name="redeem",
        persistent=False
    )
    
    # Add task conversation (admin)
    add_task_conv = ConversationHandler(
        entry_points=[CommandHandler('addtask', admin.start_add_task)],
        states={
            AWAITING_TASK_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_task_title),
                CommandHandler('cancel', admin.show_admin_menu)
            ],
            AWAITING_TASK_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_task_description),
                CommandHandler('cancel', admin.show_admin_menu)
            ],
            AWAITING_TASK_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_task_link),
                CommandHandler('cancel', admin.show_admin_menu)
            ],
            AWAITING_TASK_REWARD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_task_reward),
                CommandHandler('cancel', admin.show_admin_menu)
            ]
        },
        fallbacks=[CommandHandler('cancel', admin.show_admin_menu)],
        name="add_task",
        persistent=False
    )
    
    # Create gift code conversation (admin)
    gift_code_conv = ConversationHandler(
        entry_points=[CommandHandler('creategift', admin.start_create_gift_code)],
        states={
            AWAITING_GIFT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.create_gift_amount),
                CommandHandler('cancel', admin.show_admin_menu)
            ],
            AWAITING_GIFT_LIMIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.create_gift_limit),
                CommandHandler('cancel', admin.show_admin_menu)
            ],
            AWAITING_GIFT_EXPIRY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.create_gift_expiry),
                CommandHandler('cancel', admin.show_admin_menu)
            ]
        },
        fallbacks=[CommandHandler('cancel', admin.show_admin_menu)],
        name="gift_code",
        persistent=False
    )
    
    # Broadcast conversation (admin)
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler('broadcast', admin.start_broadcast)],
        states={
            AWAITING_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.send_broadcast),
                CommandHandler('cancel', admin.show_admin_menu)
            ]
        },
        fallbacks=[CommandHandler('cancel', admin.show_admin_menu)],
        name="broadcast",
        persistent=False
    )
    
    # --- Command Handlers ---
    application.add_handler(CommandHandler("start", user.start))
    application.add_handler(CommandHandler("menu", user.start))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin.show_admin_menu))
    
    # User commands
    application.add_handler(CommandHandler("balance", user.show_balance))
    application.add_handler(CommandHandler("tasks", user.list_tasks))
    application.add_handler(CommandHandler("referral", user.show_referral_menu))
    application.add_handler(CommandHandler("leaderboard", user.show_leaderboard_menu))
    application.add_handler(CommandHandler("support", user.show_support))
    
    # --- Conversation Handlers ---
    application.add_handler(task_submission_conv)
    application.add_handler(withdrawal_conv)
    application.add_handler(redeem_conv)
    application.add_handler(add_task_conv)
    application.add_handler(gift_code_conv)
    application.add_handler(broadcast_conv)
    
    # --- Message Handler (for buttons) ---
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # --- Command Handler for various commands ---
    application.add_handler(MessageHandler(filters.COMMAND, command_handler))
    
    # --- Error Handler ---
    application.add_error_handler(error_handler)
    
    # --- Start the bot ---
    logger.info("🚀 Starting bot...")
    logger.info(f"📱 Bot username: @{config.BOT_USERNAME}")
    logger.info(f"👑 Admin ID: {config.ADMIN_USER_IDS}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
