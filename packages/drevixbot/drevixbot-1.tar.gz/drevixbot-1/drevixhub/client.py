import requests
import time

class DrevixBot:
    def __init__(self, bot_token):
        # رابط قاعدة بياناتك ثابت ومحمي داخل المكتبة
        self.db_url = "https://test-e7f1b-default-rtdb.firebaseio.com"
        self.bot_token = bot_token
        # المسار المخصص لغرف الدردشة بناءً على هيكلة بياناتك
        self.base_path = f"{self.db_url}/chat_rooms/{self.bot_token}"

    def send_reply(self, user_id, message):
        """إرسال رد محمي: المكتبة تفرض هيكلة البيانات الصحيحة"""
        msg_id = f"msg_bot_{int(time.time()*1000)}"
        url = f"{self.base_path}/{user_id}/{msg_id}.json"
        
        data = {
            "msg": message,
            "sender": "bot", # يتم فرضه من المكتبة لمنع انتحال الهوية
            "timestamp": int(time.time() * 1000)
        }
        try:
            # الإرسال يتم مباشرة للمسار المحدد للبوت فقط
            res = requests.put(url, json=data)
            return res.status_code == 200
        except:
            return False

    def listen(self, callback):
        """بوابة الاستقبال: تراقب الرسائل الواردة من المستخدمين فقط"""
        print(f"🛡️ Drevix Secure Gate v11.0.0 | Active")
        print(f"📡 Monitoring Bot: {self.bot_token}")
        
        # فلتر زمني لتجنب معالجة الرسائل القديمة عند التشغيل
        last_time = int(time.time() * 1000)
        
        while True:
            try:
                # جلب البيانات من مسار البوت المحدد في chat_rooms
                response = requests.get(f"{self.base_path}.json")
                if response.status_code == 200 and response.json():
                    chats = response.json()
                    for user_id, messages in chats.items():
                        if isinstance(messages, dict):
                            for m_id, m_data in messages.items():
                                m_time = int(m_data.get('timestamp', 0))
                                # التحقق من أن المرسل مستخدم والرسالة جديدة
                                if m_data.get('sender') == 'user' and m_time > last_time:
                                    callback(user_id, m_data.get('msg'))
                                    last_time = m_time
            except:
                pass 
            
            time.sleep(2) # فحص كل ثانيتين لتقليل الضغط
