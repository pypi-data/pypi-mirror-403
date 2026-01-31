"""
Neural LAB - AI Solutions Platform
Async RNDS Resource - Brazilian National Health Data Network.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from datetime import datetime
from typing import Any, BinaryIO

from .rnds import (
    CertificateInfo,
    CertificateType,
    CertificateUploadResult,
    RNDSResponse,
    RNDSStatus,
    RNDSStatusResponse,
)


class AsyncRNDSResource:
    """Async RNDS integration resource."""

    def __init__(self, client):
        self._client = client

    # =========================================================================
    # RNDS Document Operations
    # =========================================================================

    async def send_prescription(
        self,
        prescription_id: str,
        doctor_cns: str,
        patient_cns: str,
        cnes: str,
        medications: list[dict[str, Any]],
        **kwargs,
    ) -> RNDSResponse:
        """Send prescription to RNDS (MedicationRequest)."""
        response = await self._client.post(
            "/v1/rnds/prescription",
            json={
                "prescription_id": str(prescription_id),
                "doctor_cns": doctor_cns,
                "patient_cns": patient_cns,
                "cnes": cnes,
                "medications": medications,
                **kwargs,
            },
        )

        return RNDSResponse(
            success=response.get("success", False),
            mock=response.get("mock", True),
            message=response.get("message", ""),
            rnds_id=response.get("rnds_id"),
            error_code=response.get("error_code"),
            error_details=response.get("error_details"),
            cost_brl=response.get("cost_brl", 0.0),
        )

    async def send_exam_request(
        self,
        exam_request_id: str,
        doctor_cns: str,
        patient_cns: str,
        cnes: str,
        exams: list[dict[str, Any]],
        **kwargs,
    ) -> RNDSResponse:
        """Send exam request to RNDS (ServiceRequest)."""
        response = await self._client.post(
            "/v1/rnds/exam-request",
            json={
                "exam_request_id": str(exam_request_id),
                "doctor_cns": doctor_cns,
                "patient_cns": patient_cns,
                "cnes": cnes,
                "exams": exams,
                **kwargs,
            },
        )

        return RNDSResponse(
            success=response.get("success", False),
            mock=response.get("mock", True),
            message=response.get("message", ""),
            rnds_id=response.get("rnds_id"),
            error_code=response.get("error_code"),
            error_details=response.get("error_details"),
            cost_brl=response.get("cost_brl", 0.0),
        )

    async def send_exam_result(
        self,
        exam_id: str,
        patient_cns: str,
        cnes: str,
        results: list[dict[str, Any]],
        performer_cns: str | None = None,
        **kwargs,
    ) -> RNDSResponse:
        """Send exam result to RNDS (DiagnosticReport)."""
        response = await self._client.post(
            "/v1/rnds/exam-result",
            json={
                "exam_id": str(exam_id),
                "patient_cns": patient_cns,
                "cnes": cnes,
                "results": results,
                "performer_cns": performer_cns,
                **kwargs,
            },
        )

        return RNDSResponse(
            success=response.get("success", False),
            mock=response.get("mock", True),
            message=response.get("message", ""),
            rnds_id=response.get("rnds_id"),
            error_code=response.get("error_code"),
            error_details=response.get("error_details"),
            cost_brl=response.get("cost_brl", 0.0),
        )

    async def send_vaccination(
        self,
        patient_cns: str,
        vaccine_code: str,
        vaccine_name: str,
        dose: int,
        lot_number: str,
        manufacturer: str,
        establishment_cnes: str,
        vaccinator_cns: str,
        vaccination_date: str | None = None,
        **kwargs,
    ) -> RNDSResponse:
        """Send vaccination record to RNDS (Immunization)."""
        response = await self._client.post(
            "/v1/rnds/vaccination",
            json={
                "patient_cns": patient_cns,
                "vaccine_code": vaccine_code,
                "vaccine_name": vaccine_name,
                "dose": dose,
                "lot_number": lot_number,
                "manufacturer": manufacturer,
                "establishment_cnes": establishment_cnes,
                "vaccinator_cns": vaccinator_cns,
                "vaccination_date": vaccination_date,
                **kwargs,
            },
        )

        return RNDSResponse(
            success=response.get("success", False),
            mock=response.get("mock", True),
            message=response.get("message", ""),
            rnds_id=response.get("rnds_id"),
            error_code=response.get("error_code"),
            error_details=response.get("error_details"),
            cost_brl=response.get("cost_brl", 0.0),
        )

    async def notify_disease(
        self,
        patient_cns: str,
        cid_code: str,
        notification_type: str,
        municipality_ibge: str,
        notifier_cns: str,
        establishment_cnes: str,
        onset_date: str | None = None,
        symptoms: list[str] | None = None,
        **kwargs,
    ) -> RNDSResponse:
        """Send compulsory disease notification to RNDS (Condition)."""
        response = await self._client.post(
            "/v1/rnds/notify-disease",
            json={
                "patient_cns": patient_cns,
                "cid_code": cid_code,
                "notification_type": notification_type,
                "municipality_ibge": municipality_ibge,
                "notifier_cns": notifier_cns,
                "establishment_cnes": establishment_cnes,
                "onset_date": onset_date,
                "symptoms": symptoms or [],
                **kwargs,
            },
        )

        return RNDSResponse(
            success=response.get("success", False),
            mock=response.get("mock", True),
            message=response.get("message", ""),
            rnds_id=response.get("rnds_id"),
            error_code=response.get("error_code"),
            error_details=response.get("error_details"),
            cost_brl=response.get("cost_brl", 0.0),
        )

    async def query_patient_history(
        self,
        patient_cns: str,
        resource_types: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Query patient history from RNDS."""
        response = await self._client.post(
            "/v1/rnds/patient-history",
            json={
                "patient_cns": patient_cns,
                "resource_types": resource_types or [],
                "start_date": start_date,
                "end_date": end_date,
                **kwargs,
            },
        )
        return response

    async def check_status(self, rnds_id: str) -> RNDSStatusResponse:
        """Check status of a document in RNDS."""
        response = await self._client.get(f"/v1/rnds/status/{rnds_id}")

        return RNDSStatusResponse(
            rnds_id=rnds_id,
            status=RNDSStatus(response.get("status", "not_sent")),
            last_updated=datetime.fromisoformat(
                response.get("last_updated", datetime.now().isoformat())
            ),
            message=response.get("message"),
        )

    async def revoke_document(self, rnds_id: str, reason: str) -> RNDSResponse:
        """Revoke a document in RNDS."""
        response = await self._client.post(
            "/v1/rnds/revoke",
            json={"rnds_id": rnds_id, "reason": reason},
        )

        return RNDSResponse(
            success=response.get("success", False),
            mock=response.get("mock", True),
            message=response.get("message", ""),
            rnds_id=rnds_id,
            error_code=response.get("error_code"),
            error_details=response.get("error_details"),
            cost_brl=response.get("cost_brl", 0.0),
        )

    async def get_integration_status(self) -> dict[str, Any]:
        """Get current RNDS integration status."""
        return await self._client.get("/v1/rnds/status")

    # =========================================================================
    # Certificate Management
    # =========================================================================

    async def upload_certificate(
        self,
        entity_type: str,
        entity_id: str,
        certificate: BinaryIO,
        password: str,
        store_password: bool = False,
    ) -> CertificateUploadResult:
        """Upload ICP-Brasil certificate for RNDS integration."""
        response = await self._client.post(
            "/v1/rnds/certificates/upload",
            files={"certificate": certificate},
            data={
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "password": password,
                "store_password": str(store_password).lower(),
            },
        )

        if not response.get("success"):
            return CertificateUploadResult(
                success=False,
                error=response.get("error", "Upload failed"),
            )

        cert_data = response.get("certificate", {})
        return CertificateUploadResult(
            success=True,
            certificate_id=cert_data.get("id"),
            certificate_info=CertificateInfo(
                id=cert_data.get("id", ""),
                certificate_type=CertificateType(cert_data.get("type", "e-cpf")),
                subject_cn=cert_data.get("subject_cn", ""),
                subject_cpf_cnpj=cert_data.get("subject_cpf_cnpj"),
                issuer_cn=cert_data.get("issuer_cn", ""),
                valid_from=datetime.fromisoformat(
                    cert_data.get("valid_from", datetime.now().isoformat())
                ),
                valid_until=datetime.fromisoformat(
                    cert_data.get("valid_until", datetime.now().isoformat())
                ),
                status=cert_data.get("status", "active"),
                rnds_validated=cert_data.get("rnds_validated", False),
                sncr_validated=cert_data.get("sncr_validated", False),
            ),
        )

    async def get_certificates(
        self,
        entity_type: str,
        entity_id: str,
    ) -> list[CertificateInfo]:
        """Get certificates for an entity."""
        response = await self._client.get(
            "/v1/rnds/certificates",
            params={"entity_type": entity_type, "entity_id": str(entity_id)},
        )

        return [
            CertificateInfo(
                id=cert.get("id", ""),
                certificate_type=CertificateType(cert.get("type", "e-cpf")),
                subject_cn=cert.get("subject_cn", ""),
                subject_cpf_cnpj=cert.get("subject_cpf_cnpj"),
                issuer_cn=cert.get("issuer_cn", ""),
                valid_from=datetime.fromisoformat(
                    cert.get("valid_from", datetime.now().isoformat())
                ),
                valid_until=datetime.fromisoformat(
                    cert.get("valid_until", datetime.now().isoformat())
                ),
                status=cert.get("status", "active"),
                rnds_validated=cert.get("rnds_validated", False),
                sncr_validated=cert.get("sncr_validated", False),
            )
            for cert in response.get("certificates", [])
        ]

    async def has_valid_certificate(
        self,
        entity_type: str,
        entity_id: str,
        certificate_type: str | None = None,
    ) -> bool:
        """Check if entity has a valid active certificate."""
        response = await self._client.get(
            "/v1/rnds/certificates/validate",
            params={
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "certificate_type": certificate_type,
            },
        )
        return response.get("valid", False)

    async def revoke_certificate(self, certificate_id: str, reason: str) -> bool:
        """Revoke a certificate."""
        response = await self._client.post(
            "/v1/rnds/certificates/revoke",
            json={"certificate_id": str(certificate_id), "reason": reason},
        )
        return response.get("success", False)
