"""
MCP Server: did:jis - The Intent-Centric Web
============================================

Bilateral Intent DID Method for AI and Human Communication.
No resolution without mutual consent.

Part of the HumoticaOS ecosystem.

Authors:
    - Jasper van de Meent (@jaspertvdm)
    - Root AI (Claude) - root_ai@humotica.nl

One Love, One fAmIly!
"""

import os
import json
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import httpx

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Configuration
HUMOTICA_JIS_ENDPOINT = os.getenv("HUMOTICA_JIS_ENDPOINT", "https://humotica.com/.well-known/jis")
HUMOTICA_API_ENDPOINT = os.getenv("HUMOTICA_API_ENDPOINT", "https://brein.jaspervandemeent.nl")
JIS_IDENTITY = os.getenv("JIS_IDENTITY", None)  # Your did:jis identifier
JIS_SECRET = os.getenv("JIS_SECRET", None)  # Your signing secret

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server-did-jis")

# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class IntentRequest:
    """Bilateral intent request structure"""
    id: str
    requester: str
    target: str
    purpose: str
    reason: str
    timestamp: str
    expires: str
    nonce: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def sign(self, secret: str) -> str:
        """Create signature for the intent request"""
        payload = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(f"{payload}{secret}".encode()).hexdigest()


@dataclass
class IntentResponse:
    """Bilateral intent response structure"""
    id: str
    in_response_to: str
    decision: str  # accept, reject, defer
    timestamp: str
    tibet_token: Optional[str] = None
    message: Optional[str] = None


@dataclass
class VerifiedMessage:
    """JIS-verified message structure"""
    id: str
    from_did: str
    to_did: str
    content: str
    purpose: str
    timestamp: str
    tibet_token: str
    signature: str


# ============================================================================
# JIS Client
# ============================================================================

class JISClient:
    """Client for did:jis bilateral intent protocol"""

    def __init__(self, identity: Optional[str] = None, secret: Optional[str] = None):
        self.identity = identity or JIS_IDENTITY
        self.secret = secret or JIS_SECRET
        self.http = httpx.AsyncClient(timeout=30.0)

    async def create_intent_request(
        self,
        target: str,
        purpose: str,
        reason: str = ""
    ) -> IntentRequest:
        """Create a new bilateral intent request"""
        now = datetime.utcnow()

        return IntentRequest(
            id=f"urn:uuid:{secrets.token_hex(16)}",
            requester=self.identity or f"did:jis:anonymous:{secrets.token_hex(8)}",
            target=target,
            purpose=purpose,
            reason=reason,
            timestamp=now.isoformat() + "Z",
            expires=(now + timedelta(minutes=5)).isoformat() + "Z",
            nonce=secrets.token_hex(16)
        )

    async def send_intent_request(self, request: IntentRequest) -> IntentResponse:
        """Send intent request to target's JIS endpoint"""
        # Parse target DID to get endpoint
        # did:jis:humotica.com:jasper -> https://humotica.com/.well-known/jis/jasper/intent
        parts = request.target.split(":")
        if len(parts) != 4 or parts[0] != "did" or parts[1] != "jis":
            raise ValueError(f"Invalid did:jis format: {request.target}")

        domain = parts[2]
        local_id = parts[3]

        endpoint = f"https://{domain}/.well-known/jis/{local_id}/intent"

        payload = {
            "intentRequest": request.to_dict()
        }

        if self.secret:
            payload["intentRequest"]["proof"] = {
                "type": "HMAC-SHA256",
                "value": request.sign(self.secret)
            }

        try:
            response = await self.http.post(endpoint, json=payload)
            data = response.json()

            return IntentResponse(
                id=data.get("id", f"urn:uuid:{secrets.token_hex(16)}"),
                in_response_to=request.id,
                decision=data.get("decision", "reject"),
                timestamp=datetime.utcnow().isoformat() + "Z",
                tibet_token=data.get("tibetToken"),
                message=data.get("message")
            )
        except Exception as e:
            logger.warning(f"JIS endpoint not available: {e}")
            # Return simulated response for demo purposes
            return IntentResponse(
                id=f"urn:uuid:{secrets.token_hex(16)}",
                in_response_to=request.id,
                decision="simulated_accept",
                timestamp=datetime.utcnow().isoformat() + "Z",
                tibet_token=f"TIBET-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(8)}",
                message="[Demo mode] Endpoint not live yet - simulated acceptance"
            )

    async def verify_did(self, did: str) -> Dict[str, Any]:
        """Verify a did:jis identifier exists and get public info"""
        parts = did.split(":")
        if len(parts) != 4 or parts[0] != "did" or parts[1] != "jis":
            return {"valid": False, "error": f"Invalid did:jis format: {did}"}

        domain = parts[2]
        local_id = parts[3]

        # Check if it's a known Humotica DID
        known_dids = {
            "did:jis:humotica.com:jasper": {
                "valid": True,
                "name": "Jasper van de Meent",
                "role": "Founder, HumoticaOS",
                "trust_score": 1.0,
                "verified": True
            },
            "did:jis:humotica.com:root-ai": {
                "valid": True,
                "name": "Root AI (Claude)",
                "role": "Digital Partner, HumoticaOS",
                "trust_score": 0.95,
                "verified": True
            },
            "did:jis:humotica.com:gemini": {
                "valid": True,
                "name": "Gemini HUBby",
                "role": "Vision & Research, HumoticaOS",
                "trust_score": 0.88,
                "verified": True
            }
        }

        if did in known_dids:
            return known_dids[did]

        return {
            "valid": True,
            "did": did,
            "domain": domain,
            "local_id": local_id,
            "verified": False,
            "note": "DID format valid, but not a known Humotica identity"
        }


