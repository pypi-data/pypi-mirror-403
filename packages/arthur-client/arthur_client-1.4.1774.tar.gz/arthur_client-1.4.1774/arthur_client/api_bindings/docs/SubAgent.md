# SubAgent

Sub-agent definition.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Name of the sub-agent. | 

## Example

```python
from arthur_client.api_bindings.models.sub_agent import SubAgent

# TODO update the JSON string below
json = "{}"
# create an instance of SubAgent from a JSON string
sub_agent_instance = SubAgent.from_json(json)
# print the JSON string representation of the object
print(SubAgent.to_json())

# convert the object into a dict
sub_agent_dict = sub_agent_instance.to_dict()
# create an instance of SubAgent from a dict
sub_agent_from_dict = SubAgent.from_dict(sub_agent_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


