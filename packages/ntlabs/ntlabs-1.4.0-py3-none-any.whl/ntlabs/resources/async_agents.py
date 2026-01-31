"""
Neural LAB - AI Solutions Platform
Async Agents Resource - Unified AI Agents access.

Provides async access to specialized AI agents:
- Dédalo (Neural LAB): Sales & Lead Qualification
- Chiron (Hipócrates): Medical AI Assistant
- Themis (Argos): Legal AI Assistant
- Hermes (Mercúrius): Notary AI Assistant
- Athena (Pólis): Public Health AI Assistant

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-30
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from .agents import AgentChatResponse, AgentInfo, AgentStreamChunk


class AsyncAgentsResource:
    """
    Async AI Agents resource.

    Provides async unified access to specialized AI agents for different products.

    Usage:
        async with AsyncNTLClient(api_key="ntl_xxx") as client:
            # List available agents
            agents = await client.agents.list()
            for agent in agents:
                print(f"{agent.name}: {agent.description_pt}")

            # Get specific agent info
            dedalo = await client.agents.get("dedalo")

            # Chat with an agent
            response = await client.agents.chat(
                agent="dedalo",
                messages=[{"role": "user", "content": "Olá!"}],
            )
            print(response.message)

            # Streaming chat
            async for chunk in client.agents.chat_stream(
                agent="dedalo",
                messages=[{"role": "user", "content": "Conte-me sobre a Neural LAB"}],
            ):
                print(chunk.content, end="", flush=True)
    """

    def __init__(self, client):
        self._client = client

    async def list(self, include_coming_soon: bool = False) -> list[AgentInfo]:
        """
        List all available AI agents.

        Args:
            include_coming_soon: Include agents not yet available

        Returns:
            List of AgentInfo objects
        """
        response = await self._client.get(
            "/v1/agents/",
            params={"include_coming_soon": include_coming_soon},
        )

        return [
            AgentInfo(
                id=a["id"],
                name=a["name"],
                product=a["product"],
                description=a["description"],
                description_pt=a["description_pt"],
                status=a["status"],
                capabilities=a.get("capabilities", []),
                languages=a.get("languages", ["pt"]),
            )
            for a in response.get("agents", [])
        ]

    async def get(self, agent_id: str) -> AgentInfo:
        """
        Get information about a specific agent.

        Args:
            agent_id: Agent ID (dedalo, chiron, themis, hermes, athena)

        Returns:
            AgentInfo object

        Raises:
            APIError: If agent not found
        """
        response = await self._client.get(f"/v1/agents/{agent_id}")

        return AgentInfo(
            id=response["id"],
            name=response["name"],
            product=response["product"],
            description=response["description"],
            description_pt=response["description_pt"],
            status=response["status"],
            capabilities=response.get("capabilities", []),
            languages=response.get("languages", ["pt"]),
        )

    async def chat(
        self,
        agent: str,
        messages: list[dict[str, str]],
        session_id: str | None = None,
        user_id: str | None = None,
        locale: str = "pt",
        temperature: float | None = None,
        max_tokens: int = 4000,
        metadata: dict[str, Any] | None = None,
    ) -> AgentChatResponse:
        """
        Chat with an AI agent.

        Args:
            agent: Agent ID (dedalo, chiron, themis, hermes, athena)
            messages: List of messages [{"role": "user", "content": "..."}]
            session_id: Session ID for context persistence
            user_id: User ID for personalization
            locale: Language code (pt, en, es)
            temperature: Override agent's default temperature
            max_tokens: Maximum tokens in response
            metadata: Additional context metadata

        Returns:
            AgentChatResponse with the agent's reply

        Example:
            response = await client.agents.chat(
                agent="dedalo",
                messages=[
                    {"role": "user", "content": "Olá!"},
                ],
                session_id="session_123",
            )
            print(response.message)
        """
        payload = {
            "agent": agent,
            "messages": messages,
            "locale": locale,
            "max_tokens": max_tokens,
            "stream": False,
        }

        if session_id:
            payload["session_id"] = session_id
        if user_id:
            payload["user_id"] = user_id
        if temperature is not None:
            payload["temperature"] = temperature
        if metadata:
            payload["metadata"] = metadata

        response = await self._client.post("/v1/agents/chat", json=payload)

        return AgentChatResponse(
            message=response.get("message", ""),
            agent=response.get("agent", agent),
            session_id=response.get("session_id"),
            intent=response.get("intent"),
            confidence=response.get("confidence"),
            should_handoff=response.get("should_handoff", False),
            handoff_reason=response.get("handoff_reason"),
            lead_score=response.get("lead_score"),
            input_tokens=response.get("input_tokens", 0),
            output_tokens=response.get("output_tokens", 0),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0.0),
        )

    async def chat_stream(
        self,
        agent: str,
        messages: list[dict[str, str]],
        session_id: str | None = None,
        user_id: str | None = None,
        locale: str = "pt",
        temperature: float | None = None,
        max_tokens: int = 4000,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[AgentStreamChunk]:
        """
        Stream chat with an AI agent using Server-Sent Events.

        Args:
            agent: Agent ID (dedalo, chiron, themis, hermes, athena)
            messages: List of messages [{"role": "user", "content": "..."}]
            session_id: Session ID for context persistence
            user_id: User ID for personalization
            locale: Language code (pt, en, es)
            temperature: Override agent's default temperature
            max_tokens: Maximum tokens in response
            metadata: Additional context metadata

        Yields:
            AgentStreamChunk objects with streaming content

        Example:
            async for chunk in client.agents.chat_stream(
                agent="dedalo",
                messages=[{"role": "user", "content": "Olá!"}],
            ):
                if chunk.type == "token":
                    print(chunk.content, end="", flush=True)
                elif chunk.type == "end":
                    print(f"\\n[Tokens: {chunk.output_tokens}]")
        """
        import json

        payload = {
            "agent": agent,
            "messages": messages,
            "locale": locale,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if session_id:
            payload["session_id"] = session_id
        if user_id:
            payload["user_id"] = user_id
        if temperature is not None:
            payload["temperature"] = temperature
        if metadata:
            payload["metadata"] = metadata

        # Make streaming request
        client = self._client._get_client()
        async with client.stream(
            "POST",
            "/v1/agents/chat/stream",
            json=payload,
            headers={"Accept": "text/event-stream"},
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        yield AgentStreamChunk(
                            type=data.get("type", "token"),
                            content=data.get("content"),
                            agent=data.get("agent"),
                            session_id=data.get("session_id"),
                            intent=data.get("intent"),
                            confidence=data.get("confidence"),
                            should_handoff=data.get("should_handoff"),
                            lead_score=data.get("lead_score"),
                            input_tokens=data.get("input_tokens"),
                            output_tokens=data.get("output_tokens"),
                            latency_ms=data.get("latency_ms"),
                            cost_brl=data.get("cost_brl"),
                            error=data.get("error"),
                        )
                    except json.JSONDecodeError:
                        continue