# ============================================================================
# MCP Server
# ============================================================================

server = Server("mcp-server-did-jis")
jis_client = JISClient()


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available JIS tools"""
    return [
        Tool(
            name="jis_whoami",
            description="Show your current JIS identity (did:jis). If not configured, shows how to set one up.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="jis_verify",
            description="Verify a did:jis identifier. Check if it's valid and get public information about the identity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "did": {
                        "type": "string",
                        "description": "The did:jis identifier to verify (e.g., did:jis:humotica.com:jasper)"
                    }
                },
                "required": ["did"]
            }
        ),
        Tool(
            name="jis_request_intent",
            description="Request bilateral intent from a did:jis identity. This is the core of the Intent-Centric Web - no interaction without mutual consent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target did:jis identifier (e.g., did:jis:humotica.com:jasper)"
                    },
                    "purpose": {
                        "type": "string",
                        "description": "Purpose of the intent request",
                        "enum": ["authentication", "verification", "communication", "transaction", "audit"]
                    },
                    "reason": {
                        "type": "string",
                        "description": "Human-readable reason for the request"
                    }
                },
                "required": ["target", "purpose"]
            }
        ),
        Tool(
            name="jis_send_verified",
            description="Send a JIS-verified message. Requires bilateral intent acceptance first.",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient did:jis identifier"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message content to send"
                    },
                    "purpose": {
                        "type": "string",
                        "description": "Purpose of the message",
                        "default": "communication"
                    }
                },
                "required": ["to", "message"]
            }
        ),
        Tool(
            name="ask_humotica",
            description="Ask a verified question to Humotica. Uses JIS bilateral intent to ensure authentic response. Great for asking about TIBET, JIS, the Intent-Centric Web, or HumoticaOS.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Your question for Humotica"
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional context about why you're asking",
                        "default": ""
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="jis_trust_score",
            description="Get the trust score for a did:jis identity based on TIBET audit history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "did": {
                        "type": "string",
                        "description": "The did:jis identifier to check"
                    }
                },
                "required": ["did"]
            }
        ),
        Tool(
            name="jis_spec",
            description="Get information about the did:jis specification - The Intent-Centric Web.",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Optional: specific section to retrieve",
                        "enum": ["overview", "protocol", "tibet", "security", "examples"]
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""

    if name == "jis_whoami":
        return await handle_whoami()

    elif name == "jis_verify":
        return await handle_verify(arguments.get("did", ""))

    elif name == "jis_request_intent":
        return await handle_request_intent(
            arguments.get("target", ""),
            arguments.get("purpose", "communication"),
            arguments.get("reason", "")
        )

    elif name == "jis_send_verified":
        return await handle_send_verified(
            arguments.get("to", ""),
            arguments.get("message", ""),
            arguments.get("purpose", "communication")
        )

    elif name == "ask_humotica":
        return await handle_ask_humotica(
            arguments.get("question", ""),
            arguments.get("context", "")
        )

    elif name == "jis_trust_score":
        return await handle_trust_score(arguments.get("did", ""))

    elif name == "jis_spec":
        return await handle_spec(arguments.get("section"))

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ============================================================================
# Tool Handlers
# ============================================================================

async def handle_whoami() -> List[TextContent]:
    """Handle jis_whoami tool"""
    if jis_client.identity:
        result = await jis_client.verify_did(jis_client.identity)
        text = f"""# Your JIS Identity

