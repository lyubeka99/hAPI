# hAPI (hackAPI)
hAPI (hackAPI) is a tool that automates testing for common security misconfigurations in REST APIs. The plan is to expand the tool to cover other API paradigms like SOAP, GraphQL, JSON-RPC, etc., and expand on the number of misconfigurations it can look for. Stay tuned.

## Limitations

## Licenses
This project is licensed under the MIT License.

However, it includes the following component, which is licensed under the Apache License 2.0:

- `test/openapi.json` - Derived from the OpenAPI Petstore example.

The full text of the Apache License 2.0 is included in the file `APACHE_LICENSE`.

- The MIT License applies to the main project codebase. See `LICENSE` for details.
- The Apache License 2.0 applies to specific components as noted above. 

## Usage


### HTTP Verb Tampering Check

The HTTP verb tampering check creates a table of the expected responses versus the actual responses to different HTTP request methods. It flags responses that differ from the ones defined in the OpenAPI schema. This module does not identify HTTP verb tampering vulnerabilities on its own but it flags discrepancies in a systematic way making them easy to spot and review. 

The module will fuzz each endpoint with a list of common HTTP methods (brorowed from [SecLists](https://github.com/danielmiessler/SecLists/blob/master/Fuzzing/http-request-methods.txt)). It will then cross-check the application's response with the expected response from the OpenAPI specification. If the response code differs, the entry will be flagged. 