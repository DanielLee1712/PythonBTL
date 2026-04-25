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
    {'name': 'Nike', 'description': 'Nike, Inc. - Sportswear and Footwear'},
    {'name': 'Adidas', 'description': 'Adidas AG - Sportswear and Footwear'},
    {'name': 'Puma', 'description': 'Puma SE - Sportswear and Footwear'},
    {'name': "L'Oreal", 'description': "L'Oreal Paris - Beauty and Skincare"},
    {'name': 'Maybelline', 'description': 'Maybelline New York - Cosmetics'},
    {'name': 'MAC', 'description': 'M·A·C Cosmetics - Professional Makeup'},
    {'name': 'Daikin', 'description': 'Daikin Industries - Air Conditioning'},
    {'name': 'Panasonic', 'description': 'Panasonic Holdings - Home Appliances'},
    {'name': 'LG', 'description': 'LG Electronics - Home Appliances, Display'},
    {'name': 'Uniqlo', 'description': 'Uniqlo Co., Ltd. - Casual Wear'},
    {'name': 'Levi\'s', 'description': 'Levi Strauss & Co. - Denim and Jeans'},
    {'name': 'Estee Lauder', 'description': 'The Estée Lauder Companies - Luxury Beauty'},
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
        'name': 'Quần áo',
        'attribute_schema': {
            'size': {'type': 'string', 'required': True},
            'color': {'type': 'string', 'required': True},
            'material': {'type': 'string', 'required': False},
        }
    },
    {
        'name': 'Mỹ phẩm',
        'attribute_schema': {
            'shade': {'type': 'string', 'required': False},
            'volume': {'type': 'string', 'required': False},
            'skin_type': {'type': 'string', 'required': False},
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
    # Electronics - Mobile
    {
        'name': 'iPhone 15 Pro Max',
        'description': 'Apple iPhone 15 Pro Max - Khung viền Titanium, USB-C',
        'price': 34990000,
        'category_slug': 'mobile',
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
        'description': 'Samsung Galaxy S24 Ultra - Đỉnh cao công nghệ AI',
        'price': 31990000,
        'category_slug': 'mobile',
        'brand_name': 'Samsung',
        'attributes': {'ram': '12GB', 'storage': '256GB', 'screen_size': '6.8 inch', 'camera': '200MP'},
        'variants': []
    },
    {
        'name': 'Xiaomi 14 Pro',
        'description': 'Xiaomi 14 Pro - Ống kính Leica thế hệ mới',
        'price': 18990000,
        'category_slug': 'mobile',
        'brand_name': 'Xiaomi',
        'attributes': {'ram': '12GB', 'storage': '256GB', 'screen_size': '6.73 inch', 'camera': '50MP'},
        'variants': []
    },
    {
        'name': 'Oppo Find X7 Ultra',
        'description': 'Oppo Find X7 Ultra - Camera Hasselblad cực đỉnh',
        'price': 21990000,
        'category_slug': 'mobile',
        'brand_name': 'Oppo',
        'attributes': {'ram': '16GB', 'storage': '512GB', 'screen_size': '6.82 inch', 'camera': '50MP Quad'},
        'variants': []
    },
    # Electronics - Điều hòa
    {
        'name': 'Daikin Inverter 1.5HP FTKC35VVMV',
        'description': 'Điều hòa Daikin Inverter 1.5HP lọc bụi mịn PM2.5',
        'price': 13490000,
        'category_slug': 'dieu-hoa',
        'brand_name': 'Daikin',
        'attributes': {'capacity': '1.5HP', 'type': 'Inverter', 'gas': 'R32'},
        'variants': []
    },
    {
        'name': 'Panasonic Inverter 1HP CU/CS-PU9WKH-8M',
        'description': 'Điều hòa Panasonic Inverter 1HP công nghệ Nanoe-G',
        'price': 9990000,
        'category_slug': 'dieu-hoa',
        'brand_name': 'Panasonic',
        'attributes': {'capacity': '1HP', 'type': 'Inverter', 'technology': 'Nanoe-G'},
        'variants': []
    },
    # Electronics - Tủ lạnh
    {
        'name': 'Samsung Bespoke 4 Cửa',
        'description': 'Tủ lạnh Samsung Bespoke thiết kế sang trọng, hiện đại',
        'price': 45990000,
        'category_slug': 'tu-lanh',
        'brand_name': 'Samsung',
        'attributes': {'capacity': '599L', 'type': 'Multi Door', 'feature': 'Bespoke Design'},
        'variants': []
    },
    {
        'name': 'LG Inverter Side by Side 635L',
        'description': 'Tủ lạnh LG Side by Side dung tích lớn, tiết kiệm điện',
        'price': 22990000,
        'category_slug': 'tu-lanh',
        'brand_name': 'LG',
        'attributes': {'capacity': '635L', 'type': 'Side by Side', 'technology': 'Inverter Linear'},
        'variants': []
    },
    # Thời trang - Áo
    {
        'name': 'Nike Dri-FIT Academy',
        'description': 'Áo bóng đá Nike Dri-FIT Academy thoải mái vận động',
        'price': 750000,
        'category_slug': 'ao',
        'brand_name': 'Nike',
        'attributes': {'size': 'M', 'color': 'Navy Blue', 'material': 'Polyester'},
        'variants': [
            {'name': 'S - Blue', 'stock': 100, 'attributes': {'size': 'S'}},
            {'name': 'M - Blue', 'stock': 150, 'attributes': {'size': 'M'}},
            {'name': 'L - Blue', 'stock': 100, 'attributes': {'size': 'L'}},
        ]
    },
    {
        'name': 'Adidas Essentials 3-Stripes Tee',
        'description': 'Áo thun Adidas Essentials phong cách cổ điển',
        'price': 650000,
        'category_slug': 'ao',
        'brand_name': 'Adidas',
        'attributes': {'size': 'L', 'color': 'White', 'material': 'Cotton'},
        'variants': []
    },
    {
        'name': 'Uniqlo AIRism Cotton T-Shirt',
        'description': 'Áo thun Uniqlo AIRism công nghệ làm mát',
        'price': 399000,
        'category_slug': 'ao',
        'brand_name': 'Uniqlo',
        'attributes': {'size': 'M', 'color': 'Black', 'material': 'AIRism Cotton'},
        'variants': []
    },
    # Thời trang - Quần
    {
        'name': 'Levi\'s 501 Original Fit Jeans',
        'description': 'Quần jeans Levi\'s 501 huyền thoại, phong cách bền bỉ',
        'price': 2290000,
        'category_slug': 'quan',
        'brand_name': 'Levi\'s',
        'attributes': {'size': '32', 'color': 'Indigo', 'material': 'Denim'},
        'variants': []
    },
    {
        'name': 'Adidas Tiro Track Pants',
        'description': 'Quần thể thao Adidas Tiro thoải mái, năng động',
        'price': 1200000,
        'category_slug': 'quan',
        'brand_name': 'Adidas',
        'attributes': {'size': 'L', 'color': 'Black', 'material': 'Recycled Polyester'},
        'variants': []
    },
    # Thời trang - Giày dép
    {
        'name': 'Nike Air Force 1 \'07',
        'description': 'Giày Nike Air Force 1 \'07 - Biểu tượng thời trang đường phố',
        'price': 2990000,
        'category_slug': 'giay-dep',
        'brand_name': 'Nike',
        'attributes': {'size': '42', 'color': 'White', 'material': 'Leather'},
        'variants': [
            {'name': 'Size 40', 'stock': 20, 'attributes': {'size': '40'}},
            {'name': 'Size 41', 'stock': 30, 'attributes': {'size': '41'}},
            {'name': 'Size 42', 'stock': 50, 'attributes': {'size': '42'}},
        ]
    },
    {
        'name': 'Adidas Ultraboost Light',
        'description': 'Giày chạy bộ Adidas Ultraboost Light cực nhẹ',
        'price': 4500000,
        'category_slug': 'giay-dep',
        'brand_name': 'Adidas',
        'attributes': {'size': '41', 'color': 'Black/Sol Red', 'material': 'Primeknit'},
        'variants': []
    },
    {
        'name': 'Puma Cali Star',
        'description': 'Giày sneaker Puma Cali Star nữ tính và phong cách',
        'price': 2100000,
        'category_slug': 'giay-dep',
        'brand_name': 'Puma',
        'attributes': {'size': '37', 'color': 'White/Gold', 'material': 'Synthetic Leather'},
        'variants': []
    },
    # Mỹ phẩm - Son môi
    {
        'name': "MAC Matte Lipstick",
        'description': "Son thỏi MAC Matte Lipstick - màu sắc chuẩn, lâu trôi",
        'price': 550000,
        'category_slug': 'son-moi',
        'brand_name': 'MAC',
        'attributes': {'shade': 'Ruby Woo', 'type': 'Matte'},
        'variants': [
            {'name': 'Ruby Woo', 'stock': 100, 'attributes': {'shade': 'Ruby Woo'}},
            {'name': 'Chili', 'stock': 80, 'attributes': {'shade': 'Chili'}},
            {'name': 'Russian Red', 'stock': 60, 'attributes': {'shade': 'Russian Red'}},
        ]
    },
    {
        'name': "Maybelline SuperStay Matte Ink",
        'description': "Son kem lì Maybelline SuperStay Matte Ink giữ màu 16h",
        'price': 205000,
        'category_slug': 'son-moi',
        'brand_name': 'Maybelline',
        'attributes': {'shade': '117 Ground-Breaker', 'type': 'Liquid Matte'},
        'variants': []
    },
    # Mỹ phẩm - Kem nền
    {
        'name': "Estee Lauder Double Wear",
        'description': "Kem nền Estee Lauder Double Wear Stay-in-Place cực bám",
        'price': 1450000,
        'category_slug': 'kem-nen',
        'brand_name': 'Estee Lauder',
        'attributes': {'shade': '1W1 Bone', 'spf': '10'},
        'variants': []
    },
    {
        'name': "L'Oreal Infallible 24H Fresh Wear",
        'description': "Kem nền L'Oreal Infallible lâu trôi, mỏng nhẹ",
        'price': 350000,
        'category_slug': 'kem-nen',
        'brand_name': "L'Oreal",
        'attributes': {'shade': '120 Vanilla', 'spf': '25'},
        'variants': []
    },

    # Bo sung them 25 san pham that theo cung mau
    # Electronics - Laptop
    {'name': 'HP Spectre x360 14', 'description': 'Laptop HP Spectre x360 14 cao cap cho cong viec sang tao', 'price': 38990000, 'category_slug': 'laptop', 'brand_name': 'HP', 'attributes': {'ram': '16GB', 'cpu': 'Intel Core Ultra 7', 'storage': '1TB SSD', 'screen_size': '14 inch OLED'}, 'variants': []},
    {'name': 'Dell Inspiron 14 5430', 'description': 'Laptop Dell Inspiron 14 can bang giua hoc tap va van phong', 'price': 20990000, 'category_slug': 'laptop', 'brand_name': 'Dell', 'attributes': {'ram': '16GB', 'cpu': 'Intel i5-1335U', 'storage': '512GB SSD', 'screen_size': '14 inch'}, 'variants': []},
    {'name': 'ASUS ROG Zephyrus G14', 'description': 'Laptop gaming ASUS ROG Zephyrus G14 hieu nang cao', 'price': 45990000, 'category_slug': 'laptop', 'brand_name': 'ASUS', 'attributes': {'ram': '32GB', 'cpu': 'AMD Ryzen 9', 'storage': '1TB SSD', 'screen_size': '14 inch'}, 'variants': []},
    {'name': 'Lenovo Yoga 7i 14', 'description': 'Laptop Lenovo Yoga 7i 2 in 1 linh hoat', 'price': 26990000, 'category_slug': 'laptop', 'brand_name': 'Lenovo', 'attributes': {'ram': '16GB', 'cpu': 'Intel Core Ultra 5', 'storage': '512GB SSD', 'screen_size': '14 inch Touch'}, 'variants': []},
    {'name': 'MacBook Air 15 M3', 'description': 'Apple MacBook Air 15 inch chip M3 cho nhu cau da nhiem', 'price': 36990000, 'category_slug': 'laptop', 'brand_name': 'Apple', 'attributes': {'ram': '16GB', 'cpu': 'Apple M3', 'storage': '512GB SSD', 'screen_size': '15.3 inch'}, 'variants': []},

    # Electronics - Mobile
    {'name': 'Samsung Galaxy Z Fold6', 'description': 'Dien thoai gap Samsung Galaxy Z Fold6 man hinh lon da nhiem', 'price': 41990000, 'category_slug': 'mobile', 'brand_name': 'Samsung', 'attributes': {'ram': '12GB', 'storage': '512GB', 'screen_size': '7.6 inch', 'camera': '50MP'}, 'variants': []},
    {'name': 'iPhone 15', 'description': 'Apple iPhone 15 phien ban tieu chuan voi Dynamic Island', 'price': 22990000, 'category_slug': 'mobile', 'brand_name': 'Apple', 'attributes': {'ram': '6GB', 'storage': '128GB', 'screen_size': '6.1 inch', 'camera': '48MP'}, 'variants': []},
    {'name': 'Xiaomi 14', 'description': 'Xiaomi 14 man hinh nho gon, chip flagship', 'price': 16990000, 'category_slug': 'mobile', 'brand_name': 'Xiaomi', 'attributes': {'ram': '12GB', 'storage': '256GB', 'screen_size': '6.36 inch', 'camera': '50MP'}, 'variants': []},
    {'name': 'Oppo Reno11 Pro 5G', 'description': 'Oppo Reno11 Pro 5G thiet ke dep, chup chan dung an tuong', 'price': 13990000, 'category_slug': 'mobile', 'brand_name': 'Oppo', 'attributes': {'ram': '12GB', 'storage': '256GB', 'screen_size': '6.7 inch', 'camera': '50MP'}, 'variants': []},
    {'name': 'Samsung Galaxy A55 5G', 'description': 'Samsung Galaxy A55 5G tam trung can bang', 'price': 9990000, 'category_slug': 'mobile', 'brand_name': 'Samsung', 'attributes': {'ram': '8GB', 'storage': '128GB', 'screen_size': '6.6 inch', 'camera': '50MP'}, 'variants': []},

    # Electronics - Dieu hoa
    {'name': 'Daikin Inverter 1HP FTKB25XVMV', 'description': 'Dieu hoa Daikin 1HP tiet kiem dien cho phong nho', 'price': 10490000, 'category_slug': 'dieu-hoa', 'brand_name': 'Daikin', 'attributes': {'capacity': '1HP', 'type': 'Inverter', 'gas': 'R32'}, 'variants': []},
    {'name': 'Panasonic Inverter 1.5HP XPU12XKH-8', 'description': 'Dieu hoa Panasonic 1.5HP voi cong nghe nanoe X', 'price': 14990000, 'category_slug': 'dieu-hoa', 'brand_name': 'Panasonic', 'attributes': {'capacity': '1.5HP', 'type': 'Inverter', 'technology': 'nanoe X'}, 'variants': []},
    {'name': 'LG DualCool Inverter 1.5HP V13WIN', 'description': 'Dieu hoa LG DualCool Inverter van hanh em ai', 'price': 13290000, 'category_slug': 'dieu-hoa', 'brand_name': 'LG', 'attributes': {'capacity': '1.5HP', 'type': 'Inverter', 'technology': 'Dual Inverter'}, 'variants': []},

    # Electronics - Tu lanh
    {'name': 'Panasonic Prime+ Edition 550L', 'description': 'Tu lanh Panasonic Prime+ Edition dung tich lon', 'price': 26990000, 'category_slug': 'tu-lanh', 'brand_name': 'Panasonic', 'attributes': {'capacity': '550L', 'type': 'Multi Door', 'technology': 'Prime Fresh+'}, 'variants': []},
    {'name': 'LG InstaView Door-in-Door 601L', 'description': 'Tu lanh LG InstaView Door-in-Door cao cap', 'price': 35990000, 'category_slug': 'tu-lanh', 'brand_name': 'LG', 'attributes': {'capacity': '601L', 'type': 'Side by Side', 'technology': 'InstaView'}, 'variants': []},

    # Thoi trang - Ao
    {'name': 'Nike Sportswear Club T-Shirt', 'description': 'Ao thun Nike Sportswear Club co ban de phoi do', 'price': 690000, 'category_slug': 'ao', 'brand_name': 'Nike', 'attributes': {'size': 'M', 'color': 'Grey', 'material': 'Cotton'}, 'variants': []},
    {'name': 'Adidas Adicolor Classics Tee', 'description': 'Ao thun Adidas Adicolor phong cach streetwear', 'price': 720000, 'category_slug': 'ao', 'brand_name': 'Adidas', 'attributes': {'size': 'L', 'color': 'Black', 'material': 'Cotton'}, 'variants': []},
    {'name': 'Uniqlo U Crew Neck T-Shirt', 'description': 'Ao thun Uniqlo U chat lieu day dan, form dep', 'price': 499000, 'category_slug': 'ao', 'brand_name': 'Uniqlo', 'attributes': {'size': 'M', 'color': 'White', 'material': 'Cotton'}, 'variants': []},

    # Thoi trang - Quan
    {'name': "Levi's 511 Slim Fit Jeans", 'description': "Quan jeans Levi's 511 slim fit de mac hang ngay", 'price': 2490000, 'category_slug': 'quan', 'brand_name': "Levi's", 'attributes': {'size': '32', 'color': 'Dark Blue', 'material': 'Denim'}, 'variants': []},
    {'name': 'Adidas Essentials Fleece Pants', 'description': 'Quan ni Adidas Essentials giu am va thoai mai', 'price': 1390000, 'category_slug': 'quan', 'brand_name': 'Adidas', 'attributes': {'size': 'L', 'color': 'Grey', 'material': 'Cotton Blend'}, 'variants': []},
    {'name': 'Nike Dri-FIT Challenger Pants', 'description': 'Quan tap Nike Dri-FIT Challenger danh cho chay bo', 'price': 1590000, 'category_slug': 'quan', 'brand_name': 'Nike', 'attributes': {'size': 'M', 'color': 'Black', 'material': 'Polyester'}, 'variants': []},

    # Thoi trang - Giay dep
    {'name': 'Nike Air Max 270', 'description': 'Giay Nike Air Max 270 de mem va em chan', 'price': 4290000, 'category_slug': 'giay-dep', 'brand_name': 'Nike', 'attributes': {'size': '42', 'color': 'Black/White', 'material': 'Mesh'}, 'variants': []},
    {'name': 'Adidas Superstar', 'description': 'Giay Adidas Superstar kinh dien voi mui vo so', 'price': 2590000, 'category_slug': 'giay-dep', 'brand_name': 'Adidas', 'attributes': {'size': '41', 'color': 'White/Black', 'material': 'Leather'}, 'variants': []},
    {'name': 'Puma RS-X Efekt', 'description': 'Giay Puma RS-X Efekt phong cach retro hien dai', 'price': 2890000, 'category_slug': 'giay-dep', 'brand_name': 'Puma', 'attributes': {'size': '40', 'color': 'Grey/Orange', 'material': 'Textile'}, 'variants': []},

    # My pham
    {'name': 'MAC Locked Kiss Ink Lipcolour', 'description': 'Son kem MAC Locked Kiss Ink ben mau dai lau', 'price': 790000, 'category_slug': 'son-moi', 'brand_name': 'MAC', 'attributes': {'shade': 'Mull It Over', 'type': 'Liquid Matte'}, 'variants': []},
]

TARGET_PRODUCT_COUNT = 50


def build_product_pool(target_count=TARGET_PRODUCT_COUNT):
    """Use only real product entries (no synthetic naming)."""
    pool = PRODUCTS
    if target_count > len(pool):
        raise ValueError(f"Requested {target_count} products but only {len(pool)} real products are defined.")
    return pool[:target_count]


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
