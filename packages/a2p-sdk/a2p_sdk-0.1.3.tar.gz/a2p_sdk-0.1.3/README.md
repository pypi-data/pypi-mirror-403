# a2p-sdk

Python SDK for the a2p (Agent 2 Profile) protocol.

## Installation

```bash
pip install a2p-sdk
# or
poetry add a2p-sdk
# or
uv add a2p-sdk
```

## Quick Start

### For Agent Developers

```python
import asyncio
from a2p import A2PClient, create_agent_client

async def main():
    # Create a client for your agent
    client = create_agent_client(
        agent_did="did:a2p:agent:my-assistant",
        private_key=os.environ.get("A2P_PRIVATE_KEY"),
    )

    # Request access to a user's profile
    profile = await client.get_profile(
        user_did="did:a2p:user:alice",
        scopes=["a2p:preferences", "a2p:interests"],
    )

    print(profile.get("common", {}).get("preferences", {}).get("communication"))

    # Propose a new memory
    await client.propose_memory(
        user_did="did:a2p:user:alice",
        content="Prefers TypeScript over JavaScript",
        category="a2p:professional.preferences",
        confidence=0.85,
        context="User mentioned this during our conversation",
    )

asyncio.run(main())
```

### For Users

```python
import asyncio
from a2p import A2PUserClient, create_user_client, SensitivityLevel

async def main():
    # Create a user client
    user = create_user_client()

    # Create a new profile
    profile = await user.create_profile(display_name="Alice")

    # Add a memory manually
    await user.add_memory(
        content="I work as a software engineer at Acme Corp",
        category="a2p:professional",
        sensitivity=SensitivityLevel.STANDARD,
    )

    # Review pending proposals
    proposals = user.get_pending_proposals()
    for proposal in proposals:
        print(f"{proposal.proposed_by['agentName']}: {proposal.memory.content}")
        
        # Approve or reject
        await user.approve_proposal(proposal.id)
        # or: await user.reject_proposal(proposal.id, reason="Not accurate")

    # Export your profile
    json_str = user.export_profile()

asyncio.run(main())
```

## Core Concepts

### Profiles

A profile contains:

- **Identity**: DID, display name, pronouns
- **Common**: Shared preferences across all contexts
- **Memories**: Structured and episodic memories
- **Sub-Profiles**: Context-specific variations (work, personal, etc.)
- **Access Policies**: Who can access what

### Scopes

Scopes control what data an agent can access:

```python
from a2p import StandardScopes

# Common scopes
StandardScopes.PREFERENCES          # 'a2p:preferences'
StandardScopes.INTERESTS            # 'a2p:interests'
StandardScopes.PROFESSIONAL         # 'a2p:professional'
StandardScopes.HEALTH               # 'a2p:health' (sensitive)
```

### Proposals

Agents can propose memories, but users must approve:

```python
# Agent proposes
await client.propose_memory(
    user_did="did:a2p:user:alice",
    content="Likes jazz music",
    category="a2p:interests.music",
    confidence=0.75,
)

# User reviews
proposals = user.get_pending_proposals()
await user.approve_proposal(proposals[0].id)
```

## API Reference

### A2PClient (for agents)

| Method | Description |
|--------|-------------|
| `get_profile(user_did, scopes, sub_profile?)` | Get filtered user profile |
| `propose_memory(user_did, content, ...)` | Propose a new memory |
| `check_permission(user_did, permission, scope?)` | Check if agent has permission |
| `set_agent_profile(profile)` | Set agent profile for trust evaluation |

### A2PUserClient (for users)

| Method | Description |
|--------|-------------|
| `create_profile(display_name?)` | Create a new profile |
| `load_profile(did)` | Load existing profile |
| `add_memory(content, ...)` | Add a memory manually |
| `get_pending_proposals()` | Get proposals awaiting review |
| `approve_proposal(id, ...)` | Approve a proposal |
| `reject_proposal(id, reason?)` | Reject a proposal |
| `export_profile()` | Export to JSON |
| `import_profile(json)` | Import from JSON |

## License

EUPL-1.2
