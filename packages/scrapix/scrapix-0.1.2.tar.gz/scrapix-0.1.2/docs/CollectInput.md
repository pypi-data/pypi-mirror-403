# CollectInput

Input schema for collecting URLs from a page. `/collect`

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
**urls_limit** | **int** | Maximum number of URLs to collect | [optional] [default to 1000]
**exclude_paths** | **str** |  | [optional] 
**include_paths** | **str** |  | [optional] 
**query** | **str** |  | [optional] 
**include_sitemap_urls** | **bool** | Include URLs from SiteMap | [optional] [default to False]
**output_format** | [**StructuredOutputFormat**](StructuredOutputFormat.md) | The format of the output | [optional] 

## Example

```python
from scrapix.models.collect_input import CollectInput

# TODO update the JSON string below
json = "{}"
# create an instance of CollectInput from a JSON string
collect_input_instance = CollectInput.from_json(json)
# print the JSON string representation of the object
print(CollectInput.to_json())

# convert the object into a dict
collect_input_dict = collect_input_instance.to_dict()
# create an instance of CollectInput from a dict
collect_input_from_dict = CollectInput.from_dict(collect_input_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


