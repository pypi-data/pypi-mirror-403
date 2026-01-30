# ProductCreationOrUpdateParameters


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**vidal_package_id** | **int** | Set vidal package id of product. If vidalPackageId is set:   - Product will be created/synchronized from vidal data.   - More fields can be added to override data (after sync) If vidalPackageId is not set:   - Given product is created/updated without vidal sync Restrictions :   - You should be from role &#39;ADMINISTRATOR&#39; to update it.  | [optional] 
**is_automatic_vidal_sync_enabled** | **bool** | Set automatic synchronization to vidal enabled or not. Automatic does not mean periodic here. It means sync can be done without it&#39;s clearly asked (Ex: When product is selected in the front end, or when product details export is requested). Triggers (single) synchronization to vidal if set to true. Restrictions :   - You should be from role &#39;ADMINISTRATOR&#39; to change its value. Otherwise,     you can just set it from true to true to trigger a (single) vidal synchronization.  | [optional] 
**barcodes** | [**Barcodes**](Barcodes.md) |  | [optional] 
**name** | **str** |  | [optional] 
**short_name** | **str** |  | [optional] 
**dci** | **str** |  | [optional] 
**unit_weight** | **float** | Weight of a single unit in grams | [optional] 
**unit_price** | **float** | Public price of the product | [optional] 
**manufacturer_price** | **float** | Manufacturer price of the product | [optional] 
**type_id** | **str** | Product Type Identifier | [optional] 
**secondary_type_id** | **str** | Product Secondary Type Identifier | [optional] 
**refund_rate** | **str** |  | [optional] 
**laboratory_id** | **int** | Laboratory ID | [optional] 
**vat_id** | **str** | VAT identifier | [optional] 
**narcotic_prescription** | **bool** |  | [optional] 
**storage_type** | **str** |  | [optional] 
**market_status** | [**ProductMarketStatus**](ProductMarketStatus.md) |  | [optional] 
**status** | [**ProductStatus**](ProductStatus.md) |  | [optional] 
**dispensation_place** | [**ProductDispensationPlace**](ProductDispensationPlace.md) |  | [optional] 
**is_otc** | **bool** |  | [optional] 
**is_drug_in_sport** | **bool** |  | [optional] 

## Example

```python
from gen.client.models.product_creation_or_update_parameters import ProductCreationOrUpdateParameters

# TODO update the JSON string below
json = "{}"
# create an instance of ProductCreationOrUpdateParameters from a JSON string
product_creation_or_update_parameters_instance = ProductCreationOrUpdateParameters.from_json(json)
# print the JSON string representation of the object
print(ProductCreationOrUpdateParameters.to_json())

# convert the object into a dict
product_creation_or_update_parameters_dict = product_creation_or_update_parameters_instance.to_dict()
# create an instance of ProductCreationOrUpdateParameters from a dict
product_creation_or_update_parameters_from_dict = ProductCreationOrUpdateParameters.from_dict(product_creation_or_update_parameters_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


