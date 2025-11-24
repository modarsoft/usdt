# fix_trade_statuses.py
from database import db

def fix_trade_statuses():
    """إصلاح حالات الصفقات في قاعدة البيانات"""
    cursor = db.conn.cursor()
    
    # تحديث الحالات العربية إلى الإنجليزية
    status_mapping = {
        'معلق': 'pending',
        'في إنتظار الدفع': 'waiting_payment', 
        'تم إرسال ال USDT': 'usdt_sent',
        'تم التأكيد': 'confirmed',
        'في إنتظار إرسال ال USDT': 'waiting_usdt_send',
        'تم إرسال ال USDT للمشتري': 'usdt_sent_to_buyer', 
        'مكتملة': 'completed',
        'ملغاة': 'cancelled',
        'تم استلام المستند': 'proof_received'
    }
    
    for arabic_status, english_status in status_mapping.items():
        cursor.execute('UPDATE trades SET status = ? WHERE status = ?', (english_status, arabic_status))
        changes = cursor.rowcount
        if changes > 0:
            print(f"✅ تم تحديث {changes} صفقة من '{arabic_status}' إلى '{english_status}'")
    
    # أيضا تأكد من أن الحالات الإنجليزية صحيحة
    cursor.execute("UPDATE trades SET status = 'completed' WHERE status = 'completed'")
    
    db.conn.commit()
    print("🎉 تم إصلاح جميع حالات الصفقات")

if __name__ == '__main__':
    fix_trade_statuses()