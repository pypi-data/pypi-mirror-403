# ScrapeInput


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
**output_format** | [**OutputFormat**](OutputFormat.md) | The format of the output | [optional] 
**structured_schema** | [**StructuredOutputSchema**](StructuredOutputSchema.md) |  | [optional] 
**summarize_schema** | [**SummarizeSchema**](SummarizeSchema.md) |  | [optional] 

## Example

```python
from scrapix.models.scrape_input import ScrapeInput

# TODO update the JSON string below
json = "{}"
# create an instance of ScrapeInput from a JSON string
scrape_input_instance = ScrapeInput.from_json(json)
# print the JSON string representation of the object
print(ScrapeInput.to_json())

# convert the object into a dict
scrape_input_dict = scrape_input_instance.to_dict()
# create an instance of ScrapeInput from a dict
scrape_input_from_dict = ScrapeInput.from_dict(scrape_input_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


