# gen.client.SearchProductApi

All URIs are relative to *https://www.lcdp.ovh/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_product**](SearchProductApi.md#get_product) | **GET** /products/{productId} | Retrieve a product with ID
[**get_products**](SearchProductApi.md#get_products) | **GET** /products | Search for products with his name or status
[**test_free_access**](SearchProductApi.md#test_free_access) | **GET** /products/testFreeAccess | Test generation without bearer


# **get_product**
> Product get_product(product_id)

Retrieve a product with ID

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.models.product import Product
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
    api_instance = gen.client.SearchProductApi(api_client)
    product_id = 56 # int | The id of the product concerned by the request

    try:
        # Retrieve a product with ID
        api_response = api_instance.get_product(product_id)
        print("The response of SearchProductApi->get_product:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchProductApi->get_product: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **product_id** | **int**| The id of the product concerned by the request | 

### Return type

[**Product**](Product.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Product found |  -  |
**400** | Bad Request |  -  |
**403** | Access denied |  -  |
**404** | Product not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_products**
> PaginatedProducts get_products(q=q, vidal_package_eq=vidal_package_eq, st_eq=st_eq, pt_eq=pt_eq, spt_eq=spt_eq, lab_eq=lab_eq, s_waiting_sale_offer_count_gte=s_waiting_sale_offer_count_gte, order_by=order_by, p=p, pp=pp)

Search for products with his name or status

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.models.paginated_products import PaginatedProducts
from gen.client.models.product_status import ProductStatus
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
    api_instance = gen.client.SearchProductApi(api_client)
    q = 'q_example' # str | Any field in the product contains 'q' (optional)
    vidal_package_eq = 56 # int | Vidal package equal this one (optional)
    st_eq = [gen.client.ProductStatus()] # List[ProductStatus] | Filter on status to include in the search (can be given multiple time which result in a OR condition) (optional)
    pt_eq = 'pt_eq_example' # str | Product type to search on (optional)
    spt_eq = 'spt_eq_example' # str | Secondary product type to search on (optional)
    lab_eq = [56] # List[int] | Laboratory to search on (can be given multiple time which result in a OR condition) (optional)
    s_waiting_sale_offer_count_gte = 56 # int | Waiting sale offers count greater than or equal (optional)
    order_by = CREATED_AT:desc # str | Sort by (optional) (default to CREATED_AT:desc)
    p = 56 # int | Page number to search for (start at 0) (optional)
    pp = 56 # int | Number of user per page (optional)

    try:
        # Search for products with his name or status
        api_response = api_instance.get_products(q=q, vidal_package_eq=vidal_package_eq, st_eq=st_eq, pt_eq=pt_eq, spt_eq=spt_eq, lab_eq=lab_eq, s_waiting_sale_offer_count_gte=s_waiting_sale_offer_count_gte, order_by=order_by, p=p, pp=pp)
        print("The response of SearchProductApi->get_products:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchProductApi->get_products: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **q** | **str**| Any field in the product contains &#39;q&#39; | [optional] 
 **vidal_package_eq** | **int**| Vidal package equal this one | [optional] 
 **st_eq** | [**List[ProductStatus]**](ProductStatus.md)| Filter on status to include in the search (can be given multiple time which result in a OR condition) | [optional] 
 **pt_eq** | **str**| Product type to search on | [optional] 
 **spt_eq** | **str**| Secondary product type to search on | [optional] 
 **lab_eq** | [**List[int]**](int.md)| Laboratory to search on (can be given multiple time which result in a OR condition) | [optional] 
 **s_waiting_sale_offer_count_gte** | **int**| Waiting sale offers count greater than or equal | [optional] 
 **order_by** | **str**| Sort by | [optional] [default to CREATED_AT:desc]
 **p** | **int**| Page number to search for (start at 0) | [optional] 
 **pp** | **int**| Number of user per page | [optional] 

### Return type

[**PaginatedProducts**](PaginatedProducts.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Product&#39;s list found |  -  |
**403** | Access denied |  -  |
**4XX** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **test_free_access**
> test_free_access()

Test generation without bearer

### Example


```python
import gen.client
from gen.client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://www.lcdp.ovh/api/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = gen.client.Configuration(
    host = "https://www.lcdp.ovh/api/v1"
)


# Enter a context with an instance of the API client
with gen.client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = gen.client.SearchProductApi(api_client)

    try:
        # Test generation without bearer
        api_instance.test_free_access()
    except Exception as e:
        print("Exception when calling SearchProductApi->test_free_access: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

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
**200** | Success |  -  |
**403** | Access denied |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

