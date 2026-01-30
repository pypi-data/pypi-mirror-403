# gen.client.AuthApi

All URIs are relative to *https://lecomptoirdespharmacies.fr/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**login**](AuthApi.md#login) | **POST** /token | Create a new session


# **login**
> login(any_authentication_credential)

Create a new session



### Example


```python
import gen.client
from gen.client.models.any_authentication_credential import AnyAuthenticationCredential
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
    any_authentication_credential = {"login":"example@example.fr","password":"mymagicpassword","grantType":"password"} # AnyAuthenticationCredential | Credentials to use in order to create the session

    try:
        # Create a new session
        api_instance.login(any_authentication_credential)
    except Exception as e:
        print("Exception when calling AuthApi->login: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **any_authentication_credential** | [**AnyAuthenticationCredential**](AnyAuthenticationCredential.md)| Credentials to use in order to create the session | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Session created |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

