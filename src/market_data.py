"""
TradeLead V3.0 — Market Data (Regions, Countries, Cities)
Pre-configured, zero user input needed.
"""

# 区域 → 国家映射
REGION_COUNTRIES: dict[str, list[tuple[str, str]]] = {
    "中东": [
        ("AE", "阿联酋"), ("SA", "沙特阿拉伯"), ("QA", "卡塔尔"),
        ("KW", "科威特"), ("OM", "阿曼"), ("TR", "土耳其"),
        ("IR", "伊朗"), ("IQ", "伊拉克"), ("JO", "约旦"),
        ("BH", "巴林"), ("LB", "黎巴嫩"),
    ],
    "非洲": [
        ("NG", "尼日利亚"), ("KE", "肯尼亚"), ("EG", "埃及"),
        ("ZA", "南非"), ("MA", "摩洛哥"), ("ET", "埃塞俄比亚"),
        ("TZ", "坦桑尼亚"), ("GH", "加纳"), ("CI", "科特迪瓦"),
        ("UG", "乌干达"), ("SN", "塞内加尔"), ("SD", "苏丹"),
        ("DZ", "阿尔及利亚"), ("AO", "安哥拉"), ("CM", "喀麦隆"),
    ],
    "中亚": [
        ("KZ", "哈萨克斯坦"), ("UZ", "乌兹别克斯坦"), ("TM", "土库曼斯坦"),
        ("KG", "吉尔吉斯斯坦"), ("TJ", "塔吉克斯坦"),
    ],
    "东南亚": [
        ("ID", "印度尼西亚"), ("TH", "泰国"), ("VN", "越南"),
        ("PH", "菲律宾"), ("MY", "马来西亚"), ("MM", "缅甸"),
        ("KH", "柬埔寨"), ("LA", "老挝"),
    ],
    "南亚": [
        ("BD", "孟加拉国"), ("PK", "巴基斯坦"), ("LK", "斯里兰卡"),
        ("NP", "尼泊尔"), ("IN", "印度"),
    ],
    "拉美": [
        ("BR", "巴西"), ("MX", "墨西哥"), ("AR", "阿根廷"),
        ("CO", "哥伦比亚"), ("PE", "秘鲁"), ("CL", "智利"),
        ("EC", "厄瓜多尔"), ("VE", "委内瑞拉"), ("BO", "玻利维亚"),
    ],
    "东欧": [
        ("RU", "俄罗斯"), ("BY", "白俄罗斯"), ("UA", "乌克兰"),
        ("PL", "波兰"), ("RO", "罗马尼亚"), ("BG", "保加利亚"),
        ("RS", "塞尔维亚"),
    ],
}

COUNTRY_ENGLISH_NAMES: dict[str, str] = {
    "AE": "United Arab Emirates", "SA": "Saudi Arabia", "QA": "Qatar",
    "KW": "Kuwait", "OM": "Oman", "TR": "Turkey", "IR": "Iran",
    "IQ": "Iraq", "JO": "Jordan", "BH": "Bahrain", "LB": "Lebanon",
    "NG": "Nigeria", "KE": "Kenya", "EG": "Egypt", "ZA": "South Africa",
    "MA": "Morocco", "ET": "Ethiopia", "TZ": "Tanzania", "GH": "Ghana",
    "CI": "Cote d'Ivoire", "UG": "Uganda", "SN": "Senegal", "SD": "Sudan",
    "DZ": "Algeria", "AO": "Angola", "CM": "Cameroon",
    "KZ": "Kazakhstan", "UZ": "Uzbekistan", "TM": "Turkmenistan",
    "KG": "Kyrgyzstan", "TJ": "Tajikistan",
    "ID": "Indonesia", "TH": "Thailand", "VN": "Vietnam",
    "PH": "Philippines", "MY": "Malaysia", "MM": "Myanmar",
    "KH": "Cambodia", "LA": "Laos", "BD": "Bangladesh",
    "PK": "Pakistan", "LK": "Sri Lanka", "NP": "Nepal", "IN": "India",
    "BR": "Brazil", "MX": "Mexico", "AR": "Argentina", "CO": "Colombia",
    "PE": "Peru", "CL": "Chile", "EC": "Ecuador", "VE": "Venezuela",
    "BO": "Bolivia", "RU": "Russia", "BY": "Belarus", "UA": "Ukraine",
    "PL": "Poland", "RO": "Romania", "BG": "Bulgaria", "RS": "Serbia",
}

