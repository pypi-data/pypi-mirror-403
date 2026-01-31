# ToolResponse

Response model for a tool with assigned ID.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | ID of the tool. | 
**name** | **str** | Name of the tool. | 
**arguments** | [**List[ToolArgumentResponse]**](ToolArgumentResponse.md) | List of arguments for this tool. | [optional] 

## Example

```python
from arthur_client.api_bindings.models.tool_response import ToolResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ToolResponse from a JSON string
tool_response_instance = ToolResponse.from_json(json)
# print the JSON string representation of the object
print(ToolResponse.to_json())

# convert the object into a dict
tool_response_dict = tool_response_instance.to_dict()
# create an instance of ToolResponse from a dict
tool_response_from_dict = ToolResponse.from_dict(tool_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


