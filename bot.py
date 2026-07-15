import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Bot tokeningiz
TOKEN = '8892311555:AAFFfNYeG7yJc1BTPjp9PqHkgKh9Jpgp7UM'
bot = telebot.TeleBot(TOKEN)

# Foydalanuvchi ma'lumotlarini saqlash uchun xotira
user_data = {}

def get_user_data(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {'channel': None, 'temp_post': None}
    return user_data[chat_id]

# Asosiy ekran tugmalari (Menu)
def main_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("📝 Yangi Post Yaratish")
    btn2 = KeyboardButton("📢 Kanalni Sozlash")
    btn3 = KeyboardButton("ℹ️ Yordam")
    markup.add(btn1, btn2, btn3)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    get_user_data(chat_id)
    bot.send_message(chat_id, "🤖 **Professional Admin Panelga xush kelibsiz!**\n\n"
                              "Pastdagi tugmalar orqali botni juda oson boshqarishingiz mumkin 👇", 
                     reply_markup=main_menu(), parse_mode="Markdown")

# --- KANALNI SOZLASH BO'LIMI ---
@bot.message_handler(func=lambda m: m.text == "📢 Kanalni Sozlash")
def set_channel_prompt(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "✍️ **Kanalingiz manzili yoki ID sini yuboring:**\n"
                                    "Misol uchun: `@mening_kanalim` yoki `-100123456789`\n\n"
                                    "⚠️ _Bot o'sha kanalda admin bo'lishi shart!_", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_channel)

def save_channel(message):
    chat_id = message.chat.id
    channel = message.text.strip()
    data = get_user_data(chat_id)
    data['channel'] = channel
    bot.send_message(chat_id, f"✅ **Kanal muvaffaqiyatli saqlandi!**\nPostlar endi to'g'ridan-to'g'ri shu kanalga ketadi: `{channel}`", 
                     reply_markup=main_menu(), parse_mode="Markdown")

# --- YANGI POST YARATISH BO'LIMI ---
@bot.message_handler(func=lambda m: m.text == "📝 Yangi Post Yaratish")
def new_post_prompt(message):
    chat_id = message.chat.id
    data = get_user_data(chat_id)
    
    if not data['channel']:
        bot.send_message(chat_id, "❌ **Avval kanalni sozlang!**\n'📢 Kanalni Sozlash' tugmasini bosing.", reply_markup=main_menu(), parse_mode="Markdown")
        return
    
    cancel_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ Bekor qilish"))
    msg = bot.send_message(chat_id, "📥 **Menga istalgan postni yuboring.**\n"
                                    "Bu rasm, video, audio, ovozli xabar yoki shunchaki formatlangan matn bo'lishi mumkin. Qanday yuborsangiz, xuddi shunday qabul qilaman:", 
                           reply_markup=cancel_kb, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_post)

def process_post(message):
    chat_id = message.chat.id
    if message.text == "❌ Bekor qilish":
        bot.send_message(chat_id, "Yaratish bekor qilindi.", reply_markup=main_menu())
        return

    data = get_user_data(chat_id)
    data['temp_post'] = {
        'message_id': message.message_id,
        'buttons': []  # Tugmalar ro'yxati
    }
    
    show_preview(chat_id)

# --- PREVIEW (KO'ZDAN KECHIRISH) VA BOSHQARUV PANEL ---
def show_preview(chat_id):
    data = get_user_data(chat_id)
    post = data['temp_post']
    
    # Inline tugmalarni shakllantirish
    markup = InlineKeyboardMarkup()
    
    # Foydalanuvchi qo'shgan tugmalar
    for btn in post['buttons']:
        markup.add(InlineKeyboardButton(text=btn['text'], url=btn['url']))
    
    # Boshqaruv paneli tugmalari
    markup.add(
        InlineKeyboardButton(text="➕ Tugma qo'shish", callback_data="add_btn"),
        InlineKeyboardButton(text="🧹 Tugmalarni tozalash", callback_data="clear_btns")
    )
    markup.add(
        InlineKeyboardButton(text="📤 Kanalga yuborish", callback_data="send_post"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_post")
    )
    
    bot.send_message(chat_id, "👀 **Post ko'rinishi (Preview):**\nPastdagi tugmalar orqali sozlang va kanalga yuboring:")
    bot.copy_message(chat_id=chat_id, from_chat_id=chat_id, message_id=post['message_id'], reply_markup=markup)

# --- TUGMA BOSILISHINI NAZORAT QILISH (CALLBACK) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = get_user_data(chat_id)
    
    if not data['temp_post']:
        bot.answer_callback_query(call.id, "Eski post ma'lumotlari topilmadi.")
        return

    if call.data == "add_btn":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "✍️ **Tugma ma'lumotini yuboring:**\n"
                                        "Format: `Tugma nomi - ssilka`\n"
                                        "Misol: `Kanalga a'zo bo'lish - https://t.me/mening_kanalim`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, add_button_to_list)
        
    elif call.data == "clear_btns":
        data['temp_post']['buttons'] = []
        bot.answer_callback_query(call.id, "Tugmalar tozalandi!")
        show_preview(chat_id)
        
    elif call.data == "cancel_post":
        data['temp_post'] = None
        bot.answer_callback_query(call.id, "Post o'chirildi.")
        bot.send_message(chat_id, "Bekor qilindi.", reply_markup=main_menu())
        
    elif call.data == "send_post":
        channel = data['channel']
        post = data['temp_post']
        
        # Faqat foydalanuvchi yaratgan tugmalarni kanalga jo'natish (boshqaruv tugmalarisiz)
        channel_markup = InlineKeyboardMarkup()
        for btn in post['buttons']:
            channel_markup.add(InlineKeyboardButton(text=btn['text'], url=btn['url']))
            
        try:
            bot.copy_message(chat_id=channel, from_chat_id=chat_id, message_id=post['message_id'], reply_markup=channel_markup)
            bot.answer_callback_query(call.id, "Kanalga yuborildi!")
            bot.send_message(chat_id, "🎉 **Post kanalingizga muvaffaqiyatli yuborildi!**", reply_markup=main_menu(), parse_mode="Markdown")
            data['temp_post'] = None
        except Exception as e:
            bot.send_message(chat_id, f"❌ **Xatolik!** Bot ushbu kanalda admin ekanligini va xabar yuborish huquqi borligini tekshiring.\n\nTafsilot: `{e}`", parse_mode="Markdown")

def add_button_to_list(message):
    chat_id = message.chat.id
    text_input = message.text
    data = get_user_data(chat_id)
    
    if '-' not in text_input:
        msg = bot.send_message(chat_id, "❌ **Noto'g'ri format!**\nQayta urinib ko'ring (Misol: `Google - https://google.com`):")
        bot.register_next_step_handler(msg, add_button_to_list)
        return
        
    try:
        name, url = text_input.split('-', 1)
        data['temp_post']['buttons'].append({
            'text': name.strip(),
            'url': url.strip()
        })
        bot.send_message(chat_id, "✅ Tugma qo'shildi!")
        show_preview(chat_id)
    except Exception:
        msg = bot.send_message(chat_id, "❌ Nimadir noto'g'ri ketdi. Formatni tekshiring:")
        bot.register_next_step_handler(msg, add_button_to_list)

# --- YORDAM BO'LIMI ---
@bot.message_handler(func=lambda m: m.text == "ℹ️ Yordam")
def help_info(message):
    bot.send_message(message.chat.id, "💡 **Qanday ishlatiladi?**\n\n"
                                      "1. **📢 Kanalni Sozlash** tugmasini bosib, kanalingizni kiriting (bir marta).\n"
                                      "2. **📝 Yangi Post Yaratish** tugmasini bosing va media yoki matn yuboring.\n"
                                      "3. Post tagida hosil bo'lgan **➕ Tugma qo'shish** tugmasi orqali istalgancha tugma ulab chiqing.\n"
                                      "4. Hammasi tayyor bo'lgach, **📤 Kanalga yuborish** tugmasini bosing va tamom!", 
                     reply_markup=main_menu(), parse_mode="Markdown")

if __name__ == '__main__':
    print("Yangi professional bot ishga tushdi...")
    bot.infinity_polling()
