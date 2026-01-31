# ToolArgumentResponse

Response model for a tool argument with assigned ID.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | ID of the tool argument. | 
**name** | **str** | Name of the tool argument. | 
**type** | **str** | Type of the tool argument. | 

## Example

```python
from arthur_client.api_bindings.models.tool_argument_response import ToolArgumentResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ToolArgumentResponse from a JSON string
tool_argument_response_instance = ToolArgumentResponse.from_json(json)
# print the JSON string representation of the object
print(ToolArgumentResponse.to_json())

# convert the object into a dict
tool_argument_response_dict = tool_argument_response_instance.to_dict()
# create an instance of ToolArgumentResponse from a dict
tool_argument_response_from_dict = ToolArgumentResponse.from_dict(tool_argument_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


