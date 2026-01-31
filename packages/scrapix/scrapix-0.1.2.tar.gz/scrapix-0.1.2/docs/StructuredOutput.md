# StructuredOutput

Structured output model for the response. This model is used to represent structured data extracted from the response.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**data** | [**Data1**](Data1.md) |  | 
**data_schema** | **Dict[str, object]** |  | [optional] 
**format** | [**StructuredOutputFormat**](StructuredOutputFormat.md) | Format of the structured output | [optional] 
**cost** | **float** | Cost incurred for generating the structured output | [optional] [default to 0.0]

## Example

```python
from scrapix.models.structured_output import StructuredOutput

# TODO update the JSON string below
json = "{}"
# create an instance of StructuredOutput from a JSON string
structured_output_instance = StructuredOutput.from_json(json)
# print the JSON string representation of the object
print(StructuredOutput.to_json())

# convert the object into a dict
structured_output_dict = structured_output_instance.to_dict()
# create an instance of StructuredOutput from a dict
structured_output_from_dict = StructuredOutput.from_dict(structured_output_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


