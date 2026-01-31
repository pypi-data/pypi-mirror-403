"""
Neural LAB - AI Solutions Platform
Async Email Resource - Send emails via Resend.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from typing import Any

from .email import EmailResult


class AsyncEmailResource:
    """
    Async email resource for sending emails via Resend.

    Usage:
        async with AsyncNeuralLabClient(api_key="nl_xxx") as client:
            result = await client.email.send(
                to=["user@example.com"],
                subject="Bem-vindo!",
                html="<h1>Olá!</h1>",
            )
            print(result.id)
    """

    def __init__(self, client):
        self._client = client

    async def send(
        self,
        to: list[str],
        subject: str,
        html: str | None = None,
        text: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        reply_to: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        tags: dict[str, str] | None = None,
    ) -> EmailResult:
        """
        Send an email.

        Args:
            to: List of recipient emails
            subject: Email subject
            html: HTML body (optional if text provided)
            text: Plain text body (optional if html provided)
            from_email: Sender email
            from_name: Sender name
            reply_to: Reply-to email
            cc: CC recipients
            bcc: BCC recipients
            tags: Email tags for tracking

        Returns:
            EmailResult with send status
        """
        if not html and not text:
            raise ValueError("Either html or text must be provided")

        payload = {
            "to": to,
            "subject": subject,
        }

        if html:
            payload["html"] = html
        if text:
            payload["text"] = text
        if from_email:
            payload["from_email"] = from_email
        if from_name:
            payload["from_name"] = from_name
        if reply_to:
            payload["reply_to"] = reply_to
        if cc:
            payload["cc"] = cc
        if bcc:
            payload["bcc"] = bcc
        if tags:
            payload["tags"] = tags

        response = await self._client.post("/v1/email/send", json=payload)

        return EmailResult(
            id=response.get("id", ""),
            status=response.get("status", "sent"),
            to=to,
            subject=subject,
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def get_providers(self) -> list[dict[str, Any]]:
        """Get available email providers."""
        response = await self._client.get("/v1/email/providers")
        return response.get("providers", [])

    async def health(self) -> dict[str, Any]:
        """Check email service health."""
        return await self._client.get("/v1/email/health")

    # =========================================================================
    # Convenience methods (extracted from products)
    # =========================================================================

    async def send_appointment_reminder(
        self,
        to: str,
        name: str,
        date: str,
        time: str,
        location: str,
        professional: str,
        from_name: str = "Sistema de Saúde",
    ) -> EmailResult:
        """
        Send appointment reminder email.

        Extracted from Sistema Pólis.

        Args:
            to: Recipient email
            name: Recipient name
            date: Appointment date (formatted string)
            time: Appointment time
            location: Health unit or clinic name
            professional: Doctor or professional name
            from_name: Sender name

        Returns:
            EmailResult
        """
        html = f"""
        <h2>Lembrete de Consulta</h2>
        <p>Olá, <strong>{name}</strong>!</p>
        <p>Este é um lembrete da sua consulta agendada:</p>
        <ul>
            <li><strong>Data:</strong> {date}</li>
            <li><strong>Horário:</strong> {time}</li>
            <li><strong>Local:</strong> {location}</li>
            <li><strong>Profissional:</strong> {professional}</li>
        </ul>
        <p>Por favor, chegue com 15 minutos de antecedência.</p>
        <p>Leve documento com foto e Cartão SUS.</p>
        <hr>
        <p><small>{from_name}</small></p>
        """
        return await self.send(
            to=[to],
            subject=f"Lembrete: Consulta em {date} às {time}",
            html=html,
            from_name=from_name,
        )

    async def send_vaccination_alert(
        self,
        to: str,
        name: str,
        vaccine_name: str,
        due_date: str,
        locations: list[str],
        from_name: str = "Sistema de Saúde",
    ) -> EmailResult:
        """
        Send vaccination alert email.

        Extracted from Sistema Pólis.

        Args:
            to: Recipient email
            name: Recipient name
            vaccine_name: Name of the vaccine
            due_date: Due date for vaccination
            locations: List of available health units
            from_name: Sender name

        Returns:
            EmailResult
        """
        units_html = "".join([f"<li>{unit}</li>" for unit in locations])
        html = f"""
        <h2>Alerta de Vacinação</h2>
        <p>Olá, <strong>{name}</strong>!</p>
        <p>Você tem uma vacina pendente:</p>
        <ul>
            <li><strong>Vacina:</strong> {vaccine_name}</li>
            <li><strong>Prazo:</strong> {due_date}</li>
        </ul>
        <p>Procure uma das unidades de saúde abaixo:</p>
        <ul>{units_html}</ul>
        <hr>
        <p><small>{from_name}</small></p>
        """
        return await self.send(
            to=[to],
            subject=f"Vacina Pendente: {vaccine_name}",
            html=html,
            from_name=from_name,
        )
