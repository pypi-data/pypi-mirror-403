# AdNotificationSending


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**notification** | [**Notification**](Notification.md) |  | [optional] 
**ad** | [**Ad**](Ad.md) |  | [optional] 

## Example

```python
from gen.client.models.ad_notification_sending import AdNotificationSending

# TODO update the JSON string below
json = "{}"
# create an instance of AdNotificationSending from a JSON string
ad_notification_sending_instance = AdNotificationSending.from_json(json)
# print the JSON string representation of the object
print(AdNotificationSending.to_json())

# convert the object into a dict
ad_notification_sending_dict = ad_notification_sending_instance.to_dict()
# create an instance of AdNotificationSending from a dict
ad_notification_sending_from_dict = AdNotificationSending.from_dict(ad_notification_sending_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


