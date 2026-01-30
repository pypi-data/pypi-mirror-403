# gen.client.ManageProductProscriptionApi

All URIs are relative to *https://www.lcdp.ovh/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_product_proscription**](ManageProductProscriptionApi.md#create_product_proscription) | **POST** /products/{productId}/proscriptions | Create a product proscription
[**delete_product_proscription**](ManageProductProscriptionApi.md#delete_product_proscription) | **DELETE** /products/{productId}/proscriptions/{proscriptionId} | Delete this product proscription


# **create_product_proscription**
> ProductProscription create_product_proscription(product_id, product_proscription_creation_parameters=product_proscription_creation_parameters)

Create a product proscription

**! WARNING !** this method can change the status of one or more sales-offers 

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.models.product_proscription import ProductProscription
from gen.client.models.product_proscription_creation_parameters import ProductProscriptionCreationParameters
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
    api_instance = gen.client.ManageProductProscriptionApi(api_client)
    product_id = 56 # int | The id of the product concerned by the request
    product_proscription_creation_parameters = gen.client.ProductProscriptionCreationParameters() # ProductProscriptionCreationParameters |  (optional)

    try:
        # Create a product proscription
        api_response = api_instance.create_product_proscription(product_id, product_proscription_creation_parameters=product_proscription_creation_parameters)
        print("The response of ManageProductProscriptionApi->create_product_proscription:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ManageProductProscriptionApi->create_product_proscription: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **product_id** | **int**| The id of the product concerned by the request | 
 **product_proscription_creation_parameters** | [**ProductProscriptionCreationParameters**](ProductProscriptionCreationParameters.md)|  | [optional] 

### Return type

[**ProductProscription**](ProductProscription.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**400** | Bad Request |  -  |
**403** | Access denied |  -  |
**404** | Product or Batch not found |  -  |
**409** | Proscription already exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_product_proscription**
> delete_product_proscription(product_id, proscription_id)

Delete this product proscription

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
    api_instance = gen.client.ManageProductProscriptionApi(api_client)
    product_id = 56 # int | The id of the product concerned by the request
    proscription_id = 56 # int | The id of the product proscription

    try:
        # Delete this product proscription
        api_instance.delete_product_proscription(product_id, proscription_id)
    except Exception as e:
        print("Exception when calling ManageProductProscriptionApi->delete_product_proscription: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **product_id** | **int**| The id of the product concerned by the request | 
 **proscription_id** | **int**| The id of the product proscription | 

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | successful operation |  -  |
**400** | Bad Request |  -  |
**403** | Access denied |  -  |
**404** | Product or Proscription Id not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

