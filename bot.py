import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Bot tokeningiz
TOKEN = '8892311555:AAFFfNYeG7yJc1BTPjp9PqHkgKh9Jpgp7UM'
bot = telebot.TeleBot(TOKEN)

# Foydalanuvchi ma'lumotlarini saqlash uchun xotira
user_data = {}

def get_user_data(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {'channels': [], 'temp_post': None}
    if 'channels' not in user_data[chat_id]:
        user_data[chat_id]['channels'] = []
    return user_data[chat_id]

# Asosiy ekran tugmalari (Menu)
def main_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("📝 Yangi Post Yaratish")
    btn2 = KeyboardButton("📢 Kanallarni Sozlash")
    btn3 = KeyboardButton("ℹ️ Yordam")
    markup.add(btn1, btn2, btn3)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    get_user_data(chat_id)
    bot.send_message(chat_id, "🤖 **Professional Multikanal Admin Paneliga xush kelibsiz!**\n\n"
                              "Pastdagi tugmalar orqali botni juda oson boshqarishingiz mumkin 👇", 
                     reply_markup=main_menu(), parse_mode="Markdown")

# --- KANALLARNI SOZLASH BO'LIMI ---
@bot.message_handler(func=lambda m: m.text in ["📢 Kanallarni Sozlash", "📢 Kanalni Sozlash"])
def manage_channels(message):
    chat_id = message.chat.id
    data = get_user_data(chat_id)
    channels = data['channels']
    
    text = "📢 **Sizning ulangan kanallaringiz ro'yxati:**\n\n"
    if not channels:
        text += "⚠️ Hozircha hech qanday kanal qo'shilmagan."
    else:
        for i, ch in enumerate(channels, 1):
            text += f"{i}. {ch}\n"
    
    text += f"\nJoriy kanallar soni: {len(channels)}/20"
    
    markup = InlineKeyboardMarkup()
    if len(channels) < 20:
        markup.add(InlineKeyboardButton("➕ Yangi kanal qo'shish", callback_data="add_channel"))
    if channels:
        markup.add(InlineKeyboardButton("🧹 Hammasini tozalash", callback_data="clear_channels"))
        
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

# --- YANGI POST YARATISH BO'LIMI ---
@bot.message_handler(func=lambda m: m.text == "📝 Yangi Post Yaratish")
def new_post_prompt(message):
    chat_id = message.chat.id
    data = get_user_data(chat_id)
    
    if not data['channels']:
        bot.send_message(chat_id, "❌ **Avval kamida bitta kanalni sozlang!**\n'📢 Kanallarni Sozlash' tugmasini bosing.", reply_markup=main_menu(), parse_mode="Markdown")
        return
    
    cancel_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("❌ Bekor qilish"))
    msg = bot.send_message(chat_id, "📥 **Menga istalgan postni yuboring.**\n"
                                    "Bu rasm, video, ovozli xabar yoki shunchaki formatlangan matn bo'lishi mumkin:", 
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
    
    markup = InlineKeyboardMarkup()
    for btn in post['buttons']:
        markup.add(InlineKeyboardButton(text=btn['text'], url=btn['url']))
    
    markup.add(
        InlineKeyboardButton(text="➕ Tugma qo'shish", callback_data="add_btn"),
        InlineKeyboardButton(text="🧹 Tugmalarni tozalash", callback_data="clear_btns")
    )
    markup.add(
        InlineKeyboardButton(text="📤 Kanalga yuborish", callback_data="send_select"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_post")
    )
    
    bot.send_message(chat_id, "👀 **Post ko'rinishi (Preview):**\nPastdagi tugmalar orqali sozlang va kanalga yuboring:")
    bot.copy_message(chat_id=chat_id, from_chat_id=chat_id, message_id=post['message_id'], reply_markup=markup)

# --- TUGMA BOSILISHINI NAZORAT QILISH (CALLBACK) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = get_user_data(chat_id)
    
    if call.data == "add_channel":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "✍️ **Yangi kanal manzili yoki ID sini yuboring:**\n"
                                        "Misol: `@mening_kanalim` yoki `-100123456789`\n\n"
                                        "⚠️ _Bot u yerda admin bo'lishi shart!_", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_channel)
        
    elif call.data == "clear_channels":
        data['channels'] = []
        bot.answer_callback_query(call.id, "Barcha kanallar o'chirildi!")
        bot.delete_message(chat_id, call.message.message_id)
        manage_channels(call.message)
        
    elif call.data == "add_btn":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "✍️ **Tugma ma'lumotini yuboring:**\n"
                                        "Format: `Tugma nomi - ssilka`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, add_button_to_list)
        
    elif call.data == "clear_btns":
        data['temp_post']['buttons'] = []
        bot.answer_callback_query(call.id, "Tugmalar tozalandi!")
        post = data['temp_post']
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(text="➕ Tugma qo'shish", callback_data="add_btn"),
            InlineKeyboardButton(text="🧹 Tugmalarni tozalash", callback_data="clear_btns")
        )
        markup.add(
            InlineKeyboardButton(text="📤 Kanalga yuborish", callback_data="send_select"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_post")
        )
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
        
    elif call.data == "cancel_post":
        data['temp_post'] = None
        bot.answer_callback_query(call.id, "Post o'chirildi.")
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, "Bekor qilindi.", reply_markup=main_menu())
        
    elif call.data == "send_select":
        bot.answer_callback_query(call.id)
        if not data['channels']:
            bot.send_message(chat_id, "❌ **Avval kanallarni sozlang!**", reply_markup=main_menu(), parse_mode="Markdown")
            return
        
        select_markup = InlineKeyboardMarkup()
        for i, ch in enumerate(data['channels']):
            select_markup.add(InlineKeyboardButton(text=f"📢 {ch}", callback_data=f"send_to:{i}"))
        
        if len(data['channels']) > 1:
            select_markup.add(InlineKeyboardButton(text="🚀 BARCHASIGA YUBORISH", callback_data="send_to_all"))
        
        select_markup.add(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_preview"))
        
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=select_markup)
        
    elif call.data == "back_to_preview":
        bot.answer_callback_query(call.id)
        post = data['temp_post']
        markup = InlineKeyboardMarkup()
        for btn in post['buttons']:
            markup.add(InlineKeyboardButton(text=btn['text'], url=btn['url']))
        markup.add(
            InlineKeyboardButton(text="➕ Tugma qo'shish", callback_data="add_btn"),
            InlineKeyboardButton(text="🧹 Tugmalarni tozalash", callback_data="clear_btns")
        )
        markup.add(
            InlineKeyboardButton(text="📤 Kanalga yuborish", callback_data="send_select"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_post")
        )
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
        
    elif call.data.startswith("send_to:"):
        bot.answer_callback_query(call.id)
        idx = int(call.data.split(":")[1])
        channel = data['channels'][idx]
        send_post_to_channel(chat_id, channel, call.message.message_id)
        
    elif call.data == "send_to_all":
        bot.answer_callback_query(call.id)
        send_post_to_all_channels(chat_id, call.message.message_id)

def save_channel(message):
    chat_id = message.chat.id
    channel = message.text.strip()
    data = get_user_data(chat_id)
    
    if len(data['channels']) >= 20:
        bot.send_message(chat_id, "❌ Ko'pida 20ta kanal qo'shishingiz mumkin!", reply_markup=main_menu())
        return
        
    if channel in data['channels']:
        bot.send_message(chat_id, "⚠️ Bu kanal allaqachon ro'yxatda bor!", reply_markup=main_menu())
        return
        
    data['channels'].append(channel)
    bot.send_message(chat_id, f"✅ **Kanal muvaffaqiyatli qo'shildi!**\nJoriy kanallar soni: {len(data['channels'])}/20", 
                     reply_markup=main_menu(), parse_mode="Markdown")

def send_post_to_channel(chat_id, channel, control_msg_id):
    data = get_user_data(chat_id)
    post = data['temp_post']
    
    channel_markup = InlineKeyboardMarkup()
    for btn in post['buttons']:
        channel_markup.add(InlineKeyboardButton(text=btn['text'], url=btn['url']))
        
    try:
        bot.copy_message(chat_id=channel, from_chat_id=chat_id, message_id=post['message_id'], reply_markup=channel_markup)
        bot.send_message(chat_id, f"🎉 **Post muvaffaqiyatli yuborildi:** `{channel}`", reply_markup=main_menu(), parse_mode="Markdown")
        try:
            bot.delete_message(chat_id, control_msg_id)
        except:
            pass
        data['temp_post'] = None
    except Exception as e:
        bot.send_message(chat_id, f"❌ **{channel} kanaliga yuborishda xatolik!**\nBot admin ekanligini va xabar yuborish huquqi borligini tekshiring.\n\nTafsilot: `{e}`", parse_mode="Markdown")

def send_post_to_all_channels(chat_id, control_msg_id):
    data = get_user_data(chat_id)
    post = data['temp_post']
    channels = data['channels']
    
    channel_markup = InlineKeyboardMarkup()
    for btn in post['buttons']:
        channel_markup.add(InlineKeyboardButton(text=btn['text'], url=btn['url']))
        
    success_count = 0
    failed_channels = []
    
    for ch in channels:
        try:
            bot.copy_message(chat_id=ch, from_chat_id=chat_id, message_id=post['message_id'], reply_markup=channel_markup)
            success_count += 1
        except Exception as e:
            failed_channels.append(f"{ch} ({str(e)})")
            
    report = f"📊 **Yuborish yakunlandi:**\n✅ Muvaffaqiyatli: {success_count}/{len(channels)}"
    if failed_channels:
        report += "\n\n❌ **Xatolik bo'lgan kanallar:**\n" + "\n".join(failed_channels)
        
    bot.send_message(chat_id, report, reply_markup=main_menu(), parse_mode="Markdown")
    try:
        bot.delete_message(chat_id, control_msg_id)
    except:
        pass
    data['temp_post'] = None

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
                                      "1. **📢 Kanallarni Sozlash** tugmasini bosib, kanallaringizni bittalab qo'shing (20tagacha).\n"
                                      "2. **📝 Yangi Post Yaratish** tugmasini bosing va har qanday media yoki matn yuboring.\n"
                                      "3. **➕ Tugma qo'shish** tugmasi orqali istalgancha tugma ulab chiqing.\n"
                                      "4. Hammasi tayyor bo'lgach, **📤 Kanalga yuborish** tugmasini bosing va o'zingiz xohlagan aniq kanalni tanlang yoki hammasiga birdan jo'nating!", 
                     reply_markup=main_menu(), parse_mode="Markdown")

if __name__ == '__main__':
    print("Yangi professional multikanal bot ishga tushdi...")
    bot.infinity_polling()
