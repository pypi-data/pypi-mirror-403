# StructuredOutputSchema


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**format** | [**StructuredOutputFormat**](StructuredOutputFormat.md) | The format of the structured output schema | [optional] 
**var_schema** | **Dict[str, object]** |  | [optional] 
**query** | **str** | A user query on what to extract from the structured output | 

## Example

```python
from scrapix.models.structured_output_schema import StructuredOutputSchema

# TODO update the JSON string below
json = "{}"
# create an instance of StructuredOutputSchema from a JSON string
structured_output_schema_instance = StructuredOutputSchema.from_json(json)
# print the JSON string representation of the object
print(StructuredOutputSchema.to_json())

# convert the object into a dict
structured_output_schema_dict = structured_output_schema_instance.to_dict()
# create an instance of StructuredOutputSchema from a dict
structured_output_schema_from_dict = StructuredOutputSchema.from_dict(structured_output_schema_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


