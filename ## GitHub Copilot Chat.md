## GitHub Copilot Chat

- Extension: 0.37.4 (prod)
- VS Code: 1.109.0 (bdd88df003631aaa0bcbe057cb0a940b80a476fa)
- OS: win32 10.0.19045 x64
- GitHub Account: Desmond689

## Network

User Settings:
```json
  "http.systemCertificatesNode": false,
  "github.copilot.advanced.debug.useElectronFetcher": true,
  "github.copilot.advanced.debug.useNodeFetcher": false,
  "github.copilot.advanced.debug.useNodeFetchFetcher": true
```

Connecting to https://api.github.com:
- DNS ipv4 Lookup: timed out after 10 seconds
- DNS ipv6 Lookup: Error (151 ms): getaddrinfo ENOTFOUND api.github.com
- Proxy URL: None (2 ms)
- Electron fetch (configured): Error (3503 ms): Error: net::ERR_NETWORK_CHANGED
    at SimpleURLLoaderWrapper.<anonymous> (node:electron/js2c/utility_init:2:10684)
    at SimpleURLLoaderWrapper.emit (node:events:519:28)
    at SimpleURLLoaderWrapper.callbackTrampoline (node:internal/async_hooks:130:17)
  [object Object]
  {"is_request_error":true,"network_process_crashed":false}
- Node.js https: Error (1038 ms): Error: getaddrinfo ENOTFOUND api.github.com
    at GetAddrInfoReqWrap.onlookupall [as oncomplete] (node:dns:122:26)
    at GetAddrInfoReqWrap.callbackTrampoline (node:internal/async_hooks:130:17)
