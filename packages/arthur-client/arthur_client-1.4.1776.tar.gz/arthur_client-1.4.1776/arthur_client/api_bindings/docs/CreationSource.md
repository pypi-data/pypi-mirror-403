# CreationSource

Source information for how an unregistered agent was created.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**task_id** | **str** |  | [optional] 
**top_level_span_name** | **str** |  | [optional] 

## Example

```python
from arthur_client.api_bindings.models.creation_source import CreationSource

# TODO update the JSON string below
json = "{}"
# create an instance of CreationSource from a JSON string
creation_source_instance = CreationSource.from_json(json)
# print the JSON string representation of the object
print(CreationSource.to_json())

# convert the object into a dict
creation_source_dict = creation_source_instance.to_dict()
# create an instance of CreationSource from a dict
creation_source_from_dict = CreationSource.from_dict(creation_source_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


