# CrawlResult

Result of crawling URLs from a page. `/crawl`

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Unique identifier for the scraping task | [optional] 
**url** | **str** | The URL that was scraped | 
**status_code** | **int** | HTTP status code of the response | 
**status** | **bool** | Whether the scraping was successful | 
**response_headers** | **Dict[str, str]** | HTTP headers of the response | 
**credits_used** | **float** | Credits used for the scraping task | [optional] [default to 0.0]
**responses** | [**List[ScrapeResult]**](ScrapeResult.md) | List of responses for each URL scraped | 

## Example

```python
from scrapix.models.crawl_result import CrawlResult

# TODO update the JSON string below
json = "{}"
# create an instance of CrawlResult from a JSON string
crawl_result_instance = CrawlResult.from_json(json)
# print the JSON string representation of the object
print(CrawlResult.to_json())

# convert the object into a dict
crawl_result_dict = crawl_result_instance.to_dict()
# create an instance of CrawlResult from a dict
crawl_result_from_dict = CrawlResult.from_dict(crawl_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


