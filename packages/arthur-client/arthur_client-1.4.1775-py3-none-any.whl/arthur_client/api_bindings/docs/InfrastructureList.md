# InfrastructureList

List of supported infrastructure values for engines.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**infrastructures** | [**List[Infrastructure]**](Infrastructure.md) | List of supported infrastructure values. | 

## Example

```python
from arthur_client.api_bindings.models.infrastructure_list import InfrastructureList

# TODO update the JSON string below
json = "{}"
# create an instance of InfrastructureList from a JSON string
infrastructure_list_instance = InfrastructureList.from_json(json)
# print the JSON string representation of the object
print(InfrastructureList.to_json())

# convert the object into a dict
infrastructure_list_dict = infrastructure_list_instance.to_dict()
# create an instance of InfrastructureList from a dict
infrastructure_list_from_dict = InfrastructureList.from_dict(infrastructure_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