# 国家 → 主要商业、港口和工业城市映射（英文检索名, 中文显示名）
COUNTRY_CITIES: dict[str, list[tuple[str, str]]] = {
    "阿联酋": [("Dubai", "迪拜"), ("Abu Dhabi", "阿布扎比"), ("Sharjah", "沙迦"), ("Ajman", "阿治曼"), ("Ras Al Khaimah", "哈伊马角"), ("Al Ain", "艾因"), ("Fujairah", "富查伊拉")],
    "沙特阿拉伯": [("Riyadh", "利雅得"), ("Jeddah", "吉达"), ("Dammam", "达曼"), ("Al Khobar", "胡拜尔"), ("Mecca", "麦加"), ("Medina", "麦地那")],
    "卡塔尔": [("Doha", "多哈"), ("Al Rayyan", "赖扬"), ("Al Wakrah", "沃克拉")],
    "科威特": [("Kuwait City", "科威特城"), ("Al Ahmadi", "艾哈迈迪"), ("Hawally", "哈瓦利")],
    "阿曼": [("Muscat", "马斯喀特"), ("Salalah", "塞拉莱"), ("Sohar", "苏哈尔"), ("Nizwa", "尼兹瓦")],
    "土耳其": [("Istanbul", "伊斯坦布尔"), ("Ankara", "安卡拉"), ("Izmir", "伊兹密尔"), ("Bursa", "布尔萨"), ("Antalya", "安塔利亚"), ("Gaziantep", "加济安泰普"), ("Mersin", "梅尔辛"), ("Konya", "科尼亚")],
    "伊朗": [("Tehran", "德黑兰"), ("Mashhad", "马什哈德"), ("Isfahan", "伊斯法罕"), ("Shiraz", "设拉子"), ("Tabriz", "大不里士"), ("Bandar Abbas", "阿巴斯港")],
    "伊拉克": [("Baghdad", "巴格达"), ("Erbil", "埃尔比勒"), ("Basra", "巴士拉"), ("Mosul", "摩苏尔"), ("Sulaymaniyah", "苏莱曼尼亚")],
    "约旦": [("Amman", "安曼"), ("Zarqa", "扎尔卡"), ("Irbid", "伊尔比德"), ("Aqaba", "亚喀巴")],
    "巴林": [("Manama", "麦纳麦"), ("Riffa", "里法"), ("Muharraq", "穆哈拉格")],
    "黎巴嫩": [("Beirut", "贝鲁特"), ("Tripoli", "的黎波里"), ("Sidon", "赛达"), ("Zahle", "扎赫勒")],

    "尼日利亚": [("Lagos", "拉各斯"), ("Abuja", "阿布贾"), ("Kano", "卡诺"), ("Port Harcourt", "哈科特港"), ("Ibadan", "伊巴丹"), ("Onitsha", "奥尼查"), ("Aba", "阿巴")],
    "肯尼亚": [("Nairobi", "内罗毕"), ("Mombasa", "蒙巴萨"), ("Kisumu", "基苏木"), ("Nakuru", "纳库鲁"), ("Eldoret", "埃尔多雷特")],
    "埃及": [("Cairo", "开罗"), ("Alexandria", "亚历山大"), ("Giza", "吉萨"), ("Port Said", "塞得港"), ("Suez", "苏伊士"), ("Mansoura", "曼苏拉")],
    "南非": [("Johannesburg", "约翰内斯堡"), ("Cape Town", "开普敦"), ("Durban", "德班"), ("Pretoria", "比勒陀利亚"), ("Gqeberha", "格贝哈"), ("Bloemfontein", "布隆方丹"), ("East London", "东伦敦")],
    "摩洛哥": [("Casablanca", "卡萨布兰卡"), ("Tangier", "丹吉尔"), ("Rabat", "拉巴特"), ("Marrakesh", "马拉喀什"), ("Agadir", "阿加迪尔"), ("Fez", "非斯")],
    "埃塞俄比亚": [("Addis Ababa", "亚的斯亚贝巴"), ("Dire Dawa", "德雷达瓦"), ("Adama", "阿达玛"), ("Hawassa", "阿瓦萨"), ("Bahir Dar", "巴赫达尔")],
    "坦桑尼亚": [("Dar es Salaam", "达累斯萨拉姆"), ("Dodoma", "多多马"), ("Arusha", "阿鲁沙"), ("Mwanza", "姆万扎"), ("Mbeya", "姆贝亚")],
    "加纳": [("Accra", "阿克拉"), ("Tema", "特马"), ("Kumasi", "库马西"), ("Takoradi", "塔科拉迪"), ("Tamale", "塔马利")],
    "科特迪瓦": [("Abidjan", "阿比让"), ("San Pedro", "圣佩德罗"), ("Bouake", "布瓦凯"), ("Yamoussoukro", "亚穆苏克罗")],
    "乌干达": [("Kampala", "坎帕拉"), ("Jinja", "金贾"), ("Mbarara", "姆巴拉拉"), ("Entebbe", "恩德培")],
    "塞内加尔": [("Dakar", "达喀尔"), ("Thies", "捷斯"), ("Saint-Louis", "圣路易")],
    "苏丹": [("Khartoum", "喀土穆"), ("Omdurman", "恩图曼"), ("Port Sudan", "苏丹港"), ("Wad Madani", "瓦德迈达尼")],
    "阿尔及利亚": [("Algiers", "阿尔及尔"), ("Oran", "奥兰"), ("Constantine", "君士坦丁"), ("Setif", "塞提夫"), ("Annaba", "安纳巴"), ("Blida", "布利达")],
    "安哥拉": [("Luanda", "罗安达"), ("Lobito", "洛比托"), ("Benguela", "本格拉"), ("Huambo", "万博")],
    "喀麦隆": [("Douala", "杜阿拉"), ("Yaounde", "雅温得"), ("Bafoussam", "巴富萨姆"), ("Garoua", "加鲁阿"), ("Limbe", "林贝")],

    "哈萨克斯坦": [("Almaty", "阿拉木图"), ("Astana", "阿斯塔纳"), ("Shymkent", "奇姆肯特"), ("Karaganda", "卡拉干达"), ("Aktobe", "阿克托别"), ("Atyrau", "阿特劳")],
    "乌兹别克斯坦": [("Tashkent", "塔什干"), ("Samarkand", "撒马尔罕"), ("Bukhara", "布哈拉"), ("Namangan", "纳曼干"), ("Andijan", "安集延")],
    "土库曼斯坦": [("Ashgabat", "阿什哈巴德"), ("Turkmenabat", "土库曼纳巴德"), ("Turkmenbashi", "土库曼巴希"), ("Mary", "马雷")],
    "吉尔吉斯斯坦": [("Bishkek", "比什凯克"), ("Osh", "奥什"), ("Jalal-Abad", "贾拉拉巴德")],
    "塔吉克斯坦": [("Dushanbe", "杜尚别"), ("Khujand", "苦盏"), ("Bokhtar", "博赫塔尔")],

    "印度尼西亚": [("Jakarta", "雅加达"), ("Surabaya", "泗水"), ("Bandung", "万隆"), ("Medan", "棉兰"), ("Semarang", "三宝垄"), ("Makassar", "望加锡"), ("Batam", "巴淡"), ("Palembang", "巨港")],
    "泰国": [("Bangkok", "曼谷"), ("Chon Buri", "春武里"), ("Chiang Mai", "清迈"), ("Pattaya", "芭堤雅"), ("Phuket", "普吉"), ("Khon Kaen", "孔敬"), ("Nakhon Ratchasima", "呵叻")],
    "越南": [("Ho Chi Minh City", "胡志明市"), ("Hanoi", "河内"), ("Hai Phong", "海防"), ("Da Nang", "岘港"), ("Can Tho", "芹苴"), ("Binh Duong", "平阳")],
    "菲律宾": [("Manila", "马尼拉"), ("Quezon City", "奎松市"), ("Cebu City", "宿务市"), ("Davao City", "达沃市"), ("Makati", "马卡蒂"), ("Cagayan de Oro", "卡加延德奥罗")],
    "马来西亚": [("Kuala Lumpur", "吉隆坡"), ("Johor Bahru", "新山"), ("George Town", "乔治市"), ("Shah Alam", "莎阿南"), ("Klang", "巴生"), ("Kota Kinabalu", "亚庇"), ("Kuching", "古晋")],
    "缅甸": [("Yangon", "仰光"), ("Mandalay", "曼德勒"), ("Naypyidaw", "内比都"), ("Mawlamyine", "毛淡棉")],
    "柬埔寨": [("Phnom Penh", "金边"), ("Sihanoukville", "西哈努克市"), ("Siem Reap", "暹粒"), ("Battambang", "马德望")],
    "老挝": [("Vientiane", "万象"), ("Savannakhet", "沙湾拿吉"), ("Pakse", "巴色")],

    "孟加拉国": [("Dhaka", "达卡"), ("Chattogram", "吉大港"), ("Khulna", "库尔纳"), ("Gazipur", "加济布尔"), ("Narayanganj", "纳拉扬甘杰"), ("Rajshahi", "拉杰沙希")],
    "巴基斯坦": [("Karachi", "卡拉奇"), ("Lahore", "拉合尔"), ("Islamabad", "伊斯兰堡"), ("Rawalpindi", "拉瓦尔品第"), ("Faisalabad", "费萨拉巴德"), ("Sialkot", "锡亚尔科特"), ("Peshawar", "白沙瓦")],
    "斯里兰卡": [("Colombo", "科伦坡"), ("Sri Jayawardenepura Kotte", "斯里贾亚瓦德纳普拉科特"), ("Kandy", "康提"), ("Galle", "加勒")],
    "尼泊尔": [("Kathmandu", "加德满都"), ("Birgunj", "比尔根杰"), ("Pokhara", "博卡拉"), ("Biratnagar", "比拉特纳加尔")],
    "印度": [("Mumbai", "孟买"), ("Delhi", "德里"), ("Bengaluru", "班加罗尔"), ("Chennai", "金奈"), ("Kolkata", "加尔各答"), ("Hyderabad", "海得拉巴"), ("Ahmedabad", "艾哈迈达巴德"), ("Pune", "浦那"), ("Surat", "苏拉特"), ("Jaipur", "斋浦尔"), ("Kochi", "科钦"), ("Coimbatore", "哥印拜陀")],

    "巴西": [("Sao Paulo", "圣保罗"), ("Rio de Janeiro", "里约热内卢"), ("Belo Horizonte", "贝洛奥里藏特"), ("Curitiba", "库里蒂巴"), ("Porto Alegre", "阿雷格里港"), ("Recife", "累西腓"), ("Salvador", "萨尔瓦多"), ("Campinas", "坎皮纳斯"), ("Manaus", "马瑙斯"), ("Fortaleza", "福塔莱萨")],
    "墨西哥": [("Mexico City", "墨西哥城"), ("Monterrey", "蒙特雷"), ("Guadalajara", "瓜达拉哈拉"), ("Puebla", "普埃布拉"), ("Tijuana", "蒂华纳"), ("Queretaro", "克雷塔罗"), ("Leon", "莱昂"), ("Ciudad Juarez", "华雷斯城"), ("Merida", "梅里达")],
    "阿根廷": [("Buenos Aires", "布宜诺斯艾利斯"), ("Cordoba", "科尔多瓦"), ("Rosario", "罗萨里奥"), ("Mendoza", "门多萨"), ("La Plata", "拉普拉塔"), ("Mar del Plata", "马德普拉塔")],
    "哥伦比亚": [("Bogota", "波哥大"), ("Medellin", "麦德林"), ("Cali", "卡利"), ("Barranquilla", "巴兰基亚"), ("Cartagena", "卡塔赫纳"), ("Bucaramanga", "布卡拉曼加")],
    "秘鲁": [("Lima", "利马"), ("Arequipa", "阿雷基帕"), ("Trujillo", "特鲁希略"), ("Callao", "卡亚俄"), ("Chiclayo", "奇克拉约")],
    "智利": [("Santiago", "圣地亚哥"), ("Valparaiso", "瓦尔帕莱索"), ("Concepcion", "康塞普西翁"), ("Antofagasta", "安托法加斯塔"), ("Iquique", "伊基克")],
    "厄瓜多尔": [("Guayaquil", "瓜亚基尔"), ("Quito", "基多"), ("Cuenca", "昆卡"), ("Manta", "曼塔"), ("Ambato", "安巴托")],
    "委内瑞拉": [("Caracas", "加拉加斯"), ("Maracaibo", "马拉开波"), ("Valencia", "瓦伦西亚"), ("Barquisimeto", "巴基西梅托"), ("Puerto Cabello", "卡贝略港")],
    "玻利维亚": [("Santa Cruz de la Sierra", "圣克鲁斯"), ("La Paz", "拉巴斯"), ("Cochabamba", "科恰班巴"), ("El Alto", "埃尔阿尔托")],

    "俄罗斯": [("Moscow", "莫斯科"), ("Saint Petersburg", "圣彼得堡"), ("Novosibirsk", "新西伯利亚"), ("Yekaterinburg", "叶卡捷琳堡"), ("Kazan", "喀山"), ("Nizhny Novgorod", "下诺夫哥罗德"), ("Samara", "萨马拉"), ("Rostov-on-Don", "顿河畔罗斯托夫"), ("Krasnodar", "克拉斯诺达尔"), ("Vladivostok", "符拉迪沃斯托克")],
    "白俄罗斯": [("Minsk", "明斯克"), ("Gomel", "戈梅利"), ("Brest", "布列斯特"), ("Grodno", "格罗德诺"), ("Mogilev", "莫吉廖夫")],
    "乌克兰": [("Kyiv", "基辅"), ("Lviv", "利沃夫"), ("Odesa", "敖德萨"), ("Dnipro", "第聂伯罗"), ("Kharkiv", "哈尔科夫")],
    "波兰": [("Warsaw", "华沙"), ("Krakow", "克拉科夫"), ("Lodz", "罗兹"), ("Wroclaw", "弗罗茨瓦夫"), ("Poznan", "波兹南"), ("Gdansk", "格但斯克"), ("Katowice", "卡托维兹")],
    "罗马尼亚": [("Bucharest", "布加勒斯特"), ("Cluj-Napoca", "克卢日-纳波卡"), ("Timisoara", "蒂米什瓦拉"), ("Constanta", "康斯坦察"), ("Brasov", "布拉索夫"), ("Iasi", "雅西")],
    "保加利亚": [("Sofia", "索非亚"), ("Plovdiv", "普罗夫迪夫"), ("Varna", "瓦尔纳"), ("Burgas", "布尔加斯"), ("Ruse", "鲁塞")],
    "塞尔维亚": [("Belgrade", "贝尔格莱德"), ("Novi Sad", "诺维萨德"), ("Nis", "尼什"), ("Kragujevac", "克拉古耶瓦茨"), ("Subotica", "苏博蒂察")],
}

