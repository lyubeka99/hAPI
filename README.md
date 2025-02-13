### hAPI is not yet ready. I accidentally made the repo public and I do not want to make it private again. First beta version to be released by the end of the week!
# hAPI (hackAPI) - BETA
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

The tool will allow users to choose any combinations of modules they would like to run. Each module consists of a separate security check. The tool generates an HTML report containing the results of each chosen module.

### HTTP Verb Tampering Check

The HTTP verb tampering check creates a table of the expected responses versus the actual responses to different HTTP request methods. It flags responses that differ from the ones defined in the OpenAPI schema. This module does not identify HTTP verb tampering vulnerabilities on its own but it flags discrepancies in a systematic way making them easy to spot and review. 

The module will fuzz each endpoint with a list of HTTP verbs. The wordlist can be supplied by the user. If not, the default wordlist (brorowed from [SecLists](https://github.com/danielmiessler/SecLists/blob/master/Fuzzing/http-request-methods.txt)) will be used. It will then cross-check the application's response with the expected response from the OpenAPI specification. If the response code differs, the entry will be flagged. 

## Future plans
If there is demand for such functionality, I may may other output formats such as JSON, Markdown (or other). Let me know.