"""
Seed Products - Management command to populate sample products.
"""
from django.core.management.base import BaseCommand
from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.infrastructure.models.brand_model import BrandModel
from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel
from modules.catalog.infrastructure.models.variant_model import VariantModel
from shared.utils import generate_slug, generate_sku


BRANDS = [
    {'name': 'Apple', 'description': 'Apple Inc. - iPhone, MacBook, iPad'},
    {'name': 'Samsung', 'description': 'Samsung Electronics - Smartphone, TV, Home Appliances'},
    {'name': 'Dell', 'description': 'Dell Technologies - Laptops, Desktops, Monitors'},
    {'name': 'ASUS', 'description': 'ASUSTek Computer Inc. - Zenbook, ROG, TUF'},
    {'name': 'HP', 'description': 'HP Inc. - Spectre, Envy, Pavilion'},
    {'name': 'Lenovo', 'description': 'Lenovo Group - ThinkPad, Legion, Yoga'},
    {'name': 'Xiaomi', 'description': 'Xiaomi Corporation - Smartphones, IoT'},
    {'name': 'Oppo', 'description': 'OPPO - Smartphones, Audio'},
    {'name': 'Daikin', 'description': 'Daikin Industries - Air Conditioning'},
    {'name': 'Panasonic', 'description': 'Panasonic Holdings - Home Appliances'},
    {'name': 'LG', 'description': 'LG Electronics - Home Appliances, Display'},
    {'name': 'Anker', 'description': 'Anker Innovations - Chargers, Cables, Accessories'},
    {'name': 'Baseus', 'description': 'Baseus - Accessories and Charging'},
    {'name': 'Logitech', 'description': 'Logitech - Mouse, Keyboard, Peripherals'},
]

PRODUCT_TYPES = [
    {
        'name': 'Laptop',
        'attribute_schema': {
            'ram': {'type': 'string', 'required': True},
            'cpu': {'type': 'string', 'required': True},
            'storage': {'type': 'string', 'required': False},
            'screen_size': {'type': 'string', 'required': False},
        }
    },
    {
        'name': 'Điện thoại',
        'attribute_schema': {
            'ram': {'type': 'string', 'required': True},
            'storage': {'type': 'string', 'required': True},
            'screen_size': {'type': 'string', 'required': False},
            'camera': {'type': 'string', 'required': False},
        }
    },
    {
        'name': 'Phụ kiện',
        'attribute_schema': {
            'type': {'type': 'string', 'required': True},
            'compatibility': {'type': 'string', 'required': False},
            'color': {'type': 'string', 'required': False},
        }
    },
    {
        'name': 'Đồng hồ',
        'attribute_schema': {
            'size': {'type': 'string', 'required': False},
            'battery': {'type': 'string', 'required': False},
            'water_resistance': {'type': 'string', 'required': False},
        }
    },
]

