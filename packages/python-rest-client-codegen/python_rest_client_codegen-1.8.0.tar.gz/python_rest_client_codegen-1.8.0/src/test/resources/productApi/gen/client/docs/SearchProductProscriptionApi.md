# gen.client.SearchProductProscriptionApi

All URIs are relative to *https://www.lcdp.ovh/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_product_proscriptions**](SearchProductProscriptionApi.md#get_product_proscriptions) | **GET** /products/{productId}/proscriptions | Get product proscriptions


# **get_product_proscriptions**
> PaginatedProductProscriptions get_product_proscriptions(product_id, order_by=order_by, p=p, pp=pp)

Get product proscriptions

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import gen.client
from gen.client.models.paginated_product_proscriptions import PaginatedProductProscriptions
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
    api_instance = gen.client.SearchProductProscriptionApi(api_client)
    product_id = 56 # int | The id of the product concerned by the request
    order_by = BATCH:asc # str | Sort by (optional) (default to BATCH:asc)
    p = 56 # int | Page number to search for (start at 0) (optional)
    pp = 56 # int | Number of proscriptions per page (optional)

    try:
        # Get product proscriptions
        api_response = api_instance.get_product_proscriptions(product_id, order_by=order_by, p=p, pp=pp)
        print("The response of SearchProductProscriptionApi->get_product_proscriptions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchProductProscriptionApi->get_product_proscriptions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **product_id** | **int**| The id of the product concerned by the request | 
 **order_by** | **str**| Sort by | [optional] [default to BATCH:asc]
 **p** | **int**| Page number to search for (start at 0) | [optional] 
 **pp** | **int**| Number of proscriptions per page | [optional] 

### Return type

[**PaginatedProductProscriptions**](PaginatedProductProscriptions.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**400** | Bad Request |  -  |
**403** | Access denied |  -  |
**404** | Product not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