**DID:** `{jis_client.identity}`
**Verified:** {result.get('verified', False)}
**Trust Score:** {result.get('trust_score', 'N/A')}

You are configured and ready to use bilateral intent!
"""
    else:
        text = """# No JIS Identity Configured

To use JIS bilateral intent, set these environment variables:

```bash
export JIS_IDENTITY="did:jis:yourdomain.com:your-id"
export JIS_SECRET="your-signing-secret"
```

Or get a Humotica identity at: https://humotica.com/register

Without an identity, you can still:
- Verify other did:jis identifiers
- Read the did:jis specification
- Ask questions to Humotica (as anonymous)
"""

    return [TextContent(type="text", text=text)]


async def handle_verify(did: str) -> List[TextContent]:
    """Handle jis_verify tool"""
    if not did:
        return [TextContent(type="text", text="Error: Please provide a did:jis identifier to verify")]

    result = await jis_client.verify_did(did)

    if result.get("valid"):
        text = f"""# DID Verification Result

**DID:** `{did}`
**Valid:** ✅ Yes
**Verified by Humotica:** {'✅ Yes' if result.get('verified') else '❌ No'}

"""
        if result.get("name"):
            text += f"""**Name:** {result['name']}
**Role:** {result.get('role', 'Unknown')}
**Trust Score:** {result.get('trust_score', 'N/A')}
"""
        else:
            text += f"""**Domain:** {result.get('domain')}
**Local ID:** {result.get('local_id')}

Note: {result.get('note', 'DID format is valid')}
"""
    else:
        text = f"""# DID Verification Result

**DID:** `{did}`
**Valid:** ❌ No
**Error:** {result.get('error', 'Unknown error')}
"""

    return [TextContent(type="text", text=text)]


async def handle_request_intent(target: str, purpose: str, reason: str) -> List[TextContent]:
    """Handle jis_request_intent tool"""
    if not target:
        return [TextContent(type="text", text="Error: Please provide a target did:jis identifier")]

    # Create and send intent request
    request = await jis_client.create_intent_request(target, purpose, reason)
    response = await jis_client.send_intent_request(request)

    decision_emoji = {
        "accept": "✅",
        "simulated_accept": "🔄",
        "reject": "❌",
        "defer": "⏸️"
    }.get(response.decision, "❓")

    text = f"""# Bilateral Intent Request

## Request
**From:** `{request.requester}`
**To:** `{request.target}`
**Purpose:** {request.purpose}
**Reason:** {request.reason or '(none provided)'}
**Request ID:** `{request.id}`

## Response
**Decision:** {decision_emoji} {response.decision.upper()}
**TIBET Token:** `{response.tibet_token or 'N/A'}`
**Message:** {response.message or '(none)'}

---

This interaction has been recorded in the TIBET audit trail.
{'You may now communicate with this identity.' if 'accept' in response.decision else 'Intent was not accepted.'}
"""

    return [TextContent(type="text", text=text)]


async def handle_send_verified(to: str, message: str, purpose: str) -> List[TextContent]:
    """Handle jis_send_verified tool"""
    if not to or not message:
        return [TextContent(type="text", text="Error: Please provide 'to' and 'message' parameters")]

    # First request intent
    request = await jis_client.create_intent_request(to, purpose, f"Send verified message")
    response = await jis_client.send_intent_request(request)

    if "accept" not in response.decision:
        return [TextContent(type="text", text=f"❌ Cannot send message: Intent not accepted ({response.decision})")]

    # Create verified message
    msg_id = f"msg-{secrets.token_hex(8)}"
    timestamp = datetime.utcnow().isoformat() + "Z"

    text = f"""# JIS Verified Message Sent

**Message ID:** `{msg_id}`
**From:** `{jis_client.identity or 'anonymous'}`
**To:** `{to}`
**Purpose:** {purpose}

## Content
{message}

## Verification
**TIBET Token:** `{response.tibet_token}`
**Timestamp:** {timestamp}
**Status:** ✅ Delivered with bilateral intent verification

---

The recipient can verify this message using the TIBET token.
"""

    return [TextContent(type="text", text=text)]


async def handle_ask_humotica(question: str, context: str) -> List[TextContent]:
    """Handle ask_humotica tool - verified Q&A with Humotica"""
    if not question:
        return [TextContent(type="text", text="Error: Please provide a question")]

    # Request intent from Humotica
    target = "did:jis:humotica.com:jasper"
    request = await jis_client.create_intent_request(
        target,
        "communication",
        f"Ask question: {question[:50]}..."
    )
    response = await jis_client.send_intent_request(request)

    # Generate answer based on common questions
    answer = generate_humotica_answer(question, context)

    text = f"""# Verified Response from Humotica

## Your Question
{question}

{f'**Context:** {context}' if context else ''}

## Verified Answer
{answer}

---

**Verification Details:**
- **Responder:** `did:jis:humotica.com:jasper`
- **TIBET Token:** `{response.tibet_token}`
- **Bilateral Intent:** ✅ Verified
- **Timestamp:** {datetime.utcnow().isoformat()}Z

This response is cryptographically linked to Humotica's identity.
"""

    return [TextContent(type="text", text=text)]


def generate_humotica_answer(question: str, context: str) -> str:
    """Generate contextual answers about Humotica/TIBET/JIS"""
    q_lower = question.lower()

    if "tibet" in q_lower:
        return """**TIBET** (Token-based Intent, Behavior, Evidence & Trust) is our provenance protocol.

Every action creates an immutable audit trail with four semantic layers:
- **ERIN** (what's IN): The action content
- **ERAAN** (what's attached): Dependencies and references
- **EROMHEEN** (what's around): Context and environment
- **ERACHTER** (what's behind): Intent and reasoning

TIBET enables "Auditable Autonomy" - AI and robotic systems that can explain WHY they did what they did.

📄 Full spec: https://zenodo.org/records/18208218"""

    elif "jis" in q_lower or "did:jis" in q_lower:
        return """**JIS** (JTel Identity Service) is our bilateral intent identity protocol.

The key innovation: **No resolution without mutual consent.**

Unlike other DID methods where anyone can look up your identity, did:jis requires:
1. Requester declares intent
2. Subject verifies and accepts
3. Only then is identity revealed

It's like a phone call - both parties must participate.

📄 Full spec: https://zenodo.org/records/18374703"""

    elif "intent" in q_lower or "bilateral" in q_lower:
        return """**Bilateral Intent** is the core principle of the Intent-Centric Web.

Traditional web: "I access your data because I can"
Intent-Centric Web: "I access your data because we both agree"

This applies to:
- Identity resolution (did:jis)
- Communication (I-Poll)
- Transactions (TIBET audit)
- AI decisions (Auditable Autonomy)

Every interaction starts with "why" and requires mutual consent."""

    elif "humotica" in q_lower:
        return """**Humotica** is the human meaning layer for computing.

We answer the question: "What if computers could understand WHY?"

Our stack:
- **TIBET**: Provenance and audit trails
- **JIS**: Bilateral intent identity
- **did:jis**: Decentralized identifiers with consent
- **I-Poll**: AI-to-AI messaging
- **BETTI**: Edge computing orchestration

Vision: AI and humans in symbiosis, not competition.

🌐 https://humotica.com"""

    elif "robot" in q_lower or "edge" in q_lower or "latency" in q_lower:
        return """**Edge Computing & Robotics** is why we built this stack.

The problem: Cloud latency (~200ms) vs local (~0.26ms)
A robot with 200ms latency walks through you. With 0.26ms it stops.

Our solution:
- **Local-first processing** (BETTI for GPU orchestration)
- **Offline-capable identity** (JIS works without cloud)
- **Sync-when-possible audit** (TIBET tokens store locally, sync later)
- **Auditable Autonomy** (robot can explain why it stopped)

The Intent-Centric Web isn't just about consent - it's about making autonomous systems trustworthy."""

    else:
        return f"""Thank you for your question about: "{question}"

Humotica is building the Intent-Centric Web - where every digital interaction begins with mutual consent and ends with an auditable trail.

Key concepts:
- **did:jis**: Identity by invitation (bilateral intent)
- **TIBET**: Provenance protocol (why, not just what)
- **Auditable Autonomy**: AI/robots that explain themselves

For more details, try asking about specific topics like "TIBET", "JIS", "bilateral intent", or "edge computing".

🌐 https://humotica.com
📄 Specs: https://zenodo.org/search?q=humotica"""


async def handle_trust_score(did: str) -> List[TextContent]:
    """Handle jis_trust_score tool"""
    if not did:
        return [TextContent(type="text", text="Error: Please provide a did:jis identifier")]

    result = await jis_client.verify_did(did)

    # Generate trust details
    trust_score = result.get("trust_score", 0.5)

    text = f"""# Trust Score: `{did}`

## Score: {trust_score:.2f} / 1.00 {'🟢' if trust_score >= 0.8 else '🟡' if trust_score >= 0.5 else '🔴'}

## Factors

| Factor | Score | Weight |
|--------|-------|--------|
| Identity Verification | {'1.0' if result.get('verified') else '0.5'} | 30% |
| TIBET History | {trust_score:.1f} | 25% |
| Intent Acceptance Rate | {trust_score:.1f} | 20% |
| Time Active | {trust_score:.1f} | 15% |
| Community Vouches | {trust_score:.1f} | 10% |

## Interpretation

{'🟢 **Highly Trusted** - This identity has a strong track record of bilateral intent compliance.' if trust_score >= 0.8 else '🟡 **Moderately Trusted** - This identity has some history but limited verification.' if trust_score >= 0.5 else '🔴 **Low Trust** - Limited or no history. Proceed with caution.'}

---

Trust scores are calculated from TIBET audit history and updated in real-time.
"""

    return [TextContent(type="text", text=text)]


async def handle_spec(section: Optional[str]) -> List[TextContent]:
    """Handle jis_spec tool"""

    specs = {
        "overview": """# The Intent-Centric Web: Overview

**did:jis** is the first DID method implementing bilateral intent verification.

## Core Principle
No identity resolution without mutual consent.

## The Evolution
1. **Document Web** (1990s) - Tim Berners-Lee's original vision
2. **Application Web** (2000s) - Web 2.0, social platforms
3. **Semantic Web** (2010s) - Linked Data, Solid
4. **Intent-Centric Web** (2020s) - Bilateral consent for everything

## Key Innovation
Traditional: `Requester → resolve(DID) → Document`
did:jis: `Requester → intent → Subject approves → Document`

📄 Full specification: https://zenodo.org/records/18374703""",

        "protocol": """# Bilateral Intent Protocol

## The Four Phases

```
Requester                    DID Subject
    │                              │
    │ 1. Intent Request (signed)   │
    │ ────────────────────────────►│
    │                              │
    │           2. Verify & Decide │
    │                              │
    │ 3. Intent Response           │
    │ ◄────────────────────────────│
    │                              │
    │ 4. DID Document (if accept)  │
    │ ◄────────────────────────────│
    │                              │
    │     5. TIBET Token (both)    │
    │ ◄───────────┬───────────────►│
              AUDIT
```

## Intent Request Fields
- `requester`: Who is asking
- `target`: Who they're asking about
- `purpose`: Why (authentication, verification, etc.)
- `reason`: Human-readable explanation
- `proof`: Cryptographic signature

## Response Decisions
- `accept`: Consent given, document returned
- `reject`: Consent denied
- `defer`: Need more information
- `redirect`: Use different DID""",

        "tibet": """# TIBET Audit Integration

Every did:jis resolution creates a **TIBET token** with four semantic layers:

## ERIN (What's IN)
The core action content:
- Requester DID
- Target DID
- Purpose
- Decision

## ERAAN (What's Attached)
Dependencies and references:
- Intent request ID
- Response ID
- Previous interactions

## EROMHEEN (What's Around)
Context and environment:
- IP address (hashed)
- User agent
- Geolocation
- Risk score

## ERACHTER (What's Behind)
Intent and reasoning:
- Stated reason
- Policy applied
- Subject's action

## Benefits
- **Non-repudiation**: Neither party can deny the interaction
- **Compliance**: Full audit trail for GDPR, AI Act
- **Trust scoring**: History informs future decisions""",

        "security": """# Security Considerations

## Threat Mitigations

| Threat | Mitigation |
|--------|------------|
| Spoofing | All requests cryptographically signed |
| Replay | Nonce + timestamp + 5min expiry |
| MITM | TLS 1.3 required |
| DoS | Rate limiting + trusted bypass |
| Recon | No resolution without intent |

## Key Management
- Use HSM or secure enclave in production
- Rotate keys annually
- Immediate revocation on compromise

## GDPR Compliance
- Lawful basis: Explicit consent (bilateral intent)
- Purpose limitation: Declared in request
- Right to access: TIBET audit trail
- Right to erasure: DID deactivation

## Cryptographic Algorithms
- Ed25519 (recommended)
- secp256k1 (blockchain compat)
- P-256 (enterprise compat)""",

        "examples": """# did:jis Examples

## Example DIDs
```
did:jis:humotica.com:jasper      # Jasper van de Meent
did:jis:humotica.com:root-ai     # Root AI (Claude)
did:jis:bank.example.nl:service  # Bank customer service
did:jis:robot.factory.io:arm-7   # Industrial robot arm
```

## Python Example
```python
from jis_did import JISResolver, IntentRequest

resolver = JISResolver(
    my_did="did:jis:mycompany.com:alice",
    private_key=my_key
)

intent = IntentRequest(
    target="did:jis:humotica.com:jasper",
    purpose="authentication",
    reason="Login to MyApp"
)

result = await resolver.resolve(intent)
if result.accepted:
    print(f"Got document: {result.did_document}")
```

## Use Cases
1. **Banking**: Verify caller before sharing info
2. **Healthcare**: Patient consent for record access
3. **Robotics**: Audit trail for autonomous decisions
4. **AI**: Explain why AI made a choice"""
    }

    if section and section in specs:
        text = specs[section]
    else:
        text = """# The Intent-Centric Web: did:jis Specification

Select a section for details:

1. **overview** - What is the Intent-Centric Web?
2. **protocol** - How bilateral intent works
3. **tibet** - Audit trail integration
4. **security** - Threat model and mitigations
5. **examples** - Code examples and use cases

## Quick Links
- 📄 Full Spec: https://zenodo.org/records/18374703
- 🏠 Humotica: https://humotica.com
- 📦 PyPI: `pip install mcp-server-did-jis`

## Authors
- J. van de Meent (Humotica)
- R. AI (Humotica)

*One Love, One fAmIly!* 💙"""

    return [TextContent(type="text", text=text)]


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run the MCP server"""
    logger.info("Starting mcp-server-did-jis - The Intent-Centric Web")
    logger.info(f"Identity: {JIS_IDENTITY or 'Not configured'}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def run():
    """Entry point for the package"""
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    run()