PRODUCTS = [
    # Electronics - Laptop
    {
        'name': 'MacBook Pro 14" M3',
        'description': 'Apple MacBook Pro 14 inch với chip M3, hiệu năng mạnh mẽ',
        'price': 49990000,
        'category_slug': 'laptop',
        'brand_name': 'Apple',
        'attributes': {'ram': '16GB', 'cpu': 'Apple M3', 'storage': '512GB SSD', 'screen_size': '14.2 inch'},
        'variants': [
            {'name': '16GB / 512GB', 'stock': 50, 'attributes': {'ram': '16GB', 'storage': '512GB'}},
            {'name': '32GB / 1TB', 'price_override': 62990000, 'stock': 30, 'attributes': {'ram': '32GB', 'storage': '1TB'}},
        ]
    },
    {
        'name': 'MacBook Air 13" M2',
        'description': 'Apple MacBook Air 13 inch chip M2 - mỏng nhẹ, pin lâu',
        'price': 27990000,
        'category_slug': 'laptop',
        'brand_name': 'Apple',
        'attributes': {'ram': '8GB', 'cpu': 'Apple M2', 'storage': '256GB SSD', 'screen_size': '13.6 inch'},
        'variants': []
    },
    {
        'name': 'Dell XPS 13 Plus',
        'description': 'Laptop Dell XPS 13 Plus mới nhất, thiết kế đột phá',
        'price': 42990000,
        'category_slug': 'laptop',
        'brand_name': 'Dell',
        'attributes': {'ram': '16GB', 'cpu': 'Intel i7-1360P', 'storage': '512GB SSD', 'screen_size': '13.4 inch'},
        'variants': []
    },
    {
        'name': 'ASUS Zenbook 14 OLED',
        'description': 'Laptop ASUS Zenbook 14 OLED UX3402 - Màn hình tuyệt đẹp',
        'price': 23990000,
        'category_slug': 'laptop',
        'brand_name': 'ASUS',
        'attributes': {'ram': '16GB', 'cpu': 'Intel i5-1240P', 'storage': '512GB SSD', 'screen_size': '14 inch'},
        'variants': []
    },
    {
        'name': 'Lenovo ThinkPad X1 Carbon Gen 11',
        'description': 'Laptop doanh nhân cao cấp Lenovo ThinkPad X1 Carbon',
        'price': 52990000,
        'category_slug': 'laptop',
        'brand_name': 'Lenovo',
        'attributes': {'ram': '32GB', 'cpu': 'Intel i7-1355U', 'storage': '1TB SSD', 'screen_size': '14 inch'},
        'variants': []
    },
    # Electronics - Điện thoại
    {
        'name': 'iPhone 15 Pro Max',
        'description': 'Apple iPhone 15 Pro Max - Khung viền Titanium, USB-C',
        'price': 34990000,
        'category_slug': 'dien-thoai',
        'brand_name': 'Apple',
        'attributes': {'ram': '8GB', 'storage': '256GB', 'screen_size': '6.7 inch', 'camera': '48MP'},
        'variants': [
            {'name': '256GB', 'stock': 100, 'attributes': {'storage': '256GB'}},
            {'name': '512GB', 'price_override': 40990000, 'stock': 50, 'attributes': {'storage': '512GB'}},
            {'name': '1TB', 'price_override': 46990000, 'stock': 20, 'attributes': {'storage': '1TB'}},
        ]
    },
    {
        'name': 'Samsung Galaxy S24 Ultra',
        'description': 'Samsung Galaxy S24 Ultra - Camera mạnh, hiệu năng cao',
        'price': 31990000,
        'category_slug': 'dien-thoai',
        'brand_name': 'Samsung',
        'attributes': {'ram': '12GB', 'storage': '256GB', 'screen_size': '6.8 inch', 'camera': '200MP'},
        'variants': []
    },
    {
        'name': 'Xiaomi 14 Pro',
        'description': 'Xiaomi 14 Pro - Ống kính Leica thế hệ mới',
        'price': 18990000,
        'category_slug': 'dien-thoai',
        'brand_name': 'Xiaomi',
        'attributes': {'ram': '12GB', 'storage': '256GB', 'screen_size': '6.73 inch', 'camera': '50MP'},
        'variants': []
    },
    {
        'name': 'Oppo Find X7 Ultra',
        'description': 'Oppo Find X7 Ultra - Camera Hasselblad cực đỉnh',
        'price': 21990000,
        'category_slug': 'dien-thoai',
        'brand_name': 'Oppo',
        'attributes': {'ram': '16GB', 'storage': '512GB', 'screen_size': '6.82 inch', 'camera': '50MP Quad'},
        'variants': []
    },
    # Electronics - Phụ kiện
    {
        'name': 'Anker 735 Charger (GaNPrime 65W)',
        'description': 'Sạc nhanh GaN 65W gọn nhẹ cho laptop/điện thoại',
        'price': 1290000,
        'category_slug': 'phu-kien',
        'brand_name': 'Anker',
        'attributes': {'type': 'Charger', 'compatibility': 'USB-C PD', 'color': 'Black'},
        'variants': []
    },
    {
        'name': 'Baseus USB-C Cable 100W',
        'description': 'Cáp sạc USB-C 100W bền chắc, hỗ trợ PD',
        'price': 189000,
        'category_slug': 'phu-kien',
        'brand_name': 'Baseus',
        'attributes': {'type': 'Cable', 'compatibility': 'USB-C PD', 'color': 'Black'},
        'variants': []
    },
    {
        'name': 'Logitech MX Master 3S',
        'description': 'Chuột không dây cao cấp Logitech MX Master 3S',
        'price': 2490000,
        'category_slug': 'phu-kien',
        'brand_name': 'Logitech',
        'attributes': {'type': 'Mouse', 'compatibility': 'Windows/macOS', 'color': 'Graphite'},
        'variants': []
    },

    # Electronics - Đồng hồ
    {
        'name': 'Apple Watch Series 9 GPS 45mm',
        'description': 'Apple Watch Series 9 theo dõi sức khỏe, thể thao',
        'price': 10990000,
        'category_slug': 'dong-ho',
        'brand_name': 'Apple',
        'attributes': {'size': '45mm', 'battery': 'Up to 18 hours', 'water_resistance': '50m'},
        'variants': []
    },
    {
        'name': 'Samsung Galaxy Watch6 44mm',
        'description': 'Samsung Galaxy Watch6 theo dõi sức khỏe, ngủ, tập luyện',
        'price': 6990000,
        'category_slug': 'dong-ho',
        'brand_name': 'Samsung',
        'attributes': {'size': '44mm', 'battery': 'Up to 40 hours', 'water_resistance': '5ATM'},
        'variants': []
    },

    # More electronics
    {'name': 'HP Spectre x360 14', 'description': 'Laptop HP Spectre x360 14 cao cap cho cong viec sang tao', 'price': 38990000, 'category_slug': 'laptop', 'brand_name': 'HP', 'attributes': {'ram': '16GB', 'cpu': 'Intel Core Ultra 7', 'storage': '1TB SSD', 'screen_size': '14 inch OLED'}, 'variants': []},
    {'name': 'Dell Inspiron 14 5430', 'description': 'Laptop Dell Inspiron 14 can bang giua hoc tap va van phong', 'price': 20990000, 'category_slug': 'laptop', 'brand_name': 'Dell', 'attributes': {'ram': '16GB', 'cpu': 'Intel i5-1335U', 'storage': '512GB SSD', 'screen_size': '14 inch'}, 'variants': []},
    {'name': 'ASUS ROG Zephyrus G14', 'description': 'Laptop gaming ASUS ROG Zephyrus G14 hieu nang cao', 'price': 45990000, 'category_slug': 'laptop', 'brand_name': 'ASUS', 'attributes': {'ram': '32GB', 'cpu': 'AMD Ryzen 9', 'storage': '1TB SSD', 'screen_size': '14 inch'}, 'variants': []},
    {'name': 'Lenovo Yoga 7i 14', 'description': 'Laptop Lenovo Yoga 7i 2 in 1 linh hoat', 'price': 26990000, 'category_slug': 'laptop', 'brand_name': 'Lenovo', 'attributes': {'ram': '16GB', 'cpu': 'Intel Core Ultra 5', 'storage': '512GB SSD', 'screen_size': '14 inch Touch'}, 'variants': []},
    {'name': 'MacBook Air 15 M3', 'description': 'Apple MacBook Air 15 inch chip M3 cho nhu cau da nhiem', 'price': 36990000, 'category_slug': 'laptop', 'brand_name': 'Apple', 'attributes': {'ram': '16GB', 'cpu': 'Apple M3', 'storage': '512GB SSD', 'screen_size': '15.3 inch'}, 'variants': []},

    {'name': 'Samsung Galaxy Z Fold6', 'description': 'Dien thoai gap Samsung Galaxy Z Fold6 man hinh lon da nhiem', 'price': 41990000, 'category_slug': 'dien-thoai', 'brand_name': 'Samsung', 'attributes': {'ram': '12GB', 'storage': '512GB', 'screen_size': '7.6 inch', 'camera': '50MP'}, 'variants': []},
    {'name': 'iPhone 15', 'description': 'Apple iPhone 15 phien ban tieu chuan voi Dynamic Island', 'price': 22990000, 'category_slug': 'dien-thoai', 'brand_name': 'Apple', 'attributes': {'ram': '6GB', 'storage': '128GB', 'screen_size': '6.1 inch', 'camera': '48MP'}, 'variants': []},
    {'name': 'Xiaomi 14', 'description': 'Xiaomi 14 man hinh nho gon, chip flagship', 'price': 16990000, 'category_slug': 'dien-thoai', 'brand_name': 'Xiaomi', 'attributes': {'ram': '12GB', 'storage': '256GB', 'screen_size': '6.36 inch', 'camera': '50MP'}, 'variants': []},
    {'name': 'Oppo Reno11 Pro 5G', 'description': 'Oppo Reno11 Pro 5G thiet ke dep, chup chan dung an tuong', 'price': 13990000, 'category_slug': 'dien-thoai', 'brand_name': 'Oppo', 'attributes': {'ram': '12GB', 'storage': '256GB', 'screen_size': '6.7 inch', 'camera': '50MP'}, 'variants': []},
    {'name': 'Samsung Galaxy A55 5G', 'description': 'Samsung Galaxy A55 5G tam trung can bang', 'price': 9990000, 'category_slug': 'dien-thoai', 'brand_name': 'Samsung', 'attributes': {'ram': '8GB', 'storage': '128GB', 'screen_size': '6.6 inch', 'camera': '50MP'}, 'variants': []},

    {'name': 'Anker PowerCore 10000 PD', 'description': 'Pin du phong 10000mAh ho tro sac nhanh PD', 'price': 790000, 'category_slug': 'phu-kien', 'brand_name': 'Anker', 'attributes': {'type': 'Power Bank', 'compatibility': 'USB-C PD', 'color': 'Black'}, 'variants': []},
    {'name': 'Baseus Bluetooth Earbuds Bowie MA10', 'description': 'Tai nghe true wireless chong on co ban', 'price': 890000, 'category_slug': 'phu-kien', 'brand_name': 'Baseus', 'attributes': {'type': 'Earbuds', 'compatibility': 'iOS/Android', 'color': 'Black'}, 'variants': []},
    {'name': 'Logitech K380 Multi-Device', 'description': 'Ban phim Bluetooth nho gon cho nhieu thiet bi', 'price': 990000, 'category_slug': 'phu-kien', 'brand_name': 'Logitech', 'attributes': {'type': 'Keyboard', 'compatibility': 'Windows/macOS', 'color': 'White'}, 'variants': []},

    {'name': 'Apple Watch SE 2 GPS 44mm', 'description': 'Apple Watch SE gen 2 phu hop nhu cau co ban', 'price': 7490000, 'category_slug': 'dong-ho', 'brand_name': 'Apple', 'attributes': {'size': '44mm', 'battery': 'Up to 18 hours', 'water_resistance': '50m'}, 'variants': []},

    # More laptops
    {'name': 'ASUS TUF Gaming F15', 'description': 'Laptop gaming ASUS TUF F15 ben bi, hieu nang on dinh', 'price': 22990000, 'category_slug': 'laptop', 'brand_name': 'ASUS', 'attributes': {'ram': '16GB', 'cpu': 'Intel i5-12500H', 'storage': '512GB SSD', 'screen_size': '15.6 inch 144Hz'}, 'variants': []},
    {'name': 'Lenovo Legion 5 15', 'description': 'Laptop gaming Lenovo Legion 5 can bang hieu nang va nhiet do', 'price': 27990000, 'category_slug': 'laptop', 'brand_name': 'Lenovo', 'attributes': {'ram': '16GB', 'cpu': 'AMD Ryzen 7', 'storage': '1TB SSD', 'screen_size': '15.6 inch 165Hz'}, 'variants': []},
    {'name': 'Dell Latitude 7440', 'description': 'Laptop doanh nhan Dell Latitude 7440 nhe, ben, bao mat tot', 'price': 33990000, 'category_slug': 'laptop', 'brand_name': 'Dell', 'attributes': {'ram': '16GB', 'cpu': 'Intel i7-1365U', 'storage': '512GB SSD', 'screen_size': '14 inch'}, 'variants': []},
    {'name': 'HP Pavilion 14', 'description': 'Laptop HP Pavilion 14 phu hop hoc tap va van phong', 'price': 15990000, 'category_slug': 'laptop', 'brand_name': 'HP', 'attributes': {'ram': '8GB', 'cpu': 'Intel i5-1235U', 'storage': '512GB SSD', 'screen_size': '14 inch'}, 'variants': []},

    # More phones
    {'name': 'Samsung Galaxy S24', 'description': 'Samsung Galaxy S24 thiet ke nho gon, man hinh dep', 'price': 21990000, 'category_slug': 'dien-thoai', 'brand_name': 'Samsung', 'attributes': {'ram': '8GB', 'storage': '256GB', 'screen_size': '6.2 inch', 'camera': '50MP'}, 'variants': []},
    {'name': 'Samsung Galaxy S24 Plus', 'description': 'Samsung Galaxy S24+ pin lon, hieu nang manh', 'price': 25990000, 'category_slug': 'dien-thoai', 'brand_name': 'Samsung', 'attributes': {'ram': '12GB', 'storage': '256GB', 'screen_size': '6.7 inch', 'camera': '50MP'}, 'variants': []},
    {'name': 'iPhone 15 Pro', 'description': 'Apple iPhone 15 Pro - Titanium, hieu nang cao', 'price': 28990000, 'category_slug': 'dien-thoai', 'brand_name': 'Apple', 'attributes': {'ram': '8GB', 'storage': '128GB', 'screen_size': '6.1 inch', 'camera': '48MP'}, 'variants': []},
    {'name': 'Xiaomi 14 Ultra', 'description': 'Xiaomi 14 Ultra camera manh, man hinh sang', 'price': 28990000, 'category_slug': 'dien-thoai', 'brand_name': 'Xiaomi', 'attributes': {'ram': '16GB', 'storage': '512GB', 'screen_size': '6.73 inch', 'camera': '50MP Quad'}, 'variants': []},
    {'name': 'Oppo Find N3', 'description': 'Oppo Find N3 dien thoai gap nhe, man hinh lon', 'price': 34990000, 'category_slug': 'dien-thoai', 'brand_name': 'Oppo', 'attributes': {'ram': '12GB', 'storage': '512GB', 'screen_size': '7.8 inch', 'camera': '48MP'}, 'variants': []},

    # More accessories
    {'name': 'Anker Nano II 30W Charger', 'description': 'Sac nhanh GaN 30W nho gon cho iPhone/Android', 'price': 399000, 'category_slug': 'phu-kien', 'brand_name': 'Anker', 'attributes': {'type': 'Charger', 'compatibility': 'USB-C PD', 'color': 'White'}, 'variants': []},
    {'name': 'Baseus Magnetic Power Bank 10000mAh', 'description': 'Pin du phong nam cham tien, sac nhanh', 'price': 990000, 'category_slug': 'phu-kien', 'brand_name': 'Baseus', 'attributes': {'type': 'Power Bank', 'compatibility': 'MagSafe', 'color': 'Black'}, 'variants': []},
    {'name': 'Logitech G304 Lightspeed', 'description': 'Chuột gaming khong day Logitech G304', 'price': 890000, 'category_slug': 'phu-kien', 'brand_name': 'Logitech', 'attributes': {'type': 'Mouse', 'compatibility': 'Windows/macOS', 'color': 'Black'}, 'variants': []},
    {'name': 'Logitech Pebble 2 Combo', 'description': 'Combo chuot va ban phim nho gon cho van phong', 'price': 1490000, 'category_slug': 'phu-kien', 'brand_name': 'Logitech', 'attributes': {'type': 'Keyboard+Mouse', 'compatibility': 'Windows/macOS', 'color': 'Sand'}, 'variants': []},

    # More watches
    {'name': 'Apple Watch Ultra 2 49mm', 'description': 'Apple Watch Ultra 2 ben bi, pin lau cho the thao', 'price': 22990000, 'category_slug': 'dong-ho', 'brand_name': 'Apple', 'attributes': {'size': '49mm', 'battery': 'Up to 36 hours', 'water_resistance': '100m'}, 'variants': []},
    {'name': 'Samsung Galaxy Watch6 Classic 47mm', 'description': 'Galaxy Watch6 Classic vong xoay co dien, man hinh lon', 'price': 8990000, 'category_slug': 'dong-ho', 'brand_name': 'Samsung', 'attributes': {'size': '47mm', 'battery': 'Up to 40 hours', 'water_resistance': '5ATM'}, 'variants': []},

    # Extra laptops
    {'name': 'MacBook Pro 16" M3 Pro', 'description': 'MacBook Pro 16 inch chip M3 Pro cho cong viec nang', 'price': 69990000, 'category_slug': 'laptop', 'brand_name': 'Apple', 'attributes': {'ram': '18GB', 'cpu': 'Apple M3 Pro', 'storage': '512GB SSD', 'screen_size': '16.2 inch'}, 'variants': []},
    {'name': 'ASUS Zenbook S 14', 'description': 'Laptop sieu nhe ASUS Zenbook S 14 cho di chuyen', 'price': 32990000, 'category_slug': 'laptop', 'brand_name': 'ASUS', 'attributes': {'ram': '16GB', 'cpu': 'Intel Core Ultra 7', 'storage': '1TB SSD', 'screen_size': '14 inch OLED'}, 'variants': []},
    {'name': 'Lenovo ThinkPad T14s Gen 4', 'description': 'ThinkPad T14s ben bi, bao mat cao, phu hop doanh nhan', 'price': 35990000, 'category_slug': 'laptop', 'brand_name': 'Lenovo', 'attributes': {'ram': '16GB', 'cpu': 'Intel i7', 'storage': '512GB SSD', 'screen_size': '14 inch'}, 'variants': []},
    {'name': 'Dell Precision 5680', 'description': 'Laptop workstation Dell Precision cho do hoa va ky thuat', 'price': 75990000, 'category_slug': 'laptop', 'brand_name': 'Dell', 'attributes': {'ram': '32GB', 'cpu': 'Intel i9', 'storage': '1TB SSD', 'screen_size': '16 inch'}, 'variants': []},
    {'name': 'HP Envy x360 14', 'description': 'Laptop 2-in-1 HP Envy x360 man hinh cam ung', 'price': 21990000, 'category_slug': 'laptop', 'brand_name': 'HP', 'attributes': {'ram': '16GB', 'cpu': 'AMD Ryzen 7', 'storage': '512GB SSD', 'screen_size': '14 inch Touch'}, 'variants': []},

    # Extra phones
    {'name': 'iPhone 14 Pro Max', 'description': 'iPhone 14 Pro Max still strong choice, man hinh dep', 'price': 24990000, 'category_slug': 'dien-thoai', 'brand_name': 'Apple', 'attributes': {'ram': '6GB', 'storage': '256GB', 'screen_size': '6.7 inch', 'camera': '48MP'}, 'variants': []},
    {'name': 'Samsung Galaxy Z Flip6', 'description': 'Galaxy Z Flip6 nho gon, thoi trang, man hinh phu tien', 'price': 25990000, 'category_slug': 'dien-thoai', 'brand_name': 'Samsung', 'attributes': {'ram': '8GB', 'storage': '256GB', 'screen_size': '6.7 inch', 'camera': '12MP'}, 'variants': []},
    {'name': 'Xiaomi Redmi Note 13 Pro', 'description': 'Redmi Note 13 Pro pin trau, gia tot cho hoc sinh', 'price': 8990000, 'category_slug': 'dien-thoai', 'brand_name': 'Xiaomi', 'attributes': {'ram': '8GB', 'storage': '256GB', 'screen_size': '6.67 inch', 'camera': '200MP'}, 'variants': []},
    {'name': 'Oppo A79 5G', 'description': 'Oppo A79 5G phu hop nhu cau co ban, gia hop ly', 'price': 6990000, 'category_slug': 'dien-thoai', 'brand_name': 'Oppo', 'attributes': {'ram': '8GB', 'storage': '128GB', 'screen_size': '6.72 inch', 'camera': '50MP'}, 'variants': []},

    # Extra accessories
    {'name': 'Anker Soundcore Q30', 'description': 'Tai nghe chong on, pin lau, gia/hiieu nang tot', 'price': 1990000, 'category_slug': 'phu-kien', 'brand_name': 'Anker', 'attributes': {'type': 'Headphones', 'compatibility': 'iOS/Android', 'color': 'Black'}, 'variants': []},
    {'name': 'Baseus 6-in-1 USB-C Hub', 'description': 'Hub USB-C da cong, ho tro HDMI/USB/PD', 'price': 790000, 'category_slug': 'phu-kien', 'brand_name': 'Baseus', 'attributes': {'type': 'USB-C Hub', 'compatibility': 'USB-C', 'color': 'Grey'}, 'variants': []},
    {'name': 'Logitech C920 HD Pro Webcam', 'description': 'Webcam Logitech C920 chat luong tot cho hoc/meet', 'price': 1690000, 'category_slug': 'phu-kien', 'brand_name': 'Logitech', 'attributes': {'type': 'Webcam', 'compatibility': 'Windows/macOS', 'color': 'Black'}, 'variants': []},
    {'name': 'Logitech M221 Silent', 'description': 'Chuột im lang, gia re, phu hop van phong', 'price': 299000, 'category_slug': 'phu-kien', 'brand_name': 'Logitech', 'attributes': {'type': 'Mouse', 'compatibility': 'Windows/macOS', 'color': 'Black'}, 'variants': []},
    {'name': 'Baseus Car Charger 65W', 'description': 'Sac xe hoi 65W, 2 cong, sac nhanh', 'price': 450000, 'category_slug': 'phu-kien', 'brand_name': 'Baseus', 'attributes': {'type': 'Car Charger', 'compatibility': 'USB-C PD', 'color': 'Black'}, 'variants': []},

    # Extra watches
    {'name': 'Apple Watch Series 8 GPS 45mm', 'description': 'Apple Watch Series 8 van rat on cho nhu cau hang ngay', 'price': 9490000, 'category_slug': 'dong-ho', 'brand_name': 'Apple', 'attributes': {'size': '45mm', 'battery': 'Up to 18 hours', 'water_resistance': '50m'}, 'variants': []},
    {'name': 'Samsung Galaxy Watch5 Pro 45mm', 'description': 'Watch5 Pro pin ben, phu hop tap luyen', 'price': 7990000, 'category_slug': 'dong-ho', 'brand_name': 'Samsung', 'attributes': {'size': '45mm', 'battery': 'Up to 80 hours', 'water_resistance': '5ATM'}, 'variants': []},
]

