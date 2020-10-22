import scrapy 
import csv
import json

class lowesSpider(scrapy.Spider):
    name = 'lowesSpider'
    start_urls = [
        'https://www.lowes.com/c/Refrigerators-Appliances'
    ]

    handle_httpstatus_list = [403]

    with open('Result.csv', "w") as file:
            writer = csv.writer(file, delimiter =';')
            writer.writerow(['SKU','Brand','Title','Rating Value','Review Count','Price','Availability','Item','Model','URL Image','URL'])

    def parse(self,response):
        links = response.xpath('//section[@id="mainContent"]/div[6]/div[1]//a/@href').getall()
        for link in links:
            try:
                yield scrapy.Request(
                    response.urljoin(link),
                    callback=self.parse_category,
                )   
            except:
                print("PARSE ERROR")

    def parse_category(self, response):
        json_data = response.xpath('//script[contains(text(), "__PRELOADED_STATE__")]/text()').extract_first()
        dict_data = json.loads(json_data.split('window.__PRELOADED_STATE__ =')[-1])
        refrigerators = dict_data['itemList']

        number_items = int(response.xpath('//*[@id="mainContent"]/div/div[2]/div[1]/div/text()').get().split()[0])
        pagination = int(number_items/36)

        for refrigerator in refrigerators:
            try:
                yield scrapy.Request(
                    response.urljoin(refrigerator['product']['pdURL']),
                    callback=self.parse_new,
                )

                if (pagination>0):
                    for i in range(36,(pagination*36+1),36):
                        try:
                            yield scrapy.Request(
                                response.urljoin(response.url + '?offset={}'.format(i)),
                                callback=self.parse_category_pagination,
                            )
                        except:
                            print("PARSE_CATEGORY(2) ERROR")

            except:
                print("PARSE_CATEGORY ERROR")

    def parse_category_pagination(self, response):
        json_data = response.xpath('//script[contains(text(), "__PRELOADED_STATE__")]/text()').extract_first()
        dict_data = json.loads(json_data.split('window.__PRELOADED_STATE__ =')[-1])
        refrigerators = dict_data['itemList']

        for refrigerator in refrigerators:
            try:
                yield scrapy.Request(
                    response.urljoin(refrigerator['product']['pdURL']),
                    callback=self.parse_new,
                )
            except:
                print("PARSE_CATEGORY_PAGINATION ERROR")

    def parse_new(self, response):
        json_item_data = json.loads(response.xpath('//script[@type="application/ld+json"]//text()').extract_first())
        
        title = json_item_data[2]['name'] 
        item = int(response.xpath('//*[@id="main"]/div/div[6]/div[1]/div[2]/div/span[1]/text()[2]').getall()[0])
        SKU = json_item_data[2]['offers']['sku']
        model = response.xpath('//*[@id="main"]/div/div[6]/div[1]/div[2]/div/span[2]/text()[2]').getall()[0]
        URL = response.url
        img = json_item_data[2]['offers']['image']
        brand = json_item_data[2]['brand']['name']
        ratingValue = float(response.xpath('//*[@id="main"]/div/div[6]/div[1]/div[1]//div/div/div/div/@aria-label').getall()[0].split()[0])
        reviewCount = float(response.xpath('//*[@id="main"]/div/div[6]/div[1]/div[1]//div/div/div/div/@aria-label').getall()[0].split()[6])   
        availability = json_item_data[2]['offers']['availability'][18:]

        if (json_item_data[2]['offers']['price']):
            price = json_item_data[2]['offers']['price']

        elif (response.xpath('//*[@id="atc"]//@data-productprice').getall()):
            price = float(response.xpath('//*[@id="atc"]//@data-productprice').getall())

        else:
            price = 'null'
            
        with open('Result.csv', "a") as file:
            writer = csv.writer(file, delimiter =';')
            writer.writerow([SKU,brand,title,ratingValue,reviewCount,price,availability,item,model,img,URL])

        yield{
          'SKU': SKU,
          'brand': brand,
          'title': title,
          'ratingValue': ratingValue,
          'reviewCount': reviewCount,
          'price': price,
          'availability': availability,
          'item': item,
          'model': model,
          'img': img,
          'URL':URL
        }