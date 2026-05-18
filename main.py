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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

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
    AWAITING_GIFT_EXPIRY, AWAITING_BROADCAST
)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.effective_chat:
        await update.effective_chat.send_message("❌ An error occurred!")

async def post_init(application: Application):
    logger.info("🤖 Bot starting...")
    try:
        db = Database()
        logger.info("✅ Database connected!")
    except Exception as e:
        logger.error(f"❌ Database error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or update.message.text.startswith('/'):
        return
    
    state = context.user_data.get('state', MAIN_MENU)
    
    if state == MAIN_MENU:
        context.user_data['state'] = await user.handle_main_menu(update, context)
    elif state == TASKS_MENU:
        context.user_data['state'] = await user.handle_tasks_menu(update, context)
    elif state == WITHDRAW_MENU:
        context.user_data['state'] = await user.handle_withdraw_menu(update, context)
    elif state == ADMIN_MENU:
        context.user_data['state'] = await admin.handle_admin_menu(update, context)
    elif state == REMOVING_TASK:
        context.user_data['state'] = await admin.handle_remove_task(update, context)
    elif state == PENDING_SUBMISSIONS:
        context.user_data['state'] = await admin.show_pending_submissions(update, context)
    elif state == MANAGING_WITHDRAWALS:
        context.user_data['state'] = await admin.show_pending_withdrawals(update, context)
    else:
        context.user_data['state'] = await user.handle_main_menu(update, context)

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    
    if text.startswith('/approve_'):
        sub_id = text.split('_')[1]
        await db.approve_submission(sub_id)
        await update.message.reply_text(f"✅ Submission {sub_id} approved!")
    elif text.startswith('/reject_'):
        sub_id = text.split('_')[1]
        await db.reject_submission(sub_id, "Not completed properly")
        await update.message.reply_text(f"❌ Submission {sub_id} rejected!")
    elif text.startswith('/approve_withdraw_'):
        w_id = text.split('_')[2]
        await db.process_withdrawal(w_id, 'approved')
        await update.message.reply_text(f"✅ Withdrawal {w_id} approved!")
    elif text.startswith('/reject_withdraw_'):
        w_id = text.split('_')[2]
        await db.process_withdrawal(w_id, 'rejected', "Rejected")
        await update.message.reply_text(f"❌ Withdrawal {w_id} rejected!")

def main():
    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()
    
    # Conversations
    task_conv = ConversationHandler(
        entry_points=[CommandHandler('submit', user.submit_task_command)],
        states={
            AWAITING_TASK_SUBMIT_SCREENSHOT: [MessageHandler(filters.PHOTO, user.receive_screenshot)],
            AWAITING_TASK_SUBMIT_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, user.receive_submission_note)],
        },
        fallbacks=[CommandHandler('cancel', user.cancel)]
    )
    
    withdraw_conv = ConversationHandler(
        entry_points=[CommandHandler('withdraw', user.request_withdrawal)],
        states={AWAITING_WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, user.process_withdrawal_amount)]},
        fallbacks=[CommandHandler('cancel', user.cancel)]
    )
    
    redeem_conv = ConversationHandler(
        entry_points=[CommandHandler('redeem', user.start_redeem)],
        states={AWAITING_GIFT_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, user.process_redeem)]},
        fallbacks=[CommandHandler('cancel', user.cancel)]
    )
    
    add_task_conv = ConversationHandler(
        entry_points=[CommandHandler('addtask', admin.start_add_task)],
        states={
            AWAITING_TASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_task_title)],
            AWAITING_TASK_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_task_description)],
            AWAITING_TASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_task_link)],
            AWAITING_TASK_REWARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_task_reward)],
        },
        fallbacks=[CommandHandler('cancel', admin.show_admin_menu)]
    )
    
    gift_conv = ConversationHandler(
        entry_points=[CommandHandler('creategift', admin.start_create_gift_code)],
        states={
            AWAITING_GIFT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.create_gift_amount)],
            AWAITING_GIFT_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.create_gift_limit)],
            AWAITING_GIFT_EXPIRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.create_gift_expiry)],
        },
        fallbacks=[CommandHandler('cancel', admin.show_admin_menu)]
    )
    
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler('broadcast', admin.start_broadcast)],
        states={AWAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.send_broadcast)]},
        fallbacks=[CommandHandler('cancel', admin.show_admin_menu)]
    )
    
    # Handlers
    application.add_handler(CommandHandler("start", user.start))
    application.add_handler(CommandHandler("menu", user.start))
    application.add_handler(CommandHandler("admin", admin.show_admin_menu))
    application.add_handler(CommandHandler("balance", user.show_balance))
    application.add_handler(CommandHandler("tasks", user.list_tasks))
    application.add_handler(CommandHandler("referral", user.show_referral_menu))
    application.add_handler(CommandHandler("leaderboard", user.show_leaderboard_menu))
    
    application.add_handler(task_conv)
    application.add_handler(withdraw_conv)
    application.add_handler(redeem_conv)
    application.add_handler(add_task_conv)
    application.add_handler(gift_conv)
    application.add_handler(broadcast_conv)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.COMMAND, command_handler))
    application.add_error_handler(error_handler)
    
    logger.info("🚀 Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
