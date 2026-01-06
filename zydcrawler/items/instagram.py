from itemloaders.processors import TakeFirst
import scrapy


class InstagramItem(scrapy.Item):
    name_en = scrapy.Field(serializer=str, output_processor=TakeFirst())
    name_ar = scrapy.Field(serializer=str, output_processor=TakeFirst())
    description = scrapy.Field(serializer=str, output_processor=TakeFirst())
    logo = scrapy.Field(serializer=str, output_processor=TakeFirst())
    url = scrapy.Field(serializer=str, output_processor=TakeFirst())
    file_name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    username = scrapy.Field(serializer=str, output_processor=TakeFirst())
    expiration_date = scrapy.Field(serializer=str, output_processor=TakeFirst())
    followers = scrapy.Field(serializer=str, output_processor=TakeFirst())
    type = scrapy.Field(serializer=str, output_processor=TakeFirst())
    posts = scrapy.Field(serializer=str, output_processor=TakeFirst())
    country = scrapy.Field(serializer=str, output_processor=TakeFirst())
    active = scrapy.Field(serializer=bool, output_processor=TakeFirst())
    food_aggregaror = scrapy.Field(serializer=str, output_processor=TakeFirst())
    phone_numbers = scrapy.Field(serializer=str, output_processor=TakeFirst())
