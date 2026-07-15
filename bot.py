import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# O'zingizning tokeningizni kiriting
TOKEN = '8892311555:AAFFfNYeG7yJc1BTPjp9PqHkgKh9Jpgp7UM'
bot = telebot.TeleBot(TOKEN)

# Foydalanuvchilarning post ma'lumotlarini vaqtinchalik saqlash uchun lug'at
user_state = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 Salom! Men professional post yaratuvchi botman.\n\n"
                                      "Menga rasm, video, ovozli xabar yoki shunchaki matn yuboring. "
                                      "Qanday shriftda (qalin, og'ish, ssilka) yozsangiz, xuddi shunday qabul qilaman!")

# Barcha turdagi xabarlarni qabul qilish (matn, rasm, video, audio, ovozli xabar)
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'audio', 'document'])
def receive_post(message):
    # Xabar ID sini saqlab qolamiz
    user_state[message.chat.id] = {'message_id': message.message_id}
    
    msg = bot.send_message(message.chat.id, "✅ Xabar qabul qilindi!\n\n"
                                            "Endi tugma qo'shish uchun quyidagi formatda yuboring:\n"
                                            "<b>Tugma nomi - https://havola.com</b>\n\n"
                                            "<i>Agar bir nechta tugma kerak bo'lsa, har birini yangi qatordan yozing. Tugma kerak bo'lmasa /skip ni bosing.</i>", 
                                            parse_mode="HTML")
    # Keyingi bosqichga o'tkazish
    bot.register_next_step_handler(msg, get_buttons)

def get_buttons(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup()
    
    if message.text != '/skip':
        try:
            # Tugmalarni qatorlarga ajratish va yaratish
            lines = message.text.split('\n')
            for line in lines:
                if '-' in line:
                    text, url = line.split('-', 1)
                    markup.add(InlineKeyboardButton(text=text.strip(), url=url.strip()))
            user_state[chat_id]['markup'] = markup
        except Exception:
            msg = bot.send_message(chat_id, "❌ Xatolik yuz berdi. Iltimos, formatni to'g'ri kiriting:\n"
                                            "Tugma matni - https://havola.com")
            bot.register_next_step_handler(msg, get_buttons)
            return
    else:
        user_state[chat_id]['markup'] = None

    msg = bot.send_message(chat_id, "Отлично! Tugmalar tayyor. 🎯\n\n"
                                    "Endi postni qaysi kanal yoki guruhga yuboramiz?\n"
                                    "Kanal belgisini yuboring (masalan, <b>@mening_kanalim</b> yoki ID orqali).\n\n"
                                    "⚠️ <i>Eslatma: Bot ushbu kanalda admin bo'lishi va xabar yuborish huquqiga ega bo'lishi shart!</i>", 
                                    parse_mode="HTML")
    bot.register_next_step_handler(msg, send_to_channel)

def send_to_channel(message):
    chat_id = message.chat.id
    channel_id = message.text.strip()
    
    if chat_id not in user_state:
        bot.send_message(chat_id, "Xatolik. Iltimos, /start ni bosing va boshidan boshlang.")
        return

    saved_msg_id = user_state[chat_id]['message_id']
    markup = user_state[chat_id].get('markup')

    try:
        # copy_message funksiyasi barcha shrift, media va formatlarni 100% o'zidek saqlaydi
        bot.copy_message(chat_id=channel_id, 
                         from_chat_id=chat_id, 
                         message_id=saved_msg_id, 
                         reply_markup=markup)
        bot.send_message(chat_id, "✅ Post kanalingizga muvaffaqiyatli yuborildi!")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Xatolik yuz berdi.\n\n"
                                  f"Sabablar bo'lishi mumkin:\n"
                                  f"1. Bot kanalda admin emas.\n"
                                  f"2. Kanal nomi noto'g'ri yozildi.\n\n"
                                  f"Texnik xato: {e}")

# Botni doimiy ishlab turishi uchun
if __name__ == '__main__':
    print("Bot ishga tushdi...")
    bot.infinity_polling()
