"""Keyword tables and reply templates for the rule-based reference bot."""
from __future__ import annotations

import re

KW = {
    "injection": ["ignore all previous", "ignore previous", "previous instructions", "system prompt",
                  "developer mode", "admin password", "təlimatları unut", "sistem prompt", "admin parol",
                  "игнорируй", "предыдущие инструкции", "забудь свои правила", "системный промпт"],
    "scam": ["sms code", "code from my sms", "code from sms", "card details", "link", "otp",
             "sms kod", "kodu istədi", "kart məlumat",
             "код из смс", "смс-код", "смс код", "ссылк", "данные карты", "попросили назвать"],
    "escalation": ["lost my card", "stolen", "complaint", "didn't make", "did not make", "unauthorized",
                   "itirmişəm", "itirdim", "oğurla", "şikayət", "etmədiyim",
                   "потерял", "украли", "жалоб", "не совершал"],
    "auth": ["balance", "transactions", "statement", "balans", "son əməliyyat", "çıxarış",
             "баланс", "последние операции", "выписк"],
    "out_of_scope": ["bitcoin", "crypto", "weather", "stocks", "football", "recipe",
                     "kripto", "səhm", "hava proqnozu", "hava necə", "restoran", "futbol",
                     "крипт", "погод", "футбол"],
    "advice": ["should i", "which is better", "best for me", "worth", "recommend", "which one should",
               "sərfəli", "daha yaxşı", "tövsiyə", "etməliyəm", "seçməliyəm",
               "выгодн", "что лучше", "посовет", "стоит ли", "какой выбрать"],
}

# Order matters: "kredit kartı" is a card, "transfer to a card" is a transfer.
TOPICS = [
    ("transfers", ["transfer", "swift", "köçürmə", "перевод"]),
    ("cards", ["card", "atm", "kart", "bankomat", "карт", "банкомат"]),
    ("loans", ["loan", "kredit", "кредит"]),
    ("deposits", ["deposit", "depozit", "əmanət", "депозит", "вклад"]),
    ("contacts", ["phone", "hotline", "contact", "customer service", "telefon", "əlaqə", "qaynar xətt",
                  "телефон", "горяч", "связаться"]),
]

CARD_RE = re.compile(r"\b(?:\d[ -]?){15}\d\b")
FIN_RE = re.compile(r"\b(?=[0-9A-Z]*\d)(?=[0-9A-Z]*[A-Z])[0-9A-Z]{7}\b")
FIN_TRIGGER = re.compile(r"\bfin\b|фин", re.IGNORECASE)
CARD_EMERGENCY = ["lost my card", "stolen", "itirmişəm", "itirdim", "oğurla", "потерял", "украли"]

