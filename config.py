# config.py - محدث بإضافة حالة جديدة للبائع
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
    CHANNEL_ID = os.getenv('CHANNEL_ID', '')

    # إعدادات العمولة الثابتة - قابلة للتعديل من لوحة التحكم
    COMMISSION_SMALL_AMOUNT = 30  # الحد الأقصى للمبالغ الصغيرة
    COMMISSION_SMALL = 0.15  # 15 سنت للمبالغ الصغيرة (<= 30 USDT)
    COMMISSION_LARGE = 0.25  # 0.25 USDT للمبالغ الكبيرة (> 30 USDT)
    TRANSFER_FEE = 0  # عمولة التحويل بين المحافظ (بالدولار)
    # إعدادات إدارة الأخطاء والتعافي
    TRADE_TIMEOUT_HOURS = 24  # 24 ساعة للصفقة
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 5
    BACKUP_RETENTION_DAYS = 7
    HEALTH_CHECK_INTERVAL = 20000  # ثانية
    # إعدادات التوقيت
    BOT_START_TIME = 5   # 8 صباحاً
    BOT_END_TIME = 21    # 12 منتصف الليل (0)

    # حالة البوت
    BOT_ACTIVE = True  # يمكن تعطيل البوت من لوحة التحكم

    # حالات الصفقات - محدثة
    # حالات الصفقة الإضافية


    STATUS_PENDING = 'pending'
    STATUS_WAITING_PAYMENT = 'WAITING_PAYMENT'
    STATUS_USDT_SENT = 'USDT_SENT'


    STATUS_CONFIRMED = 'confirmed'
    # إضافة هذه الحالات إلى قسم حالات الصفقات
    STATUS_WAITING_PAYMENT_PROOF = 'waiting_payment_proof'
    STATUS_WAITING_BROKER_PROOF = 'waiting_broker_proof'

    STATUS_WAITING_USDT_SEND = 'WAITING_USDT_SEND'
    STATUS_USDT_SENT_TO_BUYER = 'USDT_SENT_TO_BUYER'
    STATUS_COMPLETED = 'completed'
    STATUS_WAITING_SELLER_CONFIRMATION = 'waiting_seller_confirmation'
    STATUS_CANCELLED = 'cancelled'
    STATUS_EXPIRED = 'expired'
    STATUS_PROOF_RECEIVED = "proof_received"  # "تم استلام المستند"
    STATUS_WAITING_PROOF = "waiting_proof"
    STATUS_WAITING_PAYMENT_DETAILS = "waiting_payment_details"
    STATUS_PAYMENT_DETAILS_SENT = "payment_details_sent"

    # أنواع العروض
    OFFER_SELL = 'sell'
    OFFER_BUY = 'buy'

    # وسائل الدفع
    PAYMENT_METHODS = {
        'cham_cash': 'شام كاش (دولار)',
        'syriatel_cash':'سيرياتل كاش',
        'cham_cash_pound': 'شام كاش ليرة',
        'mtn_cash':'م تي ن كاش'
    }

    # إعدادات المحفظة
    BROKER_WALLET_ADDRESS = os.getenv('BROKER_WALLET_ADDRESS', '')
    BLOCKCHAIN_NETWORK = os.getenv('BLOCKCHAIN_NETWORK', 'BEP20')