# PutUnregisteredAgentsResponse

Response body for creating or updating unregistered agents.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**unregistered_agents** | [**List[UnregisteredAgentResponse]**](UnregisteredAgentResponse.md) | List of unregistered agents that were created or updated. | 

## Example

```python
from arthur_client.api_bindings.models.put_unregistered_agents_response import PutUnregisteredAgentsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of PutUnregisteredAgentsResponse from a JSON string
put_unregistered_agents_response_instance = PutUnregisteredAgentsResponse.from_json(json)
# print the JSON string representation of the object
print(PutUnregisteredAgentsResponse.to_json())

# convert the object into a dict
put_unregistered_agents_response_dict = put_unregistered_agents_response_instance.to_dict()
# create an instance of PutUnregisteredAgentsResponse from a dict
put_unregistered_agents_response_from_dict = PutUnregisteredAgentsResponse.from_dict(put_unregistered_agents_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


