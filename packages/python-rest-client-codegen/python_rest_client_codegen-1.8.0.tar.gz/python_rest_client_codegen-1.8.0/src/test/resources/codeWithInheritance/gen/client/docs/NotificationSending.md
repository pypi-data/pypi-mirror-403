# NotificationSending


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**notification** | [**Notification**](Notification.md) |  | [optional] 

## Example

```python
from gen.client.models.notification_sending import NotificationSending

# TODO update the JSON string below
json = "{}"
# create an instance of NotificationSending from a JSON string
notification_sending_instance = NotificationSending.from_json(json)
# print the JSON string representation of the object
print(NotificationSending.to_json())

# convert the object into a dict
notification_sending_dict = notification_sending_instance.to_dict()
# create an instance of NotificationSending from a dict
notification_sending_from_dict = NotificationSending.from_dict(notification_sending_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


