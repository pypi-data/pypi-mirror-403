# ExtractInput

Input schema for extracting structured data or summarization from a page. `/extract`

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
**output_format** | [**StructuredOutputFormat**](StructuredOutputFormat.md) | The format of the output | [optional] 
**structured_schema** | [**StructuredOutputSchema**](StructuredOutputSchema.md) |  | [optional] 
**summarize_schema** | [**SummarizeSchema**](SummarizeSchema.md) |  | [optional] 
**query** | **str** | Query for Structured output / Summarize / Instruct | 

## Example

```python
from scrapix.models.extract_input import ExtractInput

# TODO update the JSON string below
json = "{}"
# create an instance of ExtractInput from a JSON string
extract_input_instance = ExtractInput.from_json(json)
# print the JSON string representation of the object
print(ExtractInput.to_json())

# convert the object into a dict
extract_input_dict = extract_input_instance.to_dict()
# create an instance of ExtractInput from a dict
extract_input_from_dict = ExtractInput.from_dict(extract_input_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


