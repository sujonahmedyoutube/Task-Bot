"""
Database handler for Firebase Realtime Database
"""

import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import config

class Database:
    def __init__(self):
        """Initialize Firebase Realtime Database connection"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_FILE)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': config.FIREBASE_DB_URL
                })
            
            self.db = db.reference()
            self.initialize_collections()
            print("✅ Firebase initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing Firebase: {e}")
            raise

    def initialize_collections(self):
        """Initialize collections with sample data if empty"""
        try:
            tasks = self.db.child('tasks').get()
            if tasks is None:
                self.create_sample_task()
                print("✅ Sample task created!")
        except Exception as e:
            print(f"Error initializing collections: {e}")

    def create_sample_task(self):
        """Create a sample task"""
        sample_task = {
            'title': 'Sample Task - Join Our Channel',
            'description': 'Join our Telegram channel to earn rewards!',
            'link': 'https://t.me/NeroxaTasks_Bot',
            'reward': 10.0,
            'photo_url': '',
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
        self.db.child('tasks').push(sample_task)

    async def get_user(self, user_id: int) -> Optional[Dict]:
        try:
            return self.db.child('users').child(str(user_id)).get()
        except Exception as e:
            print(f"Error getting user {user_id}: {e}")
            return None

    async def create_user(self, user_id: int, username: str = None, referrer_id: int = None) -> Dict:
        try:
            user_data = {
                'user_id': user_id,
                'username': username,
                'balance': 0.0,
                'referrals': 0,
                'referrer_id': referrer_id,
                'total_earned': 0.0,
                'total_withdrawn': 0.0,
                'banned': False,
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }
            self.db.child('users').child(str(user_id)).set(user_data)
            if referrer_id and referrer_id != user_id:
                await self.add_referral_bonus(referrer_id)
            return user_data
        except Exception as e:
            print(f"Error creating user {user_id}: {e}")
            raise

    async def update_balance(self, user_id: int, amount: float, operation: str = 'add') -> bool:
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            new_balance = user['balance'] + amount if operation == 'add' else user['balance'] - amount
            if new_balance < 0:
                return False
            updates = {'balance': new_balance, 'last_active': datetime.now().isoformat()}
            if operation == 'add':
                updates['total_earned'] = user.get('total_earned', 0) + amount
            self.db.child('users').child(str(user_id)).update(updates)
            return True
        except Exception as e:
            print(f"Error updating balance: {e}")
            return False

    async def add_referral_bonus(self, referrer_id: int) -> bool:
        try:
            referrer = await self.get_user(referrer_id)
            if referrer and not referrer.get('banned', False):
                await self.update_balance(referrer_id, config.REFERRAL_BONUS, 'add')
                self.db.child('users').child(str(referrer_id)).update({
                    'referrals': referrer.get('referrals', 0) + 1
                })
                return True
            return False
        except Exception as e:
            print(f"Error adding referral bonus: {e}")
            return False

    async def get_active_tasks(self) -> List[Dict]:
        try:
            tasks = self.db.child('tasks').get()
            if not tasks:
                return []
            active_tasks = []
            for task_id, task_data in tasks.items():
                if task_data.get('status') == 'active':
                    task_data['id'] = task_id
                    active_tasks.append(task_data)
            return active_tasks
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []

    async def get_task(self, task_id: str) -> Optional[Dict]:
        try:
            task_data = self.db.child('tasks').child(task_id).get()
            if task_data:
                task_data['id'] = task_id
            return task_data
        except Exception as e:
            print(f"Error getting task: {e}")
            return None

    async def add_task(self, task_data: Dict) -> str:
        try:
            task_data['created_at'] = datetime.now().isoformat()
            task_data['status'] = 'active'
            new_task_ref = self.db.child('tasks').push(task_data)
            return new_task_ref.key
        except Exception as e:
            print(f"Error adding task: {e}")
            raise

    async def remove_task(self, task_id: str) -> bool:
        try:
            self.db.child('tasks').child(task_id).update({'status': 'inactive'})
            return True
        except Exception as e:
            print(f"Error removing task: {e}")
            return False

    async def create_submission(self, user_id: int, task_id: str, screenshot_url: str, note: str = None) -> bool:
        try:
            submission_data = {
                'user_id': user_id,
                'task_id': task_id,
                'screenshot_url': screenshot_url,
                'note': note,
                'status': 'pending',
                'submitted_at': datetime.now().isoformat()
            }
            self.db.child('submissions').push(submission_data)
            return True
        except Exception as e:
            print(f"Error creating submission: {e}")
            return False

    async def get_pending_submissions(self) -> List[Dict]:
        try:
            submissions = self.db.child('submissions').get()
            if not submissions:
                return []
            result = []
            for sub_id, sub_data in submissions.items():
                if sub_data.get('status') == 'pending':
                    sub_data['id'] = sub_id
                    user = await self.get_user(sub_data['user_id'])
                    sub_data['username'] = user.get('username', 'Unknown') if user else 'Unknown'
                    task = await self.get_task(sub_data['task_id'])
                    sub_data['task_title'] = task.get('title', 'Unknown') if task else 'Unknown'
                    sub_data['task_reward'] = task.get('reward', 0) if task else 0
                    result.append(sub_data)
            return result
        except Exception as e:
            print(f"Error getting pending submissions: {e}")
            return []

    async def approve_submission(self, submission_id: str) -> bool:
        try:
            submission = self.db.child('submissions').child(submission_id).get()
            if not submission or submission.get('status') != 'pending':
                return False
            task = await self.get_task(submission['task_id'])
            if not task:
                return False
            await self.update_balance(submission['user_id'], task['reward'], 'add')
            self.db.child('submissions').child(submission_id).update({
                'status': 'approved',
                'approved_at': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            print(f"Error approving submission: {e}")
            return False

    async def reject_submission(self, submission_id: str, reason: str) -> bool:
        try:
            self.db.child('submissions').child(submission_id).update({
                'status': 'rejected',
                'reject_reason': reason
            })
            return True
        except Exception as e:
            print(f"Error rejecting submission: {e}")
            return False

    async def create_withdrawal(self, user_id: int, amount: float) -> bool:
        try:
            withdrawal_data = {
                'user_id': user_id,
                'amount': amount,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            self.db.child('withdrawals').push(withdrawal_data)
            return True
        except Exception as e:
            print(f"Error creating withdrawal: {e}")
            return False

    async def get_pending_withdrawals(self) -> List[Dict]:
        try:
            withdrawals = self.db.child('withdrawals').get()
            if not withdrawals:
                return []
            result = []
            for w_id, w_data in withdrawals.items():
                if w_data.get('status') == 'pending':
                    w_data['id'] = w_id
                    user = await self.get_user(w_data['user_id'])
                    w_data['username'] = user.get('username', 'Unknown') if user else 'Unknown'
                    result.append(w_data)
            return result
        except Exception as e:
            print(f"Error getting pending withdrawals: {e}")
            return []

    async def process_withdrawal(self, withdrawal_id: str, status: str, reason: str = None) -> bool:
        try:
            withdrawal = self.db.child('withdrawals').child(withdrawal_id).get()
            if not withdrawal:
                return False
            if status == 'approved':
                user = await self.get_user(withdrawal['user_id'])
                if user and user['balance'] >= withdrawal['amount']:
                    await self.update_balance(withdrawal['user_id'], withdrawal['amount'], 'subtract')
                    self.db.child('users').child(str(withdrawal['user_id'])).update({
                        'total_withdrawn': user.get('total_withdrawn', 0) + withdrawal['amount']
                    })
                else:
                    return False
            self.db.child('withdrawals').child(withdrawal_id).update({
                'status': status,
                'reason': reason,
                'processed_at': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            print(f"Error processing withdrawal: {e}")
            return False

    async def redeem_gift_code(self, code: str, user_id: int) -> Dict:
        try:
            code_data = self.db.child('gift_codes').child(code).get()
            if not code_data:
                return {'success': False, 'message': 'Invalid gift code'}
            if code_data.get('expiry_date'):
                expiry_date = datetime.fromisoformat(code_data['expiry_date'])
                if expiry_date < datetime.now():
                    return {'success': False, 'message': 'Code expired'}
            usage_count = code_data.get('usage_count', 0)
            usage_limit = code_data.get('usage_limit', 1)
            if usage_limit != 0 and usage_count >= usage_limit:
                return {'success': False, 'message': 'Code usage limit reached'}
            used_users = code_data.get('used_users', [])
            if user_id in used_users and usage_limit != -1:
                return {'success': False, 'message': 'Already used this code'}
            await self.update_balance(user_id, code_data['amount'], 'add')
            used_users.append(user_id)
            self.db.child('gift_codes').child(code).update({
                'usage_count': usage_count + 1,
                'used_users': used_users
            })
            return {'success': True, 'message': f'Redeemed {code_data["amount"]} coins!'}
        except Exception as e:
            print(f"Error redeeming code: {e}")
            return {'success': False, 'message': 'Error redeeming code'}

    async def create_gift_code(self, code: str, amount: float, usage_limit: int, expiry_days: int = None) -> bool:
        try:
            code_data = {
                'code': code,
                'amount': amount,
                'usage_limit': usage_limit,
                'usage_count': 0,
                'used_users': [],
                'created_at': datetime.now().isoformat()
            }
            if expiry_days:
                code_data['expiry_date'] = (datetime.now() + timedelta(days=expiry_days)).isoformat()
            self.db.child('gift_codes').child(code).set(code_data)
            return True
        except Exception as e:
            print(f"Error creating gift code: {e}")
            return False

    async def add_force_join_channel(self, channel_id: str) -> bool:
        try:
            self.db.child('channels').child(channel_id).set({'created_at': datetime.now().isoformat()})
            return True
        except Exception as e:
            print(f"Error adding channel: {e}")
            return False

    async def remove_force_join_channel(self, channel_id: str) -> bool:
        try:
            self.db.child('channels').child(channel_id).delete()
            return True
        except Exception as e:
            print(f"Error removing channel: {e}")
            return False

    async def get_force_join_channels(self) -> List[str]:
        try:
            channels = self.db.child('channels').get()
            if not channels:
                return []
            return list(channels.keys())
        except Exception as e:
            print(f"Error getting channels: {e}")
            return []

    async def get_analytics(self) -> Dict:
        try:
            users = self.db.child('users').get()
            total_users = len(users) if users else 0
            active_users = 0
            total_earnings = 0
            total_withdrawn = 0
            if users:
                week_ago = datetime.now() - timedelta(days=7)
                for user_data in users.values():
                    if user_data.get('banned', False):
                        continue
                    total_earnings += user_data.get('total_earned', 0)
                    total_withdrawn += user_data.get('total_withdrawn', 0)
                    last_active = user_data.get('last_active')
                    if last_active:
                        try:
                            if datetime.fromisoformat(last_active) > week_ago:
                                active_users += 1
                        except:
                            pass
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_earnings': total_earnings,
                'total_withdrawn': total_withdrawn,
                'pending_withdrawals': len(await self.get_pending_withdrawals()),
                'pending_submissions': len(await self.get_pending_submissions())
            }
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return {}

    async def get_leaderboard(self, type: str = 'balance', limit: int = 10) -> List[Dict]:
        try:
            users = self.db.child('users').get()
            if not users:
                return []
            user_list = []
            for user_data in users.values():
                if user_data.get('banned', False):
                    continue
                user_list.append({
                    'username': user_data.get('username', 'Unknown'),
                    'balance': user_data.get('balance', 0),
                    'referrals': user_data.get('referrals', 0),
                    'total_earned': user_data.get('total_earned', 0)
                })
            if type == 'balance':
                user_list.sort(key=lambda x: x['balance'], reverse=True)
            elif type == 'referrals':
                user_list.sort(key=lambda x: x['referrals'], reverse=True)
            else:
                user_list.sort(key=lambda x: x['total_earned'], reverse=True)
            return user_list[:limit]
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            return []