# 国家 → 常用州/省/行政区。这里只预置主要商业和工业地区，页面同时支持手工输入。
COUNTRY_SUBREGIONS: dict[str, list[tuple[str, str]]] = {
    "阿联酋": [("Dubai", "迪拜酋长国"), ("Abu Dhabi", "阿布扎比酋长国"), ("Sharjah", "沙迦酋长国"), ("Ajman", "阿治曼酋长国"), ("Ras Al Khaimah", "哈伊马角酋长国"), ("Fujairah", "富查伊拉酋长国")],
    "沙特阿拉伯": [("Riyadh Province", "利雅得省"), ("Makkah Province", "麦加省"), ("Eastern Province", "东部省"), ("Medina Province", "麦地那省"), ("Qassim Province", "卡西姆省")],
    "土耳其": [("Istanbul Province", "伊斯坦布尔省"), ("Ankara Province", "安卡拉省"), ("Izmir Province", "伊兹密尔省"), ("Bursa Province", "布尔萨省"), ("Gaziantep Province", "加济安泰普省"), ("Mersin Province", "梅尔辛省")],
    "伊朗": [("Tehran Province", "德黑兰省"), ("Razavi Khorasan", "礼萨呼罗珊省"), ("Isfahan Province", "伊斯法罕省"), ("Fars Province", "法尔斯省"), ("East Azerbaijan", "东阿塞拜疆省")],
    "伊拉克": [("Baghdad Governorate", "巴格达省"), ("Erbil Governorate", "埃尔比勒省"), ("Basra Governorate", "巴士拉省"), ("Sulaymaniyah Governorate", "苏莱曼尼亚省")],
    "尼日利亚": [("Lagos State", "拉各斯州"), ("Federal Capital Territory", "联邦首都区"), ("Kano State", "卡诺州"), ("Rivers State", "河流州"), ("Oyo State", "奥约州"), ("Anambra State", "阿南布拉州")],
    "肯尼亚": [("Nairobi County", "内罗毕郡"), ("Mombasa County", "蒙巴萨郡"), ("Kiambu County", "基安布郡"), ("Nakuru County", "纳库鲁郡"), ("Kisumu County", "基苏木郡")],
    "埃及": [("Cairo Governorate", "开罗省"), ("Alexandria Governorate", "亚历山大省"), ("Giza Governorate", "吉萨省"), ("Port Said Governorate", "塞得港省"), ("Suez Governorate", "苏伊士省")],
    "南非": [("Gauteng", "豪登省"), ("Western Cape", "西开普省"), ("KwaZulu-Natal", "夸祖鲁-纳塔尔省"), ("Eastern Cape", "东开普省"), ("Free State", "自由州")],
    "摩洛哥": [("Casablanca-Settat", "卡萨布兰卡-塞塔特大区"), ("Tanger-Tetouan-Al Hoceima", "丹吉尔-得土安-胡塞马大区"), ("Rabat-Sale-Kenitra", "拉巴特-萨累-盖尼特拉大区"), ("Marrakesh-Safi", "马拉喀什-萨菲大区"), ("Souss-Massa", "苏斯-马塞大区")],
    "埃塞俄比亚": [("Addis Ababa", "亚的斯亚贝巴"), ("Oromia", "奥罗米亚州"), ("Amhara", "阿姆哈拉州"), ("Dire Dawa", "德雷达瓦"), ("Sidama", "锡达马州")],
    "坦桑尼亚": [("Dar es Salaam Region", "达累斯萨拉姆区"), ("Dodoma Region", "多多马区"), ("Arusha Region", "阿鲁沙区"), ("Mwanza Region", "姆万扎区"), ("Mbeya Region", "姆贝亚区")],
    "加纳": [("Greater Accra", "大阿克拉区"), ("Ashanti", "阿散蒂区"), ("Western Region", "西部区"), ("Northern Region", "北部区")],
    "哈萨克斯坦": [("Almaty Region", "阿拉木图州"), ("Astana", "阿斯塔纳"), ("Karaganda Region", "卡拉干达州"), ("Atyrau Region", "阿特劳州"), ("Aktobe Region", "阿克托别州")],
    "乌兹别克斯坦": [("Tashkent Region", "塔什干州"), ("Samarkand Region", "撒马尔罕州"), ("Bukhara Region", "布哈拉州"), ("Namangan Region", "纳曼干州"), ("Andijan Region", "安集延州")],
    "印度尼西亚": [("Jakarta", "雅加达首都特区"), ("East Java", "东爪哇省"), ("West Java", "西爪哇省"), ("Central Java", "中爪哇省"), ("North Sumatra", "北苏门答腊省"), ("South Sulawesi", "南苏拉威西省"), ("Riau Islands", "廖内群岛省")],
    "泰国": [("Bangkok", "曼谷都"), ("Chon Buri Province", "春武里府"), ("Chiang Mai Province", "清迈府"), ("Phuket Province", "普吉府"), ("Khon Kaen Province", "孔敬府"), ("Nakhon Ratchasima Province", "呵叻府"), ("Rayong Province", "罗勇府"), ("Samut Prakan Province", "北榄府")],
    "越南": [("Ho Chi Minh City", "胡志明市"), ("Hanoi", "河内市"), ("Hai Phong", "海防市"), ("Da Nang", "岘港市"), ("Binh Duong Province", "平阳省"), ("Dong Nai Province", "同奈省"), ("Bac Ninh Province", "北宁省")],
    "菲律宾": [("Metro Manila", "马尼拉大都会"), ("Central Luzon", "中吕宋大区"), ("CALABARZON", "卡拉巴松大区"), ("Central Visayas", "中米沙鄢大区"), ("Davao Region", "达沃大区")],
    "马来西亚": [("Kuala Lumpur", "吉隆坡联邦直辖区"), ("Selangor", "雪兰莪州"), ("Johor", "柔佛州"), ("Penang", "槟城州"), ("Perak", "霹雳州"), ("Sabah", "沙巴州"), ("Sarawak", "砂拉越州")],
    "缅甸": [("Yangon Region", "仰光省"), ("Mandalay Region", "曼德勒省"), ("Naypyidaw Union Territory", "内比都联邦区"), ("Mon State", "孟邦")],
    "柬埔寨": [("Phnom Penh", "金边"), ("Preah Sihanouk Province", "西哈努克省"), ("Siem Reap Province", "暹粒省"), ("Battambang Province", "马德望省")],
    "孟加拉国": [("Dhaka Division", "达卡专区"), ("Chattogram Division", "吉大港专区"), ("Khulna Division", "库尔纳专区"), ("Rajshahi Division", "拉杰沙希专区")],
    "巴基斯坦": [("Sindh", "信德省"), ("Punjab", "旁遮普省"), ("Islamabad Capital Territory", "伊斯兰堡首都区"), ("Khyber Pakhtunkhwa", "开伯尔-普什图省"), ("Balochistan", "俾路支省")],
    "斯里兰卡": [("Western Province", "西部省"), ("Central Province", "中央省"), ("Southern Province", "南部省"), ("North Western Province", "西北省")],
    "尼泊尔": [("Bagmati Province", "巴格马蒂省"), ("Madhesh Province", "马德什省"), ("Gandaki Province", "甘达基省"), ("Koshi Province", "戈西省")],
    "印度": [("Maharashtra", "马哈拉施特拉邦"), ("Delhi", "德里国家首都辖区"), ("Karnataka", "卡纳塔克邦"), ("Tamil Nadu", "泰米尔纳德邦"), ("Gujarat", "古吉拉特邦"), ("Telangana", "特伦甘纳邦"), ("West Bengal", "西孟加拉邦"), ("Uttar Pradesh", "北方邦"), ("Rajasthan", "拉贾斯坦邦"), ("Kerala", "喀拉拉邦")],
    "巴西": [("Sao Paulo State", "圣保罗州"), ("Rio de Janeiro State", "里约热内卢州"), ("Minas Gerais", "米纳斯吉拉斯州"), ("Parana", "巴拉那州"), ("Rio Grande do Sul", "南里奥格兰德州"), ("Pernambuco", "伯南布哥州"), ("Bahia", "巴伊亚州")],
    "墨西哥": [("Mexico City", "墨西哥城"), ("Nuevo Leon", "新莱昂州"), ("Jalisco", "哈利斯科州"), ("State of Mexico", "墨西哥州"), ("Puebla", "普埃布拉州"), ("Baja California", "下加利福尼亚州"), ("Queretaro", "克雷塔罗州"), ("Guanajuato", "瓜纳华托州")],
    "阿根廷": [("Buenos Aires Province", "布宜诺斯艾利斯省"), ("Cordoba Province", "科尔多瓦省"), ("Santa Fe Province", "圣菲省"), ("Mendoza Province", "门多萨省")],
    "哥伦比亚": [("Bogota Capital District", "波哥大首都区"), ("Antioquia", "安蒂奥基亚省"), ("Valle del Cauca", "考卡山谷省"), ("Atlantico", "大西洋省"), ("Bolivar", "玻利瓦尔省")],
    "秘鲁": [("Lima Region", "利马大区"), ("Arequipa Region", "阿雷基帕大区"), ("La Libertad", "拉利伯塔德大区"), ("Callao", "卡亚俄区")],
    "智利": [("Santiago Metropolitan Region", "圣地亚哥首都大区"), ("Valparaiso Region", "瓦尔帕莱索大区"), ("Biobio Region", "比奥比奥大区"), ("Antofagasta Region", "安托法加斯塔大区")],
    "俄罗斯": [("Moscow", "莫斯科联邦市"), ("Saint Petersburg", "圣彼得堡联邦市"), ("Moscow Oblast", "莫斯科州"), ("Novosibirsk Oblast", "新西伯利亚州"), ("Sverdlovsk Oblast", "斯维尔德洛夫斯克州"), ("Tatarstan", "鞑靼斯坦共和国"), ("Krasnodar Krai", "克拉斯诺达尔边疆区")],
    "乌克兰": [("Kyiv", "基辅市"), ("Lviv Oblast", "利沃夫州"), ("Odesa Oblast", "敖德萨州"), ("Dnipropetrovsk Oblast", "第聂伯罗彼得罗夫斯克州"), ("Kharkiv Oblast", "哈尔科夫州")],
    "波兰": [("Masovian Voivodeship", "马佐夫舍省"), ("Lesser Poland Voivodeship", "小波兰省"), ("Silesian Voivodeship", "西里西亚省"), ("Greater Poland Voivodeship", "大波兰省"), ("Lower Silesian Voivodeship", "下西里西亚省"), ("Pomeranian Voivodeship", "滨海省")],
    "罗马尼亚": [("Bucharest", "布加勒斯特"), ("Cluj County", "克卢日县"), ("Timis County", "蒂米什县"), ("Constanta County", "康斯坦察县"), ("Brasov County", "布拉索夫县")],
}

