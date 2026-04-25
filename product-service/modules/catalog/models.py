# Import all models here so Django can discover them for migrations
from modules.catalog.infrastructure.models.category_model import CategoryModel  # noqa
from modules.catalog.infrastructure.models.brand_model import BrandModel  # noqa
from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel  # noqa
from modules.catalog.infrastructure.models.product_model import ProductModel  # noqa
from modules.catalog.infrastructure.models.variant_model import VariantModel  # noqa
