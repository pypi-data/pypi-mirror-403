# ContinuousEvalTransformVariableMappingResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**transform_variable** | **str** | Name of the transform variable. | 
**eval_variable** | **str** | Name of the eval variable. | 

## Example

```python
from arthur_client.api_bindings.models.continuous_eval_transform_variable_mapping_response import ContinuousEvalTransformVariableMappingResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ContinuousEvalTransformVariableMappingResponse from a JSON string
continuous_eval_transform_variable_mapping_response_instance = ContinuousEvalTransformVariableMappingResponse.from_json(json)
# print the JSON string representation of the object
print(ContinuousEvalTransformVariableMappingResponse.to_json())

# convert the object into a dict
continuous_eval_transform_variable_mapping_response_dict = continuous_eval_transform_variable_mapping_response_instance.to_dict()
# create an instance of ContinuousEvalTransformVariableMappingResponse from a dict
continuous_eval_transform_variable_mapping_response_from_dict = ContinuousEvalTransformVariableMappingResponse.from_dict(continuous_eval_transform_variable_mapping_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


