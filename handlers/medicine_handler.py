from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

# База данных медикаментов
MEDICINE_DATA = {
    'painkillers': {
        'name': '💊 Обезболивающие и жаропонижающие',
        'medicines': [
            'Парацетамол — Panadol, Rubophen, Paramax',
            'Ибупрофен — Advil Ultra, Algoflex, Voltaren',
            'Аспирин — Aspirin, Kalmopyrin',
            'Ношпа — No-Spa',
            'Саридон — Saridon',
            'Алгофлекс Дуо — Algoflex Duo',
            'Кетафлекс / Ketodex — Ketodex',
            'Катафлам — Cataflam',
            'Терафлю — Neo Citran',
            'Колдрекс — Coldrex'
        ]
    },
    'digestive': {
        'name': '🔴 Противодиарейные и ЖКТ',
        'medicines': [
            'Имодиум — Imodium',
            'Лопедиум — Lopedium',
            'Смекта — Smecta',
            'Биогаия — BioGaia',
            'Тасектан — Tasectan',
            'Кралекс — Cralex',
            'Линекс — Linex',
            'ОРС 200 Хипп — ORS 200 Hipp',
            'Тева-Энтеробене — Teva-Enterobene',
            'Лопакут — Lopacut'
        ]
    },
    'allergy': {
        'name': '🤧 Против аллергии',
        'medicines': [
            'Цетиризин — Zyrtec, Cetimax',
            'Фенистил — Fenistil гель',
            'Аллергодил — Allergodil спрей',
            'Кларитин — Claritine',
            'Лордестин — Lordestin',
            'Ксизал — Xyzal',
            'Ревицет — Revicet',
            'Лертазин — Lertazin',
            'Зилола — Zilola'
        ]
    },
    'cough': {
        'name': '😷 От кашля и простуды',
        'medicines': [
            'Туссирекс — Tussirex сироп',
            'Ринотиол — Rhinothiol сироп и таблетки',
            'Амброксол — Ambroxol',
            'НеоТусс — NeoTuss сироп',
            'Паксразол — Paxirazol'
        ]
    },
    'throat': {
        'name': '🗣️ Препараты для горла',
        'medicines': [
            'Тантум Верде — Tantum Verde спрей',
            'Стрепсилс — Strepsils пастилки',
            'Фарингосопт — FaringoStop спрей',
            'Септолете — Septolete пастилки',
            'Мебукайна Минт — Mebucain Mint пастилки с лидокаином',
            'Доритрицин — Dorithricin пастилки'
        ]
    },
    'nasal': {
        'name': '👃 От насморка',
        'medicines': [
            'Оксиметазолин — Afrin, Otrivin, Nasivin',
            'Ксилометазолин — Otrivin',
            'Риноспрей — Rhinospray',
            'Аквамарис — Aquamaris',
            'Ринофлуимуцил — Rinofluimucil',
            'Ревентил — Reventil'
        ]
    },
    'skin': {
        'name': '🩹 Препараты для кожи и ран',
        'medicines': [
            'Бепантен — Bepanthen крем и мазь',
            'Пантефен — Panthenol спрей',
            'Лидокаин-Эгис — Lidocain-Egis мазь',
            'Эмофикс — Emofix гель кровоостанавливающий',
            'Лаванида — Lavanid гель',
            'Дермазин — Dermazin крем',
            'Гентамицин-Вагнер — Gentamicin-Wagner мазь',
            'Тирозур — Tyrosur гель',
            'Хансапласт — Hansaplast крем'
        ]
    },
    'other': {
        'name': '➕ Прочие',
        'medicines': [
            'Регидрон — ORS 200 Hipp (регидратация)',
            'Активированный уголь — Carbo Medicinalis',
            'Витамин C — различные бренды',
            'Магне B6 — Magne B6',
            'Омега-3 — различные бренды'
        ]
    }
}

