# database.py - محدث بإصلاحات كاملة مع جميع الدوال ونظام العمولة الثابتة
import sqlite3
import logging
import json
from datetime import datetime, time
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        try:
            self.conn = sqlite3.connect('usdt_broker.db', check_same_thread=False)
            logger.info("✅ تم الاتصال بقاعدة البيانات بنجاح")
            self.create_tables()
            self.initialize_settings()
        except Exception as e:
            logger.error(f"❌ فشل في الاتصال بقاعدة البيانات: {e}")
            raise
    def get_recent_trades(self, limit=20):
        """الحصول على آخر الصفقات مع معلومات الاتصال بالمستخدمين"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT
                t.id as trade_id,
                t.amount,
                t.exchange_rate,
                t.status,
                t.created_at,
                t.updated_at,
                -- معلومات البائع
                seller.user_id as seller_id,
                seller.first_name as seller_first_name,
                seller.username as seller_username,
                seller.phone as seller_phone,
                -- معلومات المشتري
                buyer.user_id as buyer_id,
                buyer.first_name as buyer_first_name,
                buyer.username as buyer_username,
                buyer.phone as buyer_phone,
                -- نوع العرض
                o.offer_type
            FROM trades t
            JOIN offers o ON t.offer_id = o.id
            JOIN users seller ON t.seller_id = seller.user_id
            JOIN users buyer ON t.buyer_id = buyer.user_id
            ORDER BY t.created_at DESC
            LIMIT ?
        ''', (limit,))

        trades = []
        for row in cursor.fetchall():
            trade = {
                'trade_id': row[0],
                'amount': row[1],
                'exchange_rate': row[2],
                'status': row[3],
                'created_at': row[4],
                'updated_at': row[5],
                'seller': {
                    'user_id': row[6],
                    'first_name': row[7],
                    'username': row[8],
                    'phone': row[9]
                },
                'buyer': {
                    'user_id': row[10],
                    'first_name': row[11],
                    'username': row[12],
                    'phone': row[13]
                },
                'offer_type': row[14]
            }
            trades.append(trade)

        return trades
    def create_tables(self):
        cursor = self.conn.cursor()

        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                user_type TEXT DEFAULT 'user',
                tier TEXT DEFAULT 'برونزي',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # جدول العروض
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                offer_type TEXT,
                amount REAL,
                exchange_rate REAL,
                payment_method TEXT,
                status TEXT DEFAULT 'active',
                channel_message_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # جدول الصفقات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offer_id INTEGER,
                buyer_id INTEGER,
                seller_id INTEGER,
                broker_id INTEGER,
                amount REAL,
                exchange_rate REAL,
                commission REAL,
                transfer_fee REAL DEFAULT 0.5,
                buyer_wallet TEXT,
                payment_proof TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (offer_id) REFERENCES offers (id),
                FOREIGN KEY (buyer_id) REFERENCES users (user_id),
                FOREIGN KEY (seller_id) REFERENCES users (user_id),
                FOREIGN KEY (broker_id) REFERENCES users (user_id)
            )
        ''')

        # جدول إعدادات النظام
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE,
                setting_value TEXT,
                description TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # جدول الرسائل القابلة للتخصيص
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_key TEXT UNIQUE,
                message_text TEXT,
                description TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()
        logger.info("✅ تم إنشاء الجداول بنجاح")

    def initialize_settings(self):
        """تهيئة الإعدادات الافتراضية"""
        cursor = self.conn.cursor()

        # إعدادات العمولة الثابتة
        default_settings = [
            ('commission_small_amount', '30', 'الحد الأقصى للمبالغ الصغيرة (USDT)'),
            ('commission_small', '0.15', 'العمولة للمبالغ الصغيرة (15 سنت)'),
            ('commission_large', '0.25', 'العمولة للمبالغ الكبيرة (0.25 USDT)'),
            ('transfer_fee', '0.50', 'عمولة التحويل بين المحافظ (بالدولار)'),
            ('bot_active', 'true', 'حالة تفعيل البوت'),
            ('welcome_message', 'مرحباً بك في نظام وساطة USDT', 'رسالة الترحيب'),
            ('trade_instructions', 'اتبع التعليمات لإتمام الصفقة', 'تعليمات الصفقة')
        ]

        for key, value, description in default_settings:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO system_settings (setting_key, setting_value, description)
                    VALUES (?, ?, ?)
                ''', (key, value, description))
            except Exception as e:
                logger.error(f"خطأ في إضافة الإعداد {key}: {e}")

        # الرسائل الافتراضية
        default_messages = [
            ('welcome', '🏦 **مرحباً بك في نظام وساطة USDT**\n\nاختر من القائمة أدناه:', 'رسالة الترحيب الرئيسية'),
            ('offer_created', '✅ **تم إنشاء العرض بنجاح!**', 'رسالة تأكيد إنشاء العرض'),
            ('trade_started', '🎉 **تم بدء صفقة جديدة!**', 'رسالة بدء الصفقة')
        ]

        for key, text, description in default_messages:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO bot_messages (message_key, message_text, description)
                    VALUES (?, ?, ?)
                ''', (key, text, description))
            except Exception as e:
                logger.error(f"خطأ في إضافة الرسالة {key}: {e}")

        self.conn.commit()

    def calculate_commission(self, amount):
        """حساب العمولة بناءً على قيمة العرض"""
        try:
            small_amount_limit = float(self.get_setting('commission_small_amount', '30'))
            small_commission = float(self.get_setting('commission_small', '0.15'))
            large_commission = float(self.get_setting('commission_large', '0.25'))

            if amount <= small_amount_limit:
                commission = small_commission
            else:
                commission = large_commission

            return commission
        except Exception as e:
            logger.error(f"خطأ في حساب العمولة: {e}")
            return 0.25

    def get_commission_small_amount(self):
        """الحصول على حد المبالغ الصغيرة"""
        return float(self.get_setting('commission_small_amount', '30'))

    def get_commission_small(self):
        """الحصول على عمولة المبالغ الصغيرة"""
        return float(self.get_setting('commission_small', '0.15'))

    def get_commission_large(self):
        """الحصول على عمولة المبالغ الكبيرة"""
        return float(self.get_setting('commission_large', '0.25'))

    def update_commission_settings(self, small_amount, small_commission, large_commission):
        """تحديث إعدادات العمولة"""
        try:
            self.update_setting('commission_small_amount', str(small_amount))
            self.update_setting('commission_small', str(small_commission))
            self.update_setting('commission_large', str(large_commission))
            logger.info(f"✅ تم تحديث إعدادات العمولة: الحد {small_amount} USDT، الصغيرة {small_commission}، الكبيرة {large_commission}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث إعدادات العمولة: {e}")
            return False

    def is_bot_working_hours(self):
        """التحقق إذا كان البوت يعمل ضمن الوقت المحدد"""
        try:
            now = datetime.now().time()
            start_time = time(Config.BOT_START_TIME, 0)  # 8:00
            end_time = time(Config.BOT_END_TIME, 0)      # 24:00

            if Config.BOT_START_TIME < Config.BOT_END_TIME:
                return start_time <= now <= end_time
            else:
                return now >= start_time or now <= end_time
        except Exception as e:
            logger.error(f"خطأ في التحقق من وقت العمل: {e}")
            return True

    def expire_all_offers(self):
        """تعطيل جميع العروض عند منتصف الليل"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                UPDATE offers SET status = 'expired'
                WHERE status = 'active'
            ''')
            self.conn.commit()
            count = cursor.rowcount
            logger.info(f"✅ تم تعطيل {count} عرض عند منتصف الليل")
            return count
        except Exception as e:
            logger.error(f"❌ خطأ في تعطيل العروض: {e}")
            return 0

    def get_transfer_fee(self):
        """الحصول على عمولة التحويل بين المحافظ"""
        fee = self.get_setting('transfer_fee', '0.50')
        return float(fee)

    def update_transfer_fee(self, new_fee):
        """تحديث عمولة التحويل بين المحافظ"""
        self.update_setting('transfer_fee', str(new_fee))

    def cancel_trade_by_admin(self, trade_id, admin_id):
        """إلغاء الصفقة بواسطة المشرف"""
        cursor = self.conn.cursor()
        try:
            # تحديث حالة الصفقة
            cursor.execute('''
                UPDATE trades SET status = ?, broker_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (Config.STATUS_CANCELLED, admin_id, trade_id))

            # استعادة حالة العرض إلى نشط
            trade = self.get_trade(trade_id)
            if trade and trade['offer_id']:
                cursor.execute('''
                    UPDATE offers SET status = 'active'
                    WHERE id = ?
                ''', (trade['offer_id'],))

            self.conn.commit()
            logger.info(f"✅ تم إلغاء الصفقة {trade_id} بواسطة المشرف {admin_id}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إلغاء الصفقة: {e}")
            self.conn.rollback()
            return False

    def reactivate_offer_after_trade_cancel(self, trade_id):
        """إعادة تفعيل العرض بعد إلغاء الصفقة"""
        cursor = self.conn.cursor()
        try:
            trade = self.get_trade(trade_id)
            if trade and trade['offer_id']:
                cursor.execute('''
                    UPDATE offers SET status = 'active'
                    WHERE id = ?
                ''', (trade['offer_id'],))
                self.conn.commit()
                logger.info(f"✅ تم إعادة تفعيل العرض {trade['offer_id']} بعد إلغاء الصفقة")
                return True
        except Exception as e:
            logger.error(f"❌ خطأ في إعادة تفعيل العرض: {e}")
        return False

    def add_user(self, user_id, username, first_name, last_name):
        """إضافة مستخدم جديد"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            self.conn.commit()
            logger.info(f"✅ تم إضافة/تحديث المستخدم: {user_id} - {username}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المستخدم {user_id}: {e}")
            self.conn.rollback()
            return False

    def get_user(self, user_id):
        """الحصول على بيانات المستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'phone': row[4],
                'user_type': row[5],
                'tier': row[6],
                'created_at': row[7]
            }
        return None

    def update_user_phone(self, user_id, phone):
        """تحديث رقم هاتف المستخدم"""
        cursor = self.conn.cursor()
        try:
            # أولاً تأكد من وجود المستخدم
            user_exists = self.get_user(user_id)
            if not user_exists:
                # إذا لم يكن المستخدم موجوداً، أنشئه أولاً
                cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, phone)
                    VALUES (?, ?)
                ''', (user_id, phone))
            else:
                # إذا كان موجوداً، قم بالتحديث فقط
                cursor.execute('UPDATE users SET phone = ? WHERE user_id = ?', (phone, user_id))

            self.conn.commit()
            logger.info(f"✅ تم حفظ/تحديث رقم الهاتف للمستخدم {user_id}: {phone}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ رقم الهاتف للمستخدم {user_id}: {e}")
            self.conn.rollback()
            return False

    def get_setting(self, key, default=None):
        """الحصول على إعداد من قاعدة البيانات"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT setting_value FROM system_settings WHERE setting_key = ?', (key,))
        result = cursor.fetchone()
        if result:
            return result[0]
        return default

    def update_setting(self, key, value):
        """تحديث إعداد في قاعدة البيانات"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO system_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        self.conn.commit()
        logger.info(f"✅ تم تحديث الإعداد {key} إلى {value}")

    def get_message(self, key, default=None):
        """الحصول على رسالة من قاعدة البيانات"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT message_text FROM bot_messages WHERE message_key = ?', (key,))
        result = cursor.fetchone()
        if result:
            return result[0]
        return default

    def update_message(self, key, text):
        """تحديث رسالة في قاعدة البيانات"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO bot_messages (message_key, message_text, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, text))
        self.conn.commit()
        logger.info(f"✅ تم تحديث الرسالة {key}")

    def get_all_settings(self):
        """الحصول على جميع الإعدادات"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT setting_key, setting_value, description FROM system_settings')
        return cursor.fetchall()

    def get_all_messages(self):
        """الحصول على جميع الرسائل"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT message_key, message_text, description FROM bot_messages')
        return cursor.fetchall()

    def is_bot_active(self):
        """التحقق من حالة تفعيل البوت"""
        active = self.get_setting('bot_active', 'true')
        return active.lower() == 'true'

    def create_offer(self, user_id, offer_type, amount, exchange_rate, payment_method, channel_message_id=None):
        """إنشاء عرض جديد"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO offers (user_id, offer_type, amount, exchange_rate, payment_method, channel_message_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, offer_type, amount, exchange_rate, payment_method, channel_message_id))
            self.conn.commit()
            offer_id = cursor.lastrowid
            logger.info(f"✅ تم إنشاء العرض في قاعدة البيانات - ID: {offer_id}")
            return offer_id
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء العرض: {e}")
            self.conn.rollback()
            return None

    def create_and_get_offer(self, user_id, offer_type, amount, exchange_rate, payment_method, channel_message_id=None):
        """إنشاء العرض ثم استرجاعه مباشرة"""
        cursor = self.conn.cursor()
        try:
            # إنشاء العرض
            cursor.execute('''
                INSERT INTO offers (user_id, offer_type, amount, exchange_rate, payment_method, channel_message_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, offer_type, amount, exchange_rate, payment_method, channel_message_id))
            self.conn.commit()
            offer_id = cursor.lastrowid

            # استرجاع العرض مباشرة
            cursor.execute('''
                SELECT o.*, u.first_name, u.tier
                FROM offers o
                JOIN users u ON o.user_id = u.user_id
                WHERE o.id = ?
            ''', (offer_id,))
            row = cursor.fetchone()

            if row:
                offer_data = {
                    'id': row[0], 'user_id': row[1], 'offer_type': row[2], 'amount': row[3],
                    'exchange_rate': row[4], 'payment_method': row[5], 'status': row[6],
                    'channel_message_id': row[7], 'created_at': row[8], 'first_name': row[9],
                    'tier': row[10]
                }
                logger.info(f"✅ تم إنشاء واسترجاع العرض بنجاح - ID: {offer_id}")
                return offer_data
            else:
                logger.error(f"❌ فشل في استرجاع العرض بعد الإنشاء - ID: {offer_id}")
                return None

        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء/استرجاع العرض: {e}")
            self.conn.rollback()
            return None

    def update_offer_message_id(self, offer_id, channel_message_id):
        """تحديث معرف رسالة القناة للعرض"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE offers SET channel_message_id = ? WHERE id = ?',
                      (channel_message_id, offer_id))
        self.conn.commit()
        logger.info(f"✅ تم تحديث معرف رسالة القناة للعرض {offer_id}: {channel_message_id}")

    def get_offer(self, offer_id):
        """الحصول على بيانات العرض"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                SELECT o.*, u.first_name, u.tier
                FROM offers o
                JOIN users u ON o.user_id = u.user_id
                WHERE o.id = ?
            ''', (offer_id,))
            row = cursor.fetchone()
            if row:
                offer_data = {
                    'id': row[0], 'user_id': row[1], 'offer_type': row[2], 'amount': row[3],
                    'exchange_rate': row[4], 'payment_method': row[5], 'status': row[6],
                    'channel_message_id': row[7], 'created_at': row[8], 'first_name': row[9],
                    'tier': row[10]
                }
                logger.info(f"✅ تم استرجاع العرض من قاعدة البيانات - ID: {offer_id}")
                return offer_data
            else:
                logger.warning(f"⚠️ لم يتم العثور على العرض في قاعدة البيانات - ID: {offer_id}")
                return None
        except Exception as e:
            logger.error(f"❌ خطأ في استرجاع العرض {offer_id}: {e}")
            return None

    def get_user_offers(self, user_id):
        """الحصول على عروض المستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM offers
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        return cursor.fetchall()

    def create_trade(self, offer_id, buyer_id, seller_id, amount, exchange_rate):
        """إنشاء صفقة جديدة مع العمولة المحددة"""
        cursor = self.conn.cursor()

        # حساب العمولة بناءً على قيمة العرض
        commission = self.calculate_commission(amount)
        transfer_fee = self.get_transfer_fee()

        cursor.execute('''
            INSERT INTO trades (offer_id, buyer_id, seller_id, amount, exchange_rate, commission, transfer_fee)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (offer_id, buyer_id, seller_id, amount, exchange_rate, commission, transfer_fee))

        # تحديث حالة العرض إلى غير نشط أثناء الصفقة
        cursor.execute('UPDATE offers SET status = ? WHERE id = ?', ('in_trade', offer_id))

        self.conn.commit()
        return cursor.lastrowid

    def update_trade_status(self, trade_id, status):
        """تحديث حالة الصفقة"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE trades SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, trade_id))
        self.conn.commit()

    def get_trade(self, trade_id):
        """الحصول على بيانات الصفقة"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.*,
                   buyer.first_name as buyer_name,
                   seller.first_name as seller_name,
                   o.offer_type
            FROM trades t
            JOIN users buyer ON t.buyer_id = buyer.user_id
            JOIN users seller ON t.seller_id = seller.user_id
            JOIN offers o ON t.offer_id = o.id
            WHERE t.id = ?
        ''', (trade_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0], 'offer_id': row[1], 'buyer_id': row[2], 'seller_id': row[3],
                'broker_id': row[4], 'amount': row[5], 'exchange_rate': row[6],
                'commission': row[7], 'transfer_fee': row[8], 'buyer_wallet': row[9],
                'payment_proof': row[10], 'status': row[11], 'created_at': row[12],
                'updated_at': row[13], 'buyer_name': row[14], 'seller_name': row[15],
                'offer_type': row[16]
            }
        return None

    def get_user_trades(self, user_id):
        """الحصول على صفقات المستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.*,
                buyer.first_name as buyer_name,
                seller.first_name as seller_name
            FROM trades t
            LEFT JOIN users buyer ON t.buyer_id = buyer.user_id
            LEFT JOIN users seller ON t.seller_id = seller.user_id
            WHERE t.buyer_id = ? OR t.seller_id = ?
            ORDER BY t.created_at DESC
        ''', (user_id, user_id))
        return cursor.fetchall()
    # في database.py - إضافة دالة للتعامل مع حالات الصفقات الجديدة
    def get_trades_waiting_proof(self):
        """الحصول على الصفقات التي تنتظر مستند إرسال"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM trades
            WHERE status = ?
        ''', (Config.STATUS_WAITING_PROOF,))
        return cursor.fetchall()
    def update_trade_payment_proof(self, trade_id, payment_proof):
        """تحديث إثبات الدفع للصفقة"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE trades SET payment_proof = ? WHERE id = ?', (payment_proof, trade_id))
        self.conn.commit()

    def update_trade_buyer_wallet(self, trade_id, wallet_address):
        """تحديث محفظة المشتري"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE trades SET buyer_wallet = ? WHERE id = ?', (wallet_address, trade_id))
        self.conn.commit()
    def get_trades_waiting_payment_details(self):
        """الحصول على الصفقات التي تنتظر تفاصيل الدفع"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM trades
            WHERE status = ?
        ''', (Config.STATUS_WAITING_PAYMENT_DETAILS,))
        return cursor.fetchall()

    def get_trades_with_payment_details_sent(self):
        """الحصول على الصفقات التي تم إرسال تفاصيل الدفع فيها"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM trades
            WHERE status = ?
        ''', (Config.STATUS_PAYMENT_DETAILS_SENT,))
        return cursor.fetchall()

db = Database()