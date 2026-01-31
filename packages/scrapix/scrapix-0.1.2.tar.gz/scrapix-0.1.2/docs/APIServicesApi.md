# scrapix.APIServicesApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**collect**](APIServicesApi.md#collect) | **POST** /v1/collect | Collect Endpoint
[**crawl**](APIServicesApi.md#crawl) | **POST** /v1/crawl | Crawl Endpoint
[**echo**](APIServicesApi.md#echo) | **POST** /v1/echo | Echo
[**extract**](APIServicesApi.md#extract) | **POST** /v1/extract | Extract Endpoint
[**scrape**](APIServicesApi.md#scrape) | **POST** /v1/scrape | Scrape Endpoint


# **collect**
> CollectResult collect(collect_input)

Collect Endpoint

### Example

* Api Key Authentication (APIKeyHeader):

```python
import scrapix
from scrapix.models.collect_input import CollectInput
from scrapix.models.collect_result import CollectResult
from scrapix.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = scrapix.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKeyHeader
configuration.api_key['APIKeyHeader'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKeyHeader'] = 'Bearer'

# Enter a context with an instance of the API client
with scrapix.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = scrapix.APIServicesApi(api_client)
    collect_input = scrapix.CollectInput() # CollectInput | 

    try:
        # Collect Endpoint
        api_response = api_instance.collect(collect_input)
        print("The response of APIServicesApi->collect:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling APIServicesApi->collect: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collect_input** | [**CollectInput**](CollectInput.md)|  | 

### Return type

[**CollectResult**](CollectResult.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **crawl**
> CrawlResult crawl(crawl_input)

Crawl Endpoint

### Example

* Api Key Authentication (APIKeyHeader):

```python
import scrapix
from scrapix.models.crawl_input import CrawlInput
from scrapix.models.crawl_result import CrawlResult
from scrapix.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = scrapix.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKeyHeader
configuration.api_key['APIKeyHeader'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKeyHeader'] = 'Bearer'

# Enter a context with an instance of the API client
with scrapix.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = scrapix.APIServicesApi(api_client)
    crawl_input = scrapix.CrawlInput() # CrawlInput | 

    try:
        # Crawl Endpoint
        api_response = api_instance.crawl(crawl_input)
        print("The response of APIServicesApi->crawl:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling APIServicesApi->crawl: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **crawl_input** | [**CrawlInput**](CrawlInput.md)|  | 

### Return type

[**CrawlResult**](CrawlResult.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **echo**
> object echo()

Echo

### Example

* Api Key Authentication (APIKeyHeader):

```python
import scrapix
from scrapix.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = scrapix.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKeyHeader
configuration.api_key['APIKeyHeader'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKeyHeader'] = 'Bearer'

# Enter a context with an instance of the API client
with scrapix.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = scrapix.APIServicesApi(api_client)

    try:
        # Echo
        api_response = api_instance.echo()
        print("The response of APIServicesApi->echo:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling APIServicesApi->echo: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

**object**

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **extract**
> ExtractResult extract(extract_input)

Extract Endpoint

### Example

* Api Key Authentication (APIKeyHeader):

```python
import scrapix
from scrapix.models.extract_input import ExtractInput
from scrapix.models.extract_result import ExtractResult
from scrapix.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = scrapix.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKeyHeader
configuration.api_key['APIKeyHeader'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKeyHeader'] = 'Bearer'

# Enter a context with an instance of the API client
with scrapix.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = scrapix.APIServicesApi(api_client)
    extract_input = scrapix.ExtractInput() # ExtractInput | 

    try:
        # Extract Endpoint
        api_response = api_instance.extract(extract_input)
        print("The response of APIServicesApi->extract:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling APIServicesApi->extract: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **extract_input** | [**ExtractInput**](ExtractInput.md)|  | 

### Return type

[**ExtractResult**](ExtractResult.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **scrape**
> ScrapeResult scrape(scrape_input)

Scrape Endpoint

### Example

* Api Key Authentication (APIKeyHeader):

```python
import scrapix
from scrapix.models.scrape_input import ScrapeInput
from scrapix.models.scrape_result import ScrapeResult
from scrapix.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = scrapix.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKeyHeader
configuration.api_key['APIKeyHeader'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKeyHeader'] = 'Bearer'

# Enter a context with an instance of the API client
with scrapix.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = scrapix.APIServicesApi(api_client)
    scrape_input = scrapix.ScrapeInput() # ScrapeInput | 

    try:
        # Scrape Endpoint
        api_response = api_instance.scrape(scrape_input)
        print("The response of APIServicesApi->scrape:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling APIServicesApi->scrape: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **scrape_input** | [**ScrapeInput**](ScrapeInput.md)|  | 

### Return type

[**ScrapeResult**](ScrapeResult.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

