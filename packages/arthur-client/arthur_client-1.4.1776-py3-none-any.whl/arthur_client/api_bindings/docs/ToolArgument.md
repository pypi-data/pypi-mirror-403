# ToolArgument

Argument definition for a tool.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Name of the tool argument. | 
**type** | **str** | Type of the tool argument. | 

## Example

```python
from arthur_client.api_bindings.models.tool_argument import ToolArgument

# TODO update the JSON string below
json = "{}"
# create an instance of ToolArgument from a JSON string
tool_argument_instance = ToolArgument.from_json(json)
# print the JSON string representation of the object
print(ToolArgument.to_json())

# convert the object into a dict
tool_argument_dict = tool_argument_instance.to_dict()
# create an instance of ToolArgument from a dict
tool_argument_from_dict = ToolArgument.from_dict(tool_argument_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


