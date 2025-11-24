# bot.py - الملف الرئيسي محدث بإصلاحات كاملة
# bot.py - الملف الرئيسي محدث بإصلاحات كاملة
import logging
import pytz
from datetime import datetime
from datetime import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import Config
from database import db
from channel_manager import ChannelManager
from telegram import Update  # تأكد من وجود هذا

# تفعيل logging مفصل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),

    ]
)
logger = logging.getLogger(__name__)

class USDTBrokerBot:
    def __init__(self):
        self.application = Application.builder().token(Config.BOT_TOKEN).build()
        self.channel_manager = ChannelManager(self.application)
        self.setup_handlers()

    async def auto_expire_offers_at_midnight(self, context: ContextTypes.DEFAULT_TYPE):
        """تعطيل جميع العروض تلقائياً عند منتصف الليل"""
        try:
            logger.info("⏰ بدء التعطيل التلقائي للعروض عند منتصف الليل...")

            # تعطيل جميع العروض في القناة
            expired_count = await self.channel_manager.expire_all_channel_offers()

            if expired_count > 0:
                logger.info(f"✅ تم تعطيل {expired_count} عرض تلقائياً عند منتصف الليل")

                # إشعار المشرف
                if Config.ADMIN_ID:
                    await context.bot.send_message(
                        Config.ADMIN_ID,
                        f"⏰ **التعطيل التلقائي للعروض**\n\nتم تعطيل {expired_count} عرض في القناة تلقائياً عند منتصف الليل.",
                        parse_mode='Markdown'
                    )
            else:
                logger.info("✅ لم تكن هناك عروض نشطة لتعطيلها")

        except Exception as e:
            logger.error(f"❌ خطأ في التعطيل التلقائي للعروض: {e}")
    async def startup_tasks_callback(self, context: ContextTypes.DEFAULT_TYPE):
        """استدعاء مهام البدء عبر job_queue"""
        try:
            logger.info("🔄 بدء مهام التعافي بعد التشغيل عبر job_queue...")

            # استعادة الصفقات النشطة
            recovered_count = await self.recover_failed_trades()
            logger.info(f"✅ تم استعادة {recovered_count} صفقة نشطة")

            # فحص صحة النظام
            health_ok = await self.system_health_check()
            if health_ok:
                logger.info("✅ فحص صحة النظام: ناجح")
            else:
                logger.warning("⚠️ فحص صحة النظام: هناك مشاكل")

            # تنظيف البيانات الميتة
            cleaned_count = await self.cleanup_orphaned_data()
            logger.info(f"🧹 تم تنظيف {cleaned_count} بيانات ميتة")

            # تعطيل العروض القديمة إذا كان الوقت خارج ساعات العمل
            if not db.is_bot_working_hours():
                logger.info("⏰ خارج وقت العمل، جاري تعطيل العروض...")
                expired_count = await self.channel_manager.expire_all_channel_offers()
                logger.info(f"✅ تم تعطيل {expired_count} عرض خارج وقت العمل")

            logger.info("✅ اكتملت جميع مهام بدء التشغيل")

        except Exception as e:
            logger.error(f"❌ خطأ في مهام بدء التشغيل: {e}")
    async def auto_expire_offers(self, context: ContextTypes.DEFAULT_TYPE):
            """تعطيل جميع العروض تلقائياً في منتصف الليل"""
            try:
                logger.info("⏰ بدء تعطيل العروض تلقائياً...")
                expired_count = await self.channel_manager.expire_all_channel_offers()
                logger.info(f"✅ تم تعطيل {expired_count} عرض تلقائياً")

                # إشعار المشرف
                if Config.ADMIN_ID:
                    await context.bot.send_message(
                        Config.ADMIN_ID,
                        f"⏰ **تعطيل العروض التلقائي**\n\nتم تعطيل {expired_count} عرض في القناة تلقائياً.",
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"❌ خطأ في التعطيل التلقائي للعروض: {e}")
    def setup_error_handling(self):
        """إعداد معالجة الأخطاء والجدولة - النسخة المصححة"""
        try:
            # التحقق من أن job_queue متاحة
            if hasattr(self.application, 'job_queue') and self.application.job_queue:
                logger.info("✅ job_queue متاحة، جاري إعداد الجدولة...")

                # جدولة المهام الدورية
               # self.application.job_queue.run_repeating(
                   # self.periodic_maintenance,
                   # interval=3600,  # كل ساعة
                    #first=10
               # )

                # جدولة النسخ الاحتياطي اليومي
                #self.application.job_queue.run_daily(
               #     self.daily_backup,
               #     time=datetime.time(hour=9, minute=50)  # 2 صباحاً
               # )

                # جدولة تعطيل العروض عند منتصف الليل
                midnight_time = time(hour=21, minute=0)
                self.application.job_queue.run_daily(
                    self.auto_expire_offers_at_midnight,
                    time=midnight_time,days=(0,1,2,3,4,5,6))

                # جدولة مهام البدء لتشغيل بعد 10 ثواني من بدء التشغيل
                self.application.job_queue.run_once(
                    self.startup_tasks_callback,
                    when=10
                )

                logger.info("✅ تم إعداد جدولة المهام الدورية والتعطيل التلقائي")
            else:
                logger.warning("⚠️ job_queue غير متاحة للجدولة")

        except Exception as e:
            logger.error(f"❌ خطأ في إعداد الجدولة: {e}")
    async def periodic_maintenance(self, context: ContextTypes.DEFAULT_TYPE):
        """الصيانة الدورية"""
        try:
            logger.info("🛠️ بدء الصيانة الدورية...")

            # تنظيف الصفقات العالقة
            await self.auto_cancel_stuck_trades()

            # تنظيف البيانات الميتة
            await self.cleanup_orphaned_data()

            # التحقق من سلامة النظام
            await self.system_health_check()

            logger.info("✅ اكتملت الصيانة الدورية")

        except Exception as e:
            logger.error(f"❌ خطأ في الصيانة الدورية: {e}")

    async def daily_backup(self, context: ContextTypes.DEFAULT_TYPE):
        """نسخ احتياطي يومي"""
        try:
            logger.info("💾 بدء النسخ الاحتياطي اليومي...")
            await self.backup_database()
            logger.info("✅ اكتمل النسخ الاحتياطي اليومي")
        except Exception as e:
            logger.error(f"❌ خطأ في النسخ الاحتياطي: {e}")

    async def system_health_check(self):
        """فحص صحة النظام"""
        try:
            # فحص قاعدة البيانات
            cursor = db.conn.cursor()
            cursor.execute('SELECT 1')

            # فحص الاتصال بـ Telegram
            await self.application.bot.get_me()

            # فحص المساحة التخزينية
            import shutil
            total, used, free = shutil.disk_usage(".")
            disk_usage_percent = (used / total) * 100

            if disk_usage_percent > 90:
                logger.warning(f"🚨 استخدام القرص مرتفع: {disk_usage_percent:.2f}%")

            logger.info("✅ فحص صحة النظام: جيد")
            return True

        except Exception as e:
            logger.error(f"❌ فحص صحة النظام فشل: {e}")
            return False
    def setup_handlers(self):
        # الأوامر الأساسية
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("menu", self.main_menu))
        self.application.add_handler(CommandHandler("my_offers", self.my_offers))
        self.application.add_handler(CommandHandler("my_trades", self.my_trades))
        self.application.add_handler(CommandHandler("admin", self.admin_panel))
        self.application.add_handler(CommandHandler("debug", self.debug_trades))

        # معالجات الاستعلامات
        self.application.add_handler(CallbackQueryHandler(self.handle_callback, pattern="^.*$"))

        # معالجات الرسائل
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, self.handle_document))
        self.application.add_handler(MessageHandler(filters.CONTACT, self.handle_contact))
    async def handle_trade_timeout(self, trade_id: int):
        """معالجة انتهاء وقت الصفقة تلقائياً"""
        try:
            logger.info(f"⏰ فحص انتهاء وقت الصفقة #{trade_id}")

            trade = db.get_trade(trade_id)
            if not trade:
                return False

            # إذا كانت الصفقة عالقة في حالة متقدمة لمدة طويلة
            if trade['status'] in [Config.STATUS_PENDING, Config.STATUS_WAITING_PROOF, Config.STATUS_WAITING_PAYMENT]:
                created_at = datetime.fromisoformat(trade['created_at'].replace('Z', '+00:00'))
                current_time = datetime.now().replace(tzinfo=created_at.tzinfo)
                time_diff = (current_time - created_at).total_seconds() / 3600  # بالساعات

                if time_diff > Config.TRADE_TIMEOUT_HOURS:
                    logger.warning(f"🚨 الصفقة #{trade_id} انتهى وقتها، جاري الإلغاء التلقائي")

                    # إلغاء الصفقة
                    db.update_trade_status(trade_id, Config.STATUS_CANCELLED)
                    db.reactivate_offer_after_trade_cancel(trade_id)

                    # إشعار الأطراف
                    cancel_text = f"""
    ❌ **تم إلغاء الصفقة تلقائياً**

    📋 **الصفقة #{trade_id} ملغية بسبب انتهاء الوقت**
    • الكمية: {trade['amount']:,.2f} USDT
    • السبب: انتهى الوقت المحدد للإتمام ({Config.TRADE_TIMEOUT_HOURS} ساعة)

    للمزيد من المعلومات، تواصل مع الدعم.
                    """

                    for participant_id in [trade['buyer_id'], trade['seller_id']]:
                        try:
                            await self.application.bot.send_message(
                                participant_id,
                                cancel_text,
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.error(f"فشل إرسال إشعار إلغاء: {e}")

                    return True
            return False

        except Exception as e:
            logger.error(f"❌ خطأ في معالجة انتهاء وقت الصفقة #{trade_id}: {e}")
            return False

    async def auto_cancel_stuck_trades(self):
        """إلغاء الصفقات العالقة تلقائياً"""
        try:
            logger.info("🔍 فحص الصفقات العالقة...")

            # الحصول على الصفقات النشطة
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT id, status, created_at
                FROM trades
                WHERE status NOT IN (?, ?, ?)
            ''', (Config.STATUS_COMPLETED, Config.STATUS_CANCELLED, Config.STATUS_USDT_SENT_TO_BUYER))

            stuck_trades = cursor.fetchall()
            cancelled_count = 0

            for trade_id, status, created_at in stuck_trades:
                try:
                    if await self.handle_trade_timeout(trade_id):
                        cancelled_count += 1
                except Exception as e:
                    logger.error(f"❌ خطأ في معالجة الصفقة #{trade_id}: {e}")
                    continue

            if cancelled_count > 0:
                logger.info(f"✅ تم إلغاء {cancelled_count} صفقة عالقة")

                # إشعار المشرف
                if Config.ADMIN_ID:
                    await self.application.bot.send_message(
                        Config.ADMIN_ID,
                        f"🔄 **تنظيف الصفقات العالقة**\n\nتم إلغاء {cancelled_count} صفقة تلقائياً",
                        parse_mode='Markdown'
                    )

            return cancelled_count

        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف الصفقات العالقة: {e}")
            return 0

    async def handle_database_error(self, error: Exception, context: ContextTypes.DEFAULT_TYPE = None):
        """معالجة أخطاء قاعدة البيانات"""
        logger.error(f"🗄️ خطأ في قاعدة البيانات: {error}")

        # محاولة إعادة الاتصال
        try:
            db.reconnect()
            logger.info("✅ تم إعادة الاتصال بقاعدة البيانات")
        except Exception as e:
            logger.critical(f"❌ فشل إعادة الاتصال بقاعدة البيانات: {e}")

            # إشعار المشرف بالخطأ الحرجة
            if Config.ADMIN_ID:
                await self.application.bot.send_message(
                    Config.ADMIN_ID,
                    f"🚨 **خطأ حرج في قاعدة البيانات**\n\n{str(e)}",
                    parse_mode='Markdown'
                )
    async def request_payment_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """طلب تفاصيل الدفع من البائع - النسخة المصححة"""
        query = update.callback_query
        await query.answer()

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # التحقق من أن المستخدم هو البائع
        if query.from_user.id != trade['seller_id']:
            await query.answer("❌ فقط البائع يمكنه إرسال تفاصيل الدفع", show_alert=True)
            return

        # تحديث حالة الصفقة
        db.update_trade_status(trade_id, Config.STATUS_WAITING_PAYMENT_DETAILS)

        # طلب تفاصيل الدفع من البائع
        payment_request = f"""
    💳 **يرجى إرسال تفاصيل حساب الدفع**

    📋 **الصفقة #{trade_id}**
    • المبلغ المستحق: {trade['amount'] * trade['exchange_rate']:,.2f}
    • وسيلة الدفع: {db.get_offer(trade['offer_id'])['payment_method']}

    📝 **أرسل معلومات الدفع التي سيستخدمها المشتري:**
    •رقم محفظة شام كاش في حال كانت وسيلة الدفع
    • رقم الموبايل لحسابات سيرياتل كاش و MTN كاش


    ⚡ **سيتم إرسال هذه المعلومات للمشتري مباشرة**
    """

        try:
            await context.bot.send_message(
                trade['seller_id'],
                payment_request,
                parse_mode='Markdown'
            )
            await query.answer("✅ تم إرسال طلب التفاصيل للبائع")
        except Exception as e:
            logger.error(f"❌ فشل في إرسال طلب التفاصيل: {e}")
            await query.answer("❌ فشل في إرسال الطلب", show_alert=True)
    async def handle_telegram_api_error(self, error: Exception, user_id: int = None):
        """معالجة أخطاء Telegram API"""
        logger.error(f"📱 خطأ في Telegram API: {error}")

        # التحقق من نوع الخطأ
        error_msg = str(error).lower()

        if "blocked" in error_msg or "bot was blocked" in error_msg:
            logger.warning(f"🔒 المستخدم {user_id} حظر البوت")
            # يمكن إضافة منطق للتعامل مع المستخدمين الحاجزين

        elif "chat not found" in error_msg:
            logger.warning(f"❌ الدردشة غير موجودة للمستخدم {user_id}")

        elif "forbidden" in error_msg:
            logger.warning(f"🚫 محظور الوصول للمستخدم {user_id}")

    async def backup_database(self):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            import shutil
            import os
            from datetime import datetime

            if not os.path.exists('backups'):
                os.makedirs('backups')

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backups/bot_backup_{timestamp}.db"

            shutil.copy2('bot_database.db', backup_file)

            # حذف النسخ القديمة (احتفظ بآخر 7 نسخ)
            backups = sorted([f for f in os.listdir('backups') if f.startswith('bot_backup_')])
            if len(backups) > 7:
                for old_backup in backups[:-7]:
                    os.remove(f"backups/{old_backup}")

            logger.info(f"💾 تم إنشاء نسخة احتياطية: {backup_file}")
            return True

        except Exception as e:
            logger.error(f"❌ فشل في إنشاء نسخة احتياطية: {e}")
            return False

    async def recover_failed_trades(self):
        """استعادة الصفقات الفاشلة بعد إعادة التشغيل"""
        try:
            logger.info("🔄 محاولة استعادة الصفقات الفاشلة...")

            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT id, status, buyer_id, seller_id, offer_id
                FROM trades
                WHERE status IN (?, ?, ?, ?)
            ''', (
                Config.STATUS_WAITING_PROOF,
                Config.STATUS_WAITING_PAYMENT,
                Config.STATUS_CONFIRMED,
                Config.STATUS_WAITING_USDT_SEND
            ))

            active_trades = cursor.fetchall()
            recovered_count = 0

            for trade_id, status, buyer_id, seller_id, offer_id in active_trades:
                try:
                    # إرسال إشعار استعادة للمستخدمين
                    recovery_text = f"""
    🔄 **استعادة الصفقة بعد إعادة التشغيل**

    📋 **الصفقة #{trade_id}**
    • الحالة: {self.get_status_text(status)}
    • تم استعادة تقدم الصفقة

    ⚡ يمكنك متابعة الصفقة من حيث توقفت.
                    """

                    for user_id in [buyer_id, seller_id]:
                        try:
                            await self.application.bot.send_message(
                                user_id,
                                recovery_text,
                                parse_mode='Markdown'
                            )
                            recovered_count += 0.5  # لكل مستخدم
                        except Exception as e:
                            logger.error(f"فشل إرسال إشعار استعادة للمستخدم {user_id}: {e}")

                except Exception as e:
                    logger.error(f"❌ خطأ في استعادة الصفقة #{trade_id}: {e}")
                    continue

            logger.info(f"✅ تم استعادة {int(recovered_count)} صفقة نشطة")
            return int(recovered_count)

        except Exception as e:
            logger.error(f"❌ خطأ في استعادة الصفقات: {e}")
            return 0
    async def show_offers_management(self, query, context: ContextTypes.DEFAULT_TYPE):
        """عرض إدارة العروض للمشرف"""
        # الحصول على العروض النشطة
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT id, user_id, offer_type, amount, exchange_rate, payment_method, created_at
            FROM offers
            WHERE status = "active"
            ORDER BY created_at DESC
        ''')
        active_offers = cursor.fetchall()

        if not active_offers:
            text = "📋 **إدارة العروض**\n\nلا توجد عروض نشطة حالياً."
            keyboard = [[InlineKeyboardButton("↩️ رجوع", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return

        text = "📋 **إدارة العروض النشطة**\n\n"

        keyboard = []
        for offer in active_offers[:20]:  # عرض أول 20 عروض فقط
            offer_id, user_id, offer_type, amount, exchange_rate, payment_method, created_at = offer
            type_text = "🟢 بيع" if offer_type == 'sell' else "🔵 شراء"

            text += f"#{offer_id} - {type_text}\n"
            text += f"الكمية: {amount:,.2f} USDT\n"
            text += f"السعر: {exchange_rate:,.3f}\n"
            text += f"الدفع: {payment_method}\n"
            text += "─" * 20 + "\n"

            # زر إغلاق لكل عرض
            keyboard.append([InlineKeyboardButton(
                f"❌ إغلاق العرض #{offer_id}",
                callback_data=f"admin_close_offer_{offer_id}"
            )])

        keyboard.append([InlineKeyboardButton("↩️ رجوع", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def admin_close_offer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, offer_id: int):
        """إغلاق عرض بواسطة المشرف"""
        query = update.callback_query
        await query.answer()

        # التحقق من أن المستخدم هو المشرف
        if not await self.is_admin(query.from_user.id):
            await query.answer("❌ فقط المشرف يمكنه إغلاق العروض", show_alert=True)
            return

        try:
            # الحصول على بيانات العرض
            offer = db.get_offer(offer_id)
            if not offer:
                await query.answer("❌ العرض غير موجود", show_alert=True)
                return

            # تحديث حالة العرض إلى منتهي
            cursor = db.conn.cursor()
            cursor.execute('UPDATE offers SET status = ? WHERE id = ?', ('expired', offer_id))
            db.conn.commit()

            # تحديث العرض في القناة
            await self.channel_manager.mark_offer_expired(offer_id)

            # إشعار مالك العرض
            try:
                await context.bot.send_message(
                    offer['user_id'],
                    f"❌ **تم إغلاق عرضك بواسطة المشرف**\n\n"
                    f"📋 **العرض #{offer_id}**\n"
                    f"• الكمية: {offer['amount']:,.2f} USDT\n"
                    f"• السعر: {offer['exchange_rate']:,.3f}\n"
                    f"• السبب: إغلاق إداري\n\n"
                    f"للمزيد من المعلومات، تواصل مع الدعم.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"فشل في إشعار مالك العرض: {e}")

            await query.answer(f"✅ تم إغلاق العرض #{offer_id}", show_alert=True)

            # تحديث القائمة
            await self.show_offers_management(query, context)

        except Exception as e:
            logger.error(f"❌ خطأ في إغلاق العرض: {e}")
            await query.answer("❌ حدث خطأ في إغلاق العرض", show_alert=True)

    async def emergency_shutdown(self, reason: str):
        """إغلاق طارئ للنظام"""
        logger.critical(f"🚨 إغلاق طارئ للنظام: {reason}")

        # تحديث حالة البوت
        db.update_setting('bot_active', 'false')

        # إشعار جميع المستخدمين النشطين
        try:
            cursor = db.conn.cursor()
            cursor.execute('SELECT DISTINCT user_id FROM trades WHERE status NOT IN (?, ?)',
                        (Config.STATUS_COMPLETED, Config.STATUS_CANCELLED))

            active_users = cursor.fetchall()

            shutdown_msg = f"""
    🚨 **إغلاق طارئ للنظام**

    📢 **إشعار مهم:**
    {reason}

    ⏸️ تم تعليق جميع الصفقات النشطة مؤقتاً.
    🔄 سنقوم باستئناف العمل قريباً.

    نعتذر للإزعاج ونشكركم على صبركم.
            """

            for (user_id,) in active_users:
                try:
                    await self.application.bot.send_message(user_id, shutdown_msg, parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"فشل إرسال إشعار إغلاق للمستخدم {user_id}: {e}")

        except Exception as e:
            logger.error(f"❌ خطأ في إرسال إشعارات الإغلاق: {e}")

        # إشعار المشرف
        if Config.ADMIN_ID:
            await self.application.bot.send_message(
                Config.ADMIN_ID,
                f"🚨 **تم تنفيذ الإغلاق الطارئ**\n\nالسبب: {reason}",
                parse_mode='Markdown'
            )
    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة مشاركة جهة الاتصال مع زر قائمة"""
        user_id = update.effective_user.id
        contact = update.message.contact

        logger.info(f"📞 تم استلام جهة اتصال من المستخدم {user_id}: {contact.phone_number}")

        # حفظ رقم الهاتف في قاعدة البيانات
        success = db.update_user_phone(user_id, contact.phone_number)

        if success:
            logger.info(f"✅ تم حفظ جهة الاتصال للمستخدم {user_id} بنجاح: {contact.phone_number}")
        else:
            logger.error(f"❌ فشل في حفظ جهة الاتصال للمستخدم {user_id}")

        # إزالة لوحة المفاتيح الخاصة بمشاركة الاتصال
        remove_keyboard = ReplyKeyboardRemove()

        # إنشاء زر القائمة الأزرق (Inline Keyboard)
        menu_keyboard = [
            [InlineKeyboardButton("📋 قائمة", callback_data="show_main_menu")]
        ]
        menu_reply_markup = InlineKeyboardMarkup(menu_keyboard)

        await update.message.reply_text(
            "✅ **تم حفظ جهة الاتصال بنجاح**\n\n"
            "📱 **رقم هاتفك:** {}\n\n"
            "يمكنك الآن استخدام زر 📋 **قائمة** لبدء الصفقات.".format(contact.phone_number),
            reply_markup=remove_keyboard,
            parse_mode='Markdown'
        )

        # إرسال رسالة منفصلة مع زر القائمة
        await update.message.reply_text(
            "🔽 **اختر من القائمة:**",
            reply_markup=menu_reply_markup,
            parse_mode='Markdown'
        )

        # متابعة الصفقة إذا كان هناك عرض معلق
        if 'current_offer' in context.user_data:
            offer_id = context.user_data['current_offer']['offer_id']
            action = context.user_data['current_offer']['action']

            logger.info(f"🔄 متابعة الصفقة المعلقة - العرض: {offer_id}, الإجراء: {action}")

            # الحصول على بيانات العرض
            offer = db.get_offer(offer_id)
            if not offer:
                await update.message.reply_text(
                    "❌ **عذراً، هذا العرض لم يعد متاحاً**\n\n"
                    "استخدم زر 📋 قائمة لإنشاء عرض جديد",
                    reply_markup=menu_reply_markup,
                    parse_mode='Markdown'
                )
                del context.user_data['current_offer']
                return

            if offer['status'] != 'active':
                await update.message.reply_text(
                    "❌ **عذراً، هذا العرض غير متاح حالياً**\n\n"
                    "استخدم زر 📋 قائمة لإنشاء عرض جديد",
                    reply_markup=menu_reply_markup,
                    parse_mode='Markdown'
                )
                del context.user_data['current_offer']
                return

            # عرض تفاصيل الصفقة
            commission = db.calculate_commission(offer['amount'])

            welcome_text = f"""
    🎉 **مرحباً بك في عملية {'الشراء' if action == 'buy' else 'البيع'}**

    📊 **تفاصيل العرض:**
    • الكمية: {offer['amount']:,.1f} USDT
    • السعر: {offer['exchange_rate']:,.2f}
    • وسيلة الدفع: {offer['payment_method']}
    • عمولة الوسيط: ${commission:.2f}
    • فئة العميل: {offer.get('tier', 'silver')}

    ⚡ **سيتم إتمام الصفقة عبر الوسيط لضمان الأمان**

    للمتابعة، اضغط على الزر أدناه:
            """

            keyboard = [
                [InlineKeyboardButton("✅ متابعة الصفقة", callback_data=f"accept_{offer_id}")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def validate_trade_integrity(self, trade_id: int) -> bool:
        """التحقق من سلامة بيانات الصفقة"""
        try:
            trade = db.get_trade(trade_id)
            if not trade:
                return False

            # التحقق من وجود العرض
            offer = db.get_offer(trade['offer_id'])
            if not offer:
                logger.error(f"❌ الصفقة #{trade_id} مرتبطة بعرض غير موجود")
                return False

            # التحقق من وجود المستخدمين
            buyer = db.get_user(trade['buyer_id'])
            seller = db.get_user(trade['seller_id'])

            if not buyer or not seller:
                logger.error(f"❌ الصفقة #{trade_id} تحتوي على مستخدمين غير موجودين")
                return False

            # التحقق من تناسق البيانات
            if trade['amount'] <= 0 or trade['exchange_rate'] <= 0:
                logger.error(f"❌ الصفقة #{trade_id} تحتوي على بيانات غير صالحة")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من سلامة الصفقة #{trade_id}: {e}")
            return False

    async def cleanup_orphaned_data(self):
        """تنظيف البيانات الميتة والمتشعبة"""
        try:
            logger.info("🧹 تنظيف البيانات الميتة...")

            cursor = db.conn.cursor()

            # تنظيف العروض المرتبطة بمستخدمين غير موجودين
            cursor.execute('''
                DELETE FROM offers
                WHERE user_id NOT IN (SELECT user_id FROM users)
            ''')
            orphaned_offers = cursor.rowcount

            # تنظيف الصفقات المرتبطة بعروض غير موجودة
            cursor.execute('''
                DELETE FROM trades
                WHERE offer_id NOT IN (SELECT id FROM offers)
            ''')
            orphaned_trades = cursor.rowcount

            db.conn.commit()

            logger.info(f"✅ تم تنظيف {orphaned_offers} عرض و {orphaned_trades} صفقة ميتة")
            return orphaned_offers + orphaned_trades

        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف البيانات الميتة: {e}")
            return 0
        # تنظيف بيانات العرض المؤقتة إذا كانت موجودة (اختياري - يمكن الاحتفاظ بها)
        # if 'current_offer' in context.user_data:
        #     logger.info(f"💾 تم الاحتفاظ ببيانات العرض للمستخدم {user_id} للمتابعة اللاحقة")
    async def check_bot_working_hours(self, user_id: int) -> bool:
        """التحقق من وقت عمل البوت"""
        if await self.is_admin(user_id):
            return True

        if not db.is_bot_working_hours():
            current_time = datetime.now().strftime("%H:%M")
            logger.info(f"⏰ محاولة استخدام خارج وقت العمل من user: {user_id} - الوقت: {current_time}")
            return False
        return True

    async def check_channel_membership(self, user_id: int) -> bool:
        """التحقق من انضمام المستخدم للقناة"""
        try:
            if not Config.CHANNEL_ID:
                return True

            member = await self.application.bot.get_chat_member(Config.CHANNEL_ID, user_id)
            return member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.error(f"Error checking channel membership: {e}")
            return False

    async def check_user_contact(self, user_id: int) -> bool:
        """التحقق من وجود جهة اتصال للمستخدم"""
        user_data = db.get_user(user_id)
        if user_data and user_data.get('phone'):
            logger.info(f"✅ المستخدم {user_id} لديه جهة اتصال مسجلة: {user_data.get('phone')}")
            return True
        else:
            logger.info(f"❌ المستخدم {user_id} لا يملك جهة اتصال مسجلة")
            return False

    async def is_admin(self, user_id: int) -> bool:
        """التحقق من إذا كان المستخدم مشرف"""
        return user_id == Config.ADMIN_ID

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db.add_user(user.id, user.username, user.first_name, user.last_name)

        # التحقق من وقت عمل البوت
        if not await self.check_bot_working_hours(user.id):
            await update.message.reply_text(
                "⏰ **البوت خارج وقت العمل**\n\n"
                "⏳ وقت العمل: من 8 صباحاً حتى 12 منتصف الليل\n"
                "🔄 العروض الجديدة متاحة من 8 صباحاً\n"

            )
            return

        # التحقق من حالة البوت
        if not db.is_bot_active() and not await self.is_admin(user.id):
            await update.message.reply_text("⏸️ البوت معطل حالياً. يرجى المحاولة لاحقاً.")
            return

        # التحقق من انضمام المستخدم للقناة
        is_member = await self.check_channel_membership(user.id)

        if not is_member and Config.CHANNEL_ID:
            welcome_text = """
🏦 **مرحباً بك في نظام وساطة USDT**

📢 **للاستفادة من خدمات البوت، يرجى الانضمام للقناة أولاً:**
            """

            channel_username = Config.CHANNEL_ID.replace('@', '')
            keyboard = [
                [InlineKeyboardButton("📢 الانضمام للقناة", url=f"https://t.me/{channel_username}")],
                [InlineKeyboardButton("✅ تم الانضمام", callback_data="check_membership")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
            return

        await self.main_menu(update, context)

    async def require_channel_membership(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """طلب الانضمام للقناة إذا لم يكن المستخدم منضم"""
        if not Config.CHANNEL_ID:
            return True

        user_id = update.effective_user.id
        is_member = await self.check_channel_membership(user_id)

        if not is_member:
            channel_username = Config.CHANNEL_ID.replace('@', '')
            keyboard = [
                [InlineKeyboardButton("📢 الانضمام للقناة", url=f"https://t.me/{channel_username}")],
                [InlineKeyboardButton("✅ تم الانضمام", callback_data="check_membership")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(
                    "❌ **يجب الانضمام للقناة أولاً**\n\nانضم للقناة ثم اضغط على 'تم الانضمام'",
                    reply_markup=reply_markup
                )
            elif hasattr(update, 'message') and update.message:
                await update.message.reply_text(
                    "❌ **يجب الانضمام للقناة أولاً**\n\nانضم للقناة ثم اضغط على 'تم الانضمام'",
                    reply_markup=reply_markup
                )
            return False
        return True

    async def debug_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دالة تصحيح لإظهار حالة الصفقات"""
        user_id = update.effective_user.id
        trades = db.get_user_trades(user_id)

        debug_text = f"🔍 **تصحيح الصفقات للمستخدم {user_id}**\n\n"

        if not trades:
            debug_text += "❌ لا توجد صفقات لهذا المستخدم"
        else:
            for i, trade_data in enumerate(trades):
                trade_id, offer_id, buyer_id, seller_id, broker_id, amount, exchange_rate, commission, transfer_fee, buyer_wallet, payment_proof, status, created_at, updated_at, buyer_name, seller_name = trade_data

                debug_text += f"**الصفقة #{trade_id}:**\n"
                debug_text += f"• الحالة: {status}\n"
                debug_text += f"• المشتري: {buyer_id} ({buyer_name})\n"
                debug_text += f"• البائع: {seller_id} ({seller_name})\n"
                debug_text += f"• يحتاج مستندات: {'نعم' if status in [Config.STATUS_CONFIRMED, Config.STATUS_WAITING_PAYMENT] else 'لا'}\n"
                debug_text += "─" * 20 + "\n"

        await update.message.reply_text(debug_text, parse_mode='Markdown')

    async def handle_channel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """معالجة النقر من القناة"""
        query = update.callback_query
        await query.answer()

        # التحقق من حالة البوت
        if not db.is_bot_active():
            await query.answer("⏸️ البوت معطل حالياً. يرجى المحاولة لاحقاً.", show_alert=True)
            return

        # التحقق من انضمام المستخدم للقناة
        if not await self.require_channel_membership(update, context):
            return

        # callback_data format: "buy_123" or "sell_123"
        action, offer_id_str = callback_data.split('_')
        offer_id = int(offer_id_str)

        offer = db.get_offer(offer_id)
        if not offer:
            await query.answer("❌ هذا العرض لم يعد متاحاً", show_alert=True)
            return

        # التحقق من أن العرض لا يزال نشطاً
        if offer['status'] != 'active':
            await query.answer("❌ هذا العرض غير متاح حالياً", show_alert=True)
            return

        user_id = query.from_user.id

        # التحقق من وجود جهة اتصال أولاً
        has_contact = await self.check_user_contact(user_id)

        # حفظ بيانات العرض للمستخدم بشكل دائم في context
        context.user_data['current_offer'] = {
            'offer_id': offer_id,
            'action': action,
            'user_id': user_id
        }

        # إذا كان المستخدم لديه جهة اتصال، نعرض زر المتابعة مباشرة
        if has_contact:
            # حساب العمولة
            commission = db.calculate_commission(offer['amount'])

            welcome_text = f"""
🎉 **مرحباً بك في عملية {'الشراء' if action == 'buy' else 'البيع'}**

📊 **تفاصيل العرض:**
• الكمية: {offer['amount']:,.2f} USDT
• السعر: {offer['exchange_rate']:,.2f}
• وسيلة الدفع: {offer['payment_method']}
• عمولة الوسيط: ${commission:.2f}

⚡ **سيتم إتمام الصفقة عبر الوسيط لضمان الأمان**

للمتابعة، اضغط على الزر أدناه:
            """

            keyboard = [
                [InlineKeyboardButton("✅ متابعة الصفقة", callback_data=f"accept_{offer_id}")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                await query.answer("✅ تم إرسال التفاصيل للبوت، يرجى متابعته")
            except Exception as e:
                await query.answer("❌ يرجى البدء بمحادثة مع البوت أولاً", show_alert=True)

        else:
            # إذا لم يكن لديه جهة اتصال، نطلبها أولاً
            contact_text = f"""
📞 **مشاركة جهة الاتصال مطلوبة**

لبدء الصفقة، يرجى مشاركة جهة اتصالك أولاً:

📊 **تفاصيل العرض:**
• الكمية: {offer['amount']:,.2f} USDT
• السعر: {offer['exchange_rate']:,.2f}
• وسيلة الدفع: {offer['payment_method']}

بعد مشاركة جهة الاتصال، يمكنك متابعة الصفقة.
            """

            contact_keyboard = [[KeyboardButton("📞 مشاركة جهة الاتصال", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(contact_keyboard, resize_keyboard=True, one_time_keyboard=True)

            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=contact_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                await query.answer("📞 يرجى مشاركة جهة الاتصال في البوت")
            except Exception as e:
                await query.answer("❌ يرجى البدء بمحادثة مع البوت أولاً", show_alert=True)

    async def accept_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE, offer_id: int):
        """بدء الصفقة - النسخة المحدثة الكاملة"""
        query = update.callback_query
        await query.answer()

        # التحقق من حالة البوت
        if not db.is_bot_active():
            await query.answer("⏸️ البوت معطل حالياً. يرجى المحاولة لاحقاً.", show_alert=True)
            return

        # التحقق من انضمام المستخدم للقناة
        if not await self.require_channel_membership(update, context):
            return

        offer = db.get_offer(offer_id)
        if not offer:
            await query.answer("❌ هذا العرض لم يعد متاحاً", show_alert=True)
            return

        user_id = query.from_user.id

        # التحقق من مشاركة جهة الاتصال - مع تحسين التخزين المؤقت
        user_data = db.get_user(user_id)

        # إذا لم يكن هناك بيانات مستخدم أو لم يكن هناك رقم هاتف
        if not user_data:
            # إنشاء بيانات المستخدم إذا لم تكن موجودة
            db.add_user(user_id, query.from_user.username, query.from_user.first_name, query.from_user.last_name)
            user_data = db.get_user(user_id)

        logger.info(f"📞 التحقق من جهة اتصال المستخدم {user_id}: {user_data.get('phone')}")

        if not user_data or not user_data.get('phone'):
            # طلب مشاركة جهة الاتصال
            keyboard = [[InlineKeyboardButton("📞 مشاركة جهة الاتصال", callback_data=f"share_contact_{offer_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(
                "📞 **مشاركة جهة الاتصال مطلوبة**\n\n"
                "يجب مشاركة جهة اتصالك للمتابعة في الصفقة:",
                reply_markup=reply_markup
            )
            return

        # إذا وصلنا إلى هنا، значит المستخدم لديه رقم هاتف مسجل
        # تحديد الأدوار
        if offer['offer_type'] == Config.OFFER_SELL:  # إذا كان عرض بيع
            buyer_id = query.from_user.id
            seller_id = offer['user_id']
        else:  # إذا كان عرض شراء
            buyer_id = offer['user_id']
            seller_id = query.from_user.id

        # إنشاء الصفقة
        trade_id = db.create_trade(offer_id, buyer_id, seller_id, offer['amount'], offer['exchange_rate'])

        # تحديث حالة العرض في القناة
        await self.channel_manager.update_offer_status(offer_id, 'in_trade')

        # حفظ معرف الصفقة في بيانات المستخدم
        context.user_data['current_trade_id'] = trade_id

        # حساب العمولة
        commission = db.calculate_commission(offer['amount'])
        transfer_fee = db.get_transfer_fee()
        total_amount = offer['amount'] + commission + (transfer_fee * 2)

        # إرسال إشعارات للطرفين
        trade_info = f"""
    🎉 **تم بدء صفقة جديدة!**

    📊 **تفاصيل الصفقة:**
    • رقم الصفقة: #{trade_id}
    • الكمية: {offer['amount']:,.2f} USDT
    • السعر: {offer['exchange_rate']:,.2f}
    • وسيلة الدفع: {offer['payment_method']}
    • عمولة الوسيط: ${commission:.2f}

    ⚡ **تعليمات الإتمام الجديدة:**
    1. سيرسل البائع USDT للوسيط
    2. سيرفع البائع مستند إثبات الإرسال
    3. سيؤكد الوسيط استلام USDT
    4. سيدفع المشتري للبائع
    5. سيرفع المشتري مستند الدفع
    6. سيؤكد البائع استلام الأموال
    7. سيرسل الوسيط USDT للمشتري
        """

        # إرسال للطرفين
        for participant_id in [buyer_id, seller_id]:
            try:
                await context.bot.send_message(participant_id, trade_info, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to send message to {participant_id}: {e}")

        # إرسال تعليمات خاصة للبائع - محدثة
        seller_wallet_info = f"""
    💰 **أنت البائع في الصفقة #{trade_id}**

    📤 **المرحلة 1: إرسال USDT للوسيط**
    • العنوان: `{Config.BROKER_WALLET_ADDRESS}`
    • الشبكة: {Config.BLOCKCHAIN_NETWORK}
    • المبلغ الإجمالي: {total_amount:,.2f} USDT

    💡 **تفاصيل المبلغ الإجمالي:**
    - مبلغ العرض: {offer['amount']:,.2f} USDT
    - عمولة الوسيط: {commission:.2f} USDT
    - مصاريف التحويل: {transfer_fee * 2:.2f} USDT

    ⚠️ **تنويه مهم:**
    • يجب تحويل المبلغ الإجمالي كاملاً
    • تأكد من صحة العنوان والشبكة
    • احفظ إثبات التحويل (screenshot)

    ⚡ **بعد الإرسال، اضغط على تأكيد الإرسال:**
    """

        seller_keyboard = [
            [InlineKeyboardButton("✅ تأكيد إرسال USDT", callback_data=f"confirm_usdt_sent_{trade_id}")],
            [InlineKeyboardButton("❌ إلغاء الصفقة", callback_data=f"cancel_trade_{trade_id}")]
        ]
        seller_reply_markup = InlineKeyboardMarkup(seller_keyboard)

        try:
            await context.bot.send_message(
                seller_id,
                seller_wallet_info,
                reply_markup=seller_reply_markup,
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم إرسال تعليمات البائع للصفقة #{trade_id}")
        except Exception as e:
            logger.error(f"❌ فشل إرسال تعليمات البائع: {e}")

        # إرسال تعليمات أولية للمشتري
        buyer_initial_info = f"""
    🛒 **أنت المشتري في الصفقة #{trade_id}**

    📊 **تفاصيل الطلب:**
    • الكمية: {offer['amount']:,.2f} USDT
    • السعر: {offer['exchange_rate']:,.2f}
    • المبلغ المستحق: {offer['amount'] * offer['exchange_rate']:,.2f}
    • وسيلة الدفع: {offer['payment_method']}

    ⏳ **جاري انتظار البائع:**
    1. إرسال USDT للوسيط
    2. رفع مستند الإثبات
    3. تأكيد الوسيط للاستلام

    ⚡ **ستتلقى تعليمات الدفع بعد تأكيد استلام USDT من الوسيط**
    """

        try:
            await context.bot.send_message(
                buyer_id,
                buyer_initial_info,
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم إرسال تعليمات المشتري للصفقة #{trade_id}")
        except Exception as e:
            logger.error(f"❌ فشل إرسال تعليمات المشتري: {e}")

        # إشعار الوسيط
        if Config.ADMIN_ID:
            broker_text = f"""
    🔔 **صفقة جديدة تحتاج لمتابعة**

    📋 **التفاصيل:**
    • رقم الصفقة: #{trade_id}
    • البائع: {seller_id} ({db.get_user(seller_id)['first_name'] if db.get_user(seller_id) else 'غير معروف'})
    • المشتري: {buyer_id} ({db.get_user(buyer_id)['first_name'] if db.get_user(buyer_id) else 'غير معروف'})
    • الكمية: {offer['amount']:,.2f} USDT
    • العمولة: ${commission:.2f}

    ⚡ **بانتظار إرسال البائع لـ USDT ومستند الإثبات**
            """
            await context.bot.send_message(Config.ADMIN_ID, broker_text, parse_mode='Markdown')
            logger.info(f"✅ تم إرسال إشعار للوسيط للصفقة #{trade_id}")

        await query.message.edit_text(
            "✅ **تم بدء الصفقة بنجاح!**\n\n"
            "📋 **رقم الصفقة: #{}**\n\n"
            "ستتلقى تعليمات الإتمام قريباً.".format(trade_id),
            parse_mode='Markdown'
        )

        logger.info(f"🎉 اكتملت بدء الصفقة #{trade_id} بنجاح")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        data = query.data
        logger.info(f"🖱️ تم استقبال callback: {data} من user: {query.from_user.id}")

        try:
            parts = data.split("_")
            trade_id = None
            offer_id = None

            # إذا كان آخر جزء رقم، نعتبره ID
            if parts[-1].isdigit():
                try:
                    trade_id = int(parts[-1])
                    offer_id = trade_id
                except ValueError:
                    trade_id = None
                    offer_id = None

            if data == "show_main_menu":
                await self.show_main_menu_from_button(update, context)
            elif data == "create_offer":
                await self.create_offer_flow(update, context)

            elif data.startswith("offer_type_"):
                await self.handle_offer_type(update, context)

            elif data.startswith("payment_"):
                await self.handle_payment_method(update, context)

            elif data.startswith("buy_") or data.startswith("sell_"):
                await self.handle_channel_callback(update, context, data)

            elif data.startswith("accept_") and offer_id is not None:
                await self.accept_trade(update, context, offer_id)
            elif data == "back_to_main_menu":
                await self.back_to_main_menu_callback(update, context)
            # إضافة هذه المعالجات في دالة handle_callback
            elif data.startswith("upload_broker_proof_") and trade_id is not None:
                await self.handle_broker_proof_upload(update, context, trade_id)

            elif data.startswith("upload_payment_proof_") and trade_id is not None:
                await self.handle_payment_proof_upload(update, context, trade_id)

            elif data.startswith("confirm_without_proof_") and trade_id is not None:
                await self.confirm_without_broker_proof(update, context, trade_id)

            elif data.startswith("confirm_without_payment_proof_") and trade_id is not None:
                await self.confirm_without_payment_proof(update, context, trade_id)
            elif data.startswith("send_payment_details_") and trade_id is not None:
                await self.send_payment_details_to_buyer(update, context, trade_id)

            elif data.startswith("request_payment_details_") and trade_id is not None:
                await self.request_payment_details(update, context, trade_id)
            elif data == "confirm_offer":
                logger.info("✅ تم التعرف على confirm_offer، جاري استدعاء complete_offer_creation")
                await self.complete_offer_creation(update, context)
            elif data == "admin_offers":
                await self.show_offers_management(query, context)
            elif data.startswith("admin_close_offer_") and trade_id is not None:
                await self.admin_close_offer(update, context, trade_id)

            elif data.startswith("share_contact_") and offer_id is not None:
                await self.request_contact(update, context, offer_id)

            elif data.startswith("confirm_usdt_sent_") and trade_id is not None:
                await self.confirm_usdt_sent(update, context, trade_id)

            elif data.startswith("request_proof_") and trade_id is not None:
                await self.request_payment_proof(update, context, trade_id)

            elif data.startswith("broker_confirm_usdt_") and trade_id is not None:
                await self.broker_confirm_usdt(update, context, trade_id)

            elif data.startswith("upload_proof_") and trade_id is not None:
                await self.request_proof_upload(update, context, trade_id)

            elif data.startswith("broker_confirm_proof_") and trade_id is not None:
                await self.broker_confirm_proof(update, context, trade_id)

            elif data.startswith("broker_reject_proof_") and trade_id is not None:
                await self.broker_reject_proof(update, context, trade_id)

            elif data.startswith("confirm_payment_") and trade_id is not None:
                await self.confirm_payment_received(update, context, trade_id)

            elif data.startswith("confirm_usdt_to_buyer_") and trade_id is not None:
                await self.confirm_usdt_to_buyer(update, context, trade_id)

            elif data.startswith("confirm_usdt_received_") and trade_id is not None:
                await self.confirm_usdt_received(update, context, trade_id)

            elif data.startswith("cancel_trade_") and trade_id is not None:
                await self.cancel_trade(update, context, trade_id)

            elif data.startswith("admin_cancel_trade_") and trade_id is not None:
                await self.admin_cancel_trade(update, context, trade_id)

            elif data == "check_membership":
                await self.check_membership_callback(update, context)

            elif data == "my_offers":
                await self.my_offers_callback(update, context)

            elif data == "my_trades":
                await self.my_trades_callback(update, context)

            elif data.startswith("reject_payment_") and trade_id is not None:
                await self.reject_payment(update, context, trade_id)

            elif data == "support":
                await self.support(update, context)

            elif data in ["cancel", "cancel_offer"]:
                await self.cancel_operation(update, context)

            elif data.startswith("request_payment_details_") and trade_id is not None:
                await self.request_payment_details(update, context, trade_id)

            elif data.startswith("send_payment_details_") and trade_id is not None:
                await self.send_payment_details_to_buyer(update, context, trade_id)

            elif data.startswith("confirm_payment_details_") and trade_id is not None:
                logger.info(f"🎯 معالجة confirm_payment_details_ - البيانات: '{data}'")
                await self.confirm_payment_details_received(update, context, trade_id)

            # معالجات لوحة التحكم
            elif data == "admin_panel":
                await self.admin_panel_callback(update, context)
            elif data == "admin_commission":
                await self.show_commission_settings(query, context)
            elif data == "admin_transfer_fee":
                await self.show_transfer_fee_settings(query, context)
            elif data == "admin_messages":
                await self.show_message_settings(query, context)
            elif data == "admin_system":
                await self.show_system_settings(query, context)

            elif data == "admin_stats":
                await self.show_admin_stats(query, context)
            elif data == "recent_trades":
                await ChannelManager.show_recent_trades_from_query(query, update)
            elif data == "set_commission_prompt":
                await self.set_commission_value(update, context)
            elif data == "set_transfer_fee_prompt":
                await self.set_transfer_fee_prompt(update, context)
            elif data.startswith("edit_message_"):
                message_key = data.replace("edit_message_", "")
                await self.edit_message_prompt(query, context, message_key)
            elif data == "toggle_bot_status":
                await self.toggle_bot_status(query, context)
            elif data == "commission_stats":
                await self.show_commission_stats(query, context)
            elif data == "expire_offers":
                await self.expire_all_offers_manual(update, context)
            elif data == "edit_commission_settings":
                await self.edit_commission_settings(update, context)
            else:
                logger.warning(f"⚠️ callback غير معروف: {data}")
                await query.answer("❌ الأمر غير معروف", show_alert=True)

        except Exception as e:
            logger.error(f"❌ خطأ في معالجة callback {data}: {e}")
            await query.answer("❌ حدث خطأ في المعالجة", show_alert=True)
    async def show_main_menu_from_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض القائمة الرئيسية من زر القائمة"""
        query = update.callback_query
        await query.answer()

        # إنشاء قائمة مع زر البدء
        menu_keyboard = [
            [InlineKeyboardButton("🚀 البدء", callback_data="create_offer")],
            [InlineKeyboardButton("📋 عروضي", callback_data="my_offers")],
            [InlineKeyboardButton("🔄 صفقاتي", callback_data="my_trades")],
            [InlineKeyboardButton("ℹ️ المساعدة", callback_data="support")]
        ]

        # إضافة زر المشرف إذا كان المستخدم مشرف
        if await self.is_admin(query.from_user.id):
            menu_keyboard.append([InlineKeyboardButton("🛠️ لوحة التحكم", callback_data="admin_panel_callback")])

        reply_markup = InlineKeyboardMarkup(menu_keyboard)

        menu_text = """
    📋 **القائمة الرئيسية**

    اختر من الخيارات:
    • 🚀 البدء: إنشاء عرض جديد
    • 📋 عروضي: عرض عروضك السابقة
    • 🔄 صفقاتي: متابعة صفقاتك
    • ℹ️ المساعدة: الحصول على الدعم
        """

        await query.message.edit_text(
            menu_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    async def confirm_usdt_sent(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """تأكيد إرسال USDT من البائع للوسيط"""
        query = update.callback_query
        await query.answer()

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # التحقق من أن المستخدم هو البائع
        if query.from_user.id != trade['seller_id']:
            await query.answer("❌ فقط البائع يمكنه تأكيد الإرسال", show_alert=True)
            return

        # تحديث حالة الصفقة
        db.update_trade_status(trade_id, Config.STATUS_USDT_SENT)

        # إشعار الوسيط بوجود مستند إرسال
        if Config.ADMIN_ID:
            broker_text = f"""
📤 **البائع أكد إرسال USDT للوسيط**

📋 **تفاصيل الصفقة:**
• رقم الصفقة: #{trade_id}
• البائع: {trade['seller_id']}
• المشتري: {trade['buyer_id']}
• الكمية: {trade['amount']:,.2f} USDT

💬 **يرجى طلب مستند الإرسال من البائع والتأكد من استلام USDT:**
            """

            keyboard = [
                [InlineKeyboardButton("📎 طلب مستند الإرسال", callback_data=f"request_proof_{trade_id}")],
                [InlineKeyboardButton("✅ تأكيد استلام USDT", callback_data=f"broker_confirm_usdt_{trade_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                Config.ADMIN_ID,
                broker_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        # إشعار المشتري
        try:
            await context.bot.send_message(
                trade['buyer_id'],
                f"✅ **تم إرسال USDT من البائع للوسيط**\n\n"
                f"الصفقة #{trade_id} في انتظار تأكيد الوسيط...",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify buyer: {e}")

        await query.message.edit_text(
            "✅ **تم تأكيد إرسال USDT للوسيط**\n\n"
            "بانتظار تأكيد الوسيط للاستلام...\n"
            "سيقوم الوسيط بالتواصل معك لطلب مستند الإرسال.",
            parse_mode='Markdown'
        )

    async def request_payment_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """طلب مستند الإرسال من البائع"""
        query = update.callback_query
        await query.answer()

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # إرسال طلب مستند الإرسال للبائع
        proof_request = f"""
📋 **مطلوب مستند إرسال USDT**

📊 **تفاصيل الصفقة #{trade_id}:**
• الكمية: {trade['amount']:,.2f} USDT
• الشبكة: {Config.BLOCKCHAIN_NETWORK}

📤 **يرجى إرسال صورة أو مستند إثبات الإرسال:**
• screenshot من محفظتك
• تأكيد التحويل transaction confirmation
• أي مستند يثبت إرسال USDT للوسيط

⚡ **سيتم متابعة الصفقة بعد التحقق من المستند**
        """

        try:
            await context.bot.send_message(
                trade['seller_id'],
                proof_request,
                parse_mode='Markdown'
            )
            await query.answer("✅ تم إرسال طلب المستند للبائع")
        except Exception as e:
            logger.error(f"Failed to send proof request: {e}")
            await query.answer("❌ فشل في إرسال الطلب", show_alert=True)

    async def broker_confirm_usdt(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """تأكيد الوسيط لاستلام USDT - النسخة المصححة الكاملة"""
        query = update.callback_query
        await query.answer()

        # التحقق من أن المستخدم هو المشرف
        if not await self.is_admin(query.from_user.id):
            await query.answer("❌ فقط المشرف يمكنه تأكيد الاستلام", show_alert=True)
            return

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # تحديث حالة الصفقة إلى انتظار تفاصيل الدفع
        db.update_trade_status(trade_id, Config.STATUS_WAITING_PAYMENT_DETAILS)

        # إشعار البائع لإرسال تفاصيل الدفع
        seller_id = trade['seller_id']
        seller_info = f"""
    💰 **يرجى إرسال تفاصيل حساب الدفع للمشتري**

    📋 **الصفقة #{trade_id}**
    • الكمية: {trade['amount']:,.2f} USDT
    • المبلغ المستحق: `{trade['amount'] * trade['exchange_rate']:,.2f}`
    • وسيلة الدفع: {db.get_offer(trade['offer_id'])['payment_method']}

    📝 **أرسل رقم الحساب أو معلومات الدفع التي سيستخدمها المشتري للدفع لك:**

    ⚡ **سيتم إرسال هذه المعلومات للمشتري ليقوم بالدفع**
    """

        # استخدام زر لطلب التفاصيل بدلاً من الانتظار التلقائي
        keyboard = [
            [InlineKeyboardButton("📤 إرسال تفاصيل الدفع", callback_data=f"send_payment_details_{trade_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_trade_{trade_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await context.bot.send_message(
                seller_id,
                seller_info,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم طلب تفاصيل الدفع من البائع للصفقة #{trade_id}")
        except Exception as e:
            logger.error(f"❌ فشل في إشعار البائع: {e}")
            await query.answer("❌ فشل في إرسال الطلب للبائع", show_alert=True)
            return

        # إشعار المشتري
        buyer_id = trade['buyer_id']
        try:
            await context.bot.send_message(
                buyer_id,
                f"✅ **تم تأكيد استلام USDT من الوسيط**\n\n"
                f"الصفقة #{trade_id} في انتظار إرسال البائع لتفاصيل الدفع...\n\n"
                f"⚡ **ستتلقى معلومات الدفع قريباً**",
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم إشعار المشتري للصفقة #{trade_id}")
        except Exception as e:
            logger.error(f"❌ فشل في إشعار المشتري: {e}")

        await query.message.edit_text(
            "✅ **تم تأكيد استلام USDT**\n\n"
            "تم طلب تفاصيل الدفع من البائع.",
            parse_mode='Markdown'
        )
    async def confirm_usdt_sent(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """تأكيد إرسال USDT من البائع للوسيط - النسخة المحدثة"""
        query = update.callback_query
        await query.answer()

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # التحقق من أن المستخدم هو البائع
        if query.from_user.id != trade['seller_id']:
            await query.answer("❌ فقط البائع يمكنه تأكيد الإرسال", show_alert=True)
            return

        # تحديث حالة الصفقة إلى انتظار المستند
        db.update_trade_status(trade_id, Config.STATUS_WAITING_PROOF)

        # طلب تحميل مستند الإرسال من البائع
        proof_request = f"""
    📤 **تم تأكيد إرسال USDT للوسيط**

    📋 **الصفقة #{trade_id}**
    • الكمية: {trade['amount']:,.2f} USDT
    • الشبكة: {Config.BLOCKCHAIN_NETWORK}
    • العنوان: `{Config.BROKER_WALLET_ADDRESS}`

    📎 **الآن يرجى إرسال مستند إثبات الإرسال:**
    • screenshot من محفظتك يظهر التحويل
    • تأكيد التحويل (transaction confirmation)
    • أي مستند يثبت إرسال USDT للوسيط

    ⚡ **يمكنك إرسال الصورة أو المستند مباشرة في هذه المحادثة**
        """

        try:
            await context.bot.send_message(
                trade['seller_id'],
                proof_request,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"فشل في إرسال طلب المستند للبائع: {e}")

        # إشعار الوسيط
        if Config.ADMIN_ID:
            broker_text = f"""
    🔔 **البائع أكد إرسال USDT للوسيط**

    📋 **تفاصيل الصفقة:**
    • رقم الصفقة: #{trade_id}
    • البائع: {trade['seller_id']}
    • المشتري: {trade['buyer_id']}
    • الكمية: {trade['amount']:,.2f} USDT

    📤 **بانتظار تحميل مستند الإرسال من البائع**
            """

            await context.bot.send_message(
                Config.ADMIN_ID,
                broker_text,
                parse_mode='Markdown'
            )

        # إشعار المشتري
        try:
            await context.bot.send_message(
                trade['buyer_id'],
                f"✅ **تم إرسال USDT من البائع للوسيط**\n\n"
                f"الصفقة #{trade_id} في انتظار تحميل مستند الإرسال...",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"فشل في إشعار المشتري: {e}")

        await query.message.edit_text(
            "✅ **تم تأكيد إرسال USDT للوسيط**\n\n"
            "📎 **يرجى الآن إرسال مستند إثبات الإرسال:**\n"
            "• screenshot من محفظتك\n"
            "• تأكيد التحويل\n"
            "• أي مستند يثبت الإرسال\n\n"
            "⚡ **أرسل الصورة أو المستند مباشرة في هذه المحادثة**",
            parse_mode='Markdown'
        )
    async def handle_proof_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_data):
        """معالجة مستند إثبات الإرسال من البائع"""
        trade_id = trade_data[0]
        user_id = update.effective_user.id

        logger.info(f"📤 معالجة مستند إثبات إرسال للصفقة #{trade_id} من البائع {user_id}")

        trade = db.get_trade(trade_id)
        if not trade:
            await update.message.reply_text("❌ خطأ في تحميل بيانات الصفقة")
            return

        # حفظ الملف
        if update.message.document:
            file_id = update.message.document.file_id
            file_name = update.message.document.file_name or "مستند_إثبات_إرسال"
            file_type = "document"
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_name = "صورة_إثبات_إرسال"
            file_type = "photo"
        else:
            await update.message.reply_text("❌ يرجى إرسال مستند أو صورة واضحة")
            return

        logger.info(f"💾 حفظ مستند الإرسال للصفقة #{trade_id} - النوع: {file_type}")

        # تحديث حالة الصفقة إلى انتظار مراجعة الوسيط
        db.update_trade_status(trade_id, Config.STATUS_PROOF_RECEIVED)

        logger.info(f"✅ تم حفظ مستند الإرسال وتحديث حالة الصفقة #{trade_id} إلى انتظار المراجعة")

        # إرسال المستند للوسيط للمراجعة
        if Config.ADMIN_ID:
            try:
                broker_notification = f"""
    📎 **تم استلام مستند إثبات الإرسال للصفقة #{trade_id}**

    📋 **تفاصيل الصفقة:**
    • البائع: {user_id} ({trade['seller_name']})
    • المشتري: {trade['buyer_id']} ({trade['buyer_name']})
    • الكمية: {trade['amount']:,.2f} USDT
    • العنوان: `{Config.BROKER_WALLET_ADDRESS}`
    • الشبكة: {Config.BLOCKCHAIN_NETWORK}

    🔍 **يرجى مراجعة المستند والتأكد من:**
    1. صحة عنوان المحفظة
    2. تطابق المبلغ المرسل
    3. صحة معلومات التحويل
                """

                await context.bot.send_message(
                    Config.ADMIN_ID,
                    broker_notification,
                    parse_mode='Markdown'
                )

                # إرسال المستند للوسيط
                if file_type == "document":
                    await context.bot.send_document(
                        Config.ADMIN_ID,
                        file_id,
                        caption=f"📎 مستند إثبات الإرسال - الصفقة #{trade_id}"
                    )
                else:
                    await context.bot.send_photo(
                        Config.ADMIN_ID,
                        file_id,
                        caption=f"🖼️ إثبات الإرسال - الصفقة #{trade_id}"
                    )

                # أزرار الموافقة أو الرفض من الوسيط
                keyboard = [
                    [
                        InlineKeyboardButton("✅ تأكيد استلام USDT", callback_data=f"broker_confirm_proof_{trade_id}"),
                        InlineKeyboardButton("❌ رفض المستند", callback_data=f"broker_reject_proof_{trade_id}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_message(
                    Config.ADMIN_ID,
                    "⚡ **اضغط على الزر المناسب بعد مراجعة المستند وتأكد من استلام USDT في محفظتك:**",
                    reply_markup=reply_markup
                )

                logger.info(f"✅ تم إرسال المستند للوسيط للمراجعة - الصفقة #{trade_id}")

            except Exception as e:
                logger.error(f"❌ فشل في إرسال المستند للوسيط: {e}")
                await update.message.reply_text(
                    "⚠️ **تم استلام المستند لكن حدث خطأ في إرساله للوسيط**\n\n"
                    "يرجى المحاولة مرة أخرى أو التواصل مع الدعم"
                )
                return

        # تأكيد للبائع
        confirmation_text = f"""
    ✅ **تم استلام مستند الإرسال بنجاح**

    📋 **الصفقة #{trade_id}**
    • الكمية: {trade['amount']:,.2f} USDT
    • الحالة: جاري المراجعة

    ⚡ **تم إرسال المستند للوسيط للمراجعة...**

    ⏳ **سيتم إعلامك فور:**
    • تأكيد استلام USDT من الوسيط، أو
    • طلب مستند بديل في حال وجود مشكلة

    شكراً لتعاونك! 🎉
        """

        await update.message.reply_text(
            confirmation_text,
            parse_mode='Markdown'
        )

        logger.info(f"🎉 اكتملت عملية استلام مستند الإرسال للصفقة #{trade_id}")

    async def handle_payment_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_data):
        """معالجة مستند الدفع من المشتري - النسخة المحدثة"""
        trade_id = trade_data[0]
        user_id = update.effective_user.id

        logger.info(f"💳 معالجة مستند دفع للصفقة #{trade_id} من المشتري {user_id}")

        trade = db.get_trade(trade_id)
        if not trade:
            await update.message.reply_text("❌ خطأ في تحميل بيانات الصفقة")
            return

        # الحصول على بيانات العرض
        offer = db.get_offer(trade['offer_id'])
        if not offer:
            await update.message.reply_text("❌ خطأ في تحميل بيانات العرض")
            return

        # حفظ الملف
        if update.message.document:
            file_id = update.message.document.file_id
            file_name = update.message.document.file_name or "مستند_دفع"
            file_type = "document"
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_name = "صورة_إثبات_دفع"
            file_type = "photo"
        else:
            await update.message.reply_text("❌ يرجى إرسال مستند أو صورة واضحة")
            return

        logger.info(f"💾 حفظ مستند الدفع للصفقة #{trade_id} - النوع: {file_type}")

        # حفظ معرف الملف في قاعدة البيانات
        db.update_trade_payment_proof(trade_id, file_id)
        db.update_trade_status(trade_id, Config.STATUS_WAITING_SELLER_CONFIRMATION)

        logger.info(f"✅ تم حفظ مستند الدفع وتحديث حالة الصفقة #{trade_id}")

        # إرسال إشعار للبائع
        seller_id = trade['seller_id']
        try:
            # إرسال رسالة للبائع
            seller_notification = f"""
    📄 **تم استلام مستند الدفع للصفقة #{trade_id}**

    📊 **تفاصيل الصفقة:**
    • الكمية: {trade['amount']:,.2f} USDT
    • السعر: {trade['exchange_rate']:,.2f}
    • المبلغ المستحق: {trade['amount'] * trade['exchange_rate']:,.2f}
    • وسيلة الدفع: {offer['payment_method']}

    🔍 **يرجى التحقق من استلام الأموال ثم الضغط على تأكيد الاستلام**
            """

            await context.bot.send_message(
                seller_id,
                seller_notification,
                parse_mode='Markdown'
            )

            # إرسال المستند للبائع
            if file_type == "document":
                await context.bot.send_document(
                    seller_id,
                    file_id,
                    caption=f"📎 مستند الدفع للصفقة #{trade_id}"
                )
            else:
                await context.bot.send_photo(
                    seller_id,
                    file_id,
                    caption=f"🖼️ إثبات الدفع للصفقة #{trade_id}"
                )

            # زر تأكيد الاستلام للبائع
            keyboard = [
                [InlineKeyboardButton("✅ تأكيد استلام الأموال", callback_data=f"confirm_payment_{trade_id}")],
                [InlineKeyboardButton("❌ لم يصل بعد", callback_data=f"reject_payment_{trade_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                seller_id,
                "⚡ **اضغط على الزر أدناه لتأكيد استلام الأموال:**",
                reply_markup=reply_markup
            )

            logger.info(f"✅ تم إرسال الإشعار والمستند للبائع {seller_id}")

        except Exception as e:
            logger.error(f"❌ فشل في إرسال المستند للبائع: {e}")
            await update.message.reply_text(
                "❌ **حدث خطأ في إرسال المستند للبائع**\n\n"
                "يرجى المحاولة مرة أخرى أو التواصل مع الدعم"
            )
            return

        # إشعار الوسيط
        if Config.ADMIN_ID:
            try:
                broker_text = f"""
    🔔 **تم استلام مستند الدفع للصفقة #{trade_id}**

    📋 **التفاصيل:**
    • المشتري: {user_id}
    • البائع: {seller_id}
    • الكمية: {trade['amount']:,.2f} USDT
    • المبلغ: {trade['amount'] * trade['exchange_rate']:,.2f}

    ⚡ **بانتظار تأكيد البائع لاستلام الأموال**
                """
                await context.bot.send_message(Config.ADMIN_ID, broker_text, parse_mode='Markdown')
                logger.info(f"✅ تم إرسال إشعار للوسيط")
            except Exception as e:
                logger.error(f"❌ فشل في إرسال إشعار للوسيط: {e}")

        # تأكيد للمشتري
        await update.message.reply_text(
            "✅ **تم إرسال مستند الدفع للبائع بنجاح**\n\n"
            "⚡ **بانتظار تأكيد استلام الأموال من البائع...**\n\n"
            "سيتم إعلامك فور تأكيد البائع للاستلام.",
            parse_mode='Markdown'
        )

        logger.info(f"🎉 اكتملت عملية استلام مستند الدفع للصفقة #{trade_id}")


    async def broker_confirm_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """تأكيد الوسيط لاستلام USDT بعد مراجعة المستند"""
        query = update.callback_query
        await query.answer()



        # التحقق من أن المستخدم هو المشرف
        if not await self.is_admin(query.from_user.id):
            await query.answer("❌ فقط المشرف يمكنه تأكيد الاستلام", show_alert=True)
            return
        # استخدام الدالة المحدثة التي تطلب تفاصيل الدفع من البائع
        await self.broker_confirm_usdt(update, context, trade_id)
        # تحديث حالة الصفقة إلى مؤكد
        db.update_trade_status(trade_id, Config.STATUS_CONFIRMED)

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # إشعار المشتري لبدء عملية الدفع
        buyer_id = trade['buyer_id']
        buyer_info = f"""
    ✅ **تم تأكيد استلام USDT من الوسيط**

    📋 **الصفقة #{trade_id}**
    • الكمية: {trade['amount']:,.2f} USDT

    💳 **يرجى إرسال مستند الدفع الآن:**
    • المبلغ: {trade['amount'] * trade['exchange_rate']:,.2f}
    • وسيلة الدفع: {db.get_offer(trade['offer_id'])['payment_method']}

    📤 **يمكنك إرسال صورة أو مستند الدفع مباشرة في هذه المحادثة**
        """

        try:
            await context.bot.send_message(
                buyer_id,
                buyer_info,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"فشل في إشعار المشتري: {e}")

        # إشعار البائع
        seller_id = trade['seller_id']
        try:
            await context.bot.send_message(
                seller_id,
                f"✅ **تم تأكيد استلام USDT من الوسيط**\n\n"
                f"الصفقة #{trade_id} في انتظار إرسال المشتري لمستند الدفع...",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"فشل في إشعار البائع: {e}")

        await query.message.edit_text(
            "✅ **تم تأكيد استلام USDT**\n\n"
            "تم إخطار المشتري لإرسال مستند الدفع.",
            parse_mode='Markdown'
        )

    async def broker_reject_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """رفض مستند الإرسال من الوسيط"""
        query = update.callback_query
        await query.answer()

        # التحقق من أن المستخدم هو المشرف
        if not await self.is_admin(query.from_user.id):
            await query.answer("❌ فقط المشرف يمكنه رفض المستند", show_alert=True)
            return

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # إشعار البائع برفض المستند
        seller_id = trade['seller_id']
        rejection_message = f"""
    ❌ **تم رفض مستند الإرسال للصفقة #{trade_id}**

    📋 **السبب المحتمل:**
    • المستند غير واضح
    • المعلومات غير مكتملة
    • لم يتم التحقق من استلام USDT

    🔄 **يرجى إرسال مستند إثبات إرسال واضح ومكتمل:**
    • تأكد من ظهور عنوان المحفظة الصحيح
    • تأكد من ظهور المبلغ والوقت
    • تأكد من وضوح الصورة

    ⚡ **أعد إرسال المستند الصحيح في هذه المحادثة**
        """

        try:
            await context.bot.send_message(
                seller_id,
                rejection_message,
                parse_mode='Markdown'
            )

            # العودة إلى حالة انتظار المستند
            db.update_trade_status(trade_id, Config.STATUS_WAITING_PROOF)

        except Exception as e:
            logger.error(f"فشل في إشعار البائع: {e}")

        await query.message.edit_text(
            "❌ **تم رفض المستند**\n\n"
            "تم إخطار البائع لإرسال مستند أفضل.",
            parse_mode='Markdown'
        )
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة جميع المستندات - النسخة المصححة"""
        user_id = update.effective_user.id

        logger.info(f"📄 استلام مستند من المستخدم {user_id}")

        # التحقق من المستندات المنتظرة من الوسيط أولاً
        if 'awaiting_broker_proof' in context.user_data:
            trade_id = context.user_data['awaiting_broker_proof']
            await self.process_broker_proof_document(update, context, trade_id)
            return

        # التحقق من المستندات المنتظرة من المشتري (دفع للبائع)
        if 'awaiting_payment_proof' in context.user_data:
            trade_id = context.user_data['awaiting_payment_proof']
            await self.process_payment_proof_document(update, context, trade_id)
            return

        # البحث في جميع صفقات المستخدم
        trades = db.get_user_trades(user_id)
        active_trade_for_proof = None  # للبائع - إثبات إرسال USDT
        active_trade_for_payment = None  # للمشتري - إثبات الدفع

        logger.info(f"🔍 العدد الإجمالي للصفقات: {len(trades)}")

        for trade_data in trades:
            trade_id, offer_id, buyer_id, seller_id, broker_id, amount, exchange_rate, commission, transfer_fee, buyer_wallet, payment_proof, status, created_at, updated_at, buyer_name, seller_name = trade_data

            logger.info(f"🔍 فحص الصفقة #{trade_id} - الحالة: {status} - المشتري: {buyer_id} - البائع: {seller_id}")

            # الحالة 1: المستخدم هو البائع وتنتظر الصفقة مستند إثبات إرسال USDT
            if user_id == seller_id and status == Config.STATUS_WAITING_PROOF:
                active_trade_for_proof = trade_data
                logger.info(f"🎯 وجدت صفقة تنتظر مستند إرسال USDT #{trade_id}")
                break

            # الحالة 2: المستخدم هو المشتري وتنتظر الصفقة مستند دفع
            if user_id == buyer_id and status in [Config.STATUS_CONFIRMED, Config.STATUS_WAITING_PAYMENT, Config.STATUS_WAITING_PAYMENT_PROOF]:
                active_trade_for_payment = trade_data
                logger.info(f"🎯 وجدت صفقة تنتظر مستند دفع #{trade_id}")
                break

        # المعالجة حسب نوع المستند
        if active_trade_for_proof:
            # معالجة مستند إثبات إرسال USDT من البائع
            await self.handle_proof_document(update, context, active_trade_for_proof)
            return

        elif active_trade_for_payment:
            # معالجة مستند الدفع من المشتري - إصلاح هنا
            await self.handle_payment_document_corrected(update, context, active_trade_for_payment)
            return

        else:
            # إذا لم تكن هناك صفقة نشطة
            await update.message.reply_text(
                "❌ **لا توجد صفقة نشطة تحتاج لإرسال مستندات**\n\n"
                "⚡ **ملاحظة:** يمكنك إرسال المستندات فقط عندما:\n"
                "• تكون البائع وتنتظر الصفقة مستند إثبات إرسال USDT للوسيط\n"
                "• تكون المشتري وتنتظر الصفقة مستند دفع للبائع\n\n"
                "🔍 **تحقق من:**\n"
                "• حالة الصفقة في /my_trades\n"
                "• أنك في الدور الصحيح (بائع/مشتري)\n"
                "• أن الصفقة في المرحلة المناسبة",
                parse_mode='Markdown'
            )
            return

    async def handle_payment_document_corrected(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_data):
        """معالجة مستند الدفع من المشتري - النسخة المصححة"""
        trade_id = trade_data[0]
        user_id = update.effective_user.id

        logger.info(f"💳 معالجة مستند دفع للصفقة #{trade_id} من المشتري {user_id}")

        trade = db.get_trade(trade_id)
        if not trade:
            await update.message.reply_text("❌ خطأ في تحميل بيانات الصفقة")
            return

        # الحصول على بيانات العرض
        offer = db.get_offer(trade['offer_id'])
        if not offer:
            await update.message.reply_text("❌ خطأ في تحميل بيانات العرض")
            return

        # حفظ الملف
        if update.message.document:
            file_id = update.message.document.file_id
            file_name = update.message.document.file_name or "مستند_دفع"
            file_type = "document"
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_name = "صورة_إثبات_دفع"
            file_type = "photo"
        else:
            await update.message.reply_text("❌ يرجى إرسال مستند أو صورة واضحة")
            return

        logger.info(f"💾 حفظ مستند الدفع للصفقة #{trade_id} - النوع: {file_type}")

        # حفظ معرف الملف في قاعدة البيانات
        db.update_trade_payment_proof(trade_id, file_id)
        db.update_trade_status(trade_id, Config.STATUS_WAITING_PAYMENT)

        logger.info(f"✅ تم حفظ مستند الدفع وتحديث حالة الصفقة #{trade_id}")

        # إرسال إشعار للبائع
        seller_id = trade['seller_id']
        try:
            # إرسال رسالة للبائع
            seller_notification = f"""
    📄 **تم استلام مستند الدفع للصفقة #{trade_id}**

    📊 **تفاصيل الصفقة:**
    • الكمية: {trade['amount']:,.2f} USDT
    • السعر: {trade['exchange_rate']:,.2f}
    • المبلغ المستحق: {trade['amount'] * trade['exchange_rate']:,.2f}
    • وسيلة الدفع: {offer['payment_method']}

    🔍 **يرجى التحقق من استلام الأموال ثم الضغط على تأكيد الاستلام**
            """

            await context.bot.send_message(
                seller_id,
                seller_notification,
                parse_mode='Markdown'
            )

            # إرسال المستند للبائع
            if file_type == "document":
                await context.bot.send_document(
                    seller_id,
                    file_id,
                    caption=f"📎 مستند الدفع للصفقة #{trade_id}"
                )
            else:
                await context.bot.send_photo(
                    seller_id,
                    file_id,
                    caption=f"🖼️ إثبات الدفع للصفقة #{trade_id}"
                )

            # زر تأكيد الاستلام للبائع
            keyboard = [
                [InlineKeyboardButton("✅ تأكيد استلام الأموال", callback_data=f"confirm_payment_{trade_id}")],
                [InlineKeyboardButton("❌ لم يصل بعد", callback_data=f"reject_payment_{trade_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                seller_id,
                "⚡ **اضغط على الزر أدناه لتأكيد استلام الأموال:**",
                reply_markup=reply_markup
            )

            logger.info(f"✅ تم إرسال الإشعار والمستند للبائع {seller_id}")

        except Exception as e:
            logger.error(f"❌ فشل في إرسال المستند للبائع: {e}")
            await update.message.reply_text(
                "❌ **حدث خطأ في إرسال المستند للبائع**\n\n"
                "يرجى المحاولة مرة أخرى أو التواصل مع الدعم"
            )
            return

        # إشعار الوسيط
        if Config.ADMIN_ID:
            try:
                broker_text = f"""
    🔔 **تم استلام مستند الدفع للصفقة #{trade_id}**

    📋 **التفاصيل:**
    • المشتري: {user_id}
    • البائع: {seller_id}
    • الكمية: {trade['amount']:,.2f} USDT
    • المبلغ: {trade['amount'] * trade['exchange_rate']:,.2f}

    ⚡ **بانتظار تأكيد البائع لاستلام الأموال**
                """
                await context.bot.send_message(Config.ADMIN_ID, broker_text, parse_mode='Markdown')
                logger.info(f"✅ تم إرسال إشعار للوسيط")
            except Exception as e:
                logger.error(f"❌ فشل في إرسال إشعار للوسيط: {e}")

        # تأكيد للمشتري
        await update.message.reply_text(
            "✅ **تم إرسال مستند الدفع للبائع بنجاح**\n\n"
            "⚡ **بانتظار تأكيد استلام الأموال من البائع...**\n\n"
            "سيتم إعلامك فور تأكيد البائع للاستلام.",
            parse_mode='Markdown'
        )

        logger.info(f"🎉 اكتملت عملية استلام مستند الدفع للصفقة #{trade_id}")


    async def reject_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """رفض استلام الأموال من البائع"""
        query = update.callback_query
        await query.answer()

        logger.info(f"❌ البائع يرفض استلام الأموال للصفقة #{trade_id}")

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # التحقق من أن المستخدم هو البائع
        if query.from_user.id != trade['seller_id']:
            await query.answer("❌ فقط البائع يمكنه رفض الاستلام", show_alert=True)
            return

        # إشعار المشتري
        try:
            buyer_message = f"""
❌ **البائع لم يؤكد استلام الأموال بعد**

📋 **الصفقة #{trade_id}**
• الكمية: {trade['amount']:,.2f} USDT
• المبلغ: {trade['amount'] * trade['exchange_rate']:,.2f}

⚡ **يرجى التواصل مع البائع لحل المشكلة:**
• تأكد من إرسال الأموال للرقم الصحيح
• تأكد من صحة وسيلة الدفع
• قد تكون هناك تأخيرات في النظام

📞 إذا استمرت المشكلة، يرجى التواصل مع الدعم.
            """

            await context.bot.send_message(
                trade['buyer_id'],
                buyer_message,
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم إشعار المشتري {trade['buyer_id']} برفض الاستلام")

        except Exception as e:
            logger.error(f"❌ فشل في إشعار المشتري: {e}")

        # إشعار الوسيط
        if Config.ADMIN_ID:
            try:
                broker_text = f"""
⚠️ **البائع لم يؤكد استلام الأموال**

📋 **الصفقة #{trade_id}**
• المشتري: {trade['buyer_id']}
• البائع: {trade['seller_id']}
• الكمية: {trade['amount']:,.2f} USDT

🔍 **يرجى متابعة المشكلة مع الطرفين**
                """
                await context.bot.send_message(Config.ADMIN_ID, broker_text, parse_mode='Markdown')
                logger.info(f"✅ تم إشعار الوسيط برفض الاستلام")
            except Exception as e:
                logger.error(f"❌ فشل في إرسال إشعار للوسيط: {e}")

        # تحديث واجهة البائع
        await query.message.edit_text(
            "❌ **تم إعلام المشتري بعدم استلام الأموال**\n\n"
            "📞 **يرجى التواصل مع المشتري لحل المشكلة:**\n"
            "• تأكد من استلام الأموال في حسابك\n"
            "• تحقق من وسيلة الدفع المستخدمة\n"
            "• قد تكون هناك تأخيرات في التحويل\n\n"
            "⚡ **عند استلام الأموال، اضغط على زر التأكيد**",
            parse_mode='Markdown'
        )

        logger.info(f"✅ اكتملت عملية رفض الاستلام للصفقة #{trade_id}")
    async def handle_payment_proof_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """معالجة تحميل مستند الدفع من المشتري"""
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            "📤 **يرجى إرسال مستند الدفع الآن:**\n\n"
            "أرسل صورة أو مستند إثبات الدفع للبائع",
            parse_mode='Markdown'
        )

        # حفظ حالة انتظار المستند من المشتري
        context.user_data['awaiting_payment_proof'] = trade_id

    async def process_payment_proof_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """معالجة مستند الدفع من المشتري وإرساله للبائع"""
        user_id = update.effective_user.id

        trade = db.get_trade(trade_id)
        if not trade:
            await update.message.reply_text("❌ الصفقة غير موجودة")
            return

        # التحقق من أن المستخدم هو المشتري
        if user_id != trade['buyer_id']:
            await update.message.reply_text("❌ فقط المشتري يمكنه إرسال مستندات الدفع")
            return

        # حفظ الملف
        if update.message.document:
            file_id = update.message.document.file_id
            file_type = "document"
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_type = "photo"
        else:
            await update.message.reply_text("❌ يرجى إرسال مستند أو صورة واضحة")
            return

        # إرسال المستند للبائع
        seller_id = trade['seller_id']
        try:
            payment_proof_text = f"""
    📋 **مستند إثبات الدفع من المشتري**

    ✅ **تم إرسال الدفع بنجاح**
    • الصفقة: #{trade_id}
    • المبلغ: {trade['amount'] * trade['exchange_rate']:,.2f}
    • وسيلة الدفع: {db.get_offer(trade['offer_id'])['payment_method']}

    🔍 **مستند إثبات الدفع:**
    """

            # إرسال الرسالة النصية أولاً
            await context.bot.send_message(
                seller_id,
                payment_proof_text,
                parse_mode='Markdown'
            )

            # ثم إرسال المستند
            if file_type == "document":
                await context.bot.send_document(
                    seller_id,
                    file_id,
                    caption=f"📎 مستند إثبات الدفع - الصفقة #{trade_id}"
                )
            else:
                await context.bot.send_photo(
                    seller_id,
                    file_id,
                    caption=f"🖼️ إثبات الدفع - الصفقة #{trade_id}"
                )

            logger.info(f"✅ تم إرسال مستند الدفع للبائع للصفقة #{trade_id}")

        except Exception as e:
            logger.error(f"❌ فشل في إرسال المستند للبائع: {e}")
            await update.message.reply_text("❌ فشل في إرسال المستند للبائع")
            return

        # تأكيد للمشتري
        await update.message.reply_text(
            "✅ **تم إرسال مستند الدفع للبائع**\n\n"
            "شكراً لإتمامك عملية الدفع!",
            parse_mode='Markdown'
        )

        # تنظيف البيانات المؤقتة
        if 'awaiting_payment_proof' in context.user_data:
            del context.user_data['awaiting_payment_proof']

        # تحديث حالة الصفقة
        db.update_trade_status(trade_id, Config.STATUS_WAITING_USDT_SEND)

        # إشعار الوسيط
        if Config.ADMIN_ID:
            broker_text = f"""
    🔔 **تم استلام مستند الدفع للصفقة #{trade_id}**

    📋 **الحالة:** جاهز لإرسال USDT للمشتري
    • المشتري: {user_id}
    • البائع: {seller_id}
    """
            await context.bot.send_message(Config.ADMIN_ID, broker_text, parse_mode='Markdown')
    async def confirm_payment_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """تأكيد استلام الأموال من البائع مع طلب عنوان محفظة المشتري"""
        query = update.callback_query
        await query.answer()

        logger.info(f"✅ البائع يؤكد استلام الأموال للصفقة #{trade_id}")

        # تحديث حالة الصفقة إلى انتظار عنوان محفظة المشتري
        db.update_trade_status(trade_id, Config.STATUS_WAITING_USDT_SEND)

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # طلب عنوان محفظة المشتري
        buyer_id = trade['buyer_id']
        wallet_request = f"""
    💰 **يرجى إرسال عنوان محفظتك USDT**

    📋 **الصفقة #{trade_id}**
    • الكمية: {trade['amount']:,.2f} USDT
    • الشبكة: {Config.BLOCKCHAIN_NETWORK}

    🔗 **أرسل عنوان محفظتك الآن:**
    • تأكد من صحة العنوان
    • تأكد من أن الشبكة {Config.BLOCKCHAIN_NETWORK}
    • سيتم إرسال USDT لهذا العنوان

    ⚡ **أرسل العنوان مباشرة في هذه المحادثة**
    """

        try:
            await context.bot.send_message(
                buyer_id,
                wallet_request,
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم طلب عنوان المحفظة من المشتري للصفقة #{trade_id}")
        except Exception as e:
            logger.error(f"❌ فشل في طلب عنوان المحفظة: {e}")
            await query.answer("❌ فشل في إرسال الطلب", show_alert=True)
            return

        # إشعار الوسيط
        if Config.ADMIN_ID:
            broker_text = f"""
    🔔 **البائع أكد استلام الأموال للصفقة #{trade_id}**

    📋 **التفاصيل:**
    • المشتري: {buyer_id}
    • البائع: {trade['seller_id']}
    • الكمية: {trade['amount']:,.2f} USDT

    💳 **بانتظار عنوان محفظة المشتري لإرسال USDT**
    """
            await context.bot.send_message(Config.ADMIN_ID, broker_text, parse_mode='Markdown')

        # تأكيد للبائع
        await query.message.edit_text(
            "✅ **تم تأكيد استلام الأموال**\n\n"
            "تم طلب عنوان محفظة المشتري لإرسال USDT.",
            parse_mode='Markdown'
        )

    async def handle_wallet_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """معالجة عنوان محفظة المشتري وإشعار الوسيط"""
        user_id = update.effective_user.id
        wallet_address = update.message.text.strip()

        # التحقق من صحة العنوان (تبسيط)
        if len(wallet_address) < 20:
            await update.message.reply_text("❌ عنوان المحفظة غير صالح، يرجى إرسال عنوان صحيح:")
            return

        # حفظ عنوان المحفظة
        db.update_trade_buyer_wallet(trade_id, wallet_address)
        db.update_trade_status(trade_id, Config.STATUS_USDT_SENT_TO_BUYER)

        trade = db.get_trade(trade_id)
        if not trade:
            await update.message.reply_text("❌ الصفقة غير موجودة")
            return

        # إشعار الوسيط
        if Config.ADMIN_ID:
            broker_text = f"""
    🔔 **تم استلام عنوان محفظة المشتري**

    📋 **الصفقة #{trade_id}**
    • المشتري: {user_id}
    • العنوان: `{wallet_address}`
    • الكمية: {trade['amount']:,.2f} USDT
    • الشبكة: {Config.BLOCKCHAIN_NETWORK}

    💰 **يرجى تحويل USDT للمشتري ثم تأكيد الإرسال**
    """

            keyboard = [
                [InlineKeyboardButton("✅ تأكيد إرسال USDT للمشتري", callback_data=f"confirm_usdt_to_buyer_{trade_id}")],
                [InlineKeyboardButton("📤 إرسال مستند الإرسال", callback_data=f"upload_broker_proof_{trade_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                Config.ADMIN_ID,
                broker_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        await update.message.reply_text(
            "✅ **تم استلام عنوان محفظتك**\n\n"
            "بانتظار تحويل USDT من الوسيط...\n"
            "سيتم إعلامك فور الإرسال.",
            parse_mode='Markdown'
        )
    async def handle_broker_proof_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """معالجة تحميل مستند إرسال USDT من الوسيط"""
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            "📤 **يرجى إرسال مستند إرسال USDT الآن:**\n\n"
            "أرسل صورة أو مستند إثبات إرسال USDT للمشتري",
            parse_mode='Markdown'
        )

        # حفظ حالة انتظار المستند من الوسيط
        context.user_data['awaiting_broker_proof'] = trade_id

    async def process_broker_proof_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """معالجة مستند إرسال USDT من الوسيط وإرساله للمشتري"""
        user_id = update.effective_user.id

        # التحقق من أن المستخدم هو الوسيط
        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ فقط الوسيط يمكنه إرسال مستندات الإرسال")
            return

        trade = db.get_trade(trade_id)
        if not trade:
            await update.message.reply_text("❌ الصفقة غير موجودة")
            return

        # حفظ الملف
        if update.message.document:
            file_id = update.message.document.file_id
            file_type = "document"
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_type = "photo"
        else:
            await update.message.reply_text("❌ يرجى إرسال مستند أو صورة واضحة")
            return

        # إرسال المستند للمشتري
        buyer_id = trade['buyer_id']
        try:
            broker_proof_text = f"""
    📋 **تم إرسال USDT لك - مستند الإثبات**

    🎉 **مبروك! تم إرسال USDT إلى محفظتك**
    • الصفقة: #{trade_id}
    • الكمية: {trade['amount']:,.2f} USDT
    • العنوان: `{trade['buyer_wallet']}`
    • الشبكة: {Config.BLOCKCHAIN_NETWORK}

    🔍 **مستند إثبات الإرسال من الوسيط:**
    """

            # إرسال الرسالة النصية أولاً
            await context.bot.send_message(
                buyer_id,
                broker_proof_text,
                parse_mode='Markdown'
            )

            # ثم إرسال المستند
            if file_type == "document":
                await context.bot.send_document(
                    buyer_id,
                    file_id,
                    caption=f"📎 مستند إثبات إرسال USDT - الصفقة #{trade_id}"
                )
            else:
                await context.bot.send_photo(
                    buyer_id,
                    file_id,
                    caption=f"🖼️ إثبات إرسال USDT - الصفقة #{trade_id}"
                )

            # زر تأكيد الاستلام للمشتري
            keyboard = [
                [InlineKeyboardButton("✅ تأكيد استلام USDT", callback_data=f"confirm_usdt_received_{trade_id}")],
                [InlineKeyboardButton("❌ لم يصل بعد", callback_data=f"reject_usdt_received_{trade_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                buyer_id,
                "⚡ **اضغط على الزر أدناه لتأكيد استلام USDT:**",
                reply_markup=reply_markup
            )

            logger.info(f"✅ تم إرسال مستند الوسيط للمشتري للصفقة #{trade_id}")

        except Exception as e:
            logger.error(f"❌ فشل في إرسال المستند للمشتري: {e}")
            await update.message.reply_text("❌ فشل في إرسال المستند للمشتري")
            return

        # تأكيد للوسيط
        await update.message.reply_text(
            "✅ **تم إرسال مستند الإرسال للمشتري**\n\n"
            "بانتظار تأكيد الاستلام من المشتري...",
            parse_mode='Markdown'
        )

        # تنظيف البيانات المؤقتة
        if 'awaiting_broker_proof' in context.user_data:
            del context.user_data['awaiting_broker_proof']
    async def confirm_usdt_to_buyer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """تأكيد إرسال USDT للمشتري مع طلب مستند الإرسال من الوسيط"""
        query = update.callback_query
        await query.answer()

        # التحقق من أن المستخدم هو المشرف
        if not await self.is_admin(query.from_user.id):
            await query.answer("❌ فقط المشرف يمكنه تأكيد الإرسال", show_alert=True)
            return

        # تحديث حالة الصفقة
        db.update_trade_status(trade_id, Config.STATUS_USDT_SENT_TO_BUYER)

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # طلب مستند إرسال USDT من الوسيط
        proof_request = f"""
    📤 **يرجى إرسال مستند إرسال USDT للمشتري**

    📋 **الصفقة #{trade_id}**
    • الكمية: {trade['amount']:,.2f} USDT
    • عنوان المشتري: `{trade['buyer_wallet']}`
    • الشبكة: {Config.BLOCKCHAIN_NETWORK}

    📎 **أرسل مستند إثبات الإرسال:**
    • screenshot من محفظة الوسيط
    • تأكيد التحويل (transaction confirmation)
    • أي مستند يثبت إرسال USDT للمشتري

    ⚡ **سيتم إرسال هذا المستند للمشتري للتأكد**
    """

        keyboard = [
            [InlineKeyboardButton("📤 إرسال مستند الإرسال", callback_data=f"upload_broker_proof_{trade_id}")],
            [InlineKeyboardButton("✅ تأكيد بدون مستند", callback_data=f"confirm_without_proof_{trade_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(
            proof_request,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


    async def confirm_usdt_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """تأكيد استلام USDT من المشتري"""
        query = update.callback_query
        await query.answer()

        # تحديث حالة الصفقة إلى مكتملة
        db.update_trade_status(trade_id, Config.STATUS_COMPLETED)

        # تنظيف المستندات
        await self.cleanup_trade_documents(trade_id)

        # إشعار جميع الأطراف
        trade = db.get_trade(trade_id)
        if trade:
            completion_text = f"""
<b>🎉 **تم إكمال الصفقة بنجاح!**</b>

<s>✅ **الصفقة #{trade_id} مكتملة**</s>
<s>• الكمية: {trade['amount']:,.2f} USDT</s>
<s>• السعر: {trade['exchange_rate']:,.2f}</s>
<s>• العمولة: ${trade['commission']:,.2f}</s>

شكراً لاستخدامكم خدماتنا
            """

            # إرسال للبائع والمشتري
            for participant_id in [trade['buyer_id'], trade['seller_id']]:
                try:
                    await context.bot.send_message(participant_id, completion_text, parse_mode='HTML')
                except Exception as e:
                    logger.error(f"Failed to send completion message: {e}")

            # إشعار الوسيط
            if Config.ADMIN_ID:
                await context.bot.send_message(Config.ADMIN_ID, completion_text, parse_mode='HTML')

            # تحديث القناة
            await self.channel_manager.mark_trade_completed(trade_id)

        await query.message.edit_text(
            "🎉 **تم تأكيد استلام USDT وإكمال الصفقة**\n\n"
            "شكراً لاستخدامكم خدماتنا!",
            parse_mode='HTML'
        )

    async def cancel_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """إلغاء الصفقة"""
        query = update.callback_query
        await query.answer()

        # تحديث حالة الصفقة إلى ملغية
        db.update_trade_status(trade_id, Config.STATUS_CANCELLED)

        # تنظيف المستندات
        await self.cleanup_trade_documents(trade_id)

        # إعادة تفعيل العرض
        db.reactivate_offer_after_trade_cancel(trade_id)

        trade = db.get_trade(trade_id)
        if trade:
            # تحديث العرض في القناة
            await self.channel_manager.update_offer_status(trade['offer_id'], 'active')

            # إشعار جميع الأطراف
            cancel_text = f"""
❌ **تم إلغاء الصفقة**

📋 **الصفقة #{trade_id} ملغية**
• الكمية: {trade['amount']:,.2f} USDT
• السعر: {trade['exchange_rate']:,.2f}

للمزيد من المعلومات، تواصل مع الدعم.
            """

            for participant_id in [trade['buyer_id'], trade['seller_id']]:
                try:
                    await context.bot.send_message(participant_id, cancel_text, parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Failed to send cancellation message: {e}")

            if Config.ADMIN_ID:
                await context.bot.send_message(Config.ADMIN_ID, cancel_text, parse_mode='Markdown')

        await query.message.edit_text(
            "❌ **تم إلغاء الصفقة**\n\n"
            "تم إخطار جميع الأطراف بالإلغاء.",
            parse_mode='Markdown'
        )

    async def admin_cancel_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """إلغاء الصفقة بواسطة المشرف"""
        query = update.callback_query
        await query.answer()

        # التحقق من أن المستخدم هو المشرف
        if not await self.is_admin(query.from_user.id):
            await query.answer("❌ فقط المشرف يمكنه إلغاء الصفقة", show_alert=True)
            return

        # إلغاء الصفقة
        success = db.cancel_trade_by_admin(trade_id, query.from_user.id)

        if success:
            # تنظيف المستندات
            await self.cleanup_trade_documents(trade_id)

            trade = db.get_trade(trade_id)
            if trade:
                # تحديث العرض في القناة
                await self.channel_manager.update_offer_status(trade['offer_id'], 'active')

                # إشعار جميع الأطراف
                cancel_text = f"""
❌ **تم إلغاء الصفقة بواسطة المشرف**

📋 **الصفقة #{trade_id} ملغية**
• الكمية: {trade['amount']:,.2f} USDT
• السعر: {trade['exchange_rate']:,.2f}

للمزيد من المعلومات، تواصل مع الدعم.
                """

                for participant_id in [trade['buyer_id'], trade['seller_id']]:
                    try:
                        await context.bot.send_message(participant_id, cancel_text, parse_mode='Markdown')
                    except Exception as e:
                        logger.error(f"Failed to send cancellation message: {e}")

            await query.message.edit_text(
                "✅ **تم إلغاء الصفقة بواسطة المشرف**\n\n"
                "تم إخطار جميع الأطراف بالإلغاء.",
                parse_mode='Markdown'
            )
        else:
            await query.answer("❌ فشل في إلغاء الصفقة", show_alert=True)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        user_id = update.effective_user.id
        text = update.message.text

        # التحقق من حالة البوت أولاً
        if not db.is_bot_active() and not await self.is_admin(user_id):
            await update.message.reply_text("⏸️ البوت معطل حالياً. يرجى المحاولة لاحقاً.")
            return

        # التحقق من وقت عمل البوت
        if not await self.check_bot_working_hours(user_id) and not await self.is_admin(user_id):
            await update.message.reply_text(
                "⏰ **البوت خارج وقت العمل**\n\n"
                "⏳ وقت العمل: من 8 صباحاً حتى 12 منتصف الليل\n"
                "🔄 العروض الجديدة متاحة من 8 صباحاً"
            )
            return
        if text == "🚀 البدء":
            await self.create_offer_flow_message(update, context)
            return
        elif text == "🛠️ لوحة التحكم" and await self.is_admin(user_id):
            await self.admin_panel_message(update, context)
            return
        elif text == "❌ إلغاء الصفقة الحالية":
            await self.cancel_current_trade_message(update, context)
            return
        # معالجة إدخال إعدادات العمولة الجديدة
        if 'awaiting_commission_settings' in context.user_data:
            await self.handle_commission_settings_input(update, context, text)
            return
        # معالجة تفاصيل الدفع من البائع
        if 'awaiting_payment_details' in context.user_data:
            await self.handle_payment_details_message(update, context)
            return
        # معالجة إدخال العمولة الجديدة
        if 'awaiting_commission' in context.user_data:
            try:
                new_commission = float(text)
                if new_commission <= 0:
                    await update.message.reply_text("❌ القيمة يجب أن تكون أكبر من الصفر")
                    return

                db.update_setting('fixed_commission', str(new_commission))
                await update.message.reply_text(
                    f"✅ تم تحديث العمولة إلى {new_commission:.6f} دولار لكل USDT"
                )
                del context.user_data['awaiting_commission']

            except ValueError:
                await update.message.reply_text("❌ يرجى إدخال رقم صحيح")
            return

        # معالجة إدخال عمولة التحويل
        if 'awaiting_transfer_fee' in context.user_data:
            try:
                new_fee = float(text)
                if new_fee < 0:
                    await update.message.reply_text("❌ القيمة يجب أن تكون أكبر أو يساوي الصفر")
                    return

                db.update_transfer_fee(new_fee)
                await update.message.reply_text(
                    f"✅ تم تحديث عمولة التحويل إلى {new_fee:.2f} دولار"
                )
                del context.user_data['awaiting_transfer_fee']

            except ValueError:
                await update.message.reply_text("❌ يرجى إدخال رقم صحيح")
            return

        # معالجة تعديل الرسائل
        if 'editing_message' in context.user_data:
            message_key = context.user_data['editing_message']
            db.update_message(message_key, text)
            await update.message.reply_text("✅ تم تحديث الرسالة بنجاح")
            del context.user_data['editing_message']
            return

        # المعالجات الأصلية تبقى كما هي
        if 'creating_offer' in context.user_data:
            await self.handle_offer_creation(update, context, text)
            return

        # التحقق مما إذا كان المستخدم يرسل عنوان محفظة
        trades = db.get_user_trades(user_id)
        for trade in trades:
            if trade[11] == Config.STATUS_WAITING_USDT_SEND and user_id == trade[2]:  # buyer waiting to send wallet
                await self.handle_wallet_address(update, context, trade[0])
                return

        # إذا لم تكن هناك عملية نشطة، عرض القائمة الرئيسية
        await self.main_menu(update, context)
    async def admin_panel_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """فتح لوحة التحكم من زر القائمة مع الحفاظ على القائمة"""
        user_id = update.effective_user.id

        # التحقق من صلاحية المشرف
        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ ليس لديك صلاحية للوصول لهذه اللوحة")
            return

        # استخدام Inline keyboard للوحة التحكم
        keyboard = [
            [InlineKeyboardButton("📋 إدارة العروض", callback_data="admin_offers")],
            [InlineKeyboardButton("💰 إعدادات العمولة", callback_data="admin_commission")],
            [InlineKeyboardButton("💸 عمولة التحويل", callback_data="admin_transfer_fee")],
            [InlineKeyboardButton("⚙️ إعدادات النظام", callback_data="admin_system")],
            [InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("📋 آخر 20 صفقة", callback_data="recent_trades")],  # الزر الجديد
            [InlineKeyboardButton("⏰ تعطيل جميع العروض", callback_data="expire_offers")],
            [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = """
    🛠️ **لوحة تحكم المشرف**

    اختر الإعداد الذي تريد تعديله:
    """

        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def cancel_trade_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """إلغاء الصفقة مباشرة مع الحفاظ على القائمة"""
        # تحديث حالة الصفقة إلى ملغية
        db.update_trade_status(trade_id, Config.STATUS_CANCELLED)

        # تنظيف المستندات
        await self.cleanup_trade_documents(trade_id)

        # إعادة تفعيل العرض
        db.reactivate_offer_after_trade_cancel(trade_id)

        trade = db.get_trade(trade_id)
        if trade:
            # تحديث العرض في القناة
            await self.channel_manager.update_offer_status(trade['offer_id'], 'active')

            # إشعار جميع الأطراف
            cancel_text = f"""
    ❌ **تم إلغاء الصفقة**

    📋 **الصفقة #{trade_id} ملغية**
    • الكمية: {trade['amount']:,.2f} USDT
    • السعر: {trade['exchange_rate']:,.2f}

    للمزيد من المعلومات، تواصل مع الدعم.
            """

            for participant_id in [trade['buyer_id'], trade['seller_id']]:
                try:
                    await context.bot.send_message(participant_id, cancel_text, parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Failed to send cancellation message: {e}")

        await update.message.reply_text(
            f"✅ **تم إلغاء الصفقة #{trade_id} بنجاح**\n\n"
            "يمكنك متابعة استخدام البوت من القائمة أدناه.",
            parse_mode='Markdown'
        )
    async def create_offer_flow_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء عملية إنشاء عرض جديد من زر القائمة"""
        user_id = update.effective_user.id

        # التحقق من وقت عمل البوت
        if not await self.check_bot_working_hours(user_id):
            await update.message.reply_text(
                "⏰ **لا يمكن إنشاء عروض جديدة خارج وقت العمل**\n\n"
                "⏳ وقت العمل: من 8 صباحاً حتى 12 منتصف الليل\n"
                "🔄 العروض الجديدة متاحة من 8 صباحاً"
            )
            return

        if not await self.require_channel_membership(update, context):
            return

        # إخفاء القائمة مؤقتاً أثناء العملية
       # remove_keyboard = ReplyKeyboardRemove()
        #await update.message.reply_text(
        #    "🔄 **جاري تحضير إنشاء عرض جديد...**",
        #    reply_markup=remove_keyboard,
           # parse_mode='Markdown'
        #)

        # استخدام نفس دالة الإنشاء ولكن مع تعديل للعودة للقائمة
        keyboard = [
            [InlineKeyboardButton("🟢 بيع USDT", callback_data="offer_type_sell")],
            [InlineKeyboardButton("🔵 شراء USDT", callback_data="offer_type_buy")]

        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = """
    📊 **إنشاء عرض جديد**

    اختر نوع العرض:
    • 🟢 **بيع USDT**: لديك USDT وتريد بيعه
    • 🔵 **شراء USDT**: تريد شراء USDT

    ⚡ **ملاحظة:** سيتم نشر عرضك في القناة وسيراه جميع الأعضاء
        """

        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def cancel_current_trade_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء الصفقة الحالية من زر القائمة - النسخة المصححة"""
        user_id = update.effective_user.id

        # البحث عن الصفقات النشطة للمستخدم
        trades = db.get_user_trades(user_id)
        active_trades = []

        logger.info(f"🔍 البحث عن الصفقات النشطة للمستخدم {user_id}")
        logger.info(f"📊 العدد الإجمالي للصفقات: {len(trades)}")

        # الحالات التي تعتبر نشطة (ليست مكتملة أو ملغية)
        inactive_statuses = [Config.STATUS_COMPLETED, Config.STATUS_CANCELLED]

        for trade in trades:
            trade_id, offer_id, buyer_id, seller_id, broker_id, amount, exchange_rate, commission, transfer_fee, buyer_wallet, payment_proof, status, created_at, updated_at, buyer_name, seller_name = trade

            logger.info(f"🔍 فحص الصفقة #{trade_id} - الحالة: {status}")

            if status not in inactive_statuses:
                active_trades.append(trade)
                logger.info(f"✅ أضيفت الصفقة #{trade_id} للقائمة النشطة")

        logger.info(f"📋 عدد الصفقات النشطة: {len(active_trades)}")

        if not active_trades:
            await update.message.reply_text(
                "✅ <b>لا توجد صفقات نشطة للإلغاء</b>\n\n"
                "جميع صفقاتك مكتملة أو ملغية مسبقاً.",
                parse_mode='HTML'
            )
            return

        # إخفاء القائمة مؤقتاً
        remove_keyboard = ReplyKeyboardRemove()
        await update.message.reply_text(
            "🔍 **جاري البحث عن الصفقات النشطة...**",
            reply_markup=remove_keyboard,
            parse_mode='HTML'
        )

        if len(active_trades) == 1:
            # إذا كان هناك صفقة واحدة فقط، إلغاؤها مباشرة
            trade_id = active_trades[0][0]
            logger.info(f"🔄 إلغاء الصفقة الوحيدة النشطة #{trade_id}")
            await self.cancel_trade_direct(update, context, trade_id)
        else:
            # إذا كان هناك أكثر من صفقة، عرض قائمة للاختيار
            keyboard = []
            for trade in active_trades:
                trade_id = trade[0]
                amount = trade[5]
                status = trade[11]

                # تحديد دور المستخدم
                if user_id == trade[2]:  # buyer_id
                    role = "مشتري"
                elif user_id == trade[3]:  # seller_id
                    role = "بائع"
                else:
                    role = "غير معروف"

                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ إلغاء الصفقة #{trade_id} ({role})",
                        callback_data=f"cancel_trade_{trade_id}"
                    )
                ])
                logger.info(f"📝 إضافة زر للصفقة #{trade_id} - الدور: {role}")

            keyboard.append([InlineKeyboardButton("↩️ رجوع للقائمة", callback_data="back_to_main_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            # إنشاء نص القائمة مع تقليل المعلومات لتجنب الخطأ 400
            trade_list = "\n".join([
                f"• الصفقة #{trade[0]} ({'مشتري' if user_id == trade[2] else 'بائع'}) - {trade[5]:,.0f} USDT"
                for trade in active_trades[:8]  # الحد الأقصى 8 صفقات
            ])

            if len(active_trades) > 8:
                trade_list += f"\n• ... و{len(active_trades) - 8} صفقات أخرى"

            await update.message.reply_text(
                f"📋 **اختر الصفقة التي تريد إلغاءها:**\n\n{trade_list}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        logger.info(f"✅ اكتملت عملية عرض الصفقات للإلغاء")
    async def cancel_trade_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """إلغاء الصفقة مباشرة وعرض القائمة بعد الإلغاء"""
        # تحديث حالة الصفقة إلى ملغية
        db.update_trade_status(trade_id, Config.STATUS_CANCELLED)



        # إعادة تفعيل العرض
        db.reactivate_offer_after_trade_cancel(trade_id)

        trade = db.get_trade(trade_id)
        if trade:
            # تحديث العرض في القناة
            await self.channel_manager.update_offer_status(trade['offer_id'], 'active')

            # إشعار جميع الأطراف
            cancel_text = f"""
    ❌ <b>تم إلغاء الصفقة</b>

    📋 <b>الصفقة #{trade_id} ملغية</b>
    • الكمية: {trade['amount']:,.2f} USDT
    • السعر: {trade['exchange_rate']:,.2f}

    للمزيد من المعلومات، تواصل مع الدعم.
            """

            for participant_id in [trade['buyer_id'], trade['seller_id']]:
                try:
                    await context.bot.send_message(participant_id, cancel_text, parse_mode='HTML')
                except Exception as e:
                    logger.error(f"Failed to send cancellation message: {e}")

        # عرض القائمة الرئيسية بعد الإلغاء
        await self.main_menu(update, context)

    async def back_to_main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """العودة للقائمة الرئيسية من الاستعلامات"""
        query = update.callback_query
        await query.answer()

        await self.main_menu(update, context)
    async def request_proof_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """طلب تحميل مستند إثبات الإرسال من البائع"""
        query = update.callback_query
        await query.answer()

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # إرسال طلب تحميل المستند للبائع
        proof_request = f"""
    📤 **يرجى تحميل مستند إثبات إرسال USDT**

    📋 **تفاصيل الصفقة #{trade_id}:**
    • الكمية: {trade['amount']:,.2f} USDT
    • الشبكة: {Config.BLOCKCHAIN_NETWORK}
    • العنوان: `{Config.BROKER_WALLET_ADDRESS}`

    📎 **يمكنك إرسال:**
    • screenshot من محفظتك يظهر التحويل
    • تأكيد التحويل (transaction confirmation)
    • أي مستند يثبت إرسال USDT للوسيط

    ⚡ **أرسل الصورة أو المستند مباشرة في هذه المحادثة**
        """

        try:
            await context.bot.send_message(
                trade['seller_id'],
                proof_request,
                parse_mode='Markdown'
            )
            await query.answer("✅ تم إرسال طلب المستند للبائع")

            # تحديث حالة الصفقة إلى انتظار المستند
            db.update_trade_status(trade_id, Config.STATUS_WAITING_PROOF)

        except Exception as e:
            logger.error(f"❌ فشل في إرسال طلب المستند: {e}")
            await query.answer("❌ فشل في إرسال الطلب", show_alert=True)
    async def handle_commission_settings_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """معالجة إدخال إعدادات العمولة الجديدة"""
        try:
            parts = text.split()
            if len(parts) != 3:
                await update.message.reply_text("❌ التنسيق غير صحيح. يرجى إرسال 3 قيم فقط.")
                return

            small_amount = float(parts[0])
            small_commission = float(parts[1])
            large_commission = float(parts[2])

            # التحقق من القيم
            if small_amount <= 0 or small_commission <= 0 or large_commission <= 0:
                await update.message.reply_text("❌ جميع القيم يجب أن تكون أكبر من الصفر.")
                return

            if small_commission >= large_commission:
                await update.message.reply_text("❌ عمولة المبالغ الكبيرة يجب أن تكون أكبر من عمولة المبالغ الصغيرة.")
                return

            # تحديث الإعدادات
            success = db.update_commission_settings(small_amount, small_commission, large_commission)

            if success:
                await update.message.reply_text(
                    f"✅ **تم تحديث إعدادات العمولة بنجاح**\n\n"
                    f"• حد المبالغ الصغيرة: {small_amount:,.2f} USDT\n"
                    f"• عمولة المبالغ الصغيرة: ${small_commission:.2f}\n"
                    f"• عمولة المبالغ الكبيرة: ${large_commission:.2f}\n\n"
                    f"سيتم تطبيق هذه الإعدادات على الصفقات الجديدة."
                )
            else:
                await update.message.reply_text("❌ حدث خطأ في تحديث الإعدادات.")

            # تنظيف البيانات المؤقتة
            if 'awaiting_commission_settings' in context.user_data:
                del context.user_data['awaiting_commission_settings']

        except ValueError:
            await update.message.reply_text("❌ يرجى إدخال أرقام صحيحة فقط.")
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة إعدادات العمولة: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة البيانات.")

    async def handle_offer_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """معالجة إدخال البيانات أثناء إنشاء العرض"""
        offer_data = context.user_data['creating_offer']

        try:
            # إذا لم يتم إدخال الكمية بعد
            if 'amount' not in offer_data:
                amount = float(text.replace(',', ''))
                if amount <= 0:
                    await update.message.reply_text("❌ الكمية يجب أن تكون أكبر من الصفر، حاول مرة أخرى:")
                    return

                offer_data['amount'] = amount
                await update.message.reply_text(f"✅ الكمية: {amount:,.2f} USDT\n\nالآن أدخل سعر الصرف (مثال: 13500):")
                return

            # إذا تم إدخال الكمية ولكن لم يتم إدخال السعر
            if 'amount' in offer_data and 'exchange_rate' not in offer_data:
                exchange_rate = float(text.replace(',', ''))
                if exchange_rate <= 0:
                    await update.message.reply_text("❌ سعر الصرف يجب أن يكون أكبر من الصفر، حاول مرة أخرى:")
                    return

                offer_data['exchange_rate'] = exchange_rate

                # عرض خيارات وسيلة الدفع
                await self.show_payment_methods(update, context)
                return

        except ValueError:
            await update.message.reply_text("❌ يرجى إدخال رقم صحيح، حاول مرة أخرى:")
            return

    async def show_payment_methods(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض خيارات وسائل الدفع"""
        keyboard = []
        for key, value in Config.PAYMENT_METHODS.items():
            keyboard.append([InlineKeyboardButton(value, callback_data=f"payment_{key}")])

        keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel_offer")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text(
                "💳 **اختر وسيلة الدفع:**",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "💳 **اختر وسيلة الدفع:**",
                reply_markup=reply_markup
            )

    async def handle_payment_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار وسيلة الدفع"""
        query = update.callback_query
        await query.answer()

        payment_key = query.data.replace('payment_', '')

        if payment_key not in Config.PAYMENT_METHODS:
            await query.answer("❌ وسيلة الدفع غير معروفة", show_alert=True)
            return

        # تحديث بيانات العرض
        if 'creating_offer' in context.user_data:
            context.user_data['creating_offer']['payment_method'] = payment_key

            # عرض تأكيد البيانات مباشرة
            await self.show_offer_confirmation_query(query, context)
        else:
            await query.answer("❌ لم يتم العثور على بيانات العرض", show_alert=True)

    async def show_offer_confirmation_query(self, query, context: ContextTypes.DEFAULT_TYPE):
        """عرض تأكيد بيانات العرض للاستعلامات"""
        if 'creating_offer' not in context.user_data:
            await query.answer("❌ لم يتم العثور على بيانات العرض", show_alert=True)
            return

        offer_data = context.user_data['creating_offer']

        # التحقق من اكتمال البيانات
        required_fields = ['type', 'payment_method', 'amount', 'exchange_rate']
        for field in required_fields:
            if field not in offer_data:
                await query.answer(f"❌ بيانات العرض غير مكتملة: {field}", show_alert=True)
                return

        # حساب العمولة
        commission = db.calculate_commission(offer_data['amount'])

        text = f"""
📊 **تأكيد بيانات العرض**

🟢 **النوع:** {'بيع' if offer_data['type'] == 'sell' else 'شراء'} USDT
💎 **الكمية:** {offer_data['amount']:,.2f} USDT
💰 **سعر الصرف:** {offer_data['exchange_rate']:,.2f}
💳 **وسيلة الدفع:** {Config.PAYMENT_METHODS[offer_data['payment_method']]}
🏦 **عمولة الوسيط:** ${commission:.2f}

⚡ **هل أنت متأكد من إنشاء هذا العرض؟**
        """

        keyboard = [
            [InlineKeyboardButton("✅ تأكيد إنشاء العرض", callback_data="confirm_offer")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_offer")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        logger.info(f"✅ تم عرض تأكيد العرض لل user: {query.from_user.id}")

    async def complete_offer_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إكمال إنشاء العرض ونشره في القناة"""
        query = update.callback_query
        await query.answer()

        logger.info(f"🔔 تم النقر على تأكيد إنشاء العرض - user: {query.from_user.id}")

        if 'creating_offer' not in context.user_data:
            error_msg = "❌ لم يتم العثور على بيانات العرض في context"
            logger.error(error_msg)
            await query.answer(error_msg, show_alert=True)
            return

        offer_data = context.user_data['creating_offer']
        logger.info(f"📋 بيانات العرض الموجودة: {offer_data}")

        # التحقق من اكتمال البيانات
        required_fields = ['type', 'payment_method', 'amount', 'exchange_rate']
        missing_fields = []
        for field in required_fields:
            if field not in offer_data:
                missing_fields.append(field)

        if missing_fields:
            error_msg = f"❌ بيانات العرض غير مكتملة: {', '.join(missing_fields)}"
            logger.error(error_msg)
            await query.answer(error_msg, show_alert=True)
            return

        try:
            # إظهار رسالة "جاري المعالجة"
            await query.message.edit_text("⏳ **جاري إنشاء العرض ونشره...**", parse_mode='Markdown')

            # إنشاء العرض في قاعدة البيانات أولاً
            logger.info(f"💾 إنشاء العرض في قاعدة البيانات...")

            # استخدام الدالة المحسنة لإنشاء واسترجاع العرض
            offer = db.create_and_get_offer(
                user_id=query.from_user.id,
                offer_type=offer_data['type'],
                amount=offer_data['amount'],
                exchange_rate=offer_data['exchange_rate'],
                payment_method=Config.PAYMENT_METHODS[offer_data['payment_method']]
            )

            if not offer:
                error_msg = "❌ فشل في إنشاء العرض في قاعدة البيانات"
                logger.error(error_msg)
                await query.message.edit_text(error_msg)
                return

            offer_id = offer['id']
            logger.info(f"✅ تم إنشاء واسترجاع العرض: {offer_id}")

            # نشر العرض في القناة
            logger.info(f"📤 محاولة نشر العرض {offer_id} في القناة...")
            channel_message_id = await self.channel_manager.post_offer_to_channel(offer)

            if channel_message_id:
                # تحديث معرف الرسالة في قاعدة البيانات
                db.update_offer_message_id(offer_id, channel_message_id)
                logger.info(f"✅ تم تحديث معرف الرسالة في قاعدة البيانات: {channel_message_id}")

                success_text = f"""
✅ **تم إنشاء العرض بنجاح!**

📊 **تفاصيل العرض:**
• النوع: {'بيع' if offer_data['type'] == 'sell' else 'شراء'} USDT
• الكمية: {offer_data['amount']:,.2f} USDT
• السعر: {offer_data['exchange_rate']:,.2f}
• وسيلة الدفع: {Config.PAYMENT_METHODS[offer_data['payment_method']]}

⚡ **تم نشر العرض في القناة وسيتمكن الأعضاء من رؤيته والتفاعل معه.**
                """
            else:
                success_text = f"""
⚠️ **تم إنشاء العرض لكن حدث خطأ في النشر**

📊 **تفاصيل العرض:**
• النوع: {'بيع' if offer_data['type'] == 'sell' else 'شراء'} USDT
• الكمية: {offer_data['amount']:,.2f} USDT
• السعر: {offer_data['exchange_rate']:,.2f}
• وسيلة الدفع: {Config.PAYMENT_METHODS[offer_data['payment_method']]}

❌ **لم يتم نشره في القناة، يرجى التحقق من:**
1. إعدادات القناة في ملف .env
2. صلاحيات البوت في القناة
3. معرف القناة (يجب أن يبدأ بـ @)

💾 **تم حفظ العرض في النظام ويمكنك مشاهدته عبر /my_offers**
                """

        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء العرض: {e}")
            success_text = f"❌ **حدث خطأ في إنشاء العرض:** {str(e)}"

        finally:
            # تنظيف بيانات العرض
            if 'creating_offer' in context.user_data:
                del context.user_data['creating_offer']
                logger.info("🧹 تم تنظيف بيانات العرض من context")

        keyboard = [
            [InlineKeyboardButton("📋 عروضي", callback_data="my_offers")],
            [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(success_text, reply_markup=reply_markup, parse_mode='Markdown')
        logger.info("🎉 تم إنهاء عملية إنشاء العرض")

    async def main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """القائمة الرئيسية مع زر قائمة"""
        # التحقق من حالة البوت
        if not db.is_bot_active():
            await update.message.reply_text("⏸️ البوت معطل حالياً. يرجى المحاولة لاحقاً.")
            return

        # التحقق من انضمام المستخدم للقناة
        if not await self.require_channel_membership(update, context):
            return

        # إنشاء لوحة مفاتيح ReplyKeyboard (تظهر في الأسفل)

        keyboard = [
            [KeyboardButton("🚀 البدء")]
          ]


        # إضافة زر لوحة التحكم إذا كان أدمن
        if await self.is_admin(update.effective_user.id):
            keyboard.append([KeyboardButton("❌ إلغاء الصفقة الحالية")])
            keyboard.append([KeyboardButton("🛠️ لوحة التحكم")])

        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False  # تبقى ظاهرة حتى يتم إخفاؤها
        )

        text = """
    🏦 **القائمة الرئيسية - وساطة USDT**

    اختر من الخيارات أدناه:
    • 🚀 **البدء**: إنشاء عرض جديد للبيع أو الشراء

    ⚡ **طريقة العمل:**
    1. اضغط على "البدء" لإنشاء عرض جديد
    2. سيتم نشر عروضك في القناة
    3. تتم الصفقة عبر الوسيط لضمان الأمان
        """

        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def cancel_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء العملية الحالية"""
        query = update.callback_query
        await query.answer()

        # تنظيف بيانات المستخدم
        if 'creating_offer' in context.user_data:
            del context.user_data['creating_offer']
        if 'current_offer' in context.user_data:
            del context.user_data['current_offer']
        if 'current_trade_id' in context.user_data:
            del context.user_data['current_trade_id']

        await query.message.edit_text("❌ **تم الإلغاء**\n\nاستخدم /menu للعودة للقائمة الرئيسية")

    async def main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة العودة للقائمة الرئيسية"""
        query = update.callback_query
        await query.answer()

        keyboard = [
            [InlineKeyboardButton("📊 إنشاء عرض جديد", callback_data="create_offer")],
            [InlineKeyboardButton("📋 عروضي", callback_data="my_offers")],
            [InlineKeyboardButton("🔄 صفقاتي", callback_data="my_trades")],
            [InlineKeyboardButton("ℹ️ المساعدة", callback_data="support")],
        ]

        # إضافة زر المشرف إذا كان المستخدم مشرف
        if await self.is_admin(query.from_user.id):
            keyboard.append([InlineKeyboardButton("🛠️ لوحة التحكم", callback_data="admin_panel")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        text = """
🏦 **القائمة الرئيسية - وساطة USDT**

اختر من الخيارات أدناه:
• 📊 إنشاء عرض جديد: لعرض رغبتك في البيع أو الشراء
• 📋 عروضي: لعرض وإدارة عروضك السابقة
• 🔄 صفقاتي: لمتابعة الصفقات النشطة والمكتملة
• ℹ️ المساعدة: للحصول على الدعم والإرشادات
        """

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def my_offers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض عروض المستخدم"""
        if not await self.require_channel_membership(update, context):
            return

        user_id = update.effective_user.id
        offers = db.get_user_offers(user_id)

        if not offers:
            text = "📋 **عروضي**\n\nلا توجد عروض سابقة."
            await update.message.reply_text(text, parse_mode='Markdown')
            return

        text = "📋 **عروضي**\n\n"
        for offer in offers[:10]:
            status_icon = "🟢" if offer[6] == 'active' else "🔴"
            type_icon = "🟢 بيع" if offer[2] == 'sell' else "🔵 شراء"
            text += f"{status_icon} {type_icon}\n"
            text += f"الكمية: {offer[3]:,.2f} USDT\n"
            text += f"السعر: {offer[4]:,.2f}\n"
            text += f"الدفع: {offer[5]}\n"
            text += f"الحالة: {'نشط' if offer[6] == 'active' else 'غير نشط'}\n"
            text += "─" * 20 + "\n"

        await update.message.reply_text(text, parse_mode='Markdown')

    async def my_offers_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة عرض عروض المستخدم عبر الاستعلام"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        offers = db.get_user_offers(user_id)

        if not offers:
            text = "📋 **عروضي**\n\nلا توجد عروض سابقة."
            await query.message.edit_text(text, parse_mode='Markdown')
            return

        text = "📋 **عروضي**\n\n"
        for offer in offers[:10]:
            status_icon = "🟢" if offer[6] == 'active' else "🔴"
            type_icon = "🟢 بيع" if offer[2] == 'sell' else "🔵 شراء"
            text += f"{status_icon} {type_icon}\n"
            text += f"الكمية: {offer[3]:,.2f} USDT\n"
            text += f"السعر: {offer[4]:,.2f}\n"
            text += f"الدفع: {offer[5]}\n"
            text += f"الحالة: {'نشط' if offer[6] == 'active' else 'غير نشط'}\n"
            text += "─" * 20 + "\n"

        await query.message.edit_text(text, parse_mode='Markdown')

    async def my_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض صفقات المستخدم"""
        if not await self.require_channel_membership(update, context):
            return

        user_id = update.effective_user.id
        trades = db.get_user_trades(user_id)

        if not trades:
            text = "🔄 **صفقاتي**\n\nلا توجد صفقات سابقة."
            await update.message.reply_text(text, parse_mode='Markdown')
            return

        text = "🔄 **صفقاتي**\n\n"
        for trade in trades[:10]:
            status_icons = {
                Config.STATUS_PENDING: '🟡',
                Config.STATUS_WAITING_PAYMENT: '🟠',
                Config.STATUS_CONFIRMED: '🔵',
                Config.STATUS_USDT_SENT: '🟣',
                Config.STATUS_WAITING_USDT_SEND: '🟢',
                Config.STATUS_USDT_SENT_TO_BUYER: '🟢',
                Config.STATUS_COMPLETED: '🟢',
                Config.STATUS_CANCELLED: '🔴'
            }
            status_icon = status_icons.get(trade[11], '⚪')

            if user_id == trade[2]:
                role = "👤 مشتري"
            else:
                role = "👥 بائع"

            text += f"{status_icon} #{trade[0]} - {role}\n"
            text += f"الكمية: {trade[5]:,.2f} USDT\n"
            text += f"الحالة: {self.get_status_text(trade[11])}\n"
            text += "─" * 20 + "\n"

        await update.message.reply_text(text, parse_mode='Markdown')

    async def my_trades_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة عرض صفقات المستخدم عبر الاستعلام"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        trades = db.get_user_trades(user_id)

        if not trades:
            text = "🔄 **صفقاتي**\n\nلا توجد صفقات سابقة."
            await query.message.edit_text(text, parse_mode='Markdown')
            return

        text = "🔄 **صفقاتي**\n\n"
        for trade in trades[:10]:
            status_icons = {
                Config.STATUS_PENDING: '🟡',
                Config.STATUS_WAITING_PAYMENT: '🟠',
                Config.STATUS_CONFIRMED: '🔵',
                Config.STATUS_USDT_SENT: '🟣',
                Config.STATUS_WAITING_USDT_SEND: '🟢',
                Config.STATUS_USDT_SENT_TO_BUYER: '🟢',
                Config.STATUS_COMPLETED: '🟢',
                Config.STATUS_CANCELLED: '🔴'
            }
            status_icon = status_icons.get(trade[11], '⚪')

            if user_id == trade[2]:
                role = "👤 مشتري"
            else:
                role = "👥 بائع"

            text += f"{status_icon} #{trade[0]} - {role}\n"
            text += f"الكمية: {trade[5]:,.2f} USDT\n"
            text += f"الحالة: {self.get_status_text(trade[11])}\n"
            text += "─" * 20 + "\n"

        await query.message.edit_text(text, parse_mode='Markdown')

    def get_status_text(self, status):
        """ترجمة حالة الصفقة - النسخة المصححة"""
        status_texts = {
            Config.STATUS_PENDING: "بانتظار البدء",
            Config.STATUS_WAITING_PAYMENT: "بانتظار الدفع",
            Config.STATUS_CONFIRMED: "تم التأكيد",
            Config.STATUS_USDT_SENT: "تم إرسال USDT",
            Config.STATUS_WAITING_USDT_SEND: "بانتظار إرسال USDT",
            Config.STATUS_USDT_SENT_TO_BUYER: "تم إرسال USDT للمشتري",
            Config.STATUS_COMPLETED: "مكتملة",
            Config.STATUS_CANCELLED: "ملغية",
            Config.STATUS_WAITING_PROOF: "بانتظار مستند الإرسال",
            Config.STATUS_PROOF_RECEIVED: "تم استلام المستند",
            Config.STATUS_WAITING_PAYMENT_DETAILS: "بانتظار تفاصيل الدفع",
            Config.STATUS_PAYMENT_DETAILS_SENT: "تم إرسال تفاصيل الدفع"
        }
        return status_texts.get(status, status)

    async def create_offer_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء عملية إنشاء عرض جديد"""
        query = update.callback_query
        await query.answer()

        # التحقق من وقت عمل البوت
        if not await self.check_bot_working_hours(query.from_user.id):
            await query.answer("⏰ لا يمكن إنشاء عروض جديدة خارج وقت العمل (8 صباحاً - 12 منتصف الليل)", show_alert=True)
            return

        if not await self.require_channel_membership(update, context):
            return

        keyboard = [
            [InlineKeyboardButton("🟢 بيع USDT", callback_data="offer_type_sell")],
            [InlineKeyboardButton("🔵 شراء USDT", callback_data="offer_type_buy")],
            [InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = """
📊 **إنشاء عرض جديد**

اختر نوع العرض:
• 🟢 **بيع USDT**: لديك USDT وتريد بيعه
• 🔵 **شراء USDT**: تريد شراء USDT

⚡ **ملاحظة:** سيتم نشر عرضك في القناة وسيراه جميع الأعضاء
        """

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_offer_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار نوع العرض"""
        query = update.callback_query
        await query.answer()

        offer_type = query.data.split('_')[2]

        # حفظ نوع العرض في بيانات المستخدم
        context.user_data['creating_offer'] = {
            'type': offer_type
        }

        await query.message.edit_text(
            f"📝 **أدخل تفاصيل العرض**\n\n"
            f"أنت تريد **{'بيع' if offer_type == 'sell' else 'شراء'} USDT**\n\n"
            f"الآن أدخل الكمية (مثال: 1000):",
            parse_mode='Markdown'
        )

    async def request_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE, offer_id: int):
        """طلب مشاركة جهة الاتصال"""
        query = update.callback_query
        await query.answer()

        contact_text = """
📞 **مشاركة جهة الاتصال**

يجب مشاركة جهة اتصالك للمتابعة في الصفقة:

اضغط على الزر أدناه لمشاركة جهة الاتصال:
        """

        contact_keyboard = [[KeyboardButton("📞 مشاركة جهة الاتصال", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(contact_keyboard, resize_keyboard=True, one_time_keyboard=True)

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=contact_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        await query.message.edit_text(
            "📞 **تم إرسال طلب مشاركة جهة الاتصال**\n\n"
            "يرجى التحقق من الدردشة مع البوت ومشاركة جهة الاتصال.",
            parse_mode='Markdown'
        )

    async def check_membership_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """التحقق من الانضمام للقناة عبر الاستعلام"""
        query = update.callback_query
        await query.answer()

        is_member = await self.check_channel_membership(query.from_user.id)

        if is_member:
            await query.message.edit_text(
                "✅ **تم التحقق من الانضمام للقناة**\n\n"
                "استخدم /menu للبدء",
                parse_mode='Markdown'
            )
        else:
            await query.answer("❌ لم يتم الانضمام للقناة بعد", show_alert=True)

    async def support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض معلومات المساعدة"""
        query = update.callback_query
        await query.answer()

        text = """
ℹ️ **مركز المساعدة**

📖 **كيفية الاستخدام:**
1. أنشئ عرضاً للبيع أو الشراء
2. شاهد العروض في القناة
3. انقر على أي عرض للبدء بالصفقة
4. اتبع التعليمات لإتمام الصفقة

🛡️ **ضمان الأمان:**
• جميع الصفقات تتم عبر وسيط
• تحويل الأموال مؤمن
• مستندات الدفع محفوظة

📞 **للتواصل والدعم:**
@username

⚡ **نعمل على تقديم أفضل خدمة لكم**
        """

        keyboard = [[InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # === لوحة تحكم المشرف ===

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لوحة تحكم المشرف"""
        user_id = update.effective_user.id

        # التحقق من صلاحية المشرف
        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ ليس لديك صلاحية للوصول لهذه اللوحة")
            return

        text = """
🛠️ **لوحة تحكم المشرف**

اختر الإعداد الذي تريد تعديله:
"""

        keyboard = [
            [InlineKeyboardButton("💰 إعدادات العمولة", callback_data="admin_commission")],
            [InlineKeyboardButton("💸 عمولة التحويل", callback_data="admin_transfer_fee")],
            [InlineKeyboardButton("📝 إدارة الرسائل", callback_data="admin_messages")],
            [InlineKeyboardButton("⚙️ إعدادات النظام", callback_data="admin_system")],
            [InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def admin_panel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة لوحة التحكم عبر الاستعلام"""
        query = update.callback_query
        await query.answer()

        text = """
    🛠️ **لوحة تحكم المشرف**

    اختر الإعداد الذي تريد تعديله:
    """

        keyboard = [
            [InlineKeyboardButton("📋 إدارة العروض", callback_data="admin_offers")],
            [InlineKeyboardButton("💰 إعدادات العمولة", callback_data="admin_commission")],
            [InlineKeyboardButton("💸 عمولة التحويل", callback_data="admin_transfer_fee")],
            [InlineKeyboardButton("⚙️ إعدادات النظام", callback_data="admin_system")],
            [InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("📋 آخر 20 صفقة", callback_data="recent_trades")],  # الزر الجديد
            [InlineKeyboardButton("⏰ تعطيل جميع العروض", callback_data="expire_offers")],
            [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_commission_settings(self, query, context: ContextTypes.DEFAULT_TYPE):
        """عرض إعدادات العمولة الثابتة"""
        small_amount_limit = db.get_commission_small_amount()
        small_commission = db.get_commission_small()
        large_commission = db.get_commission_large()
        transfer_fee = db.get_transfer_fee()

        text = f"""
💰 **إعدادات العمولة الثابتة**

📊 **الإعدادات الحالية:**
• حد المبالغ الصغيرة: {small_amount_limit:,.2f} USDT
• عمولة المبالغ الصغيرة (≤ {small_amount_limit:,.2f} USDT): ${small_commission:.2f}
• عمولة المبالغ الكبيرة (> {small_amount_limit:,.2f} USDT): ${large_commission:.2f}
• عمولة التحويل: ${transfer_fee:.2f}

💡 **مثال:**
• صفقة 20 USDT: ${small_commission + transfer_fee:.2f}
• صفقة 50 USDT: ${large_commission + transfer_fee:.2f}

اختر الإجراء:
"""

        keyboard = [
            [InlineKeyboardButton("✏️ تعديل إعدادات العمولة", callback_data="edit_commission_settings")],
            [InlineKeyboardButton("📊 عرض الإحصائيات", callback_data="commission_stats")],
            [InlineKeyboardButton("↩️ رجوع", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def edit_commission_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """طلب تعديل إعدادات العمولة"""
        query = update.callback_query
        await query.answer()

        current_small_amount = db.get_commission_small_amount()
        current_small_commission = db.get_commission_small()
        current_large_commission = db.get_commission_large()

        text = f"""
✏️ **تعديل إعدادات العمولة الثابتة**

📝 **أرسل القيم الجديدة بالتنسيق التالي:**
`الحد_الأقصى عمولة_الصغيرة عمولة_الكبيرة`

**مثال:**
`30 0.15 0.25`

**القيم الحالية:**
• الحد الأقصى: {current_small_amount:,.2f} USDT
• عمولة الصغيرة: ${current_small_commission:.2f}
• عمولة الكبيرة: ${current_large_commission:.2f}

⚡ **ملاحظة:** استخدم النقطة للكسور العشرية
"""

        await query.message.edit_text(text, parse_mode='Markdown')
        context.user_data['awaiting_commission_settings'] = True

    async def show_transfer_fee_settings(self, query, context: ContextTypes.DEFAULT_TYPE):
        """عرض إعدادات عمولة التحويل"""
        current_fee = db.get_transfer_fee()

        text = f"""
💸 **إعدادات عمولة التحويل بين المحافظ**

عمولة التحويل الحالية: ${current_fee:.2f}
(تؤخذ من البائع فقط)

اختر الإجراء:
"""

        keyboard = [
            [InlineKeyboardButton("✏️ تعديل عمولة التحويل", callback_data="set_transfer_fee_prompt")],
            [InlineKeyboardButton("↩️ رجوع", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def set_commission_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تعديل قيمة العمولة"""
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            "💰 **تعديل العمولة**\n\n"
            "أرسل قيمة العمولة الجديدة (مثال: 0.000625):\n"
            "ملاحظة: هذه القيمة لكل 1 USDT",
            parse_mode='Markdown'
        )

        context.user_data['awaiting_commission'] = True

    async def set_transfer_fee_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تعديل قيمة عمولة التحويل"""
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            "💸 **تعديل عمولة التحويل**\n\n"
            "أرسل قيمة عمولة التحويل الجديدة (مثال: 0.50):\n"
            "ملاحظة: هذه القيمة بالدولار وتؤخذ من البائع فقط",
            parse_mode='Markdown'
        )

        context.user_data['awaiting_transfer_fee'] = True

    async def show_message_settings(self, query, context: ContextTypes.DEFAULT_TYPE):
        """عرض إعدادات الرسائل"""
        messages = db.get_all_messages()

        text = "📝 **إدارة الرسائل**\n\n"

        keyboard = []
        for msg_key, msg_text, description in messages:
            # تقصير النص المعروض
            display_text = msg_text[:30] + "..." if len(msg_text) > 30 else msg_text
            keyboard.append([InlineKeyboardButton(
                f"✏️ {description}",
                callback_data=f"edit_message_{msg_key}"
            )])

        keyboard.append([InlineKeyboardButton("↩️ رجوع", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def edit_message_prompt(self, query, context: ContextTypes.DEFAULT_TYPE, message_key: str):
        """طلب تعديل رسالة"""
        current_message = db.get_message(message_key)

        await query.message.edit_text(
            f"📝 **تعديل الرسالة**\n\n"
            f"المفتاح: {message_key}\n"
            f"النص الحالي:\n{current_message}\n\n"
            f"أرسل النص الجديد:",
            parse_mode='Markdown'
        )

        context.user_data['editing_message'] = message_key

    async def show_system_settings(self, query, context: ContextTypes.DEFAULT_TYPE):
        """عرض إعدادات النظام"""
        bot_active = db.is_bot_active()
        status_icon = "🟢" if bot_active else "🔴"

        text = f"""
⚙️ **إعدادات النظام**

{status_icon} حالة البوت: {'مفعل' if bot_active else 'معطل'}

اختر الإجراء:
"""

        keyboard = [
            [InlineKeyboardButton(
                "⏸️ تعطيل البوت" if bot_active else "▶️ تفعيل البوت",
                callback_data="toggle_bot_status"
            )],
            [InlineKeyboardButton("↩️ رجوع", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def toggle_bot_status(self, query, context: ContextTypes.DEFAULT_TYPE):
        """تبديل حالة البوت"""
        current_status = db.is_bot_active()
        new_status = not current_status

        db.update_setting('bot_active', str(new_status).lower())

        status_text = "مفعل" if new_status else "معطل"
        await query.answer(f"✅ تم {status_text} البوت", show_alert=True)
        await self.show_system_settings(query, context)

    async def show_admin_stats(self, query, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات المشرف"""
        cursor = db.conn.cursor()

        # إحصائيات المستخدمين
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        # إحصائيات العروض
        cursor.execute('SELECT COUNT(*) FROM offers')
        total_offers = cursor.fetchone()[0]

        # إحصائيات الصفقات
        cursor.execute('SELECT COUNT(*) FROM trades')
        total_trades = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(commission) FROM trades WHERE status = ?', (Config.STATUS_COMPLETED,))
        total_commission = cursor.fetchone()[0] or 0

        text = f"""
📊 **إحصائيات النظام**

👥 **المستخدمين:** {total_users}
📋 **العروض:** {total_offers}
🔄 **الصفقات:** {total_trades}
💰 **إجمالي العمولات:** ${total_commission:,.2f}

🟢 **البوت يعمل بشكل طبيعي**
"""

        keyboard = [[InlineKeyboardButton("↩️ رجوع", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_commission_stats(self, query, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات العمولة"""
        cursor = db.conn.cursor()

        cursor.execute('''
            SELECT COUNT(*), SUM(commission)
            FROM trades
            WHERE status = ? AND created_at >= date('now', '-30 days')
        ''', (Config.STATUS_COMPLETED,))

        monthly_stats = cursor.fetchone()
        monthly_trades = monthly_stats[0] or 0
        monthly_commission = monthly_stats[1] or 0

        current_small_amount = db.get_commission_small_amount()
        current_small_commission = db.get_commission_small()
        current_large_commission = db.get_commission_large()
        current_transfer_fee = db.get_transfer_fee()

        text = f"""
📈 **إحصائيات العمولة**

💰 **الإعدادات الحالية:**
• حد المبالغ الصغيرة: {current_small_amount:,.2f} USDT
• عمولة الصغيرة: ${current_small_commission:.2f}
• عمولة الكبيرة: ${current_large_commission:.2f}
• عمولة التحويل: ${current_transfer_fee:.2f}

📅 **الصفقات هذا الشهر:** {monthly_trades}
💵 **إجمالي العمولات الشهرية:** ${monthly_commission:,.2f}

"""

        keyboard = [[InlineKeyboardButton("↩️ رجوع", callback_data="admin_commission")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def cleanup_trade_documents(self, trade_id: int):
        """حذف المستندات والصور المرتبطة بالصفقة"""
        try:
            trade = db.get_trade(trade_id)
            if not trade:
                return

            # حذف ملف إثبات الدفع إذا كان موجوداً
            if trade.get('payment_proof'):
                try:
                    await self.application.bot.delete_message(
                        chat_id=trade['buyer_id'],
                        message_id=trade['payment_proof']
                    )
                except Exception as e:
                    logger.warning(f"⚠️ لا يمكن حذف إثبات الدفع: {e}")

            logger.info(f"🧹 تم تنظيف مستندات الصفقة #{trade_id}")

        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف مستندات الصفقة: {e}")

    async def expire_all_offers_manual(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تعطيل جميع العروض يدوياً - النسخة المصححة"""
        query = update.callback_query
        await query.answer()

        # التحقق من أن المستخدم هو المشرف
        if not await self.is_admin(query.from_user.id):
            await query.answer("❌ فقط المشرف يمكنه تعطيل العروض", show_alert=True)
            return

        try:
            # إظهار رسالة معالجة
            await query.message.edit_text("⏳ **جاري تعطيل جميع العروض النشطة...**", parse_mode='Markdown')

            # استخدام دالة ChannelManager لتعطيل العروض
            expired_count = await self.channel_manager.expire_all_channel_offers()

            if expired_count > 0:
                success_text = f"✅ **تم تعطيل جميع العروض بنجاح**\n\nتم تعطيل {expired_count} عرض في القناة."

                # إشعار للمستخدمين الذين لديهم عروض نشطة
                cursor = db.conn.cursor()
                cursor.execute('SELECT DISTINCT user_id FROM offers WHERE status = "expired" AND updated_at > datetime("now", "-1 minute")')
                affected_users = cursor.fetchall()

                for (user_id,) in affected_users:
                    try:
                        await context.bot.send_message(
                            user_id,
                            "🔔 **إشعار مهم**\n\n"
                            "تم تعطيل جميع العروض النشطة في النظام.\n"
                            "العروض الجديدة ستكون متاحة من 8 صباحاً.\n\n"
                            "شكراً لتفهمكم.",
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.error(f"فشل في إرسال إشعار للمستخدم {user_id}: {e}")

            else:
                success_text = "✅ **تم تعطيل جميع العروض**\n\nلم تكن هناك عروض نشطة لتعطيلها."

            keyboard = [[InlineKeyboardButton("↩️ رجوع", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(success_text, reply_markup=reply_markup, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"❌ خطأ في تعطيل العروض: {e}")
            await query.answer("❌ حدث خطأ في تعطيل العروض", show_alert=True)
            await self.admin_panel_callback(update, context)

    async def broker_confirm_usdt(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """تأكيد الوسيط لاستلام USDT - النسخة المحدثة"""
        query = update.callback_query
        await query.answer()

        # التحقق من أن المستخدم هو المشرف
        if not await self.is_admin(query.from_user.id):
            await query.answer("❌ فقط المشرف يمكنه تأكيد الاستلام", show_alert=True)
            return

        # تحديث حالة الصفقة إلى انتظار تفاصيل الدفع
        db.update_trade_status(trade_id, Config.STATUS_WAITING_PAYMENT_DETAILS)

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # إشعار البائع لإرسال تفاصيل الدفع
        seller_id = trade['seller_id']
        seller_info = f"""
    💰 **يرجى إرسال تفاصيل حساب الدفع للمشتري**

    📋 **الصفقة #{trade_id}**
    • الكمية: {trade['amount']:,.2f} USDT
    • المبلغ المستحق: {trade['amount'] * trade['exchange_rate']:,.2f}
    • وسيلة الدفع: {db.get_offer(trade['offer_id'])['payment_method']}

    📝 **أرسل رقم الحساب أو معلومات الدفع التي سيستخدمها المشتري للدفع لك:**

    ⚡ **سيتم إرسال هذه المعلومات للمشتري ليقوم بالدفع**
    """

        keyboard = [
            [InlineKeyboardButton("📤 إرسال تفاصيل الدفع", callback_data=f"send_payment_details_{trade_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_trade_{trade_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await context.bot.send_message(
                seller_id,
                seller_info,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"فشل في إشعار البائع: {e}")

        # إشعار المشتري
        buyer_id = trade['buyer_id']
        try:
            await context.bot.send_message(
                buyer_id,
                f"✅ **تم تأكيد استلام USDT من الوسيط**\n\n"
                f"الصفقة #{trade_id} في انتظار إرسال البائع لتفاصيل الدفع...",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"فشل في إشعار المشتري: {e}")

        await query.message.edit_text(
            "✅ **تم تأكيد استلام USDT**\n\n"
            "تم طلب تفاصيل الدفع من البائع.",
            parse_mode='Markdown'
        )

    async def send_payment_details_to_buyer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """طلب إرسال تفاصيل الدفع من البائع"""
        query = update.callback_query
        await query.answer()

        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # التحقق من أن المستخدم هو البائع
        if query.from_user.id != trade['seller_id']:
            await query.answer("❌ فقط البائع يمكنه إرسال تفاصيل الدفع", show_alert=True)
            return

        await query.message.edit_text(
            "💳 **أرسل تفاصيل حساب الدفع:**\n\n"
            "• رقم الحساب / رقم الهاتف\n"
            "• اسم المستخدم (إذا كان مطلوباً)\n"
            "• أي معلومات أخرى يحتاجها المشتري للدفع\n\n"
            "⚡ **سيتم إرسال هذه المعلومات مباشرة للمشتري**",
            parse_mode='Markdown'
        )

        # حفظ معرف الصفقة في بيانات المستخدم
        context.user_data['awaiting_payment_details'] = trade_id

    async def handle_payment_details_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة رسالة تفاصيل الدفع من البائع - النسخة المحسنة"""
        user_id = update.effective_user.id
        payment_details = update.message.text

        if 'awaiting_payment_details' not in context.user_data:
            await update.message.reply_text("❌ لا توجد عملية انتظار لتفاصيل الدفع")
            return

        trade_id = context.user_data['awaiting_payment_details']
        trade = db.get_trade(trade_id)

        if not trade or trade['seller_id'] != user_id:
            await update.message.reply_text("❌ خطأ في معالجة البيانات")
            return

        # تحديث حالة الصفقة
        db.update_trade_status(trade_id, Config.STATUS_PAYMENT_DETAILS_SENT)

        # إرسال تفاصيل الدفع للمشتري بشكل قابل للنسخ
        buyer_id = trade['buyer_id']
        payment_info = f"""
    💳 **تفاصيل الدفع من البائع**

    📋 **الصفقة #{trade_id}**
    • الكمية: {trade['amount']:,.2f} USDT
    • المبلغ المستحق: `{trade['amount'] * trade['exchange_rate']:,.2f}`
    • وسيلة الدفع: {db.get_offer(trade['offer_id'])['payment_method']}

    📝 **معلومات الدفع:**
     `{payment_details}`

    💡 **يمكنك نسخ المعلومات بالضغط عليها**

    💸 **بعد التحويل، اضغط على تأكيد الدفع:**
    """

        keyboard = [
            [InlineKeyboardButton("✅ تأكيد الدفع", callback_data=f"confirm_payment_details_{trade_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_trade_{trade_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await context.bot.send_message(
                buyer_id,
                payment_info,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم إرسال تفاصيل الدفع للمشتري للصفقة #{trade_id}")
        except Exception as e:
            logger.error(f"❌ فشل في إرسال تفاصيل الدفع للمشتري: {e}")
            await update.message.reply_text("❌ فشل في إرسال التفاصيل للمشتري")
            return

        # تأكيد للبائع
        await update.message.reply_text(
            "✅ **تم إرسال تفاصيل الدفع للمشتري**\n\n"
            "بانتظار تأكيد الدفع من المشتري...",
            parse_mode='Markdown'
        )

        # تنظيف البيانات المؤقتة
        del context.user_data['awaiting_payment_details']

        # إشعار الوسيط
        if Config.ADMIN_ID:
            broker_text = f"""
    🔔 **تم إرسال تفاصيل الدفع للصفقة #{trade_id}**

    📋 **الحالة:** بانتظار تأكيد الدفع من المشتري
    """
            await context.bot.send_message(Config.ADMIN_ID, broker_text, parse_mode='Markdown')

    async def confirm_payment_details_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
        """تأكيد استلام تفاصيل الدفع من المشتري - النسخة المصححة"""
        query = update.callback_query
        await query.answer()

        logger.info(f"✅ المشتري يؤكد استلام تفاصيل الدفع للصفقة #{trade_id}")
        logger.info(f"🔍 DEBUG: بدء confirm_payment_details_received مع trade_id: {trade_id} (نوع: {type(trade_id)})")
        trade = db.get_trade(trade_id)
        if not trade:
            await query.answer("❌ الصفقة غير موجودة", show_alert=True)
            return

        # التحقق من أن المستخدم هو المشتري
        if query.from_user.id != trade['buyer_id']:
            await query.answer("❌ فقط المشتري يمكنه تأكيد الاستلام", show_alert=True)
            return

        # تحديث حالة الصفقة إلى انتظار مستند الدفع
        db.update_trade_status(trade_id, Config.STATUS_WAITING_PAYMENT_PROOF)

        # طلب مستند الدفع من المشتري
        payment_request = f"""
    📤 **يرجى إرسال مستند الدفع الآن**

    📋 **الصفقة #{trade_id}**
    • المبلغ: {trade['amount'] * trade['exchange_rate']:,.2f}
    • وسيلة الدفع: {db.get_offer(trade['offer_id'])['payment_method']}

    💳 **أرسل صورة أو مستند إثبات الدفع:**
    • screenshot من تطبيق الدفع
    • إشعار التحويل
    • أي مستند يثبت عملية الدفع

    ⚡ **يمكنك إرسال الصورة أو المستند مباشرة في هذه المحادثة**
    """

        try:
            await context.bot.send_message(
                trade['buyer_id'],
                payment_request,
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم طلب مستند الدفع من المشتري للصفقة #{trade_id}")
        except Exception as e:
            logger.error(f"❌ فشل في طلب مستند الدفع: {e}")
            await query.answer("❌ فشل في إرسال الطلب", show_alert=True)
            return

        # إشعار البائع
        try:
            await context.bot.send_message(
                trade['seller_id'],
                f"✅ **المشتري أكد استلام تفاصيل الدفع**\n\n"
                f"الصفقة #{trade_id} في انتظار إرسال مستند الدفع...",
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم إشعار البائع بتأكيد استلام تفاصيل الدفع للصفقة #{trade_id}")
        except Exception as e:
            logger.error(f"❌ فشل في إشعار البائع: {e}")

        await query.message.edit_text(
            "✅ **تم تأكيد استلام تفاصيل الدفع**\n\n"
            "يرجى الآن إرسال مستند إثبات الدفع.",
            parse_mode='Markdown'
        )

        logger.info(f"🎉 اكتملت عملية تأكيد استلام تفاصيل الدفع للصفقة #{trade_id}")
    def extract_trade_id_from_callback(self, data: str, prefix: str) -> int:
        """استخراج trade_id من callback data - النسخة المصححة"""
        try:
            # إزالة البادئة وأخذ آخر جزء (الذي يجب أن يكون trade_id)
            trade_id_str = data.replace(prefix, "")

            # التحقق من أن النص المتبقي هو رقم فقط
            if not trade_id_str.isdigit():
                raise ValueError(f"القيمة '{trade_id_str}' ليست رقم صالح")

            return int(trade_id_str)

        except (ValueError, IndexError) as e:
            logger.error(f"❌ فشل في استخراج trade_id من {data}: {e}")
            raise ValueError(f"تنسيق callback غير صحيح: {data}")
    def safe_extract_trade_id(self, data: str, prefix: str) -> int:
        """استخراج آمن لـ trade_id من callback data"""
        try:
            logger.info(f"🔍 DEBUG: data='{data}', prefix='{prefix}'")

            # التحقق من أن البيانات تحتوي على البادئة
            if prefix not in data:
                raise ValueError(f"البادئة '{prefix}' غير موجودة في البيانات '{data}'")

            # استخراج الرقم من نهاية السلسلة
            # نبحث عن آخر مجموعة أرقام في السلسلة
            import re
            numbers = re.findall(r'\d+', data)

            logger.info(f"🔍 DEBUG: الأرقام الموجودة: {numbers}")

            if numbers:
                # نأخذ آخر رقم (الذي يجب أن يكون trade_id)
                trade_id_str = numbers[-1]
                trade_id = int(trade_id_str)
                logger.info(f"✅ تم استخراج trade_id: {trade_id}")
                return trade_id
            else:
                raise ValueError(f"لا توجد أرقام في: {data}")

        except Exception as e:
            logger.error(f"❌ فشل في استخراج trade_id: {e}")
            raise
    def run(self):
        """تشغيل البوت مع نظام التعافي"""
        try:
            # استعادة الصفقات النشطة بعد التشغيل
            import asyncio

            async def startup_tasks():
                """مهام بدء التشغيل"""
                logger.info("🔄 بدء مهام التعافي بعد التشغيل...")

                # استعادة الصفقات النشطة
                await self.recover_failed_trades()

                # إعداد الجدولة بعد تهيئة application
                self.setup_error_handling()

                # فحص صحة النظام
                await self.system_health_check()

                logger.info("✅ اكتملت مهام بدء التشغيل")

            # تشغيل مهام البدء
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # إذا كانت الحلقة تعمل بالفعل (في بيئة async)
                loop.create_task(startup_tasks())
            else:
                # إذا لم تكن الحلقة تعمل
                loop.run_until_complete(startup_tasks())

            # بدء التشغيل
            logger.info("🤖 Bot is starting with recovery system...")
            self.application.run_polling()

        except Exception as e:
            logger.critical(f"🚨 فشل تشغيل البوت: {e}")
            # محاولة الإغلاق الآمن
            asyncio.get_event_loop().run_until_complete(self.emergency_shutdown(f"فشل التشغيل: {e}"))


if __name__ == '__main__':
    bot = USDTBrokerBot()
    logger.info("🤖 Bot is starting...")
    bot.run()