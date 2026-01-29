"""
Comment Generator - Adds human-like context to deal notifications.
"""

import random
from typing import Optional

# Circular import prevention: we only need the data structure, but we can't import DealInfo
# if it's in a file that imports this one. So we'll use duck typing or a protocol if needed,
# or just accept 'Any' and document the expected fields.
# For now, we'll assume the input object has the necessary attributes.


class CommentGenerator:
    """Generates human-like comments for deals."""

    # Category Keywords Mapping
    CATEGORY_KEYWORDS = {
        "tech": [
            "laptop",
            "bilgisayar",
            "telefon",
            "kulaklık",
            "mouse",
            "klavye",
            "tablet",
            "monitor",
            "ekran",
            "usb",
            "şarj",
        ],
        "home": [
            "kahve",
            "tava",
            "tencere",
            "ütü",
            "süpürge",
            "yastık",
            "yorgan",
            "nevresim",
            "banyo",
            "mutfak",
            "airfryer",
        ],
        "baby": ["bebek", "bez", "mama", "oyuncak", "puset", "oto koltuğu", "biberon", "emzik"],
        "fashion": ["ayakkabı", "bot", "mont", "ceket", "tişört", "pantolon", "çanta", "saat", "gözlük"],
        "book": ["kitap", "roman", "edebiyat", "hikaye"],
        "pet": ["kedi", "köpek", "mama", "kum"],
        "gaming": ["oyun", "konsol", "ps5", "xbox", "nintendo", "gamepad"],
    }

    # Comment Templates
    COMMENTS = {
        "all_time_low": [
            "Tarihi dip fiyat! Daha ucuzu görülmedi.",
            "Bu fiyata daha önce düşmemişti, tam alım fırsatı!",
            "Rekor düşük fiyat! İhtiyacınız varsa kaçırmayın.",
            "Efsane fiyat! Bu seviyeyi bir daha zor görürüz.",
        ],
        "huge_discount": [  # > 50%
            "Yarı fiyatına düşmüş, stoklar dayanmayabilir!",
            "İnanılmaz bir indirim oranı, hemen değerlendirin.",
            "Bedavadan biraz pahalı! Bu fırsat kaçmaz.",
            "Koşun! Fiyat hatası gibi duruyor.",
        ],
        "big_discount": [  # > 30%
            "Çok ciddi bir indirim oranı, kaçırmayın.",
            "Fiyatı gayet makul seviyeye inmiş.",
            "Bütçe dostu bir fırsat yakaladık.",
            "Gözden kaçırılmayacak bir indirim.",
        ],
        "tech": [
            "Teknoloji tutkunları için harika fırsat.",
            "Cihazını yenilemek isteyenler bakabilir.",
            "Performans arayanlar için güzel seçenek.",
            "Dijital ihtiyaçlarınız için uygun fiyat.",
        ],
        "home": [
            "Evinizin ihtiyacı olabilir, fiyatı düşmüşken bakın.",
            "Ev ekonomisine katkı sağlayacak bir indirim.",
            "Mutfakta işinizi kolaylaştıracak bir ürün.",
            "Evinizi güzelleştirmek için fırsat.",
        ],
        "baby": [
            "Bebek ihtiyaçları için stok yapmalık fiyat.",
            "Anne-baba adayları bu indirimi kaçırmasın.",
            "Minikler için güzel bir sürpriz olabilir.",
        ],
        "fashion": [
            "Gardırobunuzu yenilemek için güzel zaman.",
            "Şıklığı ucuza getirmek isteyenlere.",
            "Sezonun trendi, fiyatı da düşmüş.",
        ],
        "gaming": [
            "Oyuncular toplanın! Güzel bir indirim var.",
            "Setup'ını güçlendirmek isteyenler kaçırmasın.",
            "Oyun keyfini artıracak bir fırsat.",
        ],
        "pet": [
            "Patili dostlarımız için mama/kum stoğu fırsatı.",
            "Kediniz/köpeğiniz buna bayılacak.",
        ],
        "generic": [
            "Fiyat/performans oranı dikkat çekici.",
            "Değerlendirilmesi gereken bir fırsat.",
            "Fiyat takibimize takılan güzel bir ürün.",
            "Kullanıcı yorumları genelde olumlu olan bir ürün.",
            "Etiket fiyatına göre avantajlı duruyor.",
        ],
    }

    @classmethod
    def generate_comment(cls, deal) -> str:
        """
        Generate a context-aware comment for the deal.

        Args:
            deal: DealInfo object (duck-typed)

        Returns:
            str: A short, human-like comment.
        """
        candidates = []

        # 1. Priority: All Time Low
        # We check if lowest_price_all_time logic exists or infer from deal_type if available
        # Since DealInfo might not have deal_type directly exposed or it might be a string,
        # we'll rely on the 'deal_tag' or price comparison if possible.
        # But DealInfo has 'lowest_price_180d' etc.
        # Let's assume if discount > 10% and it's close to lowest_price_180d, it's good.

        # Better: Check deal_tag or reason if available, but DealInfo is simple.
        # Let's use the data we have.

        is_all_time_low = False
        if hasattr(deal, "deal_tag") and deal.deal_tag == "FİYAT DÜŞTÜ":
            # If it's a price drop alert, check if it's near 180d low
            if deal.lowest_price_180d and deal.current_price <= deal.lowest_price_180d:
                is_all_time_low = True

        if is_all_time_low:
            candidates.extend(cls.COMMENTS["all_time_low"])

        # 2. Priority: Discount Depth
        if deal.discount_percentage >= 50:
            candidates.extend(cls.COMMENTS["huge_discount"])
        elif deal.discount_percentage >= 30:
            candidates.extend(cls.COMMENTS["big_discount"])

        # 3. Priority: Category Context
        title_lower = deal.title.lower()
        category_match = None

        for cat, keywords in cls.CATEGORY_KEYWORDS.items():
            if any(k in title_lower for k in keywords):
                category_match = cat
                break

        if category_match:
            candidates.extend(cls.COMMENTS[category_match])

        # 4. Fallback
        if not candidates:
            candidates.extend(cls.COMMENTS["generic"])

        # Select one random comment from the candidates
        # We might want to weight them? For now, random is fine.
        # If we have multiple types (e.g. Tech + Huge Discount), we mix them in the pool
        # and pick one. This gives variety.

        selected_comment = random.choice(candidates)

        return selected_comment