# 国家 → 商业语言
COUNTRY_LANGUAGES: dict[str, str] = {
    "阿联酋": "ar", "沙特阿拉伯": "ar", "卡塔尔": "ar", "科威特": "ar",
    "阿曼": "ar", "巴林": "ar", "黎巴嫩": "ar", "约旦": "ar", "伊拉克": "ar",
    "伊朗": "ar",

    "尼日利亚": "en", "肯尼亚": "en", "南非": "en", "加纳": "en",
    "埃塞俄比亚": "en", "坦桑尼亚": "en", "乌干达": "en",

    "摩洛哥": "fr", "科特迪瓦": "fr", "塞内加尔": "fr", "阿尔及利亚": "fr", "喀麦隆": "fr",

    "埃及": "ar",

    "哈萨克斯坦": "ru", "乌兹别克斯坦": "ru", "土库曼斯坦": "ru",
    "吉尔吉斯斯坦": "ru", "塔吉克斯坦": "ru",

    "印度尼西亚": "en", "泰国": "en", "越南": "en", "菲律宾": "en",
    "马来西亚": "en", "缅甸": "en", "柬埔寨": "en",

    "孟加拉国": "en", "巴基斯坦": "en", "斯里兰卡": "en",
    "尼泊尔": "en", "印度": "en",

    "巴西": "pt", "墨西哥": "es", "阿根廷": "es", "哥伦比亚": "es",
    "秘鲁": "es", "智利": "es", "厄瓜多尔": "es", "委内瑞拉": "es",

    "俄罗斯": "ru", "白俄罗斯": "ru", "乌克兰": "ru",
    "波兰": "en", "罗马尼亚": "en", "保加利亚": "en",

    "土耳其": "en",
    "苏丹": "ar", "安哥拉": "pt",
}


