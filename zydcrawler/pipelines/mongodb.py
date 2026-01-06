from zydcrawler.mongodb import MongoDB


class MongoDBPipeline:
    
    def open_spider(self, spider):

        assert self.db_name is not None, "You should assgin `db_name` before use the database"

        mongodb = MongoDB(spider.settings['MONGO_URL'])
        self.client = mongodb.client
        self.db = self.client[self.db_name]
        spider.db = self.db
        spider.client = self.client
        
        self.handle_collections()
        
    def close_spider(self, spider):
        self.client.close()
    
    def handle_collections(self):
        ''' Not implemented '''

        raise NotImplementedError()
