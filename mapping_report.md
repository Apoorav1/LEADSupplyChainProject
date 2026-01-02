# Per-file mapping report

## Constraints.json
- Class: http://example.org/lead/Constraint
- id_field: None
- fields:

## Inventory.json
- Class: http://example.org/lead/Inventory
- id_field: None
- fields:

## MasterData.json
- Class: http://example.org/lead/Masterdata
- id_field: None
- fields:

## POS_History.json
- Class: http://example.org/lead/PosHistory
- id_field: None
- fields:

## Storedata.json
- Class: http://example.org/lead/Store
- id_field: store_id
- fields:
  - `store_name` -> http://www.w3.org/2000/01/rdf-schema#label
  - `store_type` -> lead:storeType
  - `location.city` -> lead:city
  - `location.state` -> lead:state
  - `location.zip` -> lead:postalCode
  - `store_size_sqft` -> lead:storeSizeSqFt
  - `sku_count` -> lead:skuCount
  - `operating_days_per_week` -> lead:operatingDaysPerWeek
  - `service_level_target` -> lead:serviceLevelTarget
  - `currency` -> lead:currency

## VendorCat.json
- Class: http://example.org/lead/Vendorcat
- id_field: None
- fields:
