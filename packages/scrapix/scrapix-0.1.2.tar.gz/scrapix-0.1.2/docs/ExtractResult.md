# ExtractResult

Result of extracting structured data or summarization from a page. `/extract`

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Unique identifier for the scraping task | [optional] 
**url** | **str** | The URL that was scraped | 
**status_code** | **int** | HTTP status code of the response | 
**status** | **bool** | Whether the scraping was successful | 
**response_headers** | **Dict[str, str]** | HTTP headers of the response | 
**credits_used** | **float** | Credits used for the scraping task | [optional] [default to 0.0]
**query** | **str** | Query for Structured output / Summarize / Instruct | 
**result** | **str** | Result of the query | 
**final_html_page** | **str** |  | [optional] 
**cost** | **float** | Cost incurred for the extraction | [optional] [default to 0.0]
**agent_type** | **str** | Type of extraction agent used | 
**tokens_used** | **float** |  | [optional] 
**structured_output** | [**StructuredOutput**](StructuredOutput.md) |  | [optional] 

## Example

```python
from scrapix.models.extract_result import ExtractResult

# TODO update the JSON string below
json = "{}"
# create an instance of ExtractResult from a JSON string
extract_result_instance = ExtractResult.from_json(json)
# print the JSON string representation of the object
print(ExtractResult.to_json())

# convert the object into a dict
extract_result_dict = extract_result_instance.to_dict()
# create an instance of ExtractResult from a dict
extract_result_from_dict = ExtractResult.from_dict(extract_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


