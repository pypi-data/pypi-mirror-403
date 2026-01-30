# gen.client.AuthApi

All URIs are relative to *https://lecomptoirdespharmacies.fr/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**login**](AuthApi.md#login) | **POST** /session | Create a new session
[**logout**](AuthApi.md#logout) | **DELETE** /session/{sessionId} | Delete an existing session


# **login**
> str login(credential)

Create a new session



### Example


```python
import gen.client
from gen.client.models.credential import Credential
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
    credential = gen.client.Credential() # Credential | Credentials to use in order to create the session

    try:
        # Create a new session
        api_response = api_instance.login(credential)
        print("The response of AuthApi->login:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AuthApi->login: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **credential** | [**Credential**](Credential.md)| Credentials to use in order to create the session | 

### Return type

**str**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Session id created |  * authorization - Session token to use for future call <br>  |
**405** | Invalid input |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **logout**
> logout(session_id, authorization=authorization)

Delete an existing session



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
    api_instance = gen.client.AuthApi(api_client)
    session_id = 56 # int | Session id to delete
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Delete an existing session
        api_instance.logout(session_id, authorization=authorization)
    except Exception as e:
        print("Exception when calling AuthApi->logout: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **session_id** | **int**| Session id to delete | 
 **authorization** | **str**|  | [optional] 

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
**400** | Invalid ID supplied |  -  |
**404** | User not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

