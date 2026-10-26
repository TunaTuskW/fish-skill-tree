# Antigravity CLI (`agy`) Wire Integration Runbook

## 1. Overview
Google Antigravity (`agy`, formerly Gemini CLI) coordinates with closed-source language servers that speak gRPC / protobuf over HTTP/2 to Google Cloud internal endpoints.

`billion-context` supports Antigravity natively via launcher mode:
```bash
bili antigravity
```

---

## 2. Wire Connection Mechanism

### Environment Override Hook
The Go language server in `agy` honors the `CLOUD_CODE_URL` environment variable:
- **Default Endpoint**: `https://daily-cloudcode-pa.googleapis.com` (Note: the bare `cloudcode-pa` domain returns HTTP 400 on internal endpoints).
- **Relay Configuration**:
  ```bash
  export CLOUD_CODE_URL="http://127.0.0.1:9090/bili/https://daily-cloudcode-pa.googleapis.com"
  ```
- **Zero Certificate MITM**: Because `CLOUD_CODE_URL` redirects the base URL cleanly, no root CA installation or TLS certificate decryption is needed.

### Wire Protocol Detection
The proxy identifies Antigravity requests by HTTP path:
- `/v1internal:streamGenerateContent`
- `/v1internal:generateContent`

Payloads flowing through this route are parsed as streaming protobuf/JSON chunks. Conversational history increments are evaluated by `acp-kernel` before reaching the model attention buffer.

---

## 3. Fallback Route: HTTPS Proxy MITM

If `CLOUD_CODE_URL` is unavailable or overridden:
1. Set standard proxy variables:
   ```bash
   export HTTPS_PROXY="http://127.0.0.1:9090"
   export HTTP_PROXY="http://127.0.0.1:9090"
   ```
2. Whitelist the internal Google host in proxy config:
   ```json
   {
     "mitm": {
       "domains": ["daily-cloudcode-pa.googleapis.com"]
     }
   }
   ```
3. Trust the local proxy root CA in macOS Keychain:
   ```bash
   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.billion-context/ca.crt
   ```