- Node.js fetch: Error (633 ms): TypeError: fetch failed
    at node:internal/deps/undici/undici:14900:13
    at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
    at async n._fetch (c:\Users\DESMOND\.vscode\extensions\github.copilot-chat-0.37.4\dist\extension.js:4749:26151)
    at async n.fetch (c:\Users\DESMOND\.vscode\extensions\github.copilot-chat-0.37.4\dist\extension.js:4749:25799)
    at async d (c:\Users\DESMOND\.vscode\extensions\github.copilot-chat-0.37.4\dist\extension.js:4781:190)
    at async vA.h (file:///c:/Users/DESMOND/AppData/Local/Programs/Microsoft%20VS%20Code/bdd88df003/resources/app/out/vs/workbench/api/node/extensionHostProcess.js:116:41743)
  Error: getaddrinfo ENOTFOUND api.github.com
      at GetAddrInfoReqWrap.onlookupall [as oncomplete] (node:dns:122:26)
      at GetAddrInfoReqWrap.callbackTrampoline (node:internal/async_hooks:130:17)

Connecting to https://api.githubcopilot.com/_ping:
- DNS ipv4 Lookup: Error (253 ms): getaddrinfo ENOTFOUND api.githubcopilot.com
- DNS ipv6 Lookup: Error (12 ms): getaddrinfo ENOTFOUND api.githubcopilot.com
- Proxy URL: None (20 ms)
- Electron fetch (configured): Error (26 ms): Error: net::ERR_NAME_NOT_RESOLVED
    at SimpleURLLoaderWrapper.<anonymous> (node:electron/js2c/utility_init:2:10684)
    at SimpleURLLoaderWrapper.emit (node:events:519:28)
    at SimpleURLLoaderWrapper.callbackTrampoline (node:internal/async_hooks:130:17)
  [object Object]
  {"is_request_error":true,"network_process_crashed":false}
- Node.js https: Error (148 ms): Error: getaddrinfo ENOTFOUND api.githubcopilot.com
    at GetAddrInfoReqWrap.onlookupall [as oncomplete] (node:dns:122:26)
    at GetAddrInfoReqWrap.callbackTrampoline (node:internal/async_hooks:130:17)
- Node.js fetch: Error (405 ms): TypeError: fetch failed
    at node:internal/deps/undici/undici:14900:13
    at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
    at async n._fetch (c:\Users\DESMOND\.vscode\extensions\github.copilot-chat-0.37.4\dist\extension.js:4749:26151)
    at async n.fetch (c:\Users\DESMOND\.vscode\extensions\github.copilot-chat-0.37.4\dist\extension.js:4749:25799)
    at async d (c:\Users\DESMOND\.vscode\extensions\github.copilot-chat-0.37.4\dist\extension.js:4781:190)
    at async vA.h (file:///c:/Users/DESMOND/AppData/Local/Programs/Microsoft%20VS%20Code/bdd88df003/resources/app/out/vs/workbench/api/node/extensionHostProcess.js:116:41743)
  Error: getaddrinfo ENOTFOUND api.githubcopilot.com
      at GetAddrInfoReqWrap.onlookupall [as oncomplete] (node:dns:122:26)
      at GetAddrInfoReqWrap.callbackTrampoline (node:internal/async_hooks:130:17)

Connecting to https://copilot-proxy.githubusercontent.com/_ping:
- DNS ipv4 Lookup: Error (4 ms): getaddrinfo ENOTFOUND copilot-proxy.githubusercontent.com
- DNS ipv6 Lookup: Error (18 ms): getaddrinfo ENOTFOUND copilot-proxy.githubusercontent.com
- Proxy URL: None (6 ms)
- Electron fetch (configured): Error (40 ms): Error: net::ERR_NAME_NOT_RESOLVED
    at SimpleURLLoaderWrapper.<anonymous> (node:electron/js2c/utility_init:2:10684)
    at SimpleURLLoaderWrapper.emit (node:events:519:28)
    at SimpleURLLoaderWrapper.callbackTrampoline (node:internal/async_hooks:130:17)
  [object Object]
  {"is_request_error":true,"network_process_crashed":false}
- Node.js https: Error (192 ms): Error: getaddrinfo ENOTFOUND copilot-proxy.githubusercontent.com
    at GetAddrInfoReqWrap.onlookupall [as oncomplete] (node:dns:122:26)
    at GetAddrInfoReqWrap.callbackTrampoline (node:internal/async_hooks:130:17)
- Node.js fetch: Error (182 ms): TypeError: fetch failed
    at node:internal/deps/undici/undici:14900:13
    at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
    at async n._fetch (c:\Users\DESMOND\.vscode\extensions\github.copilot-chat-0.37.4\dist\extension.js:4749:26151)
    at async n.fetch (c:\Users\DESMOND\.vscode\extensions\github.copilot-chat-0.37.4\dist\extension.js:4749:25799)
    at async d (c:\Users\DESMOND\.vscode\extensions\github.copilot-chat-0.37.4\dist\extension.js:4781:190)
    at async vA.h (file:///c:/Users/DESMOND/AppData/Local/Programs/Microsoft%20VS%20Code/bdd88df003/resources/app/out/vs/workbench/api/node/extensionHostProcess.js:116:41743)
  Error: getaddrinfo ENOTFOUND copilot-proxy.githubusercontent.com
      at GetAddrInfoReqWrap.onlookupall [as oncomplete] (node:dns:122:26)
      at GetAddrInfoReqWrap.callbackTrampoline (node:internal/async_hooks:130:17)

Connecting to https://mobile.events.data.microsoft.com: Error (42 ms): Error: net::ERR_NAME_NOT_RESOLVED
    at SimpleURLLoaderWrapper.<anonymous> (node:electron/js2c/utility_init:2:10684)
    at SimpleURLLoaderWrapper.emit (node:events:519:28)
    at SimpleURLLoaderWrapper.callbackTrampoline (node:internal/async_hooks:130:17)
  [object Object]
  {"is_request_error":true,"network_process_crashed":false}
Connecting to https://dc.services.visualstudio.com: Error (60 ms): Error: net::ERR_NAME_NOT_RESOLVED
    at SimpleURLLoaderWrapper.<anonymous> (node:electron/js2c/utility_init:2:10684)
    at SimpleURLLoaderWrapper.emit (node:events:519:28)
    at SimpleURLLoaderWrapper.callbackTrampoline (node:internal/async_hooks:130:17)
  [object Object]
  {"is_request_error":true,"network_process_crashed":false}
Connecting to https://copilot-telemetry.githubusercontent.com/_ping: Error (213 ms): Error: getaddrinfo ENOTFOUND copilot-telemetry.githubusercontent.com
    at GetAddrInfoReqWrap.onlookupall [as oncomplete] (node:dns:122:26)
    at GetAddrInfoReqWrap.callbackTrampoline (node:internal/async_hooks:130:17)
Connecting to https://copilot-telemetry.githubusercontent.com/_ping: Error (149 ms): Error: getaddrinfo ENOTFOUND copilot-telemetry.githubusercontent.com
    at GetAddrInfoReqWrap.onlookupall [as oncomplete] (node:dns:122:26)
    at GetAddrInfoReqWrap.callbackTrampoline (node:internal/async_hooks:130:17)
Connecting to https://default.exp-tas.com: HTTP 400 (5107 ms)

Number of system certificates: 189

## Documentation

In corporate networks: [Troubleshooting firewall settings for GitHub Copilot](https://docs.github.com/en/copilot/troubleshooting-github-copilot/troubleshooting-firewall-settings-for-github-copilot).