# UnregisteredAgentResponse

Response model for an unregistered agent with assigned ID.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**created_at** | **datetime** | Time of record creation. | 
**updated_at** | **datetime** | Time of last record update. | 
**id** | **str** | ID of the unregistered agent. | 
**name** | **str** | Name of the unregistered agent. | 
**creation_source** | [**CreationSource**](CreationSource.md) | Information about how this agent was created. | 
**first_detected** | **datetime** | Timestamp when this agent was first detected. | 
**num_spans** | **int** |  | [optional] 
**infrastructure** | [**Infrastructure**](Infrastructure.md) | Infrastructure where this agent is running. | 
**data_plane_id** | **str** | UUID of the data plane where this agent was detected. | 
**tools** | [**List[ToolResponse]**](ToolResponse.md) | List of tools used by this agent. | [optional] 
**sub_agents** | [**List[SubAgentResponse]**](SubAgentResponse.md) | List of sub-agents used by this agent. | [optional] 
**model_id** | **str** |  | [optional] 
**model_name** | **str** |  | [optional] 

## Example

```python
from arthur_client.api_bindings.models.unregistered_agent_response import UnregisteredAgentResponse

# TODO update the JSON string below
json = "{}"
# create an instance of UnregisteredAgentResponse from a JSON string
unregistered_agent_response_instance = UnregisteredAgentResponse.from_json(json)
# print the JSON string representation of the object
print(UnregisteredAgentResponse.to_json())

# convert the object into a dict
unregistered_agent_response_dict = unregistered_agent_response_instance.to_dict()
# create an instance of UnregisteredAgentResponse from a dict
unregistered_agent_response_from_dict = UnregisteredAgentResponse.from_dict(unregistered_agent_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


