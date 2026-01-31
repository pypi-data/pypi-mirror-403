# AdditionalDetailsStatusResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | The current status of the additional details task | 

## Example

```python
from revengai.models.additional_details_status_response import AdditionalDetailsStatusResponse

# TODO update the JSON string below
json = "{}"
# create an instance of AdditionalDetailsStatusResponse from a JSON string
additional_details_status_response_instance = AdditionalDetailsStatusResponse.from_json(json)
# print the JSON string representation of the object
print(AdditionalDetailsStatusResponse.to_json())

# convert the object into a dict
additional_details_status_response_dict = additional_details_status_response_instance.to_dict()
# create an instance of AdditionalDetailsStatusResponse from a dict
additional_details_status_response_from_dict = AdditionalDetailsStatusResponse.from_dict(additional_details_status_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


