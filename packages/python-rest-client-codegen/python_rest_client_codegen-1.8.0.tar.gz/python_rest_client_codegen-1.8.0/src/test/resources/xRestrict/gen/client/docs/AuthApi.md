# gen.client.AuthApi

All URIs are relative to *https://lecomptoirdespharmacies.fr/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**delete_route**](AuthApi.md#delete_route) | **DELETE** /route | Delete route
[**get_route**](AuthApi.md#get_route) | **GET** /route | Get route
[**post_route**](AuthApi.md#post_route) | **POST** /route | Create route


# **delete_route**
> delete_route()

Delete route



### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://lecomptoirdespharmacies.fr/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = gen.client.Configuration(
    host = "https://lecomptoirdespharmacies.fr/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = gen.client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with gen.client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = gen.client.AuthApi(api_client)

    try:
        # Delete route
        api_instance.delete_route()
    except Exception as e:
        print("Exception when calling AuthApi->delete_route: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**400** | Invalid ID supplied |  -  |
**404** | User not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_route**
> str get_route()

Get route



### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://lecomptoirdespharmacies.fr/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = gen.client.Configuration(
    host = "https://lecomptoirdespharmacies.fr/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = gen.client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with gen.client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = gen.client.AuthApi(api_client)

    try:
        # Get route
        api_response = api_instance.get_route()
        print("The response of AuthApi->get_route:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AuthApi->get_route: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

**str**

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Session id created |  * authorization - Session token to use for future call <br>  |
**405** | Invalid input |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_route**
> str post_route()

Create route



### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://lecomptoirdespharmacies.fr/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = gen.client.Configuration(
    host = "https://lecomptoirdespharmacies.fr/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = gen.client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with gen.client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = gen.client.AuthApi(api_client)

    try:
        # Create route
        api_response = api_instance.post_route()
        print("The response of AuthApi->post_route:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AuthApi->post_route: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

**str**

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Session id created |  * authorization - Session token to use for future call <br>  |
**405** | Invalid input |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

