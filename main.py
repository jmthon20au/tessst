import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from telegram.constants import ParseMode

# Set logging level
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8376921346:AAEVhSqrlZo8KgUg9ggCMYorh7-RCPTfLzM" 


DATA_FILE = "data.json"

(
    ADD_PRODUCT_COMPANY_NAME, ADD_PRODUCT_ID, ADD_PRODUCT_QUANTITY, ADD_PRODUCT_PRICE, ADD_PRODUCT_CATEGORY, ADD_PRODUCT_IMAGE_URL,
    UPDATE_QUANTITY_ID, UPDATE_QUANTITY_AMOUNT,
    SUBTRACT_QUANTITY_ID, SUBTRACT_QUANTITY_AMOUNT,
    SEARCH_PRODUCT_ID,
    DELETE_PRODUCT_ID, DELETE_PRODUCT_CONFIRMATION,
    EDIT_PRODUCT_ID, EDIT_CHOICE, EDIT_NEW_VALUE,
    SET_LOW_STOCK_THRESHOLD_VALUE,
    ADD_ADMIN_ID,
    REMOVE_ADMIN_ID,
    NOTIFY_LOW_STOCK_CONFIRMATION
) = range(20) # Total 20 states now


def load_data():
    """Loads data from JSON file."""
    if not os.path.exists(DATA_FILE):


        default_data = {
            "settings": {"low_stock_threshold": 50},
            "admins": [], 
            "products": []
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

        if "settings" not in data:
            data["settings"] = {"low_stock_threshold": 50}
        if "low_stock_threshold" not in data["settings"]:
            data["settings"]["low_stock_threshold"] = 50
        if "products" not in data:
            data["products"] = []
        if "admins" not in data:
            data["admins"] = [] # Initialize if missing
        return data

def save_data(data):
    """Saves data to JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_low_stock_threshold():
    """Gets the current low stock threshold."""
    data = load_data()
    return data["settings"]["low_stock_threshold"]

def set_low_stock_threshold(threshold):
    """Sets a new low stock threshold."""
    data = load_data()
    data["settings"]["low_stock_threshold"] = threshold
    save_data(data)

def get_admins():
    """Gets the list of admin IDs."""
    data = load_data()
    return data.get("admins", [])

def add_admin_id_to_data(admin_id: int) -> bool:
    """Adds an admin ID to the list."""
    data = load_data()
    admins = data.get("admins", [])
    if admin_id not in admins:
        admins.append(admin_id)
        data["admins"] = admins
        save_data(data)
        return True
    return False

def remove_admin_id_from_data(admin_id: int) -> bool:
    """Removes an admin ID from the list."""
    data = load_data()
    admins = data.get("admins", [])
    if admin_id in admins:
        admins.remove(admin_id)
        data["admins"] = admins
        save_data(data)
        return True
    return False

# ---------------- Product Helper Functions ---------------
def get_product_by_id(product_id):
    """Searches for a product by its ID."""
    data = load_data()
    for product in data["products"]:
        if product["productId"] == product_id:
            return product
    return None

def update_product_quantity(product_id, quantity_change):
    """Updates product quantity (add or subtract)."""
    data = load_data()
    for product in data["products"]:
        if product["productId"] == product_id:
            product["quantity"] += quantity_change
            if product["quantity"] < 0:
                product["quantity"] = 0  # Quantity cannot be negative
            save_data(data)
            return True
    return False

def add_new_product_to_data(company_name, product_id, quantity, price, category, image_url):
    """Adds a new product to the inventory."""
    data = load_data()
    if any(p["productId"] == product_id for p in data["products"]):
        return False  # Product already exists
    
    data["products"].append({
        "companyName": company_name,
        "productId": product_id,
        "quantity": quantity,
        "price": price,
        "category": category,
        "imageUrl": image_url
    })
    save_data(data)
    return True

def delete_existing_product(product_id):
    """Deletes a product from the inventory."""
    data = load_data()
    initial_len = len(data["products"])
    data["products"] = [p for p in data["products"] if p["productId"] != product_id]
    if len(data["products"]) < initial_len:
        save_data(data)
        return True
    return False

def edit_existing_product(product_id, field, new_value):
    """Edits a specific field of an existing product."""
    data = load_data()
    for product in data["products"]:
        if product["productId"] == product_id:
            product[field] = new_value
            save_data(data)
            return True
    return False

# ------------------ Admin Check Function ------------------
def is_admin(user_id: int) -> bool:
    """Checks if the user is an admin."""
    return user_id in get_admins()

# -- Bot Commands (Command Handlers) -----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and main menu."""
    await update.message.reply_text(
        "أهلاً بك في بوت إدارة مخزن البورسلين!\n"
        "استخدم /menu لعرض الأوامر المتاحة."
    )
    await menu(update, context) # Show menu immediately

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the main menu."""
    keyboard = [
        [InlineKeyboardButton("عرض جميع المنتجات", callback_data="view_all_products")],
        [InlineKeyboardButton("البحث عن منتج", callback_data="search_product_btn")],
        [InlineKeyboardButton("ملخص المخزون", callback_data="inventory_summary_btn")]
    ]
    # Add admin menu button only if user is an admin
    if is_admin(update.effective_user.id):
        keyboard.append([InlineKeyboardButton("إدارة المخزن (للمشرفين)", callback_data="admin_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text("اختر أحد الخيارات:", reply_markup=reply_markup)
        await update.callback_query.answer()
    else:
        await update.message.reply_text("اختر أحد الخيارات:", reply_markup=reply_markup)

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays admin commands menu."""
    if not is_admin(update.effective_user.id):
        await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return

    keyboard = [
        [InlineKeyboardButton("إضافة منتج جديد", callback_data="add_product_btn"),
         InlineKeyboardButton("إضافة كمية", callback_data="add_quantity_btn")],
        [InlineKeyboardButton("خصم كمية", callback_data="subtract_quantity_btn"),
         InlineKeyboardButton("حذف منتج", callback_data="delete_product_btn")],
        [InlineKeyboardButton("تعديل منتج", callback_data="edit_product_btn")],
        [InlineKeyboardButton("عرض المنتجات قليلة المخزون", callback_data="view_low_stock_btn")],
        [InlineKeyboardButton("تغيير عتبة المخزون المنخفض", callback_data="set_low_stock_threshold_btn")],
        [InlineKeyboardButton("توليد تقرير شامل", callback_data="generate_report_btn"),
         InlineKeyboardButton("نسخ احتياطي للبيانات", callback_data="backup_data_btn")],
        [InlineKeyboardButton("إدارة المشرفين", callback_data="manage_admins_menu")],
        [InlineKeyboardButton("العودة للقائمة الرئيسية", callback_data="main_menu_from_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text("قائمة أوامر المشرفين:", reply_markup=reply_markup)
    await update.callback_query.answer()

async def manage_admins_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays admin management options."""
    if not is_admin(update.effective_user.id):
        await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return
    
    keyboard = [
        [InlineKeyboardButton("عرض المشرفين الحاليين", callback_data="view_admins_btn")],
        [InlineKeyboardButton("إضافة مشرف جديد", callback_data="add_admin_btn")],
        [InlineKeyboardButton("حذف مشرف", callback_data="remove_admin_btn")],
        [InlineKeyboardButton("العودة لقائمة المشرفين", callback_data="admin_menu_from_manage_admins")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text("خيارات إدارة المشرفين:", reply_markup=reply_markup)
    await update.callback_query.answer()

async def view_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays all products in the inventory."""
    products = load_data()["products"]
    if not products:
    	message_text = "✨ لا توجد منتجات متوفرة حالياً في المخزن. ✨"
    else:
    	message_text = "🛍️ قائمة المنتجات المتوفرة في المخزن: ✨\n\n"
    	for i, product in enumerate(products):
    		message_text += (
    	f"*{i+1}. اسم الشركة:* {product['companyName']}\n"
            f"* تسلسل المنتج:* `{product['productId']}`\n"
            f"* التصنيف:* {product.get('category', 'غير محدد')}\n"
            f"* السعر:* {product.get('price', 'غير محدد')} ع.د\n"
            f"* الكمية:* {product['quantity']} متر\n"
            f"* رابط صورة المنتج:* {product['imageUrl']}\n"
            f"--------------------\n"
        )

    
    if update.callback_query:
        await update.callback_query.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN)
        await update.callback_query.answer()
    else:
        await update.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN)

async def view_low_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays products with low stock."""
    current_threshold = get_low_stock_threshold()
    products = load_data()["products"]
    low_stock_products = [p for p in products if p["quantity"] <= current_threshold]

    if not low_stock_products:
        message_text = f"لا توجد منتجات بكميات قليلة حالياً (أقل من أو يساوي {current_threshold})."
    else:
        message_text = f"المنتجات التي كميتها {current_threshold} أو أقل:\n\n"
        for i, product in enumerate(low_stock_products):
            price_info = f", السعر: {product.get('price', 'غير محدد')} $US" if 'price' in product else ""
            category_info = f", التصنيف: {product.get('category', 'غير محدد')}" if 'category' in product else ""
            message_text += (
                f"*{i+1}. اسم الشركة:* {product['companyName']}\n"
                f"*تسلسل المنتج:* `{product['productId']}`\n"
                f"*الكمية:* {product['quantity']}{price_info}{category_info}\n"
                f"*صورة المنتج:* {product['imageUrl']}\n"
                "--------------------\n"
            )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN)
        await update.callback_query.answer()
    else:
        await update.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN)

async def inventory_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides a quick summary of the inventory."""
    products = load_data()["products"]
    if not products:
        summary_text = "لا توجد منتجات حالياً في المخزن."
    else:
        total_unique_products = len(products)
        total_quantity_all_products = sum(p["quantity"] for p in products)
        
        current_threshold = get_low_stock_threshold()
        low_stock_products_count = sum(1 for p in products if p["quantity"] <= current_threshold)

        summary_text = (
            "*ملخص المخزون السريع:*\n"
            f"عدد أنواع المنتجات الكلي: *{total_unique_products}*\n"
            f"إجمالي الكمية لجميع المنتجات: *{total_quantity_all_products}*\n"
            f"عدد المنتجات قليلة المخزون (أقل من أو يساوي {current_threshold}): *{low_stock_products_count}*\n\n"
            "للتفاصيل، استخدم /view_products."
        )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(summary_text, parse_mode=ParseMode.MARKDOWN)
        await update.callback_query.answer()
    else:
        await update.message.reply_text(summary_text, parse_mode=ParseMode.MARKDOWN)


async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generates a comprehensive report and sends it as a text file."""
    products = load_data()["products"]
    
    report_content = "--- تقرير مخزن البورسلين ---\n\n"
    if not products:
        report_content += "لا توجد بيانات لإنشاء تقرير."
    else:
        total_products_count = len(products)
        total_quantity = sum(p["quantity"] for p in products)
        
        report_content += f"عدد المنتجات الإجمالي: {total_products_count}\n"
        report_content += f"إجمالي الكمية في المخزن: {total_quantity}\n\n"
        report_content += "تفاصيل المنتجات:\n"
        for i, product in enumerate(products):
            report_content += (
                f"{i+1}. اسم الشركة: {product['companyName']}\n"
                f"   تسلسل المنتج: {product['productId']}\n"
                f"   الكمية: {product['quantity']}\n"
                f"   السعر: {product.get('price', 'غير محدد')}\n"
                f"   التصنيف: {product.get('category', 'غير محدد')}\n"
                f"   رابط الصورة: {product['imageUrl']}\n"
                "--------------------\n"
            )
        report_content += "\n--- نهاية التقرير ---"
    
    # Save report to a temporary file
    report_filename = "inventory_report.txt"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    # Send the file
    if update.callback_query:
        await update.callback_query.message.reply_document(
            document=open(report_filename, 'rb'),
            filename=report_filename,
            caption="تقرير المخزون الشامل:"
        )
        await update.callback_query.answer()
    else:
        await update.message.reply_document(
            document=open(report_filename, 'rb'),
            filename=report_filename,
            caption="تقرير المخزون الشامل:"
        )
    
    # Clean up the temporary file
    os.remove(report_filename)

async def backup_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a backup of the data.json file."""
    if not is_admin(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        elif update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return

    # Ensure data.json exists and is up-to-date
    save_data(load_data()) 
    
    if os.path.exists(DATA_FILE):
        try:
            if update.callback_query:
                await update.callback_query.message.reply_document(
                    document=open(DATA_FILE, 'rb'),
                    filename="inventory_data_backup.json",
                    caption="نسخة احتياطية من بيانات المخزن:"
                )
                await update.callback_query.answer("تم إرسال النسخة الاحتياطية.")
            else:
                await update.message.reply_document(
                    document=open(DATA_FILE, 'rb'),
                    filename="inventory_data_backup.json",
                    caption="نسخة احتياطية من بيانات المخزن:"
                )
                await update.message.reply_text("تم إرسال النسخة الاحتياطية.")
        except Exception as e:
            logger.error(f"Failed to send backup file: {e}")
            message_source = update.callback_query.message if update.callback_query else update.message
            await message_source.reply_text("فشل إرسال النسخة الاحتياطية. يرجى المحاولة لاحقاً.")
    else:
        message_source = update.callback_query.message if update.callback_query else update.message
        await message_source.reply_text("لا يوجد ملف بيانات للنسخ الاحتياطي.")

# -------- Add Product (Conversation Handler) -------
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the add product process."""
    if not is_admin(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        elif update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return ConversationHandler.END

    message_source = update.callback_query.message if update.callback_query else update.message
    if update.callback_query: await update.callback_query.answer()
    
    await message_source.reply_text(
        "حسناً، لإضافة منتج جديد، يرجى إدخال اسم الشركة:",
        reply_markup=ForceReply(selective=True)
    )
    return ADD_PRODUCT_COMPANY_NAME

async def add_product_company_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures company name and asks for product ID."""
    context.user_data["company_name"] = update.message.text
    await update.message.reply_text(
        "الآن، يرجى إدخال تسلسل المنتج (يجب أن يكون فريداً):",
        reply_markup=ForceReply(selective=True)
    )
    return ADD_PRODUCT_ID

async def add_product_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures product ID and asks for quantity."""
    product_id = update.message.text
    if get_product_by_id(product_id):
        await update.message.reply_text(
            f"عذراً، المنتج ذو التسلسل `{product_id}` موجود بالفعل. يرجى إدخال تسلسل فريد آخر أو إلغاء العملية باستخدام /cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        return ADD_PRODUCT_ID 
    
    context.user_data["product_id"] = product_id
    await update.message.reply_text(
        "يرجى إدخال الكمية الأولية للمنتج (رقم صحيح):",
        reply_markup=ForceReply(selective=True)
    )
    return ADD_PRODUCT_QUANTITY

async def add_product_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures quantity and asks for price."""
    try:
        quantity = int(update.message.text)
        if quantity < 0:
            raise ValueError
        context.user_data["quantity"] = quantity
        await update.message.reply_text(
            "يرجى إدخال سعر المنتج (رقم عشري، مثال: 15.75):",
            reply_markup=ForceReply(selective=True)
        )
        return ADD_PRODUCT_PRICE
    except ValueError:
        await update.message.reply_text("الكمية يجب أن تكون رقماً صحيحاً وموجباً. يرجى المحاولة مرة أخرى:")
        return ADD_PRODUCT_QUANTITY

async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures price and asks for category."""
    try:
        price = float(update.message.text)
        if price < 0:
            raise ValueError
        context.user_data["price"] = price
        await update.message.reply_text(
            "يرجى إدخال تصنيف المنتج (مثال: أرضيات، جدران، مطابخ):",
            reply_markup=ForceReply(selective=True)
        )
        return ADD_PRODUCT_CATEGORY
    except ValueError:
        await update.message.reply_text("السعر يجب أن يكون رقماً صالحاً وموجباً. يرجى المحاولة مرة أخرى:")
        return ADD_PRODUCT_PRICE

async def add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures category and asks for image URL."""
    context.user_data["category"] = update.message.text
    await update.message.reply_text(
        "أخيراً، يرجى إدخال رابط الصورة للمنتج (URL):",
        reply_markup=ForceReply(selective=True)
    )
    return ADD_PRODUCT_IMAGE_URL

async def add_product_image_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures image URL and saves the product."""
    context.user_data["image_url"] = update.message.text

    company_name = context.user_data["company_name"]
    product_id = context.user_data["product_id"]
    quantity = context.user_data["quantity"]
    price = context.user_data["price"]
    category = context.user_data["category"]
    image_url = context.user_data["image_url"]

    if add_new_product_to_data(company_name, product_id, quantity, price, category, image_url):
        await update.message.reply_text(f"تمت إضافة المنتج `{product_id}` بنجاح!", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"فشل إضافة المنتج `{product_id}`.", parse_mode=ParseMode.MARKDOWN)
    
    context.user_data.clear() 
    return ConversationHandler.END

# --------- Add Quantity (Conversation Handler)------
async def add_quantity_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the add quantity process."""
    if not is_admin(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        elif update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return ConversationHandler.END

    message_source = update.callback_query.message if update.callback_query else update.message
    if update.callback_query: await update.callback_query.answer()

    await message_source.reply_text(
        "لإضافة كمية، يرجى إدخال تسلسل المنتج:",
        reply_markup=ForceReply(selective=True)
    )
    return UPDATE_QUANTITY_ID

async def add_quantity_product_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures product ID and asks for quantity to add."""
    product_id = update.message.text
    if not get_product_by_id(product_id):
        await update.message.reply_text(
            f"المنتج ذو التسلسل `{product_id}` غير موجود. يرجى التحقق من التسلسل أو إلغاء العملية باستخدام /cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        return UPDATE_QUANTITY_ID
    
    context.user_data["product_id"] = product_id
    await update.message.reply_text(
        f"المنتج: `{product_id}`. يرجى إدخال الكمية المراد إضافتها (رقم صحيح موجب):",
        reply_markup=ForceReply(selective=True),
        parse_mode=ParseMode.MARKDOWN
    )
    return UPDATE_QUANTITY_AMOUNT

async def add_quantity_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures quantity and performs the addition."""
    try:
        quantity_to_add = int(update.message.text)
        if quantity_to_add <= 0:
            raise ValueError
        
        product_id = context.user_data["product_id"]
        if update_product_quantity(product_id, quantity_to_add):
            updated_product = get_product_by_id(product_id)
            await update.message.reply_text(
                f"تمت إضافة {quantity_to_add} وحدة للمنتج `{product_id}`. الكمية الجديدة: {updated_product['quantity']}.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(f"فشل إضافة الكمية للمنتج `{product_id}`.", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("الكمية يجب أن تكون رقماً صحيحاً وموجباً. يرجى المحاولة مرة أخرى:")
        return UPDATE_QUANTITY_AMOUNT
    
    context.user_data.clear()
    return ConversationHandler.END

# ------- Subtract Quantity (Conversation Handler) 
async def subtract_quantity_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the subtract quantity process."""
    if not is_admin(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        elif update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return ConversationHandler.END

    message_source = update.callback_query.message if update.callback_query else update.message
    if update.callback_query: await update.callback_query.answer()

    await message_source.reply_text(
        "لخصم كمية، يرجى إدخال تسلسل المنتج:",
        reply_markup=ForceReply(selective=True)
    )
    return SUBTRACT_QUANTITY_ID

async def subtract_quantity_product_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures product ID and asks for quantity to subtract."""
    product_id = update.message.text
    product = get_product_by_id(product_id)
    if not product:
        await update.message.reply_text(
            f"المنتج ذو التسلسل `{product_id}` غير موجود. يرجى التحقق من التسلسل أو إلغاء العملية باستخدام /cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        return SUBTRACT_QUANTITY_ID
    
    context.user_data["product_id"] = product_id
    await update.message.reply_text(
        f"المنتج: `{product_id}`. الكمية الحالية: {product['quantity']}.\n"
        f"يرجى إدخال الكمية المراد خصمها (رقم صحيح موجب):",
        reply_markup=ForceReply(selective=True),
        parse_mode=ParseMode.MARKDOWN
    )
    return SUBTRACT_QUANTITY_AMOUNT

async def subtract_quantity_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures quantity and performs the subtraction."""
    try:
        quantity_to_subtract = int(update.message.text)
        if quantity_to_subtract <= 0:
            raise ValueError
        
        product_id = context.user_data["product_id"]
        product = get_product_by_id(product_id)
        if product and product["quantity"] < quantity_to_subtract:
            await update.message.reply_text(
                f"لا يمكن خصم {quantity_to_subtract} وحدة. الكمية المتوفرة حالياً هي {product['quantity']}."
            )
            return SUBTRACT_QUANTITY_AMOUNT 
            
        if update_product_quantity(product_id, -quantity_to_subtract): # Subtract quantity
            updated_product = get_product_by_id(product_id)
            await update.message.reply_text(
                f"تم خصم {quantity_to_subtract} وحدة من المنتج `{product_id}`. الكمية الجديدة: {updated_product['quantity']}.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(f"فشل خصم الكمية من المنتج `{product_id}`.", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("الكمية يجب أن تكون رقماً صحيحاً وموجباً. يرجى المحاولة مرة أخرى:")
        return SUBTRACT_QUANTITY_AMOUNT
    
    context.user_data.clear()
    return ConversationHandler.END

# ------ Delete Product (Conversation Handler) -----
async def delete_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the delete product process."""
    if not is_admin(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        elif update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return ConversationHandler.END

    message_source = update.callback_query.message if update.callback_query else update.message
    if update.callback_query: await update.callback_query.answer()

    await message_source.reply_text(
        "لحذف منتج، يرجى إدخال تسلسل المنتج:",
        reply_markup=ForceReply(selective=True)
    )
    return DELETE_PRODUCT_ID

async def delete_product_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures product ID and confirms deletion."""
    product_id = update.message.text
    product = get_product_by_id(product_id)
    
    if not product:
        await update.message.reply_text(f"المنتج ذو التسلسل `{product_id}` غير موجود. يرجى التحقق من التسلسل أو إلغاء العملية باستخدام /cancel.", parse_mode=ParseMode.MARKDOWN)
        return DELETE_PRODUCT_ID
    
    context.user_data["product_to_delete_id"] = product_id
    keyboard = [
        [InlineKeyboardButton("نعم، متأكد", callback_data=f"confirm_delete_{product_id}")],
        [InlineKeyboardButton("إلغاء", callback_data="cancel_delete_product")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"هل أنت متأكد من حذف المنتج:\nاسم الشركة: {product['companyName']}\nتسلسل المنتج: `{product['productId']}`؟",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    return DELETE_PRODUCT_CONFIRMATION

async def delete_product_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms final deletion."""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("confirm_delete_"):
        product_id = context.user_data.get("product_to_delete_id")
        if delete_existing_product(product_id):
            await query.edit_message_text(f"تم حذف المنتج `{product_id}` بنجاح!", parse_mode=ParseMode.MARKDOWN)
        else:
            await query.edit_message_text(f"فشل حذف المنتج `{product_id}`. قد يكون غير موجود.", parse_mode=ParseMode.MARKDOWN)
    elif query.data == "cancel_delete_product":
        await query.edit_message_text("تم إلغاء عملية الحذف.")
    
    context.user_data.clear()
    return ConversationHandler.END

# ----------- Edit Product (Conversation Handler) ----
async def edit_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the edit product process."""
    if not is_admin(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        elif update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return ConversationHandler.END

    message_source = update.callback_query.message if update.callback_query else update.message
    if update.callback_query: await update.callback_query.answer()

    await message_source.reply_text(
        "لتعديل منتج، يرجى إدخال تسلسل المنتج:",
        reply_markup=ForceReply(selective=True)
    )
    return EDIT_PRODUCT_ID

async def edit_product_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures product ID and asks for the field to edit."""
    product_id = update.message.text
    product = get_product_by_id(product_id)

    if not product:
        await update.message.reply_text(
            f"المنتج ذو التسلسل `{product_id}` غير موجود. يرجى التحقق من التسلسل أو إلغاء العملية باستخدام /cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        return EDIT_PRODUCT_ID
    
    context.user_data["product_to_edit_id"] = product_id
    
    keyboard = [
        [InlineKeyboardButton("اسم الشركة", callback_data="edit_companyName")],
        [InlineKeyboardButton("رابط الصورة", callback_data="edit_imageUrl")],
        [InlineKeyboardButton("السعر", callback_data="edit_price")],
        [InlineKeyboardButton("التصنيف", callback_data="edit_category")],
        [InlineKeyboardButton("إلغاء التعديل", callback_data="cancel_edit_product")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"تم العثور على المنتج `{product_id}`. ما الذي تريد تعديله؟\n"
        f"اسم الشركة الحالي: {product['companyName']}\n"
        f"رابط الصورة الحالي: {product['imageUrl']}\n"
        f"السعر الحالي: {product.get('price', 'غير محدد')}\n"
        f"التصنيف الحالي: {product.get('category', 'غير محدد')}",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    return EDIT_CHOICE

async def edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures field choice and asks for new value."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_edit_product":
        await query.edit_message_text("تم إلغاء عملية التعديل.")
        context.user_data.clear()
        return ConversationHandler.END
    
    context.user_data["field_to_edit"] = query.data.replace("edit_", "") 
    
    prompt_text = ""
    if context.user_data["field_to_edit"] == "companyName":
        prompt_text = "الرجاء إدخال اسم الشركة الجديد:"
    elif context.user_data["field_to_edit"] == "imageUrl":
        prompt_text = "الرجاء إدخال رابط الصورة الجديد:"
    elif context.user_data["field_to_edit"] == "price":
        prompt_text = "الرجاء إدخال السعر الجديد (رقم عشري، مثال: 25.50):"
    elif context.user_data["field_to_edit"] == "category":
        prompt_text = "الرجاء إدخال التصنيف الجديد (مثال: أرضيات، جدران):"
    
    await query.edit_message_text(prompt_text, reply_markup=ForceReply(selective=True))
    return EDIT_NEW_VALUE

async def edit_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures new value and updates the product."""
    product_id = context.user_data["product_to_edit_id"]
    field = context.user_data["field_to_edit"]
    new_value = update.message.text

    if field == "price":
        try:
            new_value = float(new_value)
            if new_value < 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("السعر يجب أن يكون رقماً صالحاً وموجباً. يرجى المحاولة مرة أخرى:")
            return EDIT_NEW_VALUE

    if edit_existing_product(product_id, field, new_value):
        await update.message.reply_text(f"تم تحديث {field} للمنتج `{product_id}` بنجاح!", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"فشل تحديث المنتج `{product_id}`.", parse_mode=ParseMode.MARKDOWN)
    
    context.user_data.clear()
    return ConversationHandler.END


# ----------- Search Product (Conversation Handler) -
async def search_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the search product process."""
    message_source = update.callback_query.message if update.callback_query else update.message
    if update.callback_query: await update.callback_query.answer()

    await message_source.reply_text(
        "للبحث عن منتج، يرجى إدخال تسلسل المنتج:",
        reply_markup=ForceReply(selective=True)
    )
    return SEARCH_PRODUCT_ID

async def search_product_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures product ID and displays its details and image."""
    product_id = update.message.text
    product = get_product_by_id(product_id)

    if product:
        price_info = f", السعر: {product.get('price', 'غير محدد')} ع.د" if 'price' in product else ""
        category_info = f", التصنيف: {product.get('category', 'غير محدد')}" if 'category' in product else ""
        message_text = (
            f"تفاصيل المنتج `{product_id}`:\n"
            f"*اسم الشركة:* {product['companyName']}\n"
            f"*الكمية:* {product['quantity']}{price_info}{category_info}\n"
            f"*رابط الصورة:* {product['imageUrl']}"
        )
        if product['imageUrl']:
            try:
                # Send photo with caption
                await update.message.reply_photo(
                    photo=product['imageUrl'],
                    caption=message_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to send photo for {product_id}: {e}")
                await update.message.reply_text(
                    f"تم العثور على المنتج `{product_id}` ولكن فشل عرض الصورة (رابط خاطئ أو غير متوفر).\n" + message_text,
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            await update.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"المنتج ذو التسلسل `{product_id}` غير موجود في المخزن.", parse_mode=ParseMode.MARKDOWN)
    
    return ConversationHandler.END

# ------------------ Set Low Stock Threshold (Conversation Handler) ------------------
async def set_low_stock_threshold_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the process to set low stock threshold."""
    if not is_admin(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        elif update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return ConversationHandler.END

    current_threshold = get_low_stock_threshold()
    message_source = update.callback_query.message if update.callback_query else update.message
    if update.callback_query: await update.callback_query.answer()

    await message_source.reply_text(
        f"القيمة الحالية لعتبة المخزون المنخفض هي: {current_threshold}.\n"
        "يرجى إدخال القيمة الجديدة (رقم صحيح موجب):",
        reply_markup=ForceReply(selective=True)
    )
    return SET_LOW_STOCK_THRESHOLD_VALUE

async def set_low_stock_threshold_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures the new low stock threshold and saves it."""
    try:
        new_threshold = int(update.message.text)
        if new_threshold < 0:
            raise ValueError
        
        set_low_stock_threshold(new_threshold)
        await update.message.reply_text(f"تم تحديث عتبة المخزون المنخفض إلى: {new_threshold}.")
    except ValueError:
        await update.message.reply_text("القيمة يجب أن تكون رقماً صحيحاً وموجباً. يرجى المحاولة مرة أخرى:")
        return SET_LOW_STOCK_THRESHOLD_VALUE
    
    return ConversationHandler.END

# - Admin Management (Conversation Handlers) -
async def view_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays current admin IDs."""
    if not is_admin(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        elif update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return

    admins_list = get_admins()
    if not admins_list:
        message_text = "لا يوجد مشرفون مسجلون حالياً. يجب إضافة مشرف واحد على الأقل."
    else:
        message_text = "*المشرفون الحاليون:*\n"
        for i, admin_id in enumerate(admins_list):
            message_text += f"{i+1}. `{admin_id}`\n"
    
    if update.callback_query:
        await update.callback_query.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN)
        await update.callback_query.answer()
    else:
        await update.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN)


async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts process to add a new admin."""
    if not is_admin(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        elif update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return ConversationHandler.END

    message_source = update.callback_query.message if update.callback_query else update.message
    if update.callback_query: await update.callback_query.answer()

    await message_source.reply_text(
        "يرجى إدخال ID المشرف الجديد الذي تريد إضافته (رقم صحيح). يمكنك الحصول على الـ ID من @userinfobot:",
        reply_markup=ForceReply(selective=True)
    )
    return ADD_ADMIN_ID

async def add_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures new admin ID and adds it."""
    try:
        new_admin_id = int(update.message.text)
        if add_admin_id_to_data(new_admin_id):
            await update.message.reply_text(f"تمت إضافة المشرف `{new_admin_id}` بنجاح!", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"المشرف `{new_admin_id}` موجود بالفعل في قائمة المشرفين.", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("الـ ID يجب أن يكون رقماً صحيحاً. يرجى المحاولة مرة أخرى:")
        return ADD_ADMIN_ID
    
    return ConversationHandler.END

async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts process to remove an admin."""
    if not is_admin(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        elif update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return ConversationHandler.END
    
    admins_list = get_admins()
    if len(admins_list) <= 1:
        message_source = update.callback_query.message if update.callback_query else update.message
        if update.callback_query: await update.callback_query.answer()
        await message_source.reply_text("لا يمكن حذف المشرف الأخير. يجب أن يبقى مشرف واحد على الأقل.")
        return ConversationHandler.END


    message_source = update.callback_query.message if update.callback_query else update.message
    if update.callback_query: await update.callback_query.answer()

    await message_source.reply_text(
        "يرجى إدخال ID المشرف الذي تريد حذفه (رقم صحيح):",
        reply_markup=ForceReply(selective=True)
    )
    return REMOVE_ADMIN_ID

async def remove_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captures admin ID to remove and removes it."""
    try:
        admin_id_to_remove = int(update.message.text)
        
        # Prevent removing the last admin
        if len(get_admins()) <= 1 and admin_id_to_remove in get_admins():
            await update.message.reply_text("لا يمكن حذف المشرف الأخير. يجب أن يبقى مشرف واحد على الأقل.")
            return REMOVE_ADMIN_ID # Stay in this state

        if remove_admin_id_from_data(admin_id_to_remove):
            await update.message.reply_text(f"تم حذف المشرف `{admin_id_to_remove}` بنجاح!", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"المشرف `{admin_id_to_remove}` غير موجود في قائمة المشرفين.", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("الـ ID يجب أن يكون رقماً صحيحاً. يرجى المحاولة مرة أخرى:")
        return REMOVE_ADMIN_ID
    
    return ConversationHandler.END


# ----------- Cancel Function (for Conversations) ----
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels any ongoing conversation."""
    await update.message.reply_text("تم إلغاء العملية.")
    context.user_data.clear()
    return ConversationHandler.END

# ------------------ Error Handler ------------------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)


# ------------------ CallbackQueryHandler ------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles inline button presses."""
    query = update.callback_query
    
    # Handle common admin menu return
    if query.data == "admin_menu_from_manage_admins":
        await admin_menu(update, context)
        return
    elif query.data == "main_menu_from_admin":
        await menu(update, context)
        return

    # Check admin permissions for admin actions
    if query.data in ["add_product_btn", "add_quantity_btn", "subtract_quantity_btn",
                      "delete_product_btn", "edit_product_btn", "view_low_stock_btn",
                      "set_low_stock_threshold_btn", "generate_report_btn",
                      "backup_data_btn", "manage_admins_menu", "add_admin_btn", "remove_admin_btn", "view_admins_btn"]:
        if not is_admin(update.effective_user.id):
            await query.answer("عذراً، هذا الأمر مخصص للمشرفين فقط.")
            return
    
    # Delegate to specific handlers
    if query.data == "view_all_products":
        await view_products(update, context)
    elif query.data == "search_product_btn":
        await search_product_start(update, context)
    elif query.data == "inventory_summary_btn":
        await inventory_summary(update, context)
    elif query.data == "admin_menu":
        await admin_menu(update, context)
    elif query.data == "add_product_btn":
        await add_product_start(update, context)
    elif query.data == "add_quantity_btn":
        await add_quantity_start(update, context)
    elif query.data == "subtract_quantity_btn":
        await subtract_quantity_start(update, context)
    elif query.data == "delete_product_btn":
        await delete_product_start(update, context)
    elif query.data == "edit_product_btn":
        await edit_product_start(update, context)
    elif query.data == "view_low_stock_btn":
        await view_low_stock(update, context)
    elif query.data == "generate_report_btn":
        await generate_report(update, context)
    elif query.data == "backup_data_btn":
        await backup_data(update, context)
    elif query.data == "set_low_stock_threshold_btn":
        await set_low_stock_threshold_start(update, context)
    elif query.data == "manage_admins_menu":
        await manage_admins_menu(update, context)
    elif query.data == "view_admins_btn":
        await view_admins(update, context)
    elif query.data == "add_admin_btn":
        await add_admin_start(update, context)
    elif query.data == "remove_admin_btn":
        await remove_admin_start(update, context)
    


    # or if the specific handler doesn't answer it.
    if query.is_callback_query_handled is False: # Check if the query has been answered by a specific handler
        await query.answer()


def main() -> None:
    """Runs the bot."""
    application = Application.builder().token(TOKEN).build()

    # Conversation Handlers
    add_product_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add_product", add_product_start), CallbackQueryHandler(add_product_start, pattern="^add_product_btn$")],
        states={
            ADD_PRODUCT_COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_company_name)],
            ADD_PRODUCT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_id)],
            ADD_PRODUCT_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_quantity)],
            ADD_PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)],
            ADD_PRODUCT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_category)],
            ADD_PRODUCT_IMAGE_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_image_url)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    add_quantity_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add_quantity", add_quantity_start), CallbackQueryHandler(add_quantity_start, pattern="^add_quantity_btn$")],
        states={
            UPDATE_QUANTITY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_quantity_product_id)],
            UPDATE_QUANTITY_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_quantity_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    subtract_quantity_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("subtract_quantity", subtract_quantity_start), CallbackQueryHandler(subtract_quantity_start, pattern="^subtract_quantity_btn$")],
        states={
            SUBTRACT_QUANTITY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, subtract_quantity_product_id)],
            SUBTRACT_QUANTITY_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, subtract_quantity_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    delete_product_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("delete_product", delete_product_start), CallbackQueryHandler(delete_product_start, pattern="^delete_product_btn$")],
        states={
            DELETE_PRODUCT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_product_id)],
            DELETE_PRODUCT_CONFIRMATION: [CallbackQueryHandler(delete_product_confirmation, pattern="^(confirm_delete_.*|cancel_delete_product)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    edit_product_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("edit_product", edit_product_start), CallbackQueryHandler(edit_product_start, pattern="^edit_product_btn$")],
        states={
            EDIT_PRODUCT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_id)],
            EDIT_CHOICE: [CallbackQueryHandler(edit_choice, pattern="^(edit_companyName|edit_imageUrl|edit_price|edit_category|cancel_edit_product)$")],
            EDIT_NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_new_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    search_product_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search_product", search_product_start), CallbackQueryHandler(search_product_start, pattern="^search_product_btn$")],
        states={
            SEARCH_PRODUCT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_product_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    set_low_stock_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set_low_stock_threshold", set_low_stock_threshold_start), CallbackQueryHandler(set_low_stock_threshold_start, pattern="^set_low_stock_threshold_btn$")],
        states={
            SET_LOW_STOCK_THRESHOLD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_low_stock_threshold_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    add_admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add_admin", add_admin_start), CallbackQueryHandler(add_admin_start, pattern="^add_admin_btn$")],
        states={
            ADD_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    remove_admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("remove_admin", remove_admin_start), CallbackQueryHandler(remove_admin_start, pattern="^remove_admin_btn$")],
        states={
            REMOVE_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_admin_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    # Adding Handlers to the Dispatcher
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("view_products", view_products)) 
    application.add_handler(CommandHandler("view_low_stock", view_low_stock))
    application.add_handler(CommandHandler("generate_report", generate_report))
    application.add_handler(CommandHandler("inventory_summary", inventory_summary))
    application.add_handler(CommandHandler("backup_data", backup_data))
    application.add_handler(CommandHandler("view_admins", view_admins))
    application.add_handler(CommandHandler("cancel", cancel)) # Global cancel command


    application.add_handler(add_product_conv_handler)
    application.add_handler(add_quantity_conv_handler)
    application.add_handler(subtract_quantity_conv_handler)
    application.add_handler(delete_product_conv_handler)
    application.add_handler(edit_product_conv_handler)
    application.add_handler(search_product_conv_handler)
    application.add_handler(set_low_stock_conv_handler)
    application.add_handler(add_admin_conv_handler)
    application.add_handler(remove_admin_conv_handler)

    application.add_handler(CallbackQueryHandler(button_handler)) # General handler for Inline buttons

    # Error Handler
    application.add_error_handler(error_handler)

    # Run the bot
    logger.info("Starting Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Telegram Bot stopped.")

if __name__ == "__main__":
    main()
