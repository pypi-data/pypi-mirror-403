# CollectResult

Result of collecting URLs from a page. `/collect`

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Unique identifier for the scraping task | [optional] 
**url** | **str** | The URL that was scraped | 
**status_code** | **int** | HTTP status code of the response | 
**status** | **bool** | Whether the scraping was successful | 
**response_headers** | **Dict[str, str]** | HTTP headers of the response | 
**credits_used** | **float** | Credits used for the scraping task | [optional] [default to 0.0]
**links** | [**StructuredOutput**](StructuredOutput.md) | links extracted from the page | [optional] 

## Example

```python
from scrapix.models.collect_result import CollectResult

# TODO update the JSON string below
json = "{}"
# create an instance of CollectResult from a JSON string
collect_result_instance = CollectResult.from_json(json)
# print the JSON string representation of the object
print(CollectResult.to_json())

# convert the object into a dict
collect_result_dict = collect_result_instance.to_dict()
# create an instance of CollectResult from a dict
collect_result_from_dict = CollectResult.from_dict(collect_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


