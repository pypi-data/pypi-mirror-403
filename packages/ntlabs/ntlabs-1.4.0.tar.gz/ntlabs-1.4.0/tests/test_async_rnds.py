"""
NTLabs SDK - Async RNDS Resource Tests
Tests for the AsyncRNDSResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
import io
from datetime import datetime
from unittest.mock import AsyncMock

from ntlabs.resources.async_rnds import AsyncRNDSResource
from ntlabs.resources.rnds import RNDSResponse, RNDSStatusResponse, CertificateUploadResult


@pytest.mark.asyncio
class TestAsyncRNDSResource:
    """Tests for AsyncRNDSResource."""

    async def test_initialization(self):
        """AsyncRNDSResource initializes with client."""
        mock_client = AsyncMock()
        rnds = AsyncRNDSResource(mock_client)
        assert rnds._client == mock_client


@pytest.mark.asyncio
class TestAsyncRNDSPrescriptions:
    """Tests for async RNDS prescriptions."""

    async def test_send_prescription(self, rnds_prescription_response):
        """Send prescription to RNDS."""
        mock_client = AsyncMock()
        mock_client.post.return_value = rnds_prescription_response

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.send_prescription(
            prescription_id="pres_123",
            doctor_cns="123456789012345",
            patient_cns="987654321098765",
            cnes="1234567",
            medications=[
                {"name": "Paracetamol", "dosage": "500mg", "quantity": "20"},
            ],
        )

        assert isinstance(result, RNDSResponse)
        assert result.success is True
        assert result.rnds_id == "rnds_abc123"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/rnds/prescription"

    async def test_send_exam_request(self, rnds_prescription_response):
        """Send exam request."""
        mock_client = AsyncMock()
        mock_client.post.return_value = rnds_prescription_response

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.send_exam_request(
            exam_request_id="exam_123",
            doctor_cns="123456789012345",
            patient_cns="987654321098765",
            cnes="1234567",
            exams=[{"code": "AB123", "name": "Hemograma"}],
        )

        assert isinstance(result, RNDSResponse)
        assert result.success is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/rnds/exam-request"

    async def test_send_exam_result(self, rnds_prescription_response):
        """Send exam result."""
        mock_client = AsyncMock()
        mock_client.post.return_value = rnds_prescription_response

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.send_exam_result(
            exam_id="exam_123",
            patient_cns="987654321098765",
            cnes="1234567",
            results=[{"code": "HB", "value": "14.5", "unit": "g/dL"}],
        )

        assert isinstance(result, RNDSResponse)
        assert result.success is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/rnds/exam-result"

    async def test_send_vaccination(self, rnds_prescription_response):
        """Send vaccination record."""
        mock_client = AsyncMock()
        mock_client.post.return_value = rnds_prescription_response

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.send_vaccination(
            patient_cns="987654321098765",
            vaccine_code="12345",
            vaccine_name="Hepatite B",
            dose=1,
            lot_number="ABC123",
            manufacturer="Butantan",
            establishment_cnes="1234567",
            vaccinator_cns="123456789012345",
        )

        assert isinstance(result, RNDSResponse)
        assert result.success is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/rnds/vaccination"

    async def test_notify_disease(self, rnds_prescription_response):
        """Send disease notification."""
        mock_client = AsyncMock()
        mock_client.post.return_value = rnds_prescription_response

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.notify_disease(
            patient_cns="987654321098765",
            cid_code="A90",
            notification_type="dengue",
            municipality_ibge="3106200",
            notifier_cns="123456789012345",
            establishment_cnes="1234567",
        )

        assert isinstance(result, RNDSResponse)
        assert result.success is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/rnds/notify-disease"


@pytest.mark.asyncio
class TestAsyncRNDSQueries:
    """Tests for async RNDS queries."""

    async def test_query_patient_history(self):
        """Query patient history."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "patient_cns": "987654321098765",
            "resources": [{"type": "MedicationRequest", "count": 10}],
        }

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.query_patient_history(
            patient_cns="987654321098765",
            resource_types=["MedicationRequest", "ServiceRequest"],
            start_date="2026-01-01",
            end_date="2026-01-31",
        )

        assert "resources" in result
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/rnds/patient-history"

    async def test_check_status(self):
        """Check document status."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "rnds_id": "rnds_abc123",
            "status": "sent",
            "last_updated": "2026-01-27T20:00:00Z",
            "message": "Document processed",
        }

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.check_status("rnds_abc123")

        assert isinstance(result, RNDSStatusResponse)
        assert result.rnds_id == "rnds_abc123"
        assert result.status.value == "sent"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/rnds/status/rnds_abc123"

    async def test_revoke_document(self, rnds_prescription_response):
        """Revoke document."""
        mock_client = AsyncMock()
        mock_client.post.return_value = rnds_prescription_response

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.revoke_document("rnds_abc123", "Wrong information")

        assert isinstance(result, RNDSResponse)
        assert result.success is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/rnds/revoke"
        assert call_args[1]["json"]["rnds_id"] == "rnds_abc123"
        assert call_args[1]["json"]["reason"] == "Wrong information"

    async def test_get_integration_status(self):
        """Get integration status."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "status": "active",
            "certificates": 2,
            "last_sync": "2026-01-27T19:00:00Z",
        }

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.get_integration_status()

        assert result["status"] == "active"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/rnds/status"


@pytest.mark.asyncio
class TestAsyncRNDSCertificates:
    """Tests for async RNDS certificates."""

    async def test_upload_certificate(self, rnds_certificate_response):
        """Upload certificate."""
        mock_client = AsyncMock()
        mock_client.post.return_value = rnds_certificate_response

        rnds = AsyncRNDSResource(mock_client)
        cert_data = io.BytesIO(b"fake_certificate_data")
        result = await rnds.upload_certificate(
            entity_type="doctor",
            entity_id="doc_123",
            certificate=cert_data,
            password="cert_pass",
            store_password=True,
        )

        assert isinstance(result, CertificateUploadResult)
        assert result.success is True
        assert result.certificate_id == "cert_123"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/rnds/certificates/upload"

    async def test_upload_certificate_failure(self):
        """Upload certificate failure."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"success": False, "error": "Invalid certificate"}

        rnds = AsyncRNDSResource(mock_client)
        cert_data = io.BytesIO(b"fake_certificate_data")
        result = await rnds.upload_certificate(
            entity_type="doctor",
            entity_id="doc_123",
            certificate=cert_data,
            password="cert_pass",
        )

        assert isinstance(result, CertificateUploadResult)
        assert result.success is False
        assert result.error == "Invalid certificate"

    async def test_get_certificates(self):
        """Get certificates."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "certificates": [
                {
                    "id": "cert_123",
                    "type": "e-cpf",
                    "subject_cn": "João Silva",
                    "valid_from": "2026-01-01T00:00:00Z",
                    "valid_until": "2027-01-01T00:00:00Z",
                    "status": "active",
                }
            ]
        }

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.get_certificates("doctor", "doc_123")

        assert len(result) == 1
        assert result[0].id == "cert_123"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/rnds/certificates"

    async def test_has_valid_certificate(self):
        """Check valid certificate."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"valid": True}

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.has_valid_certificate("doctor", "doc_123")

        assert result is True
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/rnds/certificates/validate"

    async def test_revoke_certificate(self):
        """Revoke certificate."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"success": True}

        rnds = AsyncRNDSResource(mock_client)
        result = await rnds.revoke_certificate("cert_123", "Compromised")

        assert result is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/rnds/certificates/revoke"
