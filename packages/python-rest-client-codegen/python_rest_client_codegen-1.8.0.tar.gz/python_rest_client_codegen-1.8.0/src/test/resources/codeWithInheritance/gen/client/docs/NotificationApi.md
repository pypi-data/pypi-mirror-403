# gen.client.NotificationApi

All URIs are relative to *https://lecomptoirdespharmacies.fr/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_notifications**](NotificationApi.md#get_notifications) | **GET** /notification | Request all notifications


# **get_notifications**
> List[NotificationSending] get_notifications(authorization=authorization, number=number, page=page)

Request all notifications



### Example


```python
import gen.client
from gen.client.models.notification_sending import NotificationSending
from gen.client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://lecomptoirdespharmacies.fr/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = gen.client.Configuration(
    host = "https://lecomptoirdespharmacies.fr/v1"
)


# Enter a context with an instance of the API client
with gen.client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = gen.client.NotificationApi(api_client)
    authorization = 'authorization_example' # str |  (optional)
    number = 56 # int | Number of notifications (optional)
    page = 56 # int | Page number to search for (optional)

    try:
        # Request all notifications
        api_response = api_instance.get_notifications(authorization=authorization, number=number, page=page)
        print("The response of NotificationApi->get_notifications:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling NotificationApi->get_notifications: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **authorization** | **str**|  | [optional] 
 **number** | **int**| Number of notifications | [optional] 
 **page** | **int**| Page number to search for | [optional] 

### Return type

[**List[NotificationSending]**](NotificationSending.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**400** | Invalid ID supplied |  -  |
**403** | Access denied |  -  |
**405** | User not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

