# CrawlInput

Input schema for crawling URLs from a page. `/crawl`

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Unique identifier for the scraping task | [optional] 
**url** | **str** | Input URL | 
**timeout** | **int** | Timeout in seconds for the request | [optional] [default to 40]
**max_retries** | **int** | Max retries before failing | [optional] [default to 5]
**max_cost** | **float** |  | [optional] 
**render** | **bool** | Render the Page | [optional] [default to False]
**premium_proxies** | **bool** | Use premium proxy | [optional] [default to False]
**use_captcha_solver** | **bool** | Use captcha solvers to avoid blocking | [optional] [default to False]
**use_cache** | **bool** | If enabled will serve from fresh crawl | [optional] [default to True]
**urls_limit** | **int** | Maximum number of URLs to collect | [optional] [default to 5]
**output_format** | [**OutputFormat**](OutputFormat.md) | The format of the output | [optional] 
**include_sitemap_urls** | **bool** | Include URLs from SiteMap | [optional] [default to False]
**exclude_paths** | **str** |  | [optional] 
**include_paths** | **str** |  | [optional] 

## Example

```python
from scrapix.models.crawl_input import CrawlInput

# TODO update the JSON string below
json = "{}"
# create an instance of CrawlInput from a JSON string
crawl_input_instance = CrawlInput.from_json(json)
# print the JSON string representation of the object
print(CrawlInput.to_json())

# convert the object into a dict
crawl_input_dict = crawl_input_instance.to_dict()
# create an instance of CrawlInput from a dict
crawl_input_from_dict = CrawlInput.from_dict(crawl_input_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


