# gen.client.ManageProductImageApi

All URIs are relative to *https://www.lcdp.ovh/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_product_image**](ManageProductImageApi.md#create_product_image) | **POST** /products/{productId}/images | Upload one or more images
[**delete_product_image**](ManageProductImageApi.md#delete_product_image) | **DELETE** /products/{productId}/images/{imageId} | Remove product&#39;s image


# **create_product_image**
> create_product_image(product_id, images=images)

Upload one or more images

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
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
    api_instance = gen.client.ManageProductImageApi(api_client)
    product_id = 56 # int | The id of the product concerned by the request
    images = None # List[bytearray] | File to upload related to image type (Max 10 Mo) (optional)

    try:
        # Upload one or more images
        api_instance.create_product_image(product_id, images=images)
    except Exception as e:
        print("Exception when calling ManageProductImageApi->create_product_image: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **product_id** | **int**| The id of the product concerned by the request | 
 **images** | **List[bytearray]**| File to upload related to image type (Max 10 Mo) | [optional] 

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | successful operation |  -  |
**404** | No product found |  -  |
**403** | Bad request |  -  |
**413** | Image too large maximum allowed is 10 MB |  -  |
**415** | Wrong media type |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_product_image**
> delete_product_image(product_id, image_id)

Remove product's image

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
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
    api_instance = gen.client.ManageProductImageApi(api_client)
    product_id = 56 # int | The id of the product concerned by the request
    image_id = 56 # int | The id of the product image concerned by the request

    try:
        # Remove product's image
        api_instance.delete_product_image(product_id, image_id)
    except Exception as e:
        print("Exception when calling ManageProductImageApi->delete_product_image: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **product_id** | **int**| The id of the product concerned by the request | 
 **image_id** | **int**| The id of the product image concerned by the request | 

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
**204** | successful operation |  -  |
**404** | No product found |  -  |
**403** | Access denied |  -  |
**4XX** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

