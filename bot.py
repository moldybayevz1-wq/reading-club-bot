"""
Reading Club — English level test bot (Kazakh interface)

Запуск:
    pip install "python-telegram-bot>=21,<22"
    export BOT_TOKEN="токен от @BotFather"
    export ADMIN_CHAT_ID="ваш Telegram ID"   # необязательно: сюда придут результаты
    python bot.py
"""
import asyncio
import csv
import logging
import os
import random
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
RESULTS_FILE = "results.csv"

PHONE = "+7 771 385 0305"
WHATSAPP_URL = "https://wa.me/77713850305"
PRICE = "3 990 ₸"

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Сұрақтар: (сұрақ, [жауап нұсқалары], дұрыс жауаптың индексі)
# Әр деңгейге 5 сұрақ, барлығы 25
# ---------------------------------------------------------------------------
QUESTIONS = [
    # Beginner
    ("I ___ a student.", ["am", "is", "are", "be"], 0),
    ("She ___ from Kazakhstan.", ["are", "is", "am", "do"], 1),
    ("They ___ two brothers.", ["has", "is", "have", "are"], 2),
    ("___ you speak English?", ["Does", "Are", "Is", "Do"], 3),
    ("There ___ a book on the table.", ["is", "are", "am", "be"], 0),
    # Elementary
    ("Yesterday I ___ to the cinema.", ["go", "goes", "went", "gone"], 2),
    ("Look! He ___ TV now.", ["watches", "is watching", "watch", "watched"], 1),
    ("This bag is ___ than that one.", ["big", "biggest", "more big", "bigger"], 3),
    ("I don't have ___ money.", ["any", "some", "a", "an"], 0),
    ("What time ___ you usually get up?", ["does", "are", "do", "did"], 2),
    # Pre-Intermediate
    ("I ___ in Almaty since 2018.", ["live", "have lived", "lived", "am living"], 1),
    ("If it rains tomorrow, we ___ at home.", ["stay", "stayed", "would stay", "will stay"], 3),
    ("You ___ wear a seatbelt in the car. It's the law.", ["might", "can", "must", "would"], 2),
    ("English is ___ all over the world.", ["speak", "spoken", "speaking", "spoke"], 1),
    ("When I was a child, I used to ___ football every day.", ["play", "playing", "played", "plays"], 0),
    # Intermediate
    ("If I ___ you, I would take that job.", ["am", "was", "were", "be"], 2),
    (
        "By the time we arrived, the film ___.",
        ["already started", "had already started", "has already started", "was already starting"],
        1,
    ),
    ("I'm looking forward ___ you.", ["to see", "see", "seeing", "to seeing"], 3),
    ("She suggested ___ a break.", ["to take", "taking", "take", "took"], 1),
    ("The man ___ car was stolen called the police.", ["who", "which", "whose", "whom"], 2),
    # Upper-Intermediate
    ("I wish I ___ more time yesterday.", ["have", "had", "would have", "had had"], 3),
    ("Hardly ___ the house when it started to rain.", ["I had left", "had I left", "I left", "did I leave"], 1),
    ("He denied ___ the window.", ["to break", "break", "breaking", "having broke"], 2),
    ("The company is ___ to launch a new product next month.", ["put", "made", "done", "set"], 3),
    ("Had I known, I ___ you.", ["would tell", "would have told", "told", "will tell"], 1),
]

# (минимум ұпай, деңгей, CEFR, сипаттама)
LEVELS = [
    (
        21,
        "Upper-Intermediate",
        "B2",
        "Керемет нәтиже! 🦋 Сен ағылшын тілін еркін меңгеріп келесің. "
        "Біздің клубта күрделі кітаптарды оқып, терең пікірталастарға қатыса аласың.",
    ),
    (
        16,
        "Intermediate",
        "B1–B2",
        "Өте жақсы! Сен ағылшынша өз ойыңды анық жеткізе аласың. "
        "Клубта сөздік қорыңды кеңейтіп, сөйлеуді одан әрі дамытасың.",
    ),
    (
        11,
        "Pre-Intermediate",
        "A2–B1",
        "Жақсы бастама! Негізгі грамматиканы білесің. "
        "Кітап оқу арқылы жаңа сөздерді үйреніп, сенімділігіңді арттырасың.",
    ),
    (
        6,
        "Elementary",
        "A2",
        "Сен дұрыс жолдасың! Базалық білімің бар. "
        "Қарапайым кітаптарды оқып, күн сайын алға жылжисың.",
    ),
    (
        0,
        "Beginner",
        "A1",
        "Бастау — ең маңызды қадам! 🌱 Біз сені қолдаймыз: "
        "жеңіл мәтіндерден бастап, қадам-қадаммен өсесің.",
    ),
]


def get_level(score: int):
    for min_score, name, cefr, text in LEVELS:
        if score >= min_score:
            return name, cefr, text
    return LEVELS[-1][1:]


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Тестті бастау", callback_data="begin")]])
    await update.message.reply_text(
        "📚 *Reading Club*\n"
        "_Read together. Grow together._\n\n"
        "Сәлем! Мен сенің ағылшын тілі деңгейіңді анықтауға көмектесемін.\n\n"
        "✅ 25 сұрақ\n"
        "⏱ шамамен 5–7 минут\n"
        "🎯 соңында клубтағы өз деңгейіңді білесің\n\n"
        "Жауапты білмесең, болжама — өз деңгейіңді дәл анықтау үшін "
        "«білмеймін» дегенді таңда да, келесі сұраққа өт.",
        reply_markup=kb,
        parse_mode="Markdown",
    )


async def begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data.clear()
    context.user_data["awaiting_name"] = True
    await q.message.reply_text("Алдымен танысайық! Атың кім? ✍️")


async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_name"):
        await update.message.reply_text("Тестті бастау үшін /start басыңыз.")
        return
    context.user_data["awaiting_name"] = False
    context.user_data["name"] = update.message.text.strip()[:60]
    context.user_data["idx"] = 0
    context.user_data["score"] = 0
    await update.message.reply_text(f"Өте жақсы, {context.user_data['name']}! Бастаймыз 👇")
    await send_question(update.message, context)


async def send_question(message, context: ContextTypes.DEFAULT_TYPE, edit: bool = False):
    idx = context.user_data["idx"]
    text, options, correct = QUESTIONS[idx]

    # нұсқаларды араластырамыз, дұрыс жауап орнын есте сақтаймыз
    order = list(range(len(options)))
    random.shuffle(order)
    context.user_data["correct_pos"] = order.index(correct)

    rows = [
        [InlineKeyboardButton(options[o], callback_data=f"a:{idx}:{pos}")]
        for pos, o in enumerate(order)
    ]
    rows.append([InlineKeyboardButton("🤷 Білмеймін", callback_data=f"a:{idx}:-1")])

    body = f"*Сұрақ {idx + 1}/{len(QUESTIONS)}*\n\n{text}"
    markup = InlineKeyboardMarkup(rows)
    if edit:
        await message.edit_text(body, reply_markup=markup, parse_mode="Markdown")
    else:
        await message.reply_text(body, reply_markup=markup, parse_mode="Markdown")


async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ud = context.user_data
    if "idx" not in ud:
        await q.message.reply_text("Сессия аяқталды. Қайта бастау үшін /start басыңыз.")
        return

    _, q_idx, pos = q.data.split(":")
    if int(q_idx) != ud["idx"]:  # ескі батырма басылды
        return

    if int(pos) == ud["correct_pos"]:
        ud["score"] += 1
    ud["idx"] += 1

    if ud["idx"] >= len(QUESTIONS):
        await finish(q, update, context)
    else:
        await send_question(q.message, context, edit=True)


async def finish(q, update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    score = ud["score"]
    level, cefr, desc = get_level(score)
    user = update.effective_user

    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💬 WhatsApp-қа жазу", url=WHATSAPP_URL)],
            [InlineKeyboardButton("🔄 Тестті қайта тапсыру", callback_data="begin")],
        ]
    )
    await q.message.edit_text(
        f"🎉 *Тест аяқталды, {ud['name']}!*\n\n"
        f"Нәтиже: *{score}/{len(QUESTIONS)}*\n"
        f"Сенің деңгейің: *{level}* ({cefr})\n\n"
        f"{desc}\n\n"
        "━━━━━━━━━━━━\n"
        "📖 *Reading Club*\n"
        "• 4 апта · 12 кездесу\n"
        "• Аптасына 2 рет — Book Discussion\n"
        "• Аптасына 1 рет — Weekly Recap\n"
        "• Vocabulary Quiz, Kahoot, mini-prizes\n"
        "• English-speaking community\n\n"
        f"💰 Қатысу құны: *{PRICE}*\n"
        f"📞 Жекеге жазыңыз немесе WhatsApp: {PHONE}",
        reply_markup=kb,
        parse_mode="Markdown",
    )

    save_result(user, ud["name"], score, level)
    if ADMIN_CHAT_ID:
        username = f"@{user.username}" if user.username else "username жоқ"
        try:
            await context.bot.send_message(
                ADMIN_CHAT_ID,
                f"🆕 Жаңа нәтиже\n"
                f"Аты: {ud['name']}\n"
                f"Telegram: {username} (id {user.id})\n"
                f"Ұпай: {score}/{len(QUESTIONS)}\n"
                f"Деңгей: {level} ({cefr})",
            )
        except Exception as e:  # noqa: BLE001
            logging.warning("Admin notify failed: %s", e)


def save_result(user, name, score, level):
    new_file = not os.path.exists(RESULTS_FILE)
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["date", "telegram_id", "username", "name", "score", "level"])
        w.writerow(
            [datetime.now().isoformat(timespec="seconds"), user.id, user.username or "", name, score, level]
        )


class _Ping(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def start_ping_server():
    """Мини-сервер для бесплатных хостингов (Render): внешний пинг не даёт боту уснуть."""
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), _Ping)
    threading.Thread(target=server.serve_forever, daemon=True).start()


def main():
    start_ping_server()
    asyncio.set_event_loop(asyncio.new_event_loop())  # нужно для Python 3.14+
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(begin, pattern="^begin$"))
    app.add_handler(CallbackQueryHandler(answer, pattern=r"^a:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
