# gen.client.SearchSaleOfferApi

All URIs are relative to *https://lecomptoirdespharmacies.fr/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_sale_offers**](SearchSaleOfferApi.md#get_sale_offers) | **GET** /sale-offers | Search sale offers
[**get_sale_offers_by_status**](SearchSaleOfferApi.md#get_sale_offers_by_status) | **GET** /sale-offers/{saleOfferStatus} | Search sale offers by status


# **get_sale_offers**
> str get_sale_offers(st_eq=st_eq)

Search sale offers



### Example


```python
import gen.client
from gen.client.models.sale_offer_status import SaleOfferStatus
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
    api_instance = gen.client.SearchSaleOfferApi(api_client)
    st_eq = [gen.client.SaleOfferStatus()] # List[SaleOfferStatus] | Filter on status to include in the search (can be given multiple time which result in a OR condition) (optional)

    try:
        # Search sale offers
        api_response = api_instance.get_sale_offers(st_eq=st_eq)
        print("The response of SearchSaleOfferApi->get_sale_offers:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchSaleOfferApi->get_sale_offers: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **st_eq** | [**List[SaleOfferStatus]**](SaleOfferStatus.md)| Filter on status to include in the search (can be given multiple time which result in a OR condition) | [optional] 

### Return type

**str**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Session id created |  * authorization - Session token to use for future call <br>  |
**405** | Invalid input |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_sale_offers_by_status**
> get_sale_offers_by_status(sale_offer_status)

Search sale offers by status

### Example


```python
import gen.client
from gen.client.models.sale_offer_status import SaleOfferStatus
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
    api_instance = gen.client.SearchSaleOfferApi(api_client)
    sale_offer_status = gen.client.SaleOfferStatus() # SaleOfferStatus | 

    try:
        # Search sale offers by status
        api_instance.get_sale_offers_by_status(sale_offer_status)
    except Exception as e:
        print("Exception when calling SearchSaleOfferApi->get_sale_offers_by_status: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **sale_offer_status** | [**SaleOfferStatus**](.md)|  | 

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
**400** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

