# PatchUnregisteredAgent

Request body for partially updating an unregistered agent.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**first_detected** | **datetime** |  | [optional] 
**num_spans** | **int** |  | [optional] 
**model_id** | **str** |  | [optional] 
**tools** | [**List[Tool]**](Tool.md) |  | [optional] 
**sub_agents** | [**List[SubAgent]**](SubAgent.md) |  | [optional] 

## Example

```python
from arthur_client.api_bindings.models.patch_unregistered_agent import PatchUnregisteredAgent

# TODO update the JSON string below
json = "{}"
# create an instance of PatchUnregisteredAgent from a JSON string
patch_unregistered_agent_instance = PatchUnregisteredAgent.from_json(json)
# print the JSON string representation of the object
print(PatchUnregisteredAgent.to_json())

# convert the object into a dict
patch_unregistered_agent_dict = patch_unregistered_agent_instance.to_dict()
# create an instance of PatchUnregisteredAgent from a dict
patch_unregistered_agent_from_dict = PatchUnregisteredAgent.from_dict(patch_unregistered_agent_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


