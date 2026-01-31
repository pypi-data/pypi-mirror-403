# UnregisteredAgent

An unregistered agent detected in the system.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Name of the unregistered agent. | 
**creation_source** | [**CreationSource**](CreationSource.md) | Information about how this agent was created. | 
**first_detected** | **datetime** | Timestamp when this agent was first detected. | 
**num_spans** | **int** |  | [optional] 
**infrastructure** | [**Infrastructure**](Infrastructure.md) | Infrastructure where this agent is running. | 
**data_plane_id** | **str** | UUID of the data plane where this agent was detected. | 
**tools** | [**List[Tool]**](Tool.md) | List of tools used by this agent. | [optional] 
**sub_agents** | [**List[SubAgent]**](SubAgent.md) | List of sub-agents used by this agent. | [optional] 

## Example

```python
from arthur_client.api_bindings.models.unregistered_agent import UnregisteredAgent

# TODO update the JSON string below
json = "{}"
# create an instance of UnregisteredAgent from a JSON string
unregistered_agent_instance = UnregisteredAgent.from_json(json)
# print the JSON string representation of the object
print(UnregisteredAgent.to_json())

# convert the object into a dict
unregistered_agent_dict = unregistered_agent_instance.to_dict()
# create an instance of UnregisteredAgent from a dict
unregistered_agent_from_dict = UnregisteredAgent.from_dict(unregistered_agent_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


