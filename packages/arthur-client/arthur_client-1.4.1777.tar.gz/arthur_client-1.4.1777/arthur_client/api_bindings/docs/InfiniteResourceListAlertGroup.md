# InfiniteResourceListAlertGroup


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**records** | [**List[AlertGroup]**](AlertGroup.md) | List of records. | 
**pagination** | [**InfinitePagination**](InfinitePagination.md) | Pagination information. | 

## Example

```python
from arthur_client.api_bindings.models.infinite_resource_list_alert_group import InfiniteResourceListAlertGroup

# TODO update the JSON string below
json = "{}"
# create an instance of InfiniteResourceListAlertGroup from a JSON string
infinite_resource_list_alert_group_instance = InfiniteResourceListAlertGroup.from_json(json)
# print the JSON string representation of the object
print(InfiniteResourceListAlertGroup.to_json())

# convert the object into a dict
infinite_resource_list_alert_group_dict = infinite_resource_list_alert_group_instance.to_dict()
# create an instance of InfiniteResourceListAlertGroup from a dict
infinite_resource_list_alert_group_from_dict = InfiniteResourceListAlertGroup.from_dict(infinite_resource_list_alert_group_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


