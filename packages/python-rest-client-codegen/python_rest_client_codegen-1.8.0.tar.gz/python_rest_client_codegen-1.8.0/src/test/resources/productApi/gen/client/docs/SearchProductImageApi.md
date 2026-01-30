# gen.client.SearchProductImageApi

All URIs are relative to *https://www.lcdp.ovh/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_product_image**](SearchProductImageApi.md#get_product_image) | **GET** /products/{productId}/images/{imageId} | Return product&#39;s images
[**get_product_images**](SearchProductImageApi.md#get_product_images) | **GET** /products/{productId}/images | Return product&#39;s images


# **get_product_image**
> Image get_product_image(product_id, image_id)

Return product's images

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.models.image import Image
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
    api_instance = gen.client.SearchProductImageApi(api_client)
    product_id = 56 # int | The id of the product concerned by the request
    image_id = 56 # int | The id of the product image concerned by the request

    try:
        # Return product's images
        api_response = api_instance.get_product_image(product_id, image_id)
        print("The response of SearchProductImageApi->get_product_image:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchProductImageApi->get_product_image: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **product_id** | **int**| The id of the product concerned by the request | 
 **image_id** | **int**| The id of the product image concerned by the request | 

### Return type

[**Image**](Image.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**403** | Access denied |  -  |
**404** | Product not found |  -  |
**4XX** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_product_images**
> List[Image] get_product_images(product_id)

Return product's images

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.models.image import Image
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
    api_instance = gen.client.SearchProductImageApi(api_client)
    product_id = 56 # int | The id of the product concerned by the request

    try:
        # Return product's images
        api_response = api_instance.get_product_images(product_id)
        print("The response of SearchProductImageApi->get_product_images:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchProductImageApi->get_product_images: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **product_id** | **int**| The id of the product concerned by the request | 

### Return type

[**List[Image]**](Image.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**403** | Access denied |  -  |
**404** | Product not found |  -  |
**4XX** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