async def hp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список медикаментов с категориями"""
    
    keyboard = [
        [
            InlineKeyboardButton("💊 Обезболивающие", callback_data="hp:painkillers"),
            InlineKeyboardButton("🔴 ЖКТ", callback_data="hp:digestive")
        ],
        [
            InlineKeyboardButton("🤧 Аллергия", callback_data="hp:allergy"),
            InlineKeyboardButton("😷 Кашель", callback_data="hp:cough")
        ],
        [
            InlineKeyboardButton("🗣️ Горло", callback_data="hp:throat"),
            InlineKeyboardButton("👃 Насморк", callback_data="hp:nasal")
        ],
        [
            InlineKeyboardButton("🩹 Кожа/Раны", callback_data="hp:skin"),
            InlineKeyboardButton("➕ Прочие", callback_data="hp:other")
        ],
        [InlineKeyboardButton("📋 Все категории", callback_data="hp:all")]
    ]
    
    text = (
        "💊 **Препараты без рецепта в Венгрии**\n\n"
        "Выберите категорию для просмотра:\n\n"
        "⚠️ *Важно:*\n"
        "• Консультируйтесь с врачом\n"
        "• Читайте инструкции\n"
        "• Соблюдайте дозировки\n"
        "• Проверяйте противопоказания"
    )
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_hp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback для медикаментов"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    category = data[1] if len(data) > 1 else None
    
    if category == "all":
        await show_all_medicines(update, context)
    elif category in MEDICINE_DATA:
        await show_medicine_category(update, context, category)
    elif category == "back":
        await show_medicine_menu(update, context)
    else:
        await query.answer("Категория не найдена", show_alert=True)

async def show_medicine_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    """Показать конкретную категорию медикаментов"""
    query = update.callback_query
    
    if category not in MEDICINE_DATA:
        await query.answer("Категория не найдена", show_alert=True)
        return
    
    cat_data = MEDICINE_DATA[category]
    
    text = f"**{cat_data['name']}**\n\n"
    
    for i, medicine in enumerate(cat_data['medicines'], 1):
        text += f"{i}. {medicine}\n"
    
    text += "\n⚠️ *Перед применением консультируйтесь с врачом*"
    
    keyboard = [
        [InlineKeyboardButton("◀️ Назад к категориям", callback_data="hp:back")]
    ]
    
    try:
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error showing medicine category: {e}")
        await query.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def show_all_medicines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все медикаменты"""
    query = update.callback_query
    
    text = "💊 **Препараты без рецепта в Венгрии**\n\n"
    
    for category_key, cat_data in MEDICINE_DATA.items():
        text += f"\n**{cat_data['name']}**\n"
        for i, medicine in enumerate(cat_data['medicines'], 1):
            text += f"{i}. {medicine}\n"
    
    text += "\n\n⚠️ *Важно:*\n"
    text += "• Консультируйтесь с врачом\n"
    text += "• Читайте инструкции\n"
    text += "• Соблюдайте дозировки"
    
    keyboard = [
        [InlineKeyboardButton("◀️ Назад к категориям", callback_data="hp:back")]
    ]
    
    # Разбиваем на части если текст слишком длинный
    if len(text) > 4000:
        # Отправляем по категориям
        for category_key, cat_data in MEDICINE_DATA.items():
            category_text = f"**{cat_data['name']}**\n\n"
            for i, medicine in enumerate(cat_data['medicines'], 1):
                category_text += f"{i}. {medicine}\n"
            
            await query.message.reply_text(
                category_text,
                parse_mode='Markdown'
            )
        
        await query.message.reply_text(
            "⚠️ *Важно: Консультируйтесь с врачом перед применением*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        try:
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error showing all medicines: {e}")
            await query.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )

async def show_medicine_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню выбора категорий"""
    query = update.callback_query
    
    keyboard = [
        [
            InlineKeyboardButton("💊 Обезболивающие", callback_data="hp:painkillers"),
            InlineKeyboardButton("🔴 ЖКТ", callback_data="hp:digestive")
        ],
        [
            InlineKeyboardButton("🤧 Аллергия", callback_data="hp:allergy"),
            InlineKeyboardButton("😷 Кашель", callback_data="hp:cough")
        ],
        [
            InlineKeyboardButton("🗣️ Горло", callback_data="hp:throat"),
            InlineKeyboardButton("👃 Насморк", callback_data="hp:nasal")
        ],
        [
            InlineKeyboardButton("🩹 Кожа/Раны", callback_data="hp:skin"),
            InlineKeyboardButton("➕ Прочие", callback_data="hp:other")
        ],
        [InlineKeyboardButton("📋 Все категории", callback_data="hp:all")]
    ]
    
    text = (
        "💊 **Препараты без рецепта в Венгрии**\n\n"
        "Выберите категорию для просмотра:\n\n"
        "⚠️ *Важно:*\n"
        "• Консультируйтесь с врачом\n"
        "• Читайте инструкции\n"
        "• Соблюдайте дозировки\n"
        "• Проверяйте противопоказания"
    )
    
    try:
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error showing medicine menu: {e}")
        await query.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
