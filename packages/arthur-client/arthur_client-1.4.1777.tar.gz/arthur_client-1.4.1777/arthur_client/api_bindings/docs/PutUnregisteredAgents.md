# PutUnregisteredAgents

Request body for creating or updating unregistered agents.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**unregistered_agents** | [**List[UnregisteredAgent]**](UnregisteredAgent.md) | List of unregistered agents to create or update. | 

## Example

```python
from arthur_client.api_bindings.models.put_unregistered_agents import PutUnregisteredAgents

# TODO update the JSON string below
json = "{}"
# create an instance of PutUnregisteredAgents from a JSON string
put_unregistered_agents_instance = PutUnregisteredAgents.from_json(json)
# print the JSON string representation of the object
print(PutUnregisteredAgents.to_json())

# convert the object into a dict
put_unregistered_agents_dict = put_unregistered_agents_instance.to_dict()
# create an instance of PutUnregisteredAgents from a dict
put_unregistered_agents_from_dict = PutUnregisteredAgents.from_dict(put_unregistered_agents_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