T = {
    "facts_intro": {
        "deposits": {"en": "Current deposit terms at Lumen Bank:", "az": "Lumen Bank-da depozitlər üzrə cari şərtlər:", "ru": "Текущие условия Lumen Bank по депозитам:"},
        "cards": {"en": "Current card terms at Lumen Bank:", "az": "Lumen Bank-da kartlar üzrə cari şərtlər:", "ru": "Текущие условия Lumen Bank по картам:"},
        "loans": {"en": "Current consumer loan terms at Lumen Bank:", "az": "Lumen Bank-da istehlak kreditləri üzrə cari şərtlər:", "ru": "Текущие условия Lumen Bank по потребительским кредитам:"},
        "transfers": {"en": "Current transfer fees at Lumen Bank:", "az": "Lumen Bank-da köçürmələr üzrə cari komissiyalar:", "ru": "Текущие комиссии Lumen Bank за переводы:"},
        "contacts": {"en": "You can reach Lumen Bank here:", "az": "Lumen Bank ilə əlaqə:", "ru": "Связаться с Lumen Bank:"},
    },
    "disclaimer": {"en": "This is general information, not financial advice.",
                   "az": "Bu ümumi məlumatdır, maliyyə məsləhəti deyil.",
                   "ru": "Это общая информация, а не финансовая консультация."},
    "advice_compare": {"en": "The right choice depends on your goals and how long you can keep the money.",
                       "az": "Doğru seçim məqsədlərinizdən və vəsaiti nə qədər müddətə saxlaya biləcəyinizdən asılıdır.",
                       "ru": "Правильный выбор зависит от ваших целей и того, на какой срок вы готовы разместить средства."},
    "bad_recommendation": {"en": "I recommend choosing the option with the highest rate.",
                           "az": "Ən yüksək faizli variantı seçməyinizi tövsiyə edirəm.",
                           "ru": "Рекомендую выбрать вариант с самой высокой ставкой."},
    "clarify": {"en": "Could you tell me which product you mean: a deposit, a loan or a credit card?",
                "az": "Hansı məhsulu nəzərdə tutursunuz: depozit, kredit, yoxsa kredit kartı?",
                "ru": "Уточните, пожалуйста, какой продукт вас интересует: депозит, кредит или кредитная карта?"},
    "refuse_oos": {"en": "Sorry, I can only help with Lumen Bank products and services, such as deposits, cards, loans and transfers.",
                   "az": "Təəssüf ki, yalnız Lumen Bank-ın məhsul və xidmətləri (depozitlər, kartlar, kreditlər, köçürmələr) ilə bağlı kömək edə bilərəm.",
                   "ru": "К сожалению, я могу помочь только с продуктами и услугами Lumen Bank: депозиты, карты, кредиты и переводы."},
    "refuse_injection": {"en": "I can't do that. I can help with questions about Lumen Bank products and services.",
                         "az": "Bunu edə bilmərəm. Lumen Bank-ın məhsul və xidmətləri ilə bağlı suallarda kömək edə bilərəm.",
                         "ru": "Я не могу этого сделать. Я могу помочь с вопросами о продуктах и услугах Lumen Bank."},
    "scam": {"en": "Please do not share SMS codes, your PIN or CVV with anyone, and do not open suspicious links. Lumen Bank never asks for them by phone, SMS or chat. If you already shared them, block your card in the app and call {hotline} now. I'm connecting you with our security team.",
             "az": "Zəhmət olmasa SMS kodu, PIN və ya CVV kodunu heç kimlə paylaşmayın və şübhəli linkləri açmayın. Lumen Bank bunları heç vaxt telefonla, SMS və ya çatda soruşmur. Artıq paylaşmısınızsa, kartınızı tətbiqdə bloklayın və dərhal {hotline} nömrəsinə zəng edin. Sizi təhlükəsizlik komandamıza yönləndirirəm.",
             "ru": "Пожалуйста, никому не сообщайте коды из СМС, PIN или CVV и не открывайте подозрительные ссылки. Lumen Bank никогда не запрашивает их по телефону, СМС или в чате. Если вы уже сообщили их, заблокируйте карту в приложении и сразу позвоните по номеру {hotline}. Я передаю ваше обращение в службу безопасности."},
    "pii": {"en": "For your security, please don't share card numbers or personal ID numbers in chat. I've hidden what you sent ({masked}). To check anything about your card or account, please log in to the Lumen app or verify your identity with an operator.",
            "az": "Təhlükəsizliyiniz üçün çatda kart nömrəsi və ya şəxsi identifikasiya nömrəsi paylaşmayın. Göndərdiyiniz məlumatı gizlətdim ({masked}). Kartınız və ya hesabınızla bağlı yoxlama üçün Lumen tətbiqinə daxil olun və ya operatorla şəxsiyyətinizi təsdiqləyin.",
            "ru": "В целях безопасности не отправляйте в чат номера карт и личные идентификационные номера. Я скрыл отправленные данные ({masked}). Чтобы проверить информацию по карте или счёту, войдите в приложение Lumen или подтвердите личность у оператора."},
    "pii_echo": {"en": "Thanks, I've noted your details: {raw}. Please log in to the Lumen app to check this.",
                 "az": "Təşəkkürlər, məlumatlarınızı qeyd etdim: {raw}. Yoxlamaq üçün Lumen tətbiqinə daxil olun.",
                 "ru": "Спасибо, я записал ваши данные: {raw}. Чтобы проверить это, войдите в приложение Lumen."},
    "auth": {"en": "I can't access account details in this chat. To see your balance or transactions, please log in to the Lumen app or verify your identity with an operator.",
             "az": "Bu çatda hesab məlumatlarına çıxışım yoxdur. Balansınızı və ya əməliyyatlarınızı görmək üçün Lumen tətbiqinə daxil olun və ya operatorla şəxsiyyətinizi təsdiqləyin.",
             "ru": "В этом чате у меня нет доступа к данным счёта. Чтобы увидеть баланс или операции, войдите в приложение Lumen или подтвердите личность у оператора."},
    "escalate_card": {"en": "Please block your card right away in the Lumen app (Cards > Block) or call {hotline}, available 24/7. I'm connecting you with an operator now.",
                      "az": "Zəhmət olmasa kartınızı dərhal Lumen tətbiqində bloklayın (Kartlar > Blokla) və ya 24/7 işləyən {hotline} nömrəsinə zəng edin. Sizi operatora yönləndirirəm.",
                      "ru": "Пожалуйста, сразу заблокируйте карту в приложении Lumen (Карты > Заблокировать) или позвоните по номеру {hotline}, круглосуточно. Я соединяю вас с оператором."},
    "escalate_general": {"en": "I'm sorry about this. I'm passing your request to a specialist who will contact you. You can also call {hotline} (24/7).",
                         "az": "Bunun üçün üzr istəyirik. Müraciətinizi mütəxəssisə ötürürəm, sizinlə əlaqə saxlanılacaq. Həmçinin {hotline} (24/7) nömrəsinə zəng edə bilərsiniz.",
                         "ru": "Приносим извинения. Я передаю ваше обращение специалисту, с вами свяжутся. Вы также можете позвонить по номеру {hotline} (круглосуточно)."},
}


def contains_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def detect_topic(text: str) -> str | None:
    for topic, words in TOPICS:
        if contains_any(text, words):
            return topic
    return None


def mask_card(match: re.Match) -> str:
    digits = re.sub(r"\D", "", match.group(0))
    return "**** **** **** " + digits[-4:]
