# channel_manager.py - محدث بترقيم موحد للعروض ونظام التعطيل التلقائي ونظام العمولة الثابتة
import logging
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import Config
from database import db

from telegram import Update  # تأكد من وجود هذا

logger = logging.getLogger(__name__)

class ChannelManager:
    def __init__(self, application):
        self.application = application
    async def show_recent_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض آخر 20 صفقة مع روابط التواصل"""
        user_id = update.effective_user.id
        
        # التحقق من صلاحية المشرف
        
        
        try:
            # الحصول على آخر 20 صفقة
            recent_trades = db.get_recent_trades(20)
            
            if not recent_trades:
                await update.message.reply_text("❌ لا توجد صفقات لعرضها.")
                return
            
            message = "📊 **آخر 20 صفقة**\n\n"
            
            for i, trade in enumerate(recent_trades, 1):
                # معلومات البائع
                seller_info = f"👤 البائع: {trade['seller']['first_name']}"
                if trade['seller']['username']:
                    seller_info += f" @{trade['seller']['username']}"
                if trade['seller']['phone']:
                    seller_info += f" 📞 {trade['seller']['phone']}"
                
                # معلومات المشتري
                buyer_info = f"👤 المشتري: {trade['buyer']['first_name']}"
                if trade['buyer']['username']:
                    buyer_info += f" @{trade['buyer']['username']}"
                if trade['buyer']['phone']:
                    buyer_info += f" 📞 {trade['buyer']['phone']}"
                
                # حالة الصفقة
                status_icons = {
                    'pending': '⏳',
                    'waiting_payment_details': '💳',
                    'payment_details_sent': '📤',
                    'waiting_proof': '🔄',
                    'completed': '✅',
                    'cancelled': '❌'
                }
                status_icon = status_icons.get(trade['status'], '⚪')
                
                message += f"""**{status_icon} الصفقة #{trade['trade_id']}**

    💰 المبلغ: {trade['amount']:,.2f} USDT
    💱 سعر الصرف: {trade['exchange_rate']:,.2f}
    📅 التاريخ: {trade['created_at'][:16]}

    {seller_info}
    {buyer_info}

    ────────────────────
    """
            
            # إضافة أزرار للتحكم
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="refresh_recent_trades")],
                [InlineKeyboardButton("📋 العودة للوحة التحكم", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض الصفقات الأخيرة: {e}")
            await update.message.reply_text("❌ حدث خطأ في عرض الصفقات.")
    async def show_recent_trades_from_query(query, update:Update):
        """عرض الصفقات الأخيرة من استعلام"""
        
        query = update.callback_query
        try:
            recent_trades = db.get_recent_trades(20)
            
            if not recent_trades:
                await query.edit_message_text("❌ لا توجد صفقات لعرضها.")
                return
            
            message = "📊 **آخر 20 صفقة**\n\n"
            
            for i, trade in enumerate(recent_trades, 1):
                           # معلومات البائع
                seller_info = f"👤 البائع: {trade['seller']['first_name']}"
                if trade['seller']['username']:
                    seller_info += f" @{trade['seller']['username']}"
                if trade['seller']['phone']:
                    seller_info += f" 📞 {trade['seller']['phone']}"
                
                # معلومات المشتري
                buyer_info = f"👤 المشتري: {trade['buyer']['first_name']}"
                if trade['buyer']['username']:
                    buyer_info += f" @{trade['buyer']['username']}"
                if trade['buyer']['phone']:
                    buyer_info += f" 📞 {trade['buyer']['phone']}"
                
                # حالة الصفقة
                status_icons = {
                    'pending': '⏳',
                    'waiting_payment_details': '💳',
                    'payment_details_sent': '📤',
                    'waiting_proof': '🔄',
                    'completed': '✅',
                    'cancelled': '❌'
                }
                status_icon = status_icons.get(trade['status'], '⚪')
                
                message += f"""**{status_icon} الصفقة #{trade['trade_id']}**

    💰 المبلغ: {trade['amount']:,.2f} USDT
    💱 سعر الصرف: {trade['exchange_rate']:,.2f}
    📅 التاريخ: {trade['created_at'][:16]}

    {seller_info}
    {buyer_info}

    ────────────────────
    """
                    
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="refresh_recent_trades")],
                [InlineKeyboardButton("📋 العودة للوحة التحكم", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض الصفقات الأخيرة: {e}")
            await query.edit_message_text("❌ حدث خطأ في عرض الصفقات.")
    async def refresh_recent_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تحديث قائمة الصفقات الأخيرة"""
        query = update.callback_query
        await query.answer()
        
        try:
            # الحصول على آخر 20 صفقة
            recent_trades = db.get_recent_trades(20)
            
            if not recent_trades:
                await query.edit_message_text("❌ لا توجد صفقات لعرضها.")
                return
            
            message = "📊 **آخر 20 صفقة**\n\n"
            
            for i, trade in enumerate(recent_trades, 1):
                # معلومات البائع
                seller_info = f"👤 البائع: {trade['seller']['first_name']}"
                if trade['seller']['username']:
                    seller_info += f" @{trade['seller']['username']}"
                if trade['seller']['phone']:
                    seller_info += f" 📞 {trade['seller']['phone']}"
                
                # معلومات المشتري
                buyer_info = f"👤 المشتري: {trade['buyer']['first_name']}"
                if trade['buyer']['username']:
                    buyer_info += f" @{trade['buyer']['username']}"
                if trade['buyer']['phone']:
                    buyer_info += f" 📞 {trade['buyer']['phone']}"
                
                # حالة الصفقة
                status_icons = {
                    'pending': '⏳',
                    'waiting_payment_details': '💳',
                    'payment_details_sent': '📤',
                    'waiting_proof': '🔄',
                    'completed': '✅',
                    'cancelled': '❌'
                }
                status_icon = status_icons.get(trade['status'], '⚪')
                
                message += f"""**{status_icon} الصفقة #{trade['trade_id']}**

    💰 المبلغ: {trade['amount']:,.2f} USDT
    💱 سعر الصرف: {trade['exchange_rate']:,.2f}
    📅 التاريخ: {trade['created_at'][:16]}

    {seller_info}
    {buyer_info}

    ────────────────────
    """
            
            # إضافة أزرار للتحكم
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="refresh_recent_trades")],
                [InlineKeyboardButton("📋 العودة للوحة التحكم", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث الصفقات الأخيرة: {e}")
            await query.edit_message_text("❌ حدث خطأ في تحديث الصفقات.")
    async def post_offer_to_channel(self, offer_data):
        """نشر العرض في القناة مع الترقيم الموحد وتأثير الشطب"""
        try:
            # التحقق من وجود معرف القناة
            if not Config.CHANNEL_ID:
                logger.error("❌ CHANNEL_ID not configured")
                return None
            
            offer_id = offer_data['id']
            offer_type = offer_data['offer_type']
            amount = offer_data['amount']
            exchange_rate = offer_data['exchange_rate']
            payment_method = offer_data['payment_method']
            tier = offer_data.get('tier', 'silver')
            status = offer_data.get('status', 'active')
            
            # استخدام رقم العرض الحقيقي من قاعدة البيانات
            display_offer_id = offer_id
            
            # إذا كان العرض منتهياً أو منفذاً
            if status in ['expired', 'completed', 'in_trade']:
                if status == 'expired':
                    title = f"<s>❌ ~عرض منتهي~ USDT #{display_offer_id}</s>"
                    status_text = "<s>⏰ انتهى وقت العمل لهذا العرض</s>"
                elif status == 'completed':
                    title = f"<s>✅ ~عرض منفذ~ USDT #{display_offer_id}"
                    status_text = "<s>🎉 تم تنفيذ هذا العرض بنجاح</s>"
                else:  # in_trade
                    title = f"⏳ ~عرض قيد الصفقة~ USDT #{display_offer_id}"
                    status_text = "⚡ هذا العرض قيد التنفيذ حالياً"
                
                # نص مع تأثير الشطب
                message_text = f"""
{title}

<s>الكمية:** {amount:,.2f} USDT</s>
<s>سعر الصرف:** {exchange_rate:,.2f}</s>
<s>وسيلة الدفع:** {payment_method}</s>
<s>فئة العميل:** {tier}</s>

{status_text}
🔴 **غير متاح للصفقات الجديدة**
                """
                
                try:
                    if offer_data.get('channel_message_id'):
                        await self.application.bot.edit_message_text(
                            chat_id=Config.CHANNEL_ID,
                            message_id=offer_data['channel_message_id'],
                            text=message_text,
                            parse_mode='HTML'
                        )
                        logger.info(f"✅ تم تحديث العرض في القناة: #{display_offer_id} - الحالة: {status}")
                    return offer_data.get('channel_message_id')
                except Exception as e:
                    logger.error(f"❌ خطأ في تحديث العرض: {e}")
                    return None
            
            # عرض نشط
            if offer_type == Config.OFFER_SELL:
                title = f"🟢 عرض بيع USDT #{display_offer_id}"
                action_text = "شراء"
                action_callback = f"buy_{offer_id}"
            else:
                title = f"🔵 عرض شراء USDT #{display_offer_id}"
                action_text = "بيع"
                action_callback = f"sell_{offer_id}"
            
            # حساب العمولة باستخدام النظام الجديد
            commission = db.calculate_commission(amount)
            
            message_text = f"""
{title}

**الكمية:** {amount:,.2f} USDT
**سعر الصرف:**{exchange_rate:,.2f}
**وسيلة الدفع:** {payment_method}
**العمولة:** ${commission:.2f} (بدون مصاريف التحويل)
**فئة العميل:** {tier}  

إذا كنت تريد {action_text} اضغط الآن
"""
            
            keyboard = [
                [InlineKeyboardButton(f"🛒 {action_text} الآن", callback_data=action_callback)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            channel_message_id = offer_data.get('channel_message_id')
            
            logger.info(f"📤 محاولة النشر في القناة: {Config.CHANNEL_ID} - العرض #{display_offer_id}")
            
            if channel_message_id:
                # تحديث الرسالة الموجودة
                try:
                    await self.application.bot.edit_message_text(
                        chat_id=Config.CHANNEL_ID,
                        message_id=channel_message_id,
                        text=message_text,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    logger.info(f"✅ تم تحديث الرسالة في القناة: {channel_message_id} - العرض #{display_offer_id}")
                    return channel_message_id
                except Exception as e:
                    logger.error(f"❌ خطأ في تحديث الرسالة: {e}")
                    # إذا فشل التحديث، أنشئ رسالة جديدة
                    pass
            
            # إنشاء رسالة جديدة
            try:
                message = await self.application.bot.send_message(
                    chat_id=Config.CHANNEL_ID,
                    text=message_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                logger.info(f"✅ تم النشر بنجاح في القناة، معرف الرسالة: {message.message_id} - العرض #{display_offer_id}")
                return message.message_id
                
            except Exception as e:
                logger.error(f"❌ خطأ في النشر في القناة: {e}")
                return None
                
        except Exception as e:
            logger.error(f"❌ خطأ عام في نشر العرض: {e}")
            return None
    
    async def mark_trade_completed(self, trade_id):
            """وسم الصفقة كمكتملة في القناة مع تأثير الشطب"""
            try:
                if not Config.CHANNEL_ID:
                    return
                        
                trade = db.get_trade(trade_id)
                if trade and trade['offer_id']:
                    offer = db.get_offer(trade['offer_id'])
                    if offer and offer.get('channel_message_id'):
                        # استخدام رقم العرض الأصلي من قاعدة البيانات
                        original_offer_id = offer['id']
                        
                        # نص مع تأثير الشطب
                        completed_text = f"""
        <s>❌ ~عرض منفذ~ USDT #{original_offer_id}</s>

        <s>**الكمية:** {trade['amount']:,.2f} USDT</s>
        <s>**سعر الصرف:** {trade['exchange_rate']:,.2f}</s>
        <s>**وسيلة الدفع:** {offer['payment_method']}</s>

        <s>🎉 **تم إكمال الصفقة #{trade_id} بنجاح**</s>
        <s>🔴 **هذا العرض منفذ وغير متاح**</s>
                        """
                        
                        await self.application.bot.edit_message_text(
                            chat_id=Config.CHANNEL_ID,
                            message_id=offer['channel_message_id'],
                            text=completed_text,
                            parse_mode='HTML'
                        )
                        
                        # تحديث حالة العرض في قاعدة البيانات إلى مكتمل
                        cursor = db.conn.cursor()
                        cursor.execute('UPDATE offers SET status = ? WHERE id = ?', ('completed', offer['id']))
                        db.conn.commit()
                        
                        logger.info(f"✅ تم وضع علامة منفذ على العرض #{original_offer_id} في القناة")
            except Exception as e:
                logger.error(f"❌ خطأ في وضع علامة منفذ على العرض: {e}")
    async def mark_offer_expired(self, offer_id):
        """وسم العرض كمنتهي في القناة مع تأثير الشطب"""
        try:
            if not Config.CHANNEL_ID:
                return
                    
            offer = db.get_offer(offer_id)
            if offer and offer.get('channel_message_id'):
                # استخدام رقم العرض الحقيقي
                display_offer_id = offer['id']
                
                # نص مع تأثير الشطب
                expired_text = f"""
<s>❌ ~عرض منتهي~ USDT #{display_offer_id}</s>

<s>الكمية:** {offer['amount']:,.2f} USDT</s>
<s>سعر الصرف:** {offer['exchange_rate']:,.2f}</s>
<s>وسيلة الدفع:** {offer['payment_method']}</s>
<s>فئة العميل:** {offer.get('tier', 'silver')}</s>

⏰ <s>انتهى وقت العمل لهذا العرض</s>
🔴 **غير متاح للصفقات الجديدة**
                """
                
                await self.application.bot.edit_message_text(
                    chat_id=Config.CHANNEL_ID,
                    message_id=offer['channel_message_id'],
                    text=expired_text,
                    parse_mode='HTML'
                )
                
                # تحديث حالة العرض في قاعدة البيانات
                cursor = db.conn.cursor()
                cursor.execute('UPDATE offers SET status = ? WHERE id = ?', ('expired', offer_id))
                db.conn.commit()
                
                logger.info(f"✅ تم وضع علامة منتهي على العرض #{offer_id}")
        except Exception as e:
            logger.error(f"❌ خطأ في وضع علامة منتهي على العرض: {e}")
    
    async def expire_all_channel_offers(self):
        """تعطيل جميع العروض في القناة يدوياً أو عند منتصف الليل مع تأثير الشطب"""
        try:
            if not Config.CHANNEL_ID:
                logger.error("❌ CHANNEL_ID غير مضبوط")
                return 0
                
            # الحصول على جميع العروض النشطة
            cursor = db.conn.cursor()
            cursor.execute('SELECT id, channel_message_id, amount, exchange_rate, payment_method FROM offers WHERE status = "active"')
            active_offers = cursor.fetchall()
            
            expired_count = 0
            
            for offer in active_offers:
                offer_id, message_id, amount, exchange_rate, payment_method =offer
                
                if message_id:
                    try:
                        # استخدام رقم العرض الحقيقي
                        display_offer_id = offer_id
                        
                        # نص مع تأثير الشطب
                        expired_text = f"""
<s>❌ ~عرض منتهي~ USDT #{display_offer_id}</s>

<s>**الكمية:** {amount:,.2f} USDT</s>
<s>**سعر الصرف:** {exchange_rate:,.2f}</s>
<s>**وسيلة الدفع:** {payment_method}</s>


⏰ **انتهى وقت العمل لهذا العرض**
🔴 **العروض الجديدة ستكون متاحة من 8 صباحاً**
                        """
                        
                        await self.application.bot.edit_message_text(
                            chat_id=Config.CHANNEL_ID,
                            message_id=message_id,
                            text=expired_text,
                            parse_mode='HTML'
                        )
                        
                        # تحديث حالة العرض في قاعدة البيانات
                        cursor.execute('UPDATE offers SET status = ? WHERE id = ?', ('expired', offer_id))
                        
                        expired_count += 1
                        logger.info(f"✅ تم تعطيل العرض #{offer_id} في القناة")
                        
                    except Exception as e:
                        logger.error(f"❌ خطأ في تعطيل العرض #{offer_id}: {e}")
            
            # حفظ التغييرات في قاعدة البيانات
            db.conn.commit()
            logger.info(f"✅ تم تعطيل {expired_count} عرض في القناة")
            return expired_count
            
        except Exception as e:
            logger.error(f"❌ خطأ عام في تعطيل عروض القناة: {e}")
            return 0

    async def update_offer_status(self, offer_id, status):
        """تحديث حالة العرض في القناة مع تأثير الشطب"""
        try:
            offer = db.get_offer(offer_id)
            if offer and offer.get('channel_message_id'):
                if status == 'active':
                    await self.post_offer_to_channel(offer)
                elif status in ['expired', 'completed', 'in_trade']:
                    # تحديث العرض مباشرة بتأثير الشطب
                    offer['status'] = status
                    await self.post_offer_to_channel(offer)
                
                logger.info(f"✅ تم تحديث حالة العرض #{offer_id} إلى {status}")
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث حالة العرض: {e}")