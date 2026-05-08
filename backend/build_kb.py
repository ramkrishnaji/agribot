import json
import time
import re
import torch
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from concurrent.futures import ThreadPoolExecutor, as_completed

TARGET_COUNT = 10000
KNOWLEDGE_PATH = "knowledge.json"
EMBEDDINGS_PATH = "embeddings.pt"
HEADERS = {"User-Agent": "AgriBot/1.0 (Educational Research Project)"}

# Section name -> URL path segment for matching article links
KJ_SECTIONS = [
    "https://krishijagran.com/agripedia",
    "https://krishijagran.com/crop-care",
    "https://krishijagran.com/news",
    "https://krishijagran.com/success-story",
    "https://krishijagran.com/agriculture-world",
    "https://krishijagran.com/animal-husbandry",
    "https://krishijagran.com/farm-mechanization",
]

def get_kj_article_links(section_url, max_pages=25):
    """Extract article links from a KJ section listing page."""
    links = set()
    section_path = section_url.rstrip("/").split("/")[-1]
    # Match relative URLs like /agripedia/some-slug/ or absolute
    rel_pattern = re.compile(rf"^/{re.escape(section_path)}/[a-z0-9][a-z0-9\-]+/$")
    
    for page in range(1, max_pages + 1):
        url = f"{section_url}?page={page}" if page > 1 else section_url
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, "html.parser")
            found_any = False
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if not href.endswith("/"):
                    href += "/"
                if rel_pattern.match(href):
                    full_url = f"https://krishijagran.com{href}"
                    links.add(full_url)
                    found_any = True
                elif href.startswith("https://krishijagran.com/"):
                    # Check absolute URLs too
                    path = "/" + href.replace("https://krishijagran.com/", "")
                    if rel_pattern.match(path):
                        links.add(href)
                        found_any = True
            if not found_any:
                break
        except Exception:
            pass
    return links

def scrape_kj_article(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        article = soup.find("div", class_="article-content") or soup.find("article") or soup.find("div", class_="post-content")
        if not article:
            return []
        paragraphs = []
        for p in article.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 80 and not text.startswith("Also Read") and not text.startswith("Subscribe"):
                paragraphs.append(text)
        return paragraphs
    except Exception:
        return []

# ─── ICAR Article Crawler ────────────────────────────────────────────
ICAR_ARCHIVE_URLS = [
    "https://epubs.icar.org.in/index.php/IndFarm/issue/current",
    "https://epubs.icar.org.in/index.php/IndFarm/issue/archive",
]

def get_icar_article_links():
    links = set()
    for url in ICAR_ARCHIVE_URLS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/article/view/" in href and "/article/view/" in href:
                    links.add(href)
        except Exception:
            pass
    return links

def scrape_icar_article(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        abstract = soup.find("div", class_="item abstract") or soup.find("section", class_="item abstract")
        if abstract:
            text = abstract.get_text(strip=True)
            if len(text) > 80:
                return [text]
        return []
    except Exception:
        return []

# ─── Curated Indian Agriculture Knowledge ────────────────────────────
def get_curated_content():
    """Comprehensive curated paragraphs about Indian agriculture from official sources."""
    return [
        # ICAR - from icar.org.in/en/about-us
        "The Indian Council of Agricultural Research (ICAR) is an autonomous organisation under the Department of Agricultural Research and Education (DARE), Ministry of Agriculture and Farmers Welfare, Government of India. Formerly known as Imperial Council of Agricultural Research, it was established on 16 July 1929 as a registered society under the Societies Registration Act, 1860. The ICAR has its headquarters at New Delhi.",
        "ICAR is the apex body for co-ordinating, guiding and managing research and education in agriculture including horticulture, fisheries and animal sciences in the entire country. With 113 ICAR institutes and 74 agricultural universities spread across the country, this is one of the largest national agricultural systems in the world.",
        "ICAR has played a pioneering role in ushering Green Revolution and subsequent developments in agriculture in India through its research and technology development that has enabled the country to increase the production of foodgrains by 6.21 times, horticultural crops by 11.53 times, fish by 21.61 times, milk by 13.01 times and eggs by 70.74 times since 1950-51 to 2021-22, thus making a visible impact on the national food and nutritional security.",

        # Government Schemes
        "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi) is a Central Sector scheme launched in February 2019 that provides income support of Rs 6,000 per year to all landholding farmer families across the country. The amount is paid in three equal installments of Rs 2,000 each, directly into the bank accounts of eligible farmers. As of 2024, the scheme has benefited over 11 crore farmers.",
        "Pradhan Mantri Fasal Bima Yojana (PMFBY) is the government crop insurance scheme launched in 2016. It provides comprehensive crop insurance against non-preventable natural risks from pre-sowing to post-harvest. Farmers pay a premium of only 2% for Kharif crops, 1.5% for Rabi crops, and 5% for commercial and horticultural crops.",
        "The Soil Health Card (SHC) scheme was launched in 2015 to provide soil health cards to all farmers in the country. The card carries crop-wise recommendations of nutrients and fertilizers required for individual farms, helping farmers improve productivity through judicious use of inputs. Over 23 crore soil health cards have been distributed.",
        "The Minimum Support Price (MSP) is the price at which the Government of India purchases crops from farmers. MSP is announced for 22 mandated crops and fair and remunerative price (FRP) for sugarcane. The Commission for Agricultural Costs and Prices (CACP) recommends MSPs based on cost of production, demand-supply, market price trends, and other factors.",
        "The National Mission for Sustainable Agriculture (NMSA) aims to make Indian agriculture more productive, sustainable, remunerative and climate resilient by promoting location specific integrated and composite farming systems, soil and moisture conservation measures, comprehensive soil health management, and efficient water management practices.",
        "Rashtriya Krishi Vikas Yojana (RKVY) was launched in 2007 to incentivize states to increase public investment in agriculture and allied sectors. It provides flexibility and autonomy to states in planning and executing agriculture development programs based on local needs and priorities.",
        "The e-NAM (National Agriculture Market) is a pan-India electronic trading portal that networks existing APMC mandis to create a unified national market for agricultural commodities. It promotes transparency in pricing, removes information asymmetry, and enables farmers to discover better prices for their produce.",
        "Kisan Credit Card (KCC) scheme provides farmers with affordable credit for cultivation, post-harvest expenses, produce marketing, and maintenance of farm assets. The interest rate is 4% per annum for loans up to Rs 3 lakh (after interest subvention). KCC has been extended to fisheries and animal husbandry sectors as well.",
        "The Paramparagat Krishi Vikas Yojana (PKVY) promotes organic farming through adoption of organic village clusters. Under this scheme, groups of 50 or more farmers form a cluster of 50 acres each to take up organic farming. The government provides Rs 50,000 per hectare for three years for organic inputs, seeds, and marketing.",

        # Major Crops
        "Rice is India's most important food crop and the staple food for over 65% of the population. India is the world's second-largest producer of rice after China. Major rice-growing states include West Bengal, Uttar Pradesh, Andhra Pradesh, Punjab, Tamil Nadu, Odisha, Bihar, and Chhattisgarh. India produces around 130 million tonnes of rice annually.",
        "Wheat is the second most important cereal crop in India after rice. India is the second-largest wheat producer in the world. Major wheat-growing states are Uttar Pradesh, Punjab, Haryana, Madhya Pradesh, and Rajasthan. The crop is grown during the Rabi season (October-March) and India produces around 110 million tonnes annually.",
        "Sugarcane is one of the most important commercial crops in India. India is the world's second-largest producer of sugarcane after Brazil. Major sugarcane-producing states include Uttar Pradesh, Maharashtra, Karnataka, Tamil Nadu, and Gujarat. Sugarcane requires tropical or subtropical climate with hot and humid weather.",
        "Cotton is the most important fibre crop in India and is known as 'White Gold'. India is the largest producer of cotton in the world. Major cotton-producing states include Gujarat, Maharashtra, Telangana, Andhra Pradesh, Rajasthan, Madhya Pradesh, Haryana, and Punjab. Bt cotton has significantly increased yields since its introduction in 2002.",
        "India is the world's largest producer, consumer, and exporter of spices. Major spices grown include black pepper, cardamom, turmeric, ginger, chilli, cumin, coriander, and fennel. Kerala is known as the 'Spice Garden of India' and produces most of the country's black pepper, cardamom, and vanilla.",
        "Tea is one of India's most important plantation crops. India is the second-largest tea producer in the world after China. Major tea-producing regions include Assam, Darjeeling (West Bengal), Nilgiri Hills (Tamil Nadu), and Kerala. Assam alone produces over 50% of India's total tea production.",
        "Potato is the most important vegetable crop in India. India is the second-largest potato producer in the world after China. Major potato-growing states include Uttar Pradesh, West Bengal, Bihar, Gujarat, Madhya Pradesh, and Punjab. Potatoes grow best in cool climatic conditions with temperatures between 15-25°C.",
        "India is the largest producer of pulses in the world, accounting for about 25% of global production. Major pulses grown include chickpea (chana), pigeon pea (arhar/tur), lentil (masoor), green gram (moong), and black gram (urad). Madhya Pradesh is the largest pulse-producing state.",
        "Maize (corn) is the third most important cereal crop in India after rice and wheat. It is used for food, animal feed, and industrial purposes. Major maize-producing states include Karnataka, Madhya Pradesh, Bihar, Tamil Nadu, Rajasthan, and Andhra Pradesh.",
        "India is the largest producer and consumer of milk in the world, producing about 230 million tonnes annually. The White Revolution (Operation Flood), launched by Dr. Verghese Kurien in 1970, transformed India from a milk-deficient nation to the world's largest milk producer.",
        "Jute is known as the 'Golden Fibre' and India is the largest producer of jute in the world. West Bengal alone produces about 75% of India's total jute production. Other jute-growing states include Bihar, Assam, and Odisha. Jute requires hot and humid climate with temperatures between 24-35°C.",
        "Coconut is an important plantation crop in India. India is the largest producer of coconuts in the world. Major coconut-producing states include Kerala, Karnataka, Tamil Nadu, and Andhra Pradesh. Kerala is called the 'Land of Coconuts' and accounts for about 45% of India's coconut production.",
        "India is the second-largest fruit producer in the world after China. Major fruits grown include mango, banana, papaya, guava, orange, apple, grapes, and pomegranate. Maharashtra is the largest mango producer, while Tamil Nadu leads in banana production. India produces over 100 million tonnes of fruits annually.",
        "India is the second-largest vegetable producer in the world after China. Major vegetables grown include potato, tomato, onion, brinjal, cabbage, cauliflower, okra, and peas. India produces over 200 million tonnes of vegetables annually from about 10 million hectares.",

        # Soil Types
        "Alluvial soil is the most widely spread and important soil in India, covering about 40% of the total area. It is found in the Indo-Gangetic plains and river deltas. Alluvial soil is very fertile and ideal for growing rice, wheat, sugarcane, and other crops. It is rich in potash but poor in phosphorus.",
        "Black soil (Regur soil) is found mainly in the Deccan Plateau of Maharashtra, Madhya Pradesh, Gujarat, Andhra Pradesh, and Tamil Nadu. It is formed from volcanic basalt rock and is excellent for growing cotton, hence also called 'Black Cotton Soil'. It has high moisture-retaining capacity.",
        "Red soil covers about 10% of India's total area and is found in Tamil Nadu, Karnataka, Andhra Pradesh, Odisha, Jharkhand, and parts of Madhya Pradesh. It is formed due to weathering of old crystalline and metamorphic rocks. Red soil is suitable for growing millets, groundnut, and pulses.",
        "Laterite soil is found in areas with high temperature and heavy rainfall such as Kerala, Karnataka, Tamil Nadu, and Meghalaya. It is rich in iron and aluminium but deficient in nitrogen, phosphorus, and potassium. With proper fertilization, it is suitable for tea, coffee, rubber, and cashew cultivation.",

        # Irrigation
        "India has one of the largest irrigation networks in the world. About 48% of India's net sown area is irrigated. Major sources of irrigation include canals, tube wells, tanks, and wells. Groundwater accounts for about 62% of total irrigation in India.",
        "Drip irrigation is a method that saves 30-70% water compared to flood irrigation. It delivers water directly to the root zone of plants through a network of pipes and emitters. The Government of India promotes drip irrigation through the Pradhan Mantri Krishi Sinchayee Yojana (PMKSY) with the motto 'Per Drop More Crop'.",
        "The Pradhan Mantri Krishi Sinchayee Yojana (PMKSY) was launched in 2015 with the vision of extending the coverage of irrigation and improving water use efficiency. It focuses on creating protective irrigation sources, promoting micro-irrigation, and ensuring end-to-end solution on source creation, distribution, management, and application.",

        # Seasons
        "Indian agriculture follows three main cropping seasons: Kharif (monsoon season, June-October), Rabi (winter season, October-March), and Zaid (summer season, March-June). Kharif crops include rice, maize, cotton, sugarcane, and soybean. Rabi crops include wheat, barley, mustard, gram, and peas. Zaid crops include watermelon, muskmelon, and cucumber.",
        "The Indian monsoon is crucial for agriculture as about 50% of India's farmland is rain-fed. The southwest monsoon (June-September) provides about 75% of India's annual rainfall. A good monsoon is essential for the Kharif crop season and also recharges groundwater for Rabi season irrigation.",

        # Technology
        "Precision agriculture in India uses GPS, sensors, drones, and data analytics to optimize crop production. Technologies like soil moisture sensors, weather stations, satellite imaging, and variable rate technology help farmers apply inputs precisely where and when needed, reducing waste and increasing yields.",
        "The Kisan Sarathi platform is a digital initiative that provides Indian farmers with expert advisory services through video calling, messaging, and AI-powered recommendations. It connects farmers directly with agricultural scientists and extension workers for real-time problem-solving.",
        "The UPAg (Unified Portal for Agricultural Statistics) is a centralized digital platform providing near real-time data on crop production, area, yield, market prices, and trade statistics for all major agricultural commodities in India. It supports evidence-based policy making and helps farmers with market intelligence.",
        "The Agriculture Skill Council of India (ASCI) was set up by the National Skill Development Corporation (NSDC) to facilitate skill development in the agriculture sector. ASCI develops National Occupational Standards, curriculum, and certification for various agriculture-related job roles.",

        # Organic & Natural Farming
        "Zero Budget Natural Farming (ZBNF) is a set of farming methods promoted in India, particularly in Andhra Pradesh. It involves four key practices: Bijamrita (seed treatment), Jivamrita (microbial culture), Mulching, and Whapasa (moisture management). ZBNF aims to eliminate chemical inputs and reduce farming costs to near zero.",
        "India ranks first in the number of organic farmers (over 4.4 million) and ninth in terms of area under organic farming. Sikkim became the first fully organic state in India in 2016. Other states actively promoting organic farming include Uttarakhand, Meghalaya, Mizoram, and Kerala.",
        "Vermicomposting is a process of composting using earthworms to convert organic waste into nutrient-rich manure. It is widely promoted in India as a sustainable alternative to chemical fertilizers. Vermicompost improves soil structure, increases water-holding capacity, and provides essential nutrients like nitrogen, phosphorus, and potassium.",

        # Pests & Diseases
        "Fall Armyworm (Spodoptera frugiperda) is an invasive pest that has caused significant damage to maize crops in India since 2018. It originated in the Americas and can destroy entire maize fields. Integrated pest management combining biological control agents, pheromone traps, and judicious use of pesticides is recommended.",
        "Integrated Pest Management (IPM) in Indian agriculture combines biological, cultural, physical, and chemical methods to control pests while minimizing environmental damage. Key practices include crop rotation, use of resistant varieties, biological control agents like Trichogramma, pheromone traps, and neem-based pesticides.",
        "Late blight caused by Phytophthora infestans is one of the most devastating diseases of potato and tomato in India. It causes rapid destruction of foliage and tubers, especially during cool and humid weather. Management includes use of resistant varieties, fungicide sprays, and proper seed selection.",

        # Animal Husbandry
        "India has the world's largest livestock population with over 536 million animals. The livestock sector contributes about 4.1% to India's GDP and about 25.6% to agricultural GDP. Major livestock include cattle, buffalo, goat, sheep, and poultry.",
        "The National Livestock Mission was launched to ensure quantitative and qualitative improvement in livestock production systems. It focuses on breed improvement, feed and fodder development, innovation, and extension of livestock-based livelihoods.",
        "Fisheries sector in India has been growing at an annual rate of about 7%. India is the second-largest fish producer in the world and the fourth-largest exporter of fish and fish products. The Pradhan Mantri Matsya Sampada Yojana (PMMSY) aims to bring about Blue Revolution.",

        # Regional Agriculture
        "Punjab and Haryana are known as the 'Granary of India' due to their high production of wheat and rice. These states were at the forefront of the Green Revolution in the 1960s-70s. However, excessive use of groundwater, chemical fertilizers, and monocropping has led to environmental concerns including declining water tables and soil degradation.",
        "Kerala's agriculture is dominated by plantation crops including rubber, tea, coffee, cardamom, pepper, and coconut. The state also has significant production of rice, tapioca, banana, and cashew. Kerala's spice trade has historical significance dating back thousands of years.",
        "Northeast India has diverse agro-climatic conditions suitable for growing a wide range of crops including rice, maize, tea, rubber, citrus fruits, pineapple, ginger, turmeric, and bamboo. The region practices jhum (shifting) cultivation in hilly areas. Organic farming is naturally prevalent due to minimal use of chemical inputs.",
        "Rajasthan, despite being largely arid, is India's largest producer of mustard, bajra (pearl millet), and several spices. The Indira Gandhi Canal has transformed parts of the Thar Desert into productive farmland. Water conservation techniques like rainwater harvesting and drip irrigation are crucial for agriculture in the state.",
    ]


def main():
    documents = []

    # Step 1: Curated content (guaranteed high quality)
    print("Loading curated Indian agriculture content...")
    curated = get_curated_content()
    documents.extend(curated)
    print(f"  Added {len(curated)} curated paragraphs.")

    # Step 2: Crawl Krishi Jagran
    print("Crawling Krishi Jagran articles...")
    kj_links = set()
    for section in KJ_SECTIONS:
        print(f"  Scanning section: {section}")
        links = get_kj_article_links(section, max_pages=20)
        kj_links.update(links)
        print(f"    Found {len(links)} article links.")
    print(f"  Total unique KJ links: {len(kj_links)}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(scrape_kj_article, url): url for url in kj_links}
        done = 0
        for future in as_completed(futures):
            paras = future.result()
            documents.extend(paras)
            done += 1
            if done % 50 == 0:
                print(f"  Scraped {done}/{len(kj_links)} KJ articles, total paragraphs: {len(documents)}")

    print(f"  After KJ crawl: {len(documents)} paragraphs.")

    # Step 3: Crawl ICAR Indian Farming
    print("Crawling ICAR Indian Farming articles...")
    icar_links = get_icar_article_links()
    print(f"  Found {len(icar_links)} ICAR article links.")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scrape_icar_article, url): url for url in icar_links}
        for future in as_completed(futures):
            paras = future.result()
            documents.extend(paras)

    print(f"  After ICAR crawl: {len(documents)} paragraphs.")

    # Step 4: Deduplicate
    seen = set()
    unique = []
    for doc in documents:
        clean = doc.strip()
        if clean and clean not in seen and len(clean) > 60:
            seen.add(clean)
            unique.append(clean)
    documents = unique[:TARGET_COUNT]
    print(f"After dedup & trim: {len(documents)} unique paragraphs.")

    # Step 5: Save
    with open(KNOWLEDGE_PATH, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    print(f"Saved to {KNOWLEDGE_PATH}")

    # Step 6: Compute embeddings
    print("Computing embeddings (this may take several minutes)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    start = time.time()
    embeddings = model.encode(documents, convert_to_tensor=True, show_progress_bar=True, batch_size=64)
    torch.save(embeddings, EMBEDDINGS_PATH)
    print(f"Computed embeddings in {time.time()-start:.1f}s. Saved to {EMBEDDINGS_PATH}")
    print("Build complete!")

if __name__ == "__main__":
    main()
