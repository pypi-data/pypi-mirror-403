# ConfigResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dashboard_url** | **str** | The domain of the RevEng.AI platform you are connected to | [optional] [default to '']
**max_file_size_bytes** | **int** | Maximum file size (in bytes) that can be uploaded for analysis | 
**ai_decompiler_unsupported_languages** | **List[str]** | List of programming languages that are not supported for AI decompilation | 

## Example

```python
from revengai.models.config_response import ConfigResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ConfigResponse from a JSON string
config_response_instance = ConfigResponse.from_json(json)
# print the JSON string representation of the object
print(ConfigResponse.to_json())

# convert the object into a dict
config_response_dict = config_response_instance.to_dict()
# create an instance of ConfigResponse from a dict
config_response_from_dict = ConfigResponse.from_dict(config_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