def get_regions() -> list[str]:
    return list(REGION_COUNTRIES.keys())


def get_countries_for_region(region: str) -> list[tuple[str, str]]:
    return REGION_COUNTRIES.get(region, [])


def get_cities_for_country(country_cn: str) -> list[tuple[str, str]]:
    return COUNTRY_CITIES.get(country_cn, [])


def get_subregions_for_country(country_cn: str) -> list[tuple[str, str]]:
    return COUNTRY_SUBREGIONS.get(country_cn, [])


def get_language_for_country(country_cn: str) -> str:
    return COUNTRY_LANGUAGES.get(country_cn, "en")


# 品类 → 目标客户类型
CATEGORY_BUYER_TYPES: dict[str, list[str]] = {
    "默认": ["hardware store", "building materials supplier", "construction supply", "trading company"],
    "建筑五金": ["hardware store", "building materials", "construction supply", "tools supplier"],
    "塑料制品": ["plastic products distributor", "household goods wholesaler", "kitchenware store", "home supply"],
    "塑料机械": ["plastic machinery dealer", "recycling equipment supplier", "industrial equipment trader"],
    "普通二手机床": ["used machinery dealer", "metalworking supplier", "industrial equipment trader"],
    "汽车配件": ["auto parts store", "car accessories distributor", "vehicle spare parts supplier"],
    "纺织品": ["fabric wholesaler", "textile distributor", "garment supplier"],
    "农产品": ["food importer", "agricultural products trader", "grocery wholesaler"],
}