TARGET_PRODUCT_COUNT = len(PRODUCTS)


def build_product_pool(target_count=TARGET_PRODUCT_COUNT):
    """Use only real product entries (no synthetic naming)."""
    pool = PRODUCTS
    return pool[: min(target_count, len(pool))]


class Command(BaseCommand):
    help = 'Seed sample brands, product types, and products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products and variants before seeding',
        )
        parser.add_argument(
            '--target-count',
            type=int,
            default=TARGET_PRODUCT_COUNT,
            help=f'Number of products to seed (default: {TARGET_PRODUCT_COUNT})',
        )

    def handle(self, *args, **options):
        target_count = options['target_count']
        if target_count < 1:
            self.stdout.write(self.style.ERROR('target-count must be >= 1'))
            return

        if options['clear']:
            self.stdout.write('Clearing existing products and variants...')
            VariantModel.objects.all().delete()
            ProductModel.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared!'))

        self.stdout.write('Seeding brands...')
        brand_map = {}
        for b in BRANDS:
            brand, created = BrandModel.objects.get_or_create(
                slug=generate_slug(b['name']),
                defaults={'name': b['name'], 'description': b['description']}
            )
            brand_map[b['name']] = brand
            self.stdout.write(f"  {'Created' if created else 'Exists'}: {b['name']}")

        self.stdout.write('Seeding product types...')
        for pt in PRODUCT_TYPES:
            _, created = ProductTypeModel.objects.get_or_create(
                slug=generate_slug(pt['name']),
                defaults={'name': pt['name'], 'attribute_schema': pt['attribute_schema']}
            )
            self.stdout.write(f"  {'Created' if created else 'Exists'}: {pt['name']}")

        products_to_seed = build_product_pool(target_count)
        self.stdout.write(f'Seeding products (target: {target_count})...')
        for p in products_to_seed:
            category = CategoryModel.objects.filter(slug=p['category_slug']).first()
            brand = brand_map.get(p['brand_name'])

            product, created = ProductModel.objects.get_or_create(
                slug=generate_slug(p['name']),
                defaults={
                    'name': p['name'],
                    'description': p['description'],
                    'price': p['price'],
                    'category': category,
                    'brand': brand,
                    'attributes': p['attributes'],
                    'image_url': '',
                    'stock_quantity': 100,
                }
            )
            self.stdout.write(f"  {'Created' if created else 'Exists'}: {p['name']}")

            if (created or options['clear']) and p.get('variants'):
                for v in p['variants']:
                    VariantModel.objects.create(
                        product=product,
                        sku=generate_sku('VAR'),
                        name=v['name'],
                        price_override=v.get('price_override'),
                        stock=v.get('stock', 0),
                        attributes=v.get('attributes', {}),
                    )
                    self.stdout.write(f"    Created variant: {v['name']}")

        final_total = ProductModel.objects.count()
        total_variants = VariantModel.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'Done! Products: {final_total}, Variants: {total_variants}'
        ))
