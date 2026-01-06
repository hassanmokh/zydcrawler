from itemloaders.processors import TakeFirst
import scrapy


class ZydaClientsItem(scrapy.Item):
    followers = scrapy.Field(serializer=str, output_processor=TakeFirst())
    store_id = scrapy.Field(serializer=str, output_processor=TakeFirst())
    posts = scrapy.Field(serializer=str, output_processor=TakeFirst())
    name = scrapy.Field(serializer=str, output_processor=TakeFirst())
    bio = scrapy.Field(serializer=str, output_processor=TakeFirst())
    bio_url = scrapy.Field(serializer=str, output_processor=TakeFirst())
