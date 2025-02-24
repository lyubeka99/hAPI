# hAPI (hackAPI)
hAPI (hackAPI) is a tool that automates testing for common security misconfigurations in REST APIs. You can select a subset of checks to perform or simply run all. The tool will run the tests against your API and create a report with the results in HTML or JSON format.

Currently, hAPI is in beta release and supports tests for the following misconfigurations:
* HTTP Verb Tampering
* Lack of Rate Limiting
* Insecure Cross-Origin Resource Policy (CORS)
* Common HTTP Security Headers Misconfigurations
* Usage of HTTP Basic Authentication

More functionality is coming very soon! Stay tuned!

Please find an example HTML report from the tool in the repo! This report was generated by running hAPI against the [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template)

## Limitiations
* Currently, the tool only works with an OpenAPI/Swagger schema as input. In the next version the tool will also work with a simple list of endpoints (for most modules). Coming soon!
* Not all modules are yet implemented. I am working on adding more. If you have suggestions, feel free to dm me.

## Installation

1. Clone repo.

```bash
git clone https://github.com/lyubeka99/hAPI
```

2. The tool should be runnable out-of-the-box on most UNIX distros.
```bash
cd hAPI
python3 hAPI/cli.py
``` 

3. If you get any missing libraries erros, install requirements.
```bash
pip install -r requirements.txt
```

## Usage

Enter project folder.
```bash
cd hAPI
```

Display available options and modules.
```bash
python3 hAPI/cli.py -h
```

Display available options for a specific module.

```bash
python3 hAPI/cli.py verb_tampering -h
```

The module 'all' allows you to pass any module-specific arguments.
```bash
python3 hAPI/cli.py all -h
```

You can also provide a list of specific modules that you want to run.
```bash
python3 hAPI/cli.py HTML rate_limiting cors -h
```

Regardless of which module you choose, the mandatory arguments are:
* `-u` URL
* `-i` input (path to the OpenAPI spec)
* `-f` format (HTML/JSON)

```bash
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML <MODULE NAME>
```

Optionally, you may specify headers and cookies.
```bash
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -C 'JSESSIONID=cookies; Test=test' -H 'User-Agent: EVIL; X-Api-Key:xyz' <MODULE NAME>
```

If you need to route thorugh a web proxy like BurpSuite or OWASP ZAP, you can use `--proxy` or `-x`.
```bash
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -C 'JSESSIONID=cookies; Test=test' -H 'User-Agent: EVIL; X-Api-Key:xyz' -x http://127.0.0.1:5000 <MODULE NAME>
```

If you are testing a private API and you need to disable certificate verification, you can use `--ignore-ssl`. WARNING: This will make your traffic interceptable and thus vulnerable to a Man-in-the-Middle (MitM) attack.
```bash
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -C 'JSESSIONID=cookies; Test=test' -H 'User-Agent: EVIL; X-Api-Key:xyz' -x http://127.0.0.1:5000 --ignore-ssl <MODULE NAME>
```

#### Some modules also have module-specific arguments. For exmaple, if you want to pass a wordlist to the verb tampering check:
```bash
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -C 'JSESSIONID=cookies; Test=test' -H 'User-Agent: EVIL; X-Api-Key:xyz' -x http://127.0.0.1:5000 --ignore-ssl verb_tampering --vt-wordlist /path/to/file
```

### All

This module runs all available modules.

Requires a URL, a path to your OpenAPI specification in JSON or YAML and the output format (HTML/JSON).
```bash
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -x http://127.0.0.1:5000 all
```

Optionally, you may specify headers and cookies.
```bash
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -C 'JSESSIONID=cookies; Test=test' -H 'User-Agent: EVIL; X-Api-Key:xyz' -x http://127.0.0.1:5000 all
```

### HTTP Verb Tampering Check

The HTTP verb tampering check creates a table of the expected responses versus the actual responses to different HTTP request methods. It flags responses that differ from the ones defined in the OpenAPI schema. This module does not identify HTTP verb tampering vulnerabilities on its own but it flags discrepancies in a systematic way making them easy to spot and review. 

The module will fuzz each endpoint with a list of HTTP verbs. The wordlist can be supplied by the user. If not, the default wordlist (brorowed from [SecLists](https://github.com/danielmiessler/SecLists/blob/master/Fuzzing/http-request-methods.txt)) will be used. It will then cross-check the application's response with the expected response from the OpenAPI specification. If the response code differs, the entry will be flagged. 

```
$ python3 hAPI/cli.py verb_tampering -h
...

Module-Specific Arguments:

verb_tampering Options:
usage: verb_tampering module [--vt-wordlist VT_WORDLIST]

options:
  --vt-wordlist VT_WORDLIST
                        Path to a custom wordlist for HTTP verbs for the verb tampering module.
```

### Rate Limiting Check
The rate limiting check sends a high volume of requests to API endpoints to determine if rate limits are enforced. If the API fails to implement proper rate limiting, attackers could abuse it for credential stuffing, scraping, or denial-of-service (DoS) attacks.

This module will send multiple requests per second to an endpoint and analyze the responses. If the API allows unlimited requests without blocking or returning `429 Too Many Requests`, the entry will be flagged. Users can configure the request rate and threshold.

```
$ python3 hAPI/cli.py rate_limiting -h 
...  

Module-Specific Arguments:

rate_limiting Options:
usage: rate_limiting module [--rl-threshold RL_THRESHOLD] [--rl-endpoints RL_ENDPOINTS]

options:
  --rl-threshold RL_THRESHOLD
                        Threshold for rate limiting detection.
  --rl-endpoints RL_ENDPOINTS
                        A comma-separated list of target endpoints.
```

### CORS Check

The CORS check analyzes the API's Cross-Origin Resource Sharing (CORS) policy to identify misconfigurations that could allow unauthorized cross-origin access. If an API permits `Access-Control-Allow-Origin: *` or incorrectly allows `Access-Control-Allow-Credentials: true`, an attacker could exploit this to steal user data.

The module sends cross-origin requests with different `Origin` headers to see how the API responds. It flags permissive or unsafe CORS configurations that could be exploited.

```
$ python3 hAPI/cli.py cors -h  
... 

Module-Specific Arguments:

cors Options:
usage: cors module [--cors-endpoints CORS_ENDPOINTS] [--cors-custom-origin CORS_CUSTOM_ORIGIN]

options:
  --cors-endpoints CORS_ENDPOINTS
                        A comma-separated list of target endpoints.
  --cors-custom-origin CORS_CUSTOM_ORIGIN
                        Custom origin to test against the target API.
```

### Common HTTP Security Headers Check

The HTTP security headers check scans API responses to identify missing or misconfigured security headers. Proper security headers help mitigate attacks such as MIME-type sniffing, clickjacking, and cross-site scripting (XSS).

This module checks for headers like `Strict-Transport-Security`, `X-Content-Type-Options`, `Server` and `X-Powered-By`. If critical security headers are missing or improperly configured, they will be flagged.

```
$ python3 hAPI/cli.py common_security_headers -h
...

Module-Specific Arguments:

common_security_headers Options:
usage: common_security_headers module [--csh-endpoints CSH_ENDPOINTS]

options:
  --csh-endpoints CSH_ENDPOINTS
                        A comma-separated list of endpoints to check security headers.
```

### HTTP Basic Auth Check

The HTTP Basic Auth check scans API endpoints for the use of Basic Authentication, which transmits credentials in a Base64-encoded format without encryption. This authentication method is outdated and exposes users to credential interception and replay attacks.

The module sends requests to detect `Authorization: Basic` headers in responses. If found, the endpoint will be flagged, and recommendations for secure alternatives will be provided.

```
$ python3 hAPI/cli.py basic_auth -h
...

Module-Specific Arguments:

basic_auth Options:
usage: basic_auth module [--ba-endpoints BA_ENDPOINTS] [--ba-username BA_USERNAME]
                         [--ba-password BA_PASSWORD]

options:
  --ba-endpoints BA_ENDPOINTS
                        A comma-separated list of target endpoints.
  --ba-username BA_USERNAME
                        Valid username for basic authentication testing.
  --ba-password BA_PASSWORD
                        Valid password for basic authentication testing.
```

## JSON output

The tool is optimized for HTML reporting. However, it still produces useful data in JSON format that can be used as input for other systems. Each module produces a JSON object in the format found below. If you need only the data from the security checks, you can simply extract the `table` attribute from the JSON. 

```json
{
    "module": module_name,
    "description_paragraphs": description_paragraphs,
    "references": references,
    "remediation_paragraphs": remediation_paragraphs,
    "verification_command":verification_command
    "table": {
        "headers": ["Path", "Verb", "Expected Response Code", "Actual Response Code", "Test Result"],
        "rows": unformatted_results,
    }
}
```

## Licenses
This project is licensed under the MIT License.

However, for testing purposes I used the OpenAPI Petstore example JSON as well as the [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template). Big thanks to these projects. If you are a contributor on these projects and you want me to include a license or attribution - please let me know, I would be happy to. 