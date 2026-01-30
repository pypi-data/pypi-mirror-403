# gen.client.AuthApi

All URIs are relative to *https://lecomptoirdespharmacies.fr/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_sessions**](AuthApi.md#get_sessions) | **GET** /sessions | 


# **get_sessions**
> List[Session] get_sessions()



### Example


```python
import gen.client
from gen.client.models.session import Session
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
    api_instance = gen.client.AuthApi(api_client)

    try:
        api_response = api_instance.get_sessions()
        print("The response of AuthApi->get_sessions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AuthApi->get_sessions: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[Session]**](Session.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Session |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

