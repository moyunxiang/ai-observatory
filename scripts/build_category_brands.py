"""Build data/category_brands.csv (Task 2) from a curated selection + saved web evidence.

The brand SELECTION below is hand-curated: for each category, brands that are real
and clearly belong to it, chosen from the pages logged in data/raw/task2/evidence.jsonl
plus the category's Task 1 seed brands. This script only attaches provenance:

  - source_url: first evidence page *for this category* whose brand list contains the
    brand (after normalization + aliases). If none, the seed source (Kantar) for seed
    brands; else an evidence page from another category (logged as cross-category).
  - origin: "seed" if the brand is a Task 1 seed of this category, else "expanded".

Post-validation additions (Task 3 feedback): accepted rows of
data/raw/task2/post_validation_decisions.csv are appended with origin=added_post_validation and
the Wikipedia page as source, so `score` can report recall with and without them.

Any brand with no source fails the build, so every row stays traceable.

    python scripts/build_category_brands.py
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from observatory.data import DATA_DIR, alias_maps, load_categories, load_seed_brands  # noqa: E402
from observatory.normalize import normalize_brand  # noqa: E402

KANTAR_URLS = {
    "Kantar BrandZ 2025 Global Top 100": "https://www.mediar.cz/wp-content/uploads/2025/05/kantar-brandz-2025.pdf",
    "Kantar BrandZ 2025 China Top 100": "https://indd.adobe.com/view/publication/453609a6-8380-4e63-aa8c-f00afae4952c/qin4/publication-web-resources/pdf/Kantar_BrandZ_2025_Most_Valuable_Chinese_Brands_EN.pdf",
}

# "Brand|W" or "Brand|C"  (W = World, C = China: HQ in mainland China / Hong Kong / Macau)
SELECTION = {
    "smartphones": "Apple|W; Samsung|W; Xiaomi|C; vivo|C; Huawei|C; OPPO|C; Honor|C; realme|C; Tecno|C; Infinix|C; Motorola|W",
    "search_engines": "Google|W; Bing|W; Baidu|C; Yandex|W; Yahoo|W; DuckDuckGo|W; Ecosia|W; Brave Search|W; Sogou|C; Qwant|W; Startpage|W; Petal Search|C",
    "social_media": "Facebook|W; Instagram|W; WhatsApp|W; YouTube|W; TikTok|C; WeChat|C; Telegram|W; Facebook Messenger|W; Snapchat|W; Douyin|C; Kuaishou|C; Reddit|W; Weibo|C; X|W; QQ|C; LinkedIn|W; Xiaohongshu|C",
    "short_video": "TikTok|C; Douyin|C; Kuaishou|C; Instagram Reels|W; YouTube Shorts|W; Snapchat Spotlight|W; Facebook Reels|W; Clapper|W; Lemon8|C; Triller|W; Likee|W; Xiaohongshu|C; Skylight|W",
    "video_streaming": "Netflix|W; YouTube|W; Prime Video|W; Disney+|W; Hulu|W; HBO Max|W; Apple TV|W; Paramount+|W; Peacock|W; JioHotstar|W; Tencent Video|C; iQIYI|C; Youku|C; Mango TV|C; Bilibili|C; Crunchyroll|W",
    "music_streaming": "Spotify|W; Apple Music|W; Amazon Music|W; YouTube Music|W; Tencent Music|C; NetEase Cloud Music|C; Yandex Music|W; Deezer|W; Qobuz|W; Kugou|C",
    "ecommerce": "Amazon|W; Alibaba|C; JD|C; Pinduoduo|C; Mercado Libre|W; Taobao|C; Tmall|C; eBay|W; Shopee|W; Temu|C; Walmart|W",
    "fast_food": "McDonald's|W; KFC|W; Chipotle|W; Burger King|W; Subway|W; Taco Bell|W; Pizza Hut|W; Domino's|W; Wendy's|W; Chick-fil-A|W; Popeyes|W; Tim Hortons|W; Dairy Queen|W; Papa John's|W; Jack in the Box|W",
    "coffee_chains": "Starbucks|W; Luckin Coffee|C; Costa Coffee|W; Cotti Coffee|C; Caffè Nero|W; Caribou Coffee|W; The Coffee Bean & Tea Leaf|W; Café Amazon|W; Café Coffee Day|W; Blue Bottle Coffee|W; % Arabica|W; Compose Coffee|W; Tim Hortons|W; Dunkin'|W",
    "bubble_tea": "Mixue Bingcheng|C; Heytea|C; Chagee|C; Good Me|C; Auntea Jenny|C; Baicha Baidao|C; Nayuki|C; Chatime|W; CoCo Fresh Tea & Juice|W; Gong Cha|W; Yi Dian Dian|W; Tiger Sugar|W; Xing Fu Tang|W; Kung Fu Tea|W; The Alley|W; Tealive|W",
    "hot_pot": "Haidilao|C; Xiabu Xiabu|C; Banu|C; Coucou|C; Xiaolongkan|C; Dezhuang|C; Liuyishou|C; Shu Daxia|C; Dalongyi|C; Little Sheep|C",
    "soft_drinks": "Coca-Cola|W; Genki Forest|C; Pepsi|W; Sprite|W; Fanta|W; 7 Up|W; Dr Pepper|W; Schweppes|W; RC Cola|W; Irn-Bru|W; Jones Soda|W",
    "bottled_water": "Nongfu Spring|C; Evian|W; Perrier|W; San Pellegrino|W; Volvic|W; Nestlé Pure Life|W; Aquafina|W; Dasani|W; Poland Spring|W; Fiji Water|W; Voss|W; Ganten|C; Watsons Water|C; Topo Chico|W; Gerolsteiner|W; Icelandic Glacial|W; Crystal Geyser|W",
    "dairy": "Yili|C; Mengniu|C; Lactalis|W; Nestlé|W; Danone|W; Fonterra|W; Arla|W; FrieslandCampina|W; Amul|W; Saputo|W; Dairy Farmers of America|W; Müller|W; Grupo Lala|W",
    "baijiu": "Moutai|C; Wuliangye|C; Luzhou Laojiao|C; National Cellar 1573|C; Yanghe|C; Gujing Gong Jiu|C; Fenjiu|C; Guoyuan|C; Langjiu|C; Jiannanchun|C; Shuijingfang|C; Xifeng|C; Xijiu|C; Jiugui|C; Jiang Xiaobai|C; Niulanshan|C; Shede|C",
    "beer": "Tsingtao|C; Snow|C; Corona|W; Heineken|W; Budweiser|W; Michelob Ultra|W; Modelo|W; Guinness|W; Stella Artois|W; Carlsberg|W; Harbin|C; Yanjing|C; Zhujiang|C; Wusu|C",
    "energy_drinks": "Eastroc Beverage|C; Red Bull|W; Monster Energy|W; Celsius|W; Rockstar Energy|W; Lucozade|W; Prime|W; 5-Hour Energy|W; NOS|W; Amp|W; Krating Daeng|W; Lipovitan|W; V|W; Power Horse|W; Hi-Tiger|C",
    "soy_sauce": "Haday|C; Kikkoman|W; Lee Kum Kee|C; Yamasa|W; Pearl River Bridge|C; Qianhe|C; Chubang|C; Marukin|W; San-J|W; Wan Ja Shan|W; La Choy|W; ABC|W; Aloha Shoyu|W",
    "processed_meat": "Shuanghui|C; Yurun|C; Smithfield|W; Oscar Mayer|W; Hormel|W; Hillshire Farm|W; Boar's Head|W; Ball Park|W; Jimmy Dean|W; Tyson|W; Applegate|W; Land O' Frost|W",
    "banks": ("Chase|W; J.P. Morgan|W; Wells Fargo|W; Bank of America|W; RBC|W; HDFC Bank|W; BCA|W; CommBank|W; Morgan Stanley|W; "
              "ICBC|C; Agricultural Bank of China|C; China Construction Bank|C; Bank of China|C; China Merchants Bank|C; Bank of Communications|C; "
              "China Everbright Bank|C; China CITIC Bank|C; Bank of Ningbo|C; China Minsheng Bank|C; "
              "HSBC|W; Citi|W; BNP Paribas|W; Barclays|W; Banco Santander|W; MUFG|W; Goldman Sachs|W; Deutsche Bank|W; UBS|W; TD Bank|W"),
    "payment_networks": "Visa|W; Mastercard|W; American Express|W; UnionPay|C; Discover|W; JCB|W; Diners Club|W; RuPay|W; Elo|W; Mir|W; Interac|W",
    "digital_payments": "PayPal|W; Stripe|W; Apple Pay|W; Google Pay|W; WeChat Pay|C; Alipay|C; Venmo|W; Cash App|W; Zelle|W; Samsung Pay|W; Wise|W; PhonePe|W",
    "insurance": ("Ping An|C; China Life|C; CPIC|C; PICC|C; Taikang|C; NCI|C; Allianz|W; AXA|W; MetLife|W; Prudential|W; Generali|W; AIG|W; "
                  "Zurich|W; State Farm|W; Allstate|W; Progressive|W; Liberty Mutual|W; Nippon Life|W; Manulife|W; Aviva|W; LIC|W"),
    "health_insurance": "UnitedHealthcare|W; Elevance Health|W; Anthem|W; Aetna|W; Centene|W; Ambetter|W; Health Care Service Corporation|W; Blue Cross Blue Shield|W; Cigna|W; Kaiser Permanente|W; Humana|W",
    "mobile_carriers": ("China Mobile|C; China Telecom|C; China Unicom|C; Verizon|W; AT&T|W; T-Mobile|W; Airtel|W; Reliance Jio|W; Vodafone|W; "
                        "América Móvil|W; Orange|W; Telefónica|W; MTN|W; Deutsche Telekom|W; NTT Docomo|W; Telkomsel|W; Etisalat|W; Telenor|W; Viettel|W; Ooredoo|W; Vodafone Idea|W"),
    "isps": "Spectrum|W; Xfinity|W; AT&T|W; Verizon|W; Frontier|W; Optimum|W; Cox|W; T-Mobile|W; Google Fiber|W; Starlink|W; Astound|W; WOW!|W",
    "airlines": ("Air China|C; China Southern Airlines|C; China Eastern Airlines|C; Hainan Airlines|C; Cathay Pacific|C; Qatar Airways|W; Singapore Airlines|W; "
                 "Emirates|W; ANA|W; Turkish Airlines|W; Korean Air|W; Air France|W; Japan Airlines|W; Swiss|W; EVA Air|W; British Airways|W; Qantas|W; "
                 "Lufthansa|W; Virgin Atlantic|W; Delta Air Lines|W; American Airlines|W; United Airlines|W; Southwest Airlines|W; Ryanair|W"),
    "express_delivery": "UPS|W; FedEx|W; DHL|W; SF Express|C; ZTO Express|C; YTO Express|C; Yunda|C; STO Express|C; J&T Express|C; JD Logistics|C; USPS|W; Royal Mail|W; DPD|W; GLS|W; Aramex|W",
    "food_delivery": "Meituan|C; Ele.me|C; DoorDash|W; Uber Eats|W; Deliveroo|W; Just Eat Takeaway|W; Zomato|W; Swiggy|W; Grab|W; iFood|W; Foodpanda|W; Glovo|W; Talabat|W; Baemin|W",
    "ride_hailing": "Uber|W; Didi|C; Lyft|W; Grab|W; Bolt|W; inDrive|W; Ola|W; Gojek|W; Yandex Go|W; Careem|W",
    "online_travel": "Ctrip|C; Booking.com|W; Qunar|C; Fliggy|C; Expedia|W; Airbnb|W; MakeMyTrip|W; Tongcheng|C; Tripadvisor|W; Agoda|W; Priceline|W; KAYAK|W; Despegar|W; eDreams|W",
    "hotel_chains": ("Hilton|W; Marriott|W; Hyatt|W; IHG|W; Holiday Inn|W; Four Seasons|W; The Ritz-Carlton|W; Sheraton|W; Shangri-La|C; Hampton by Hilton|W; "
                     "Best Western|W; Ibis|W; Sofitel|W; Fairmont|W; Mandarin Oriental|C; Hanting|C; Waldorf Astoria|W; Taj Hotels|W; Motel 6|W"),
    "restaurant_reviews": "Dianping|C; Yelp|W; Tripadvisor|W; Google Maps|W; OpenTable|W; Zomato|W; Foursquare|W; Zagat|W; TheFork|W; Michelin Guide|W; Tabelog|W; Resy|W",
    "real_estate_agencies": ("KE|C; Lianjia|C; Compass|W; eXp Realty|W; RE/MAX|W; Century 21|W; Coldwell Banker|W; Keller Williams|W; Sotheby's International Realty|W; "
                             "Berkshire Hathaway HomeServices|W; Douglas Elliman|W; Redfin|W; Better Homes and Gardens Real Estate|W"),
    "property_developers": "Vanke|C; Poly|C; CR Land|C; China Overseas Land|C; Greentown|C; China Merchants Shekou|C; C&D Real Estate|C; China Jinmao|C; Yuexiu Property|C; Binjiang Group|C; Greenland|C",
    "electric_vehicles": ("Tesla|W; BYD|C; Li Auto|C; Xpeng|C; NIO|C; Geely|C; Leapmotor|C; Wuling|C; Xiaomi|C; BMW|W; Volkswagen|W; Mercedes-Benz|W; "
                          "Hyundai|W; Kia|W; Ford|W; Audi|W; Lucid|W; Rivian|W; Nissan|W"),
    "cars": "Toyota|W; Mercedes-Benz|W; BMW|W; Volkswagen|W; Porsche|W; Audi|W; Tesla|W; BYD|C; Ferrari|W; Hyundai|W; Ford|W; Honda|W; Nissan|W; Kia|W; Chevrolet|W; Geely|C",
    "luxury_fashion": "Louis Vuitton|W; Hermès|W; Chanel|W; Gucci|W; Dior|W; Prada|W; Burberry|W; Moncler|W; Coach|W; Michael Kors|W; Tom Ford|W; Dolce & Gabbana|W; Christian Louboutin|W; Polo Ralph Lauren|W",
    "sportswear": "Nike|W; Adidas|W; Anta|C; Puma|W; Lululemon|W; Under Armour|W; New Balance|W; ASICS|W; Skechers|W; Li-Ning|C",
    "fast_fashion": "Zara|W; Uniqlo|W; Shein|C; H&M|W; Mango|W; Gap|W; Primark|W; Fashion Nova|W; Forever 21|W; ASOS|W; Boohoo|W; New Look|W; Stradivarius|W",
    "cosmetics": ("L'Oréal Paris|W; Chanel|W; Lancôme|W; Estée Lauder|W; Shiseido|W; Nivea|W; Guerlain|W; Maybelline|W; MAC|W; NARS|W; Clinique|W; "
                  "Fenty Beauty|W; Dior|W; Revlon|W; CoverGirl|W; e.l.f.|W; Avon|W; Pechoin|C"),
    "jewelry": "Chow Tai Fook|C; Cartier|W; Tiffany & Co.|W; Bulgari|W; Pandora|W; Swarovski|W; Chopard|W; Chow Sang Sang|C; Lao Feng Xiang|C; Luk Fook|C; Zhou Da Sheng|C; Chao Hong Ji|C; Laopu Gold|C",
    "home_appliances": "Haier|C; Midea|C; Gree|C; Whirlpool|W; Electrolux|W; Bosch|W; LG|W; Samsung|W; Beko|W; Siemens|W; Miele|W; Panasonic|W; Dyson|W; Hisense|C; GE Appliances|W",
    "air_conditioners": "Gree|C; Daikin|W; Carrier|W; Midea|C; LG|W; Mitsubishi Electric|W; Panasonic|W; Trane|W; Haier|C; Hitachi|W; Johnson Controls|W",
    "televisions": "TCL|C; Samsung|W; Hisense|C; LG|W; Xiaomi|C; Vizio|W; Sony|W; Panasonic|W; Roku|W; Philips|W",
    "laptops": "Lenovo|C; Dell|W; HP|W; Apple|W; Asus|W; Acer|W; Microsoft Surface|W; MSI|W; Razer|W; Alienware|W; Huawei|C",
    "drones": "DJI|C; Autel|C; Skydio|W; Parrot|W; Yuneec|C; Hubsan|C; PowerVision|C; HoverAir|C; Potensic|C; Holy Stone|W; Antigravity|C; Insta360|C",
    "game_consoles": "Xbox|W; PlayStation|W; Nintendo|W; Steam Deck|W; ROG Ally|W; Legion Go|C; MSI Claw|W; Ayaneo|C; Meta Quest|W; Sega|W; Atari|W; Nex Playground|W",
    "consumer_electronics": "Sony|W; Apple|W; Samsung|W; LG|W; Panasonic|W; Huawei|C; Xiaomi|C; Philips|W; Toshiba|W; Epson|W; Bose|W",
    "ai_chatbots": "ChatGPT|W; DeepSeek|C; Gemini|W; Perplexity|W; Claude|W; Microsoft Copilot|W; Grok|W; Poe|W; Meta AI|W; Mistral|W; Doubao|C; Kimi|C; ChatGLM|C",
    "supermarkets": "Walmart|W; Costco|W; Aldi|W; Freshippo|C; Carrefour|W; Lidl|W; Tesco|W; Kroger|W; Albertsons|W; Aeon|W; Edeka|W; Auchan|W; Kaufland|W; Lotte Mart|W",
    "home_improvement": "The Home Depot|W; Lowe's|W; Ace Hardware|W; True Value|W; Menards|W; Leroy Merlin|W; B&Q|W; Castorama|W; Screwfix|W; Bunnings|W; OBI|W; Bauhaus|W; Sodimac|W",
    "furniture": "IKEA|W; Wayfair|W; Williams-Sonoma|W; Pottery Barn|W; West Elm|W; Ashley Furniture|W; RH|W; La-Z-Boy|W; Rooms To Go|W; Raymour & Flanigan|W",
    "tcm": "Tong Ren Tang|C; Yunnan Baiyao|C; Dong E E Jiao|C; CR Sanjiu|C; Pien Tze Huang|C; Guangyuyuan|C; Chen Liji|C; Hu Qing Yu Tang|C; Baiyunshan|C; Eu Yan Sang|W",
    "online_healthcare": "WeDoctor|C; Ping An Good Doctor|C; JD Health|C; AliHealth|C; Haodf|C; Teladoc|W; Amwell|W; Doctor On Demand|W; MDLIVE|W; Sesame|W; PlushCare|W; LifeMD|W; LiveHealth Online|W",
    "job_platforms": "Boss Zhipin|C; LinkedIn|W; Indeed|W; Glassdoor|W; ZipRecruiter|W; Monster|W; CareerBuilder|W; SimplyHired|W; Dice|W; FlexJobs|W; Zhaopin|C; 51job|C; Liepin|C; Lagou|C; Maimai|C",
    "news_apps": "Toutiao|C; Google News|W; Apple News|W; Flipboard|W; SmartNews|W; Yahoo News|W; BBC News|W; CNN|W; AP News|W; NewsBreak|W; Fox News|W; The New York Times|W; Tencent News|C; NetEase News|C",
    "video_games": ("Tencent|C; NetEase|C; Sony Interactive Entertainment|W; Xbox|W; Nintendo|W; Electronic Arts|W; Take-Two Interactive|W; Valve|W; Epic Games|W; "
                    "Roblox|W; miHoYo|C; Bandai Namco|W; Nexon|W; Sega|W; Krafton|W; Konami|W; Activision Blizzard|W; Riot Games|W; Supercell|W"),
    "movie_studios": ("Disney|W; Warner Bros.|W; Universal Pictures|W; Sony Pictures|W; Paramount Pictures|W; Lionsgate|W; A24|W; Amazon MGM Studios|W; "
                      "20th Century Studios|W; Columbia Pictures|W; DreamWorks|W; Marvel Studios|W; Lucasfilm|W; Legendary|W; Blumhouse|W; Neon|W"),
    "cigarettes": "Marlboro|W; L&M|W; Pall Mall|W; Winston|W; Camel|W; Rothmans|W; Chesterfield|W; Newport|W; Gold Flake|W; Sampoerna|W",
}

LABEL = {"W": "World", "C": "China"}


def parse_selection(spec: str) -> list[tuple[str, str]]:
    out = []
    for item in spec.split(";"):
        name, wc = item.strip().rsplit("|", 1)
        out.append((name.strip(), LABEL[wc.strip()]))
    return out


def main() -> int:
    evidence = [json.loads(line) for line in open(DATA_DIR / "raw" / "task2" / "evidence.jsonl", encoding="utf-8")]
    seeds = load_seed_brands()
    b2c = [c["category_id"] for c in load_categories(b2c_only=True)]
    amaps = alias_maps(b2c)

    missing_cats = sorted(set(b2c) - set(SELECTION))
    if missing_cats:
        print(f"No selection for: {missing_cats}")
        return 1

    rows, errors, cross = [], [], []
    for cid in b2c:
        amap = amaps[cid]
        seed_by_key = {normalize_brand(s["brand"], amap): s for s in seeds if s["primary_category_id"] == cid}
        for brand, wc in parse_selection(SELECTION[cid]):
            key = normalize_brand(brand, amap)
            url, method = None, None
            for ev in evidence:
                if ev["category_id"] == cid and key in {normalize_brand(b, amap) for b in ev["brands_on_page"]}:
                    url, method = ev["url"], ev["method"]
                    break
            seed = seed_by_key.get(key)
            if url is None and seed:
                url, method = KANTAR_URLS[seed["source_list"].split("; ")[0]], "kantar_seed"
            if url is None:
                for ev in evidence:
                    if key in {normalize_brand(b, amap) for b in ev["brands_on_page"]}:
                        url, method = ev["url"], "cross_category:" + ev["method"]
                        cross.append(f"{cid}/{brand} <- {ev['category_id']}")
                        break
            if url is None:
                errors.append(f"{cid}/{brand}: no evidence")
                continue
            if seed and seed["world_china"] != wc:
                errors.append(f"{cid}/{brand}: world_china {wc} != seed {seed['world_china']}")
            rows.append({"category_id": cid, "brand": brand, "world_china": wc,
                         "origin": "seed" if seed else "expanded", "source_url": url, "source_method": method})

    existing = {(r["category_id"], normalize_brand(r["brand"], amaps[r["category_id"]])) for r in rows}
    n_post = 0
    with open(DATA_DIR / "raw" / "task2" / "post_validation_decisions.csv", newline="", encoding="utf-8") as f:
        for d in csv.DictReader(f):
            if d["decision"] != "accept":
                continue
            key = (d["category_id"], normalize_brand(d["brand"], amaps[d["category_id"]]))
            if key in existing:
                errors.append(f"{d['category_id']}/{d['brand']}: post-validation addition already in table")
                continue
            existing.add(key)
            n_post += 1
            rows.append({"category_id": d["category_id"], "brand": d["brand"], "world_china": d["world_china"],
                         "origin": "added_post_validation", "source_url": d["wiki_url"],
                         "source_method": d.get("source_method") or "wikipedia_summary"})

    if errors:
        print("\n".join(errors))
        return 1
    with open(DATA_DIR / "category_brands.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows ({n_post} added_post_validation) for {len(b2c)} categories -> data/category_brands.csv")
    if cross:
        print(f"{len(cross)} cross-category sources: " + "; ".join(cross))
    return 0


if __name__ == "__main__":
    sys.exit(main())
