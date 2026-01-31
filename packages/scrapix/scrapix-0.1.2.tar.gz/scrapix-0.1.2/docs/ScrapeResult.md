# ScrapeResult

Result of a single URL scrape. `/scrape`

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Unique identifier for the scraping task | [optional] 
**url** | **str** | The URL that was scraped | 
**status_code** | **int** | HTTP status code of the response | 
**status** | **bool** | Whether the scraping was successful | 
**response_headers** | **Dict[str, str]** | HTTP headers of the response | 
**credits_used** | **float** | Credits used for the scraping task | [optional] [default to 0.0]
**data** | **Dict[str, str]** |  | 
**structured_output** | [**StructuredOutput**](StructuredOutput.md) |  | [optional] 
**summarized_data** | **Dict[str, object]** |  | [optional] 

## Example

```python
from scrapix.models.scrape_result import ScrapeResult

# TODO update the JSON string below
json = "{}"
# create an instance of ScrapeResult from a JSON string
scrape_result_instance = ScrapeResult.from_json(json)
# print the JSON string representation of the object
print(ScrapeResult.to_json())

# convert the object into a dict
scrape_result_dict = scrape_result_instance.to_dict()
# create an instance of ScrapeResult from a dict
scrape_result_from_dict = ScrapeResult.from_dict(scrape_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


