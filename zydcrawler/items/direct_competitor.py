from itemloaders.processors import TakeFirst
import scrapy


class RestaurantMainItem(scrapy.Item):
    file_name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    url = scrapy.Field(serializer=str, output_processor=TakeFirst())
    name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    name_ar = scrapy.Field(serializer=str, output_processor=TakeFirst())
    logo = scrapy.Field(serializer=str, output_processor=TakeFirst())
    country = scrapy.Field(serializer=str, output_processor=TakeFirst())
    product = scrapy.Field(serializer=dict, output_processor=TakeFirst())


class ProductMainItem(scrapy.Item):
    name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    name_ar = scrapy.Field(serializer=str, output_processor=TakeFirst())
    description = scrapy.Field(serializer=str, output_processor=TakeFirst())
    description_ar = scrapy.Field(serializer=str, output_processor=TakeFirst())
    price = scrapy.Field(serializer=str, output_processor=TakeFirst())
    logo = scrapy.Field(serializer=str, output_processor=TakeFirst())
    category = scrapy.Field(serializer=str, output_processor=TakeFirst())
    variant = scrapy.Field(serializer=dict, output_processor=TakeFirst())


class VariantMainItem(scrapy.Item):
    min_choice = scrapy.Field(serializer=str, output_processor=TakeFirst())
    max_choice = scrapy.Field(serializer=str, output_processor=TakeFirst())
    description = scrapy.Field(serializer=str, output_processor=TakeFirst())
    name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    name_ar = scrapy.Field(serializer=str, output_processor=TakeFirst())
    options = scrapy.Field(serializer=list)

class OptionMainItem(scrapy.Item):
    name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    name_ar = scrapy.Field(serializer=str, output_processor=TakeFirst())
    price = scrapy.Field(serializer=str, output_processor=TakeFirst())


class ItsOrderableProductItem(ProductMainItem):
    currency = scrapy.Field(serializer=str, output_processor=TakeFirst())