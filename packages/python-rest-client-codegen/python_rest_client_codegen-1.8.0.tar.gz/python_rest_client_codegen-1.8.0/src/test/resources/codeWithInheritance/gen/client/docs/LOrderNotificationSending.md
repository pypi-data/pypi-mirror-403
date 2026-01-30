# LOrderNotificationSending


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**notification** | [**Notification**](Notification.md) |  | [optional] 
**ad** | [**LOrder**](LOrder.md) |  | [optional] 

## Example

```python
from gen.client.models.l_order_notification_sending import LOrderNotificationSending

# TODO update the JSON string below
json = "{}"
# create an instance of LOrderNotificationSending from a JSON string
l_order_notification_sending_instance = LOrderNotificationSending.from_json(json)
# print the JSON string representation of the object
print(LOrderNotificationSending.to_json())

# convert the object into a dict
l_order_notification_sending_dict = l_order_notification_sending_instance.to_dict()
# create an instance of LOrderNotificationSending from a dict
l_order_notification_sending_from_dict = LOrderNotificationSending.from_dict(l_order_notification_sending_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