REGION_BUYER_TERMS: dict[str, list[str]] = {
    "中东": ["trading company", "general trading", "building materials trading"],
    "非洲": ["wholesale supplier", "import company", "general merchant"],
    "中亚": ["construction materials", "wholesale market"],
    "东南亚": ["hardware shop", "construction supply", "building materials shop"],
    "南亚": ["hardware store", "building material dealer", "construction company"],
    "拉美": ["ferreteria", "materiales de construccion", "ferragens", "distribuidora"],
    "东欧": ["building supply", "construction wholesaler"],
}


def get_country_code(country_cn: str) -> str:
    """Get ISO country code from Chinese country name."""
    for region_data in REGION_COUNTRIES.values():
        for code, name in region_data:
            if name == country_cn:
                return code
    return ""


def get_country_english_name(country_cn: str) -> str:
    code = get_country_code(country_cn)
    return COUNTRY_ENGLISH_NAMES.get(code, country_cn)

def search_keywords_template(
    product_keywords: str,
    country_en: str,
    city_en: str = "",
    category: str = "",
    region: str = "",
    buyer_types: str = "",
    end_user_types: str = "",
    subregion_en: str = "",
) -> list[str]:
    """Generate buyer-oriented search keywords for the target market."""
    location_parts = [
        value for value in [city_en, subregion_en, country_en] if value
    ]
    location = " ".join(dict.fromkeys(location_parts))

    # Get buyer types for this product category
    inferred_buyers = [item.strip() for item in buyer_types.split(",") if item.strip()]
    target_buyers = _specific_buyers_first(
        inferred_buyers
        or CATEGORY_BUYER_TYPES.get(category, CATEGORY_BUYER_TYPES["默认"])
    )
    end_users = [
        item.strip() for item in end_user_types.split(",") if item.strip()
    ]
    # Add region-specific terms
    region_terms = REGION_BUYER_TERMS.get(region, [])

    product_terms = [item.strip() for item in product_keywords.split(",") if item.strip()]
    queries = []
    if target_buyers:
        queries.append(f'"{target_buyers[0]}" {location}')
    if product_terms:
        queries.append(f'"{product_terms[0]}" distributor {location}')
    if product_terms and end_users:
        queries.append(f'"{product_terms[0]}" "{end_users[0]}" {location}')
    if len(target_buyers) > 1:
        queries.append(f'"{target_buyers[1]}" {location}')
    for bt in target_buyers[2:6]:
        queries.append(f'"{bt}" {location}')
    for end_user in end_users[1:4]:
        if product_terms:
            queries.append(f'"{product_terms[0]}" "{end_user}" {location}')
        else:
            queries.append(f'"{end_user}" {location}')
    for bt in target_buyers[:3]:
        queries.append(f'{bt} {location}')
    for rt in region_terms[:2]:
        queries.append(f'{rt} {location}')

    # Also include product keywords for niche distributors
    for main_kw in product_terms[:3]:
        queries.append(f'"{main_kw}" distributor {location}')

    return list(dict.fromkeys(queries))


def _specific_buyers_first(buyer_types: list[str]) -> list[str]:
    generic = {
        "hardware store", "building materials", "building materials supplier",
        "construction supply", "construction supply company", "tools supplier",
        "trading company", "general trading company", "distributor",
        "wholesaler", "importer", "supplier",
    }
    return sorted(
        buyer_types,
        key=lambda value: (" ".join(value.lower().split()) in generic,),
    )
