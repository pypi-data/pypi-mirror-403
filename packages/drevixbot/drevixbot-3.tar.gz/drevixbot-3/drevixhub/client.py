import requests
import time

class DrevixBot:
    def __init__(self, bot_token):
        # ⚠️ أضفت https:// هنا لكي يعمل الرابط
        self.db_url = "https://drevixhub1-default-rtdb.firebaseio.com"
        self.bot_token = bot_token
        self.base_path = f"{self.db_url}/chat_rooms/{self.bot_token}"

    def send_reply(self, user_id, message):
        """إرسال رد محمي"""
        msg_id = f"msg_bot_{int(time.time()*1000)}"
        url = f"{self.base_path}/{user_id}/{msg_id}.json"
        
        data = {
            "msg": message,
            "sender": "bot", 
            "timestamp": int(time.time() * 1000)
        }
        try:
            res = requests.put(url, json=data)
            return res.status_code == 200
        except:
            return False

    def listen(self, callback):
        """بوابة الاستقبال"""
        print(f"🛡️ Drevix Secure Gate v11.0.0 | Active")
        print(f"📡 Monitoring Bot: {self.bot_token}")
        
        last_time = int(time.time() * 1000)
        
        while True:
            try:
                response = requests.get(f"{self.base_path}.json")
                if response.status_code == 200 and response.json():
                    chats = response.json()
                    for user_id, messages in chats.items():
                        if isinstance(messages, dict):
                            for m_id, m_data in messages.items():
                                m_time = int(m_data.get('timestamp', 0))
                                if m_data.get('sender') == 'user' and m_time > last_time:
                                    callback(user_id, m_data.get('msg'))
                                    last_time = m_time
            except:
                pass 
            
            time.sleep(2)
