"""
NTLabs SDK - RNDS Resource Tests
Tests for the RNDSResource class (Brazilian National Health Data Network).

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import io

from ntlabs.resources.rnds import (
    CertificateInfo,
    CertificateType,
    CertificateUploadResult,
    RNDSResource,
    RNDSResponse,
    RNDSStatus,
    RNDSStatusResponse,
)


class TestRNDSResponse:
    """Tests for RNDSResponse dataclass."""

    def test_create_success_response(self):
        """Create success response."""
        response = RNDSResponse(
            success=True,
            mock=False,
            message="Prescription sent successfully",
            rnds_id="rnds-123",
            cost_brl=0.05,
        )
        assert response.success is True
        assert response.rnds_id == "rnds-123"

    def test_create_error_response(self):
        """Create error response."""
        response = RNDSResponse(
            success=False,
            mock=False,
            message="Failed to send",
            error_code="INVALID_CNS",
            error_details="Patient CNS not found",
        )
        assert response.success is False
        assert response.error_code == "INVALID_CNS"


class TestRNDSStatus:
    """Tests for RNDSStatus enum."""

    def test_status_values(self):
        """Status enum has expected values."""
        assert RNDSStatus.NOT_SENT == "not_sent"
        assert RNDSStatus.PENDING == "pending"
        assert RNDSStatus.SENT == "sent"
        assert RNDSStatus.ERROR == "error"
        assert RNDSStatus.MOCK == "mock"


class TestCertificateType:
    """Tests for CertificateType enum."""

    def test_certificate_types(self):
        """Certificate type enum values."""
        assert CertificateType.E_CPF == "e-cpf"
        assert CertificateType.E_CNPJ == "e-cnpj"


class TestRNDSResource:
    """Tests for RNDSResource."""

    def test_initialization(self, mock_client):
        """RNDSResource initializes with client."""
        rnds = RNDSResource(mock_client)
        assert rnds._client == mock_client

    def test_send_prescription(self, mock_client, mock_response):
        """Send prescription to RNDS."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "success": True,
                "mock": False,
                "message": "Prescription sent",
                "rnds_id": "rnds-rx-123",
                "cost_brl": 0.05,
            }
        )

        result = mock_client.rnds.send_prescription(
            prescription_id="presc-123",
            doctor_cns="123456789012345",
            patient_cns="987654321098765",
            cnes="1234567",
            medications=[{"nome": "Dipirona", "dosagem": "500mg", "quantidade": 20}],
        )

        assert isinstance(result, RNDSResponse)
        assert result.success is True
        assert result.rnds_id == "rnds-rx-123"

    def test_send_exam_request(self, mock_client, mock_response):
        """Send exam request to RNDS."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "success": True,
                "mock": False,
                "message": "Exam request sent",
                "rnds_id": "rnds-exam-123",
                "cost_brl": 0.05,
            }
        )

        result = mock_client.rnds.send_exam_request(
            exam_request_id="exam-123",
            doctor_cns="123456789012345",
            patient_cns="987654321098765",
            cnes="1234567",
            exams=[{"codigo": "40301630", "descricao": "Hemograma completo"}],
        )

        assert isinstance(result, RNDSResponse)
        assert result.success is True

    def test_send_exam_result(self, mock_client, mock_response):
        """Send exam result to RNDS."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "success": True,
                "mock": False,
                "message": "Exam result sent",
                "rnds_id": "rnds-result-123",
            }
        )

        result = mock_client.rnds.send_exam_result(
            exam_id="exam-123",
            patient_cns="987654321098765",
            cnes="1234567",
            results=[{"parametro": "Hemoglobina", "valor": 14.5, "unidade": "g/dL"}],
        )

        assert isinstance(result, RNDSResponse)
        assert result.success is True

    def test_send_vaccination(self, mock_client, mock_response):
        """Send vaccination record to RNDS."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "success": True,
                "mock": False,
                "message": "Vaccination recorded",
                "rnds_id": "rnds-vac-123",
            }
        )

        result = mock_client.rnds.send_vaccination(
            patient_cns="987654321098765",
            vaccine_code="86",
            vaccine_name="COVID-19 Pfizer",
            dose=1,
            lot_number="EF1234",
            manufacturer="Pfizer",
            establishment_cnes="1234567",
            vaccinator_cns="123456789012345",
        )

        assert isinstance(result, RNDSResponse)
        assert result.success is True

    def test_notify_disease(self, mock_client, mock_response):
        """Notify disease to RNDS."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "success": True,
                "mock": False,
                "message": "Disease notification sent",
                "rnds_id": "rnds-notif-123",
            }
        )

        result = mock_client.rnds.notify_disease(
            patient_cns="987654321098765",
            cid_code="A90",
            notification_type="compulsory",
            municipality_ibge="3106200",
            notifier_cns="123456789012345",
            establishment_cnes="1234567",
            symptoms=["febre", "cefaleia"],
        )

        assert isinstance(result, RNDSResponse)
        assert result.success is True

    def test_query_patient_history(self, mock_client, mock_response):
        """Query patient history."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "patient_cns": "987654321098765",
                "records": [
                    {"type": "Immunization", "date": "2024-01-15"},
                    {"type": "MedicationRequest", "date": "2024-02-20"},
                ],
                "total": 2,
            }
        )

        result = mock_client.rnds.query_patient_history(
            patient_cns="987654321098765",
            resource_types=["Immunization", "MedicationRequest"],
        )

        assert "records" in result
        assert len(result["records"]) == 2

    def test_check_status(self, mock_client, mock_response):
        """Check document status."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "status": "sent",
                "last_updated": "2026-01-25T10:00:00",
                "message": "Document processed",
            }
        )

        result = mock_client.rnds.check_status("rnds-123")

        assert isinstance(result, RNDSStatusResponse)
        assert result.status == RNDSStatus.SENT
        assert result.rnds_id == "rnds-123"

    def test_revoke_document(self, mock_client, mock_response):
        """Revoke RNDS document."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "success": True,
                "mock": False,
                "message": "Document revoked",
            }
        )

        result = mock_client.rnds.revoke_document(
            rnds_id="rnds-123",
            reason="Prescription error",
        )

        assert isinstance(result, RNDSResponse)
        assert result.success is True

    def test_get_integration_status(self, mock_client, mock_response):
        """Get RNDS integration status."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "status": "connected",
                "environment": "production",
                "certificate_valid": True,
            }
        )

        result = mock_client.rnds.get_integration_status()

        assert result["status"] == "connected"

    def test_upload_certificate(self, mock_client, mock_response):
        """Upload ICP-Brasil certificate."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "success": True,
                "certificate": {
                    "id": "cert-123",
                    "type": "e-cnpj",
                    "subject_cn": "CLINICA XYZ LTDA",
                    "subject_cpf_cnpj": "12345678000190",
                    "issuer_cn": "AC CERTISIGN",
                    "valid_from": "2025-01-01T00:00:00",
                    "valid_until": "2028-01-01T00:00:00",
                    "status": "active",
                    "rnds_validated": True,
                    "sncr_validated": False,
                },
            }
        )

        cert_file = io.BytesIO(b"fake pfx content")
        result = mock_client.rnds.upload_certificate(
            entity_type="clinic",
            entity_id="clinic-123",
            certificate=cert_file,
            password="secret123",
        )

        assert isinstance(result, CertificateUploadResult)
        assert result.success is True
        assert result.certificate_id == "cert-123"

    def test_upload_certificate_failure(self, mock_client, mock_response):
        """Handle certificate upload failure."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "success": False,
                "error": "Invalid certificate password",
            }
        )

        cert_file = io.BytesIO(b"fake pfx content")
        result = mock_client.rnds.upload_certificate(
            entity_type="clinic",
            entity_id="clinic-123",
            certificate=cert_file,
            password="wrong_password",
        )

        assert result.success is False
        assert result.error == "Invalid certificate password"

    def test_get_certificates(self, mock_client, mock_response):
        """Get entity certificates."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "certificates": [
                    {
                        "id": "cert-1",
                        "type": "e-cnpj",
                        "subject_cn": "CLINICA XYZ",
                        "issuer_cn": "AC CERTISIGN",
                        "valid_from": "2025-01-01T00:00:00",
                        "valid_until": "2028-01-01T00:00:00",
                        "status": "active",
                        "rnds_validated": True,
                        "sncr_validated": False,
                    }
                ]
            }
        )

        result = mock_client.rnds.get_certificates(
            entity_type="clinic",
            entity_id="clinic-123",
        )

        assert len(result) == 1
        assert isinstance(result[0], CertificateInfo)
        assert result[0].certificate_type == CertificateType.E_CNPJ

    def test_has_valid_certificate(self, mock_client, mock_response):
        """Check if entity has valid certificate."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "valid": True,
            }
        )

        result = mock_client.rnds.has_valid_certificate(
            entity_type="clinic",
            entity_id="clinic-123",
        )

        assert result is True

    def test_has_no_valid_certificate(self, mock_client, mock_response):
        """Check when entity has no valid certificate."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "valid": False,
            }
        )

        result = mock_client.rnds.has_valid_certificate(
            entity_type="doctor",
            entity_id="doctor-123",
        )

        assert result is False

    def test_revoke_certificate(self, mock_client, mock_response):
        """Revoke certificate."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "success": True,
            }
        )

        result = mock_client.rnds.revoke_certificate(
            certificate_id="cert-123",
            reason="Certificate compromised",
        )

        assert result is True

    def test_empty_response_handling(self, mock_client, mock_response):
        """Handle empty responses gracefully."""
        mock_client._mock_http.request.return_value = mock_response({})

        # Send prescription
        result = mock_client.rnds.send_prescription(
            prescription_id="presc-123",
            doctor_cns="123",
            patient_cns="456",
            cnes="789",
            medications=[],
        )
        assert result.success is False
        assert result.mock is True

        # Get certificates
        result = mock_client.rnds.get_certificates(
            entity_type="clinic",
            entity_id="clinic-123",
        )
        assert result == []
