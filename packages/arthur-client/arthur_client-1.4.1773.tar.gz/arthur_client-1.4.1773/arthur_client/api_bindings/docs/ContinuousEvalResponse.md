# ContinuousEvalResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | ID of the transform. | 
**name** | **str** | Name of the continuous eval. | 
**description** | **str** |  | [optional] 
**task_id** | **str** | ID of the parent task. | 
**llm_eval_name** | **str** | Name of the llm eval. | 
**llm_eval_version** | **int** | Version of the llm eval. | 
**transform_id** | **str** | ID of the transform. | 
**transform_variable_mapping** | [**List[ContinuousEvalTransformVariableMappingResponse]**](ContinuousEvalTransformVariableMappingResponse.md) | Mapping of transform variables to eval variables. | [optional] 
**enabled** | **bool** | Whether the continuous eval is enabled. | [optional] [default to True]
**created_at** | **datetime** | Timestamp representing the time the transform was added to the llm eval. | 
**updated_at** | **datetime** | Timestamp representing the time the continuous eval was last updated. | 

## Example

```python
from arthur_client.api_bindings.models.continuous_eval_response import ContinuousEvalResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ContinuousEvalResponse from a JSON string
continuous_eval_response_instance = ContinuousEvalResponse.from_json(json)
# print the JSON string representation of the object
print(ContinuousEvalResponse.to_json())

# convert the object into a dict
continuous_eval_response_dict = continuous_eval_response_instance.to_dict()
# create an instance of ContinuousEvalResponse from a dict
continuous_eval_response_from_dict = ContinuousEvalResponse.from_dict(continuous_eval_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


