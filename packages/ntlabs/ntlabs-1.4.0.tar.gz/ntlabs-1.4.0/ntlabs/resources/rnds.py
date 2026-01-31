"""
Neural LAB - AI Solutions Platform
RNDS Resource - Brazilian National Health Data Network integration.

RNDS (Rede Nacional de Dados em Saude) is Brazil's national health data network,
managed by DATASUS. This resource provides:
- Send prescriptions (MedicationRequest)
- Send exam requests (ServiceRequest)
- Send vaccinations (Immunization) - for Polis
- Disease notifications (Condition) - for Polis
- Query patient history
- Certificate management (ICP-Brasil)

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, BinaryIO

from ..base import DataclassMixin


class RNDSStatus(str, Enum):
    """RNDS document status."""

    NOT_SENT = "not_sent"
    PENDING = "pending"
    SENT = "sent"
    ERROR = "error"
    MOCK = "mock"


class CertificateType(str, Enum):
    """ICP-Brasil certificate types."""

    E_CPF = "e-cpf"
    E_CNPJ = "e-cnpj"


@dataclass
class RNDSResponse(DataclassMixin):
    """Response from RNDS operations."""

    success: bool
    mock: bool
    message: str
    rnds_id: str | None = None
    error_code: str | None = None
    error_details: str | None = None
    cost_brl: float = 0.0


@dataclass
class RNDSStatusResponse(DataclassMixin):
    """Response for RNDS status check."""

    rnds_id: str
    status: RNDSStatus
    last_updated: datetime
    message: str | None = None


@dataclass
class CertificateInfo(DataclassMixin):
    """ICP-Brasil certificate information."""

    id: str
    certificate_type: CertificateType
    subject_cn: str
    subject_cpf_cnpj: str | None
    issuer_cn: str
    valid_from: datetime
    valid_until: datetime
    status: str
    rnds_validated: bool
    sncr_validated: bool


@dataclass
class CertificateUploadResult(DataclassMixin):
    """Result of certificate upload operation."""

    success: bool
    certificate_id: str | None = None
    certificate_info: CertificateInfo | None = None
    error: str | None = None


class RNDSResource:
    """
    RNDS (Rede Nacional de Dados em Saude) integration resource.

    Provides access to Brazil's national health data network for:
    - Hipocrates: Prescriptions, exam requests
    - Polis: Vaccinations, disease notifications, surveillance

    Usage:
        # Send prescription
        result = client.rnds.send_prescription(
            prescription_id="uuid",
            doctor_cns="...",
            patient_cns="...",
            cnes="...",
            medications=[...]
        )

        # Send vaccination (Polis)
        result = client.rnds.send_vaccination(
            patient_cns="...",
            vaccine_code="...",
            dose=1,
            establishment_cnes="...",
            vaccinator_cns="..."
        )

        # Notify disease (Polis)
        result = client.rnds.notify_disease(
            patient_cns="...",
            cid_code="A90",
            notification_type="compulsory",
            municipality_ibge="...",
            notifier_cns="..."
        )

        # Query patient history
        history = client.rnds.query_patient_history(patient_cns="...")

        # Manage certificates
        result = client.rnds.upload_certificate(
            entity_type="clinic",
            entity_id="uuid",
            certificate=pfx_bytes,
            password="..."
        )
    """

    def __init__(self, client):
        self._client = client

    # =========================================================================
    # RNDS Document Operations
    # =========================================================================

    def send_prescription(
        self,
        prescription_id: str,
        doctor_cns: str,
        patient_cns: str,
        cnes: str,
        medications: list[dict[str, Any]],
        **kwargs,
    ) -> RNDSResponse:
        """
        Send prescription to RNDS (MedicationRequest).

        Args:
            prescription_id: UUID of the prescription
            doctor_cns: Doctor's CNS (Cartao Nacional de Saude)
            patient_cns: Patient's CNS
            cnes: CNES code of the establishment
            medications: List of medications with dosage
            **kwargs: Additional FHIR MedicationRequest fields

        Returns:
            RNDSResponse with success status and RNDS ID
        """
        response = self._client.post(
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

    def send_exam_request(
        self,
        exam_request_id: str,
        doctor_cns: str,
        patient_cns: str,
        cnes: str,
        exams: list[dict[str, Any]],
        **kwargs,
    ) -> RNDSResponse:
        """
        Send exam request to RNDS (ServiceRequest).

        Args:
            exam_request_id: UUID of the exam request
            doctor_cns: Doctor's CNS
            patient_cns: Patient's CNS
            cnes: CNES code of the establishment
            exams: List of exams requested
            **kwargs: Additional FHIR ServiceRequest fields

        Returns:
            RNDSResponse with success status and RNDS ID
        """
        response = self._client.post(
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

    def send_exam_result(
        self,
        exam_id: str,
        patient_cns: str,
        cnes: str,
        results: list[dict[str, Any]],
        performer_cns: str | None = None,
        **kwargs,
    ) -> RNDSResponse:
        """
        Send exam result to RNDS (DiagnosticReport).

        Args:
            exam_id: UUID of the exam
            patient_cns: Patient's CNS
            cnes: CNES code of the laboratory
            results: List of exam results
            performer_cns: Analyst's CNS (optional)
            **kwargs: Additional FHIR DiagnosticReport fields

        Returns:
            RNDSResponse with success status and RNDS ID
        """
        response = self._client.post(
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

    def send_vaccination(
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
        """
        Send vaccination record to RNDS (Immunization).

        For use by Polis (government health system).

        Args:
            patient_cns: Patient's CNS
            vaccine_code: Vaccine code (SIPNI)
            vaccine_name: Vaccine name
            dose: Dose number (1, 2, 3, etc.)
            lot_number: Vaccine lot number
            manufacturer: Vaccine manufacturer
            establishment_cnes: CNES of vaccination site
            vaccinator_cns: Vaccinator's CNS
            vaccination_date: Date of vaccination (ISO format)
            **kwargs: Additional FHIR Immunization fields

        Returns:
            RNDSResponse with success status and RNDS ID
        """
        response = self._client.post(
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

    def notify_disease(
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
        """
        Send compulsory disease notification to RNDS (Condition).

        For use by Polis (epidemiological surveillance).

        Args:
            patient_cns: Patient's CNS
            cid_code: CID-10 code of the disease
            notification_type: Type (compulsory, immediate, weekly)
            municipality_ibge: IBGE code of the municipality
            notifier_cns: Notifier's CNS (doctor/nurse)
            establishment_cnes: CNES of notifying establishment
            onset_date: Date of symptom onset (ISO format)
            symptoms: List of symptoms
            **kwargs: Additional FHIR Condition fields

        Returns:
            RNDSResponse with success status and RNDS ID
        """
        response = self._client.post(
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

    def query_patient_history(
        self,
        patient_cns: str,
        resource_types: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Query patient history from RNDS.

        Args:
            patient_cns: Patient's CNS
            resource_types: FHIR resource types to query
                (MedicationRequest, Immunization, DiagnosticReport, etc.)
            start_date: Filter start date (ISO format)
            end_date: Filter end date (ISO format)
            **kwargs: Additional query parameters

        Returns:
            Patient history data
        """
        response = self._client.post(
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

    def check_status(self, rnds_id: str) -> RNDSStatusResponse:
        """
        Check status of a document in RNDS.

        Args:
            rnds_id: RNDS document ID

        Returns:
            RNDSStatusResponse with current status
        """
        response = self._client.get(
            f"/v1/rnds/status/{rnds_id}",
        )

        return RNDSStatusResponse(
            rnds_id=rnds_id,
            status=RNDSStatus(response.get("status", "not_sent")),
            last_updated=datetime.fromisoformat(
                response.get("last_updated", datetime.now().isoformat())
            ),
            message=response.get("message"),
        )

    def revoke_document(self, rnds_id: str, reason: str) -> RNDSResponse:
        """
        Revoke a document in RNDS.

        Args:
            rnds_id: RNDS document ID to revoke
            reason: Reason for revocation

        Returns:
            RNDSResponse with revocation status
        """
        response = self._client.post(
            "/v1/rnds/revoke",
            json={
                "rnds_id": rnds_id,
                "reason": reason,
            },
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

    def get_integration_status(self) -> dict[str, Any]:
        """
        Get current RNDS integration status.

        Returns:
            Dictionary with integration status information
        """
        response = self._client.get("/v1/rnds/status")
        return response

    # =========================================================================
    # Certificate Management
    # =========================================================================

    def upload_certificate(
        self,
        entity_type: str,
        entity_id: str,
        certificate: BinaryIO,
        password: str,
        store_password: bool = False,
    ) -> CertificateUploadResult:
        """
        Upload ICP-Brasil certificate for RNDS integration.

        Args:
            entity_type: 'clinic' (E-CNPJ) or 'doctor' (E-CPF)
            entity_id: UUID of the clinic or doctor
            certificate: PKCS#12 (.pfx) certificate file
            password: Certificate password
            store_password: Whether to store encrypted password

        Returns:
            CertificateUploadResult with certificate info
        """
        response = self._client.post(
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

    def get_certificates(
        self,
        entity_type: str,
        entity_id: str,
    ) -> list[CertificateInfo]:
        """
        Get certificates for an entity.

        Args:
            entity_type: 'clinic' or 'doctor'
            entity_id: UUID of the entity

        Returns:
            List of certificate info
        """
        response = self._client.get(
            "/v1/rnds/certificates",
            params={
                "entity_type": entity_type,
                "entity_id": str(entity_id),
            },
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

    def has_valid_certificate(
        self,
        entity_type: str,
        entity_id: str,
        certificate_type: str | None = None,
    ) -> bool:
        """
        Check if entity has a valid active certificate.

        Args:
            entity_type: 'clinic' or 'doctor'
            entity_id: UUID of the entity
            certificate_type: Optional type filter ('e-cpf' or 'e-cnpj')

        Returns:
            True if valid certificate exists
        """
        response = self._client.get(
            "/v1/rnds/certificates/validate",
            params={
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "certificate_type": certificate_type,
            },
        )

        return response.get("valid", False)

    def revoke_certificate(
        self,
        certificate_id: str,
        reason: str,
    ) -> bool:
        """
        Revoke a certificate.

        Args:
            certificate_id: UUID of the certificate
            reason: Reason for revocation

        Returns:
            True if successful
        """
        response = self._client.post(
            "/v1/rnds/certificates/revoke",
            json={
                "certificate_id": str(certificate_id),
                "reason": reason,
            },
        )

        return response.get("success", False)
