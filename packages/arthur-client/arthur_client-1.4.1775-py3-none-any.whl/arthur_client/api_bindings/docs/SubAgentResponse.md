# SubAgentResponse

Response model for a sub-agent with assigned ID.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | ID of the sub-agent. | 
**name** | **str** | Name of the sub-agent. | 

## Example

```python
from arthur_client.api_bindings.models.sub_agent_response import SubAgentResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SubAgentResponse from a JSON string
sub_agent_response_instance = SubAgentResponse.from_json(json)
# print the JSON string representation of the object
print(SubAgentResponse.to_json())

# convert the object into a dict
sub_agent_response_dict = sub_agent_response_instance.to_dict()
# create an instance of SubAgentResponse from a dict
sub_agent_response_from_dict = SubAgentResponse.from_dict(sub_agent_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


