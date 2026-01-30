# gen.client.SearchProductMetadataApi

All URIs are relative to *https://www.lcdp.ovh/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_product_secondary_types**](SearchProductMetadataApi.md#get_product_secondary_types) | **GET** /products/secondary-types | Get product secondary types
[**get_product_types**](SearchProductMetadataApi.md#get_product_types) | **GET** /products/types | Get product types


# **get_product_secondary_types**
> List[ProductSecondaryType] get_product_secondary_types()

Get product secondary types

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.models.product_secondary_type import ProductSecondaryType
from gen.client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://www.lcdp.ovh/api/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = gen.client.Configuration(
    host = "https://www.lcdp.ovh/api/v1"
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
    api_instance = gen.client.SearchProductMetadataApi(api_client)

    try:
        # Get product secondary types
        api_response = api_instance.get_product_secondary_types()
        print("The response of SearchProductMetadataApi->get_product_secondary_types:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchProductMetadataApi->get_product_secondary_types: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[ProductSecondaryType]**](ProductSecondaryType.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Product&#39;s types found |  -  |
**403** | Access denied |  -  |
**4XX** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_product_types**
> List[ProductType] get_product_types()

Get product types

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.models.product_type import ProductType
from gen.client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://www.lcdp.ovh/api/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = gen.client.Configuration(
    host = "https://www.lcdp.ovh/api/v1"
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
    api_instance = gen.client.SearchProductMetadataApi(api_client)

    try:
        # Get product types
        api_response = api_instance.get_product_types()
        print("The response of SearchProductMetadataApi->get_product_types:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchProductMetadataApi->get_product_types: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[ProductType]**](ProductType.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Product&#39;s types found |  -  |
**403** | Access denied |  -  |
**4XX** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

