# gen.client.SearchUserApi

All URIs are relative to *https://lecomptoirdespharmacies.fr/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_user**](SearchUserApi.md#get_user) | **GET** /users/{userId} | Retrieve one user


# **get_user**
> get_user(user_id)

Retrieve one user



### Example


```python
import gen.client
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
    api_instance = gen.client.SearchUserApi(api_client)
    user_id = 56 # int | The id of the user concerned by the request

    try:
        # Retrieve one user
        api_instance.get_user(user_id)
    except Exception as e:
        print("Exception when calling SearchUserApi->get_user: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_id** | **int**| The id of the user concerned by the request | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**404** | User not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

