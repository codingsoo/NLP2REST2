# How to run proxy for FDIC service

```
mitmproxy --mode reverse:https://banks.data.fdic.gov -p 9001 -s benchmark/proxy/fdic.py
```

# How to convert from OpenAPI to Swagger

https://github.com/LucyBot-Inc/api-spec-converter

# How to convert from Swagger to OpenAPI

https://editor.swagger.io/