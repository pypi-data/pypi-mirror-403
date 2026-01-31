# AlertGroup


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**alert_rule_id** | **str** | The ID of the alert rule. | 
**alert_rule_name** | **str** | The name of the alert rule. | 
**count** | **int** | The number of alerts in this group. | 
**latest_timestamp** | **datetime** | The timestamp of the newest alert in this group. | 
**model_id** | **str** | The model ID associated with this alert rule. | 
**model_name** | **str** | The name of the model associated with this alert rule. | 
**bound** | [**AlertBound**](AlertBound.md) | The bound of the alert rule. | 
**alerts** | [**List[Alert]**](Alert.md) | The list of alerts in this group. | 

## Example

```python
from arthur_client.api_bindings.models.alert_group import AlertGroup

# TODO update the JSON string below
json = "{}"
# create an instance of AlertGroup from a JSON string
alert_group_instance = AlertGroup.from_json(json)
# print the JSON string representation of the object
print(AlertGroup.to_json())

# convert the object into a dict
alert_group_dict = alert_group_instance.to_dict()
# create an instance of AlertGroup from a dict
alert_group_from_dict = AlertGroup.from_dict(alert_group_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


