# gen.client.ManageProductApi

All URIs are relative to *https://www.lcdp.ovh/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_product**](ManageProductApi.md#create_product) | **POST** /products | Create product from product form
[**set_product_vidal_package**](ManageProductApi.md#set_product_vidal_package) | **PUT** /products/{productId}/vidal-package | Synchronize product against vidal id
[**update_product**](ManageProductApi.md#update_product) | **PATCH** /products/{productId} | Update product from product form


# **create_product**
> Product create_product(product_creation_or_update_parameters)

Create product from product form

Required parameters for creation of vidal synchronized product :  - vidalPackageId  Required parameters for creation of product from scratch :  - name  - barcodes  - dci  - laboratoryId  - unitWeight  - vatId  - unitPrice  - typeId 

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.models.product import Product
from gen.client.models.product_creation_or_update_parameters import ProductCreationOrUpdateParameters
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
    api_instance = gen.client.ManageProductApi(api_client)
    product_creation_or_update_parameters = gen.client.ProductCreationOrUpdateParameters() # ProductCreationOrUpdateParameters | Product to add

    try:
        # Create product from product form
        api_response = api_instance.create_product(product_creation_or_update_parameters)
        print("The response of ManageProductApi->create_product:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ManageProductApi->create_product: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **product_creation_or_update_parameters** | [**ProductCreationOrUpdateParameters**](ProductCreationOrUpdateParameters.md)| Product to add | 

### Return type

[**Product**](Product.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**403** | Access denied |  -  |
**409** | Product already exist |  -  |
**4XX** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_product_vidal_package**
> set_product_vidal_package(product_id, update_vidal_package_parameters=update_vidal_package_parameters)

Synchronize product against vidal id

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.models.update_vidal_package_parameters import UpdateVidalPackageParameters
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
    api_instance = gen.client.ManageProductApi(api_client)
    product_id = 56 # int | The id of the product concerned by the request
    update_vidal_package_parameters = gen.client.UpdateVidalPackageParameters() # UpdateVidalPackageParameters |  (optional)

    try:
        # Synchronize product against vidal id
        api_instance.set_product_vidal_package(product_id, update_vidal_package_parameters=update_vidal_package_parameters)
    except Exception as e:
        print("Exception when calling ManageProductApi->set_product_vidal_package: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **product_id** | **int**| The id of the product concerned by the request | 
 **update_vidal_package_parameters** | [**UpdateVidalPackageParameters**](UpdateVidalPackageParameters.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | successful operation |  -  |
**403** | Access denied |  -  |
**404** | Product not found |  -  |
**4XX** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_product**
> Product update_product(product_id, product_creation_or_update_parameters)

Update product from product form

Administrator can update every fields (override allowed) Other users can only update the following fields if empty :   - unitWeight   - vat   - unitPrice   - type 

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.models.product import Product
from gen.client.models.product_creation_or_update_parameters import ProductCreationOrUpdateParameters
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
    api_instance = gen.client.ManageProductApi(api_client)
    product_id = 56 # int | The id of the product concerned by the request
    product_creation_or_update_parameters = gen.client.ProductCreationOrUpdateParameters() # ProductCreationOrUpdateParameters | Modifications to apply

    try:
        # Update product from product form
        api_response = api_instance.update_product(product_id, product_creation_or_update_parameters)
        print("The response of ManageProductApi->update_product:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ManageProductApi->update_product: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **product_id** | **int**| The id of the product concerned by the request | 
 **product_creation_or_update_parameters** | [**ProductCreationOrUpdateParameters**](ProductCreationOrUpdateParameters.md)| Modifications to apply | 

### Return type

[**Product**](Product.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/merge-patch+json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**400** | Bad Request |  -  |
**403** | Access denied |  -  |
**404** | Product not found |  -  |
**409** | Product already exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

