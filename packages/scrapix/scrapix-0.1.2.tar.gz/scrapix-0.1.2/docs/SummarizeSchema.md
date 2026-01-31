# SummarizeSchema


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**query** | **str** |  | [optional] 

## Example

```python
from scrapix.models.summarize_schema import SummarizeSchema

# TODO update the JSON string below
json = "{}"
# create an instance of SummarizeSchema from a JSON string
summarize_schema_instance = SummarizeSchema.from_json(json)
# print the JSON string representation of the object
print(SummarizeSchema.to_json())

# convert the object into a dict
summarize_schema_dict = summarize_schema_instance.to_dict()
# create an instance of SummarizeSchema from a dict
summarize_schema_from_dict = SummarizeSchema.from_dict(summarize_schema_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


