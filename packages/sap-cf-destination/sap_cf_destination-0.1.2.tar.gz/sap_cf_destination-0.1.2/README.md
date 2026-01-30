# SAP Cloud Foundry Destination

sap-cf-destination is as open-source destination client built on top of HTTPX to connect to HTTP remote-services using destination when deploying your python application on BTP.

Install sap-cf-destination using 

```bash
$ pip install sap-cf-destination
```

## Pre-requisites:
- Access to BTP subaccount with permission to create destinations.
- Cloud Foundry space with instances of Destination service and connectivity service (only for on-premise destinations).

*Note: On-Premise destinations requires cloud-connector to be set-up in the BTP subaccount.*

---

Now, lets get started:

```python
from sap_cf_destination import Destination

dest = Destination("<Destination Name>")

client = dest.get_client() # HTTPX client with preconfigured base-url and headers from destination configuration

response = client.get("/").json()

```

The library also supports async clients

```python
client = dest.get_aclient()

response = await client.get("/").json()
```

Only the following Authentication type are supported:
1. NoAuthentication
2. BasicAuthentication
3. OAuth2ClientCredentials
4. PrincipalPropagation

and the following Proxy types are supported:
1. Internet
2. OnPremise

## Environment Variables

The library supports service binding and retrieves the instance credentials from `VCAP_SERVICES`. It also supports providing destinations as a list of dictionary in the environment varibales, this is useful when testing the application locally. The following parameters are supported:

|     | Description |
| --- | ----------- |
| name | Destination Name |
| url | URL to remote service |
| proxy_type | Internet or OnPremise |
| authentication | Authentication used by remote service currently only the following authentication types are supported: NoAuthentication, BasicAuthentication |
| username | username for Basic authentication |
| password | password for Basic authentication |
| forwardAuthToken | true or false |
| proxyHost | proxy host for on-premise services |
| proxyPort | proxy port for on-premise services |
| timeout | request timeout |

