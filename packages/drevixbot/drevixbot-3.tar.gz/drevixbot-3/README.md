# DrevixHub 10.0.0
المكتبة الرسمية لاستقبال رسائل البوتات في نظام Drevix.

## كيفية الاستخدام:
```python
from drevixhub import DrevixReceiver

bot = DrevixReceiver("TOKEN_BOT")
bot.listen("YOUR_TOKEN", callback=my_function)
