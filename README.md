### hAPI is not yet ready. I accidentally made the repo public and I do not want to make it private again. First beta version to be released by the end of the week!
# hAPI (hackAPI) - BETA
hAPI (hackAPI) is a tool that automates testing for common security misconfigurations in REST APIs. The plan is to expand the tool to cover other API paradigms like SOAP, GraphQL, JSON-RPC, etc., and expand on the number of misconfigurations it can look for. Stay tuned.

## Licenses
This project is licensed under the MIT License.

However, for testing purposes I used the OpenAPI Petstore example JSON as well as the [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template). Big thanks to these projects. If you are a contributor on these projects and you want me to include a license or attribution - please let me know, I would be happy to. 

## Usage

The tool will allow users to choose any combinations of modules they would like to run. Each module consists of a separate security check. The tool generates an HTML report containing the results of each chosen module.

### HTTP Verb Tampering Check

The HTTP verb tampering check creates a table of the expected responses versus the actual responses to different HTTP request methods. It flags responses that differ from the ones defined in the OpenAPI schema. This module does not identify HTTP verb tampering vulnerabilities on its own but it flags discrepancies in a systematic way making them easy to spot and review. 

The module will fuzz each endpoint with a list of HTTP verbs. The wordlist can be supplied by the user. If not, the default wordlist (brorowed from [SecLists](https://github.com/danielmiessler/SecLists/blob/master/Fuzzing/http-request-methods.txt)) will be used. It will then cross-check the application's response with the expected response from the OpenAPI specification. If the response code differs, the entry will be flagged. 

## Limitiation and future plans
Currently, the tool only works with an OpenAPI schema as input. I plan to expand the possible inputs.

Currently, the tool only creates reports in HTML format. If there is demand for such functionality, I may add other output formats such as JSON, Markdown (or other). Let me know.