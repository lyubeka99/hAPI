# hAPI (hackAPI) - BETA
hAPI (hackAPI) is a tool that automates testing for common security misconfigurations in REST APIs. You can select a subset of checks to perform or simply run all. The tool will run the tests against your API and create a report with the results in HTML or JSON format.

Currently, hAPI is in beta release and only supports an HTTP verb tampering test. However, more functionality is coming very soon! Stay tuned!

## Usage

Display available options and modules.
```
python3 hAPI/cli.py -h
```

Display available options for a specific module.

```
python3 hAPI/cli.py verb_tampering -h
```

The module 'all' allows you to pass any module-specific arguments.
```
python3 hAPI/cli.py all -h
```

Regardsless of which module you choose, the mandatory arguments are:
* `-u` URL
* `-i` input (path to the OpenAPI spec)
* `-f` format (HTML/JSON)

```
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -x http://127.0.0.1:5000 <MODULE NAME>
```

Optionally, you may specify headers and cookies.
```
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -C 'JSESSIONID=cookies; Test=test' -H 'User-Agent: EVIL; X-Api-Key:xyz' -x http://127.0.0.1:5000 <MODULE NAME>
```

If you need to route thorugh a web proxy like BurpSuite or OWASP ZAP, you can use `--proxy`.
```
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -C 'JSESSIONID=cookies; Test=test' -H 'User-Agent: EVIL; X-Api-Key:xyz' -x http://127.0.0.1:5000 --proxy <MODULE NAME>
```

If you are testing a private API and you need to disable certificate verification, you can use `--ignore-ssl`. WARNING: This will make your traffic interceptable and thus vulnerable to a Man-in-the-Middle (MitM) attack.
```
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -C 'JSESSIONID=cookies; Test=test' -H 'User-Agent: EVIL; X-Api-Key:xyz' -x http://127.0.0.1:5000 --ignore-ssl <MODULE NAME>
```

#### Some modules also have module-specific arguments. For exmaple, if you want to pass a wordlist to the verb tampering check:
```
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -C 'JSESSIONID=cookies; Test=test' -H 'User-Agent: EVIL; X-Api-Key:xyz' -x http://127.0.0.1:5000 --ignore-ssl verb_tampering --vt-wordlist /path/to/file
```

### All

This module runs all available modules.

Requires a URL, a path to your OpenAPI specification in JSON or YAML and the output format (HTML/JSON).
```
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -x http://127.0.0.1:5000 all
```

Optionally, you may specify headers and cookies.
```
python3 hAPI/cli.py -u http://127.0.0.1:8000 -i tests/localtest.json -f HTML -C 'JSESSIONID=cookies; Test=test' -H 'User-Agent: EVIL; X-Api-Key:xyz' -x http://127.0.0.1:5000 all
```

### HTTP Verb Tampering Check

The HTTP verb tampering check creates a table of the expected responses versus the actual responses to different HTTP request methods. It flags responses that differ from the ones defined in the OpenAPI schema. This module does not identify HTTP verb tampering vulnerabilities on its own but it flags discrepancies in a systematic way making them easy to spot and review. 

The module will fuzz each endpoint with a list of HTTP verbs. The wordlist can be supplied by the user. If not, the default wordlist (brorowed from [SecLists](https://github.com/danielmiessler/SecLists/blob/master/Fuzzing/http-request-methods.txt)) will be used. It will then cross-check the application's response with the expected response from the OpenAPI specification. If the response code differs, the entry will be flagged. 

## Limitiations
* Currently, the tool only works with an OpenAPI schema as input. I will try to include more possible inputs depending on different use cases.
* The tool generates reports in HTML and JSON. Let me know if you would like any other report formats.

## Licenses
This project is licensed under the MIT License.

However, for testing purposes I used the OpenAPI Petstore example JSON as well as the [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template). Big thanks to these projects. If you are a contributor on these projects and you want me to include a license or attribution - please let me know, I would be happy to. 