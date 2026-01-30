# gen.client.DefaultApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_mode**](DefaultApi.md#get_mode) | **GET** /modes | 


# **get_mode**
> AnyMode get_mode()



### Example


```python
import gen.client
from gen.client.models.any_mode import AnyMode
from gen.client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = gen.client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with gen.client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = gen.client.DefaultApi(api_client)

    try:
        api_response = api_instance.get_mode()
        print("The response of DefaultApi->get_mode:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_mode: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**AnyMode**](AnyMode.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

