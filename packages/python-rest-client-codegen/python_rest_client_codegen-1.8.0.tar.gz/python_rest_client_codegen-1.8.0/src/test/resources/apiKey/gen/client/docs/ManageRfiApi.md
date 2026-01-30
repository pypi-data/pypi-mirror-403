# gen.client.ManageRfiApi

All URIs are relative to *https://lecomptoirdespharmacies.fr/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_rfi**](ManageRfiApi.md#create_rfi) | **POST** /rfis | Contact form


# **create_rfi**
> create_rfi()

Contact form

### Example

* Api Key Authentication (apiKeyAuth):
* Api Key Authentication (captchaApiKey):
* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://lecomptoirdespharmacies.fr/api/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = gen.client.Configuration(
    host = "https://lecomptoirdespharmacies.fr/api/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: apiKeyAuth
configuration.api_key['apiKeyAuth'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['apiKeyAuth'] = 'Bearer'

# Configure API key authorization: captchaApiKey
configuration.api_key['captchaApiKey'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['captchaApiKey'] = 'Bearer'

# Configure Bearer authorization (JWT): bearerAuth
configuration = gen.client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with gen.client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = gen.client.ManageRfiApi(api_client)

    try:
        # Contact form
        api_instance.create_rfi()
    except Exception as e:
        print("Exception when calling ManageRfiApi->create_rfi: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

[apiKeyAuth](../README.md#apiKeyAuth), [captchaApiKey](../README.md#captchaApiKey), [bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Message sent |  -  |
**404** | Order not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

