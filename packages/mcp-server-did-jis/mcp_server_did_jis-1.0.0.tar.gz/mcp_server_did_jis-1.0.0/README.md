# mcp-server-did-jis

[![PyPI](https://img.shields.io/pypi/v/mcp-server-did-jis.svg)](https://pypi.org/project/mcp-server-did-jis/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**The Intent-Centric Web: MCP Server for did:jis bilateral intent identity.**

> *"The web was built for documents. Then it evolved for applications.
> Now it must evolve for intent — where every interaction begins with 'why'."*

Part of the [HumoticaOS](https://humotica.com) ecosystem.

## What is did:jis?

`did:jis` is the first DID (Decentralized Identifier) method implementing **bilateral intent verification**. Unlike traditional identity systems where anyone can look up your information, did:jis requires **mutual consent** before any identity exchange.

**Traditional DID:**
```
Requester → resolve(did:web:example.com) → DID Document
Anyone can resolve. No consent needed.
```

**did:jis:**
```
Requester → intent request → Subject accepts → DID Document
No resolution without mutual consent.
```

📄 **Full Specification:** [DOI: 10.5281/zenodo.18374703](https://zenodo.org/records/18374703)

## Installation

```bash
pip install mcp-server-did-jis
```

## Usage

### With Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "did-jis": {
      "command": "mcp-server-did-jis",
      "env": {
        "JIS_IDENTITY": "did:jis:yourdomain.com:your-id",
        "JIS_SECRET": "your-signing-secret"
      }
    }
  }
}
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JIS_IDENTITY` | No | Your did:jis identifier |
| `JIS_SECRET` | No | Your signing secret for proofs |
| `HUMOTICA_JIS_ENDPOINT` | No | Custom JIS endpoint (default: humotica.com) |

## Available Tools

### `jis_whoami`
Show your current JIS identity configuration.

### `jis_verify`
Verify a did:jis identifier and get public information.

```
jis_verify did:jis:humotica.com:jasper
```

### `jis_request_intent`
Request bilateral intent from a did:jis identity. The core of the Intent-Centric Web.

```
jis_request_intent
  target: did:jis:humotica.com:jasper
  purpose: authentication
  reason: "Login to my application"
```

### `jis_send_verified`
Send a JIS-verified message with bilateral intent confirmation.

### `ask_humotica`
Ask a verified question to Humotica about TIBET, JIS, or the Intent-Centric Web.

```
ask_humotica "What is bilateral intent?"
```

### `jis_trust_score`
Get the trust score for a did:jis identity based on TIBET audit history.

### `jis_spec`
Get information about the did:jis specification sections.

## Example Session

```
User: Verify the Humotica founder's identity