from itemloaders.processors import TakeFirst
import scrapy


class RestaurantItem(scrapy.Item):
    file_name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    url = scrapy.Field(serializer=str, output_processor=TakeFirst())
    name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    area_name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    area_ar = scrapy.Field(serializer=str, output_processor=TakeFirst())
    logo = scrapy.Field(serializer=str, output_processor=TakeFirst())
    city = scrapy.Field(serializer=str, output_processor=TakeFirst())
    city_ar = scrapy.Field(serializer=str, output_processor=TakeFirst())
    country = scrapy.Field(serializer=str, output_processor=TakeFirst())
    country_ar = scrapy.Field(serializer=str, output_processor=TakeFirst())
    products = scrapy.Field(serializer=dict, output_processor=TakeFirst())


class RestaurantProductItem(scrapy.Item):
    name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    description = scrapy.Field(serializer=str, output_processor=TakeFirst())
    price = scrapy.Field(serializer=str, output_processor=TakeFirst())
    currency = scrapy.Field(serializer=str, output_processor=TakeFirst())
    image = scrapy.Field(serializer=str, output_processor=TakeFirst())
    section_name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    category_name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    variant = scrapy.Field(serializer=dict, output_processor=TakeFirst())


class RestaurantMenuDatatItem(scrapy.Item):
    name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    min_choice = scrapy.Field(serializer=str, output_processor=TakeFirst())
    max_choice = scrapy.Field(serializer=str, output_processor=TakeFirst())
    

class RestaurantVariantItem(RestaurantMenuDatatItem):
    variants_values = scrapy.Field(serializer=dict, output_processor=TakeFirst())


class RestaurantOptionItem(RestaurantMenuDatatItem):
    options_values = scrapy.Field(serializer=list)


class RestaurantOptionValueItem(scrapy.Item):
    name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    price = scrapy.Field(serializer=str, output_processor=TakeFirst())
    old_price = scrapy.Field(serializer=str, output_processor=TakeFirst())
    options = scrapy.Field(serializer=list)
