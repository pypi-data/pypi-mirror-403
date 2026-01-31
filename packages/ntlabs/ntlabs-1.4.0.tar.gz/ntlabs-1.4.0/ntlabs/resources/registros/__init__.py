"""
Neural LAB - Registros Module
Integração com centrais de registro brasileiras.

- CRC Nacional (ARPEN) - Registro Civil
- CENSEC (CNB) - Testamentos, Procurações, Escrituras
- e-Notariado (CNB) - Fluxo de Assinaturas Eletrônicas
- ONR/SREI (CNJ) - Registro de Imóveis
"""

from .async_censec import AsyncCENSECResource
from .async_crc import AsyncCRCResource
from .async_enotariado import AsyncENotariadoResource
from .async_onr import AsyncONRResource
from .censec import (
    BuscaEscrituraResult,
    BuscaProcuracaoResult,
    BuscaTestamentoResult,
    CENSECResource,
    EscrituraResult,
    ProcuracaoResult,
    RegistroAtoResult,
    SinalPublicoResult,
    StatusAto,
    TestamentoResult,
    TipoAtoNotarial,
    TipoProcuracao,
    TipoTestamento,
)
from .crc import (
    AverbacaoResult,
    BuscaCertidaoResult,
    CertidaoResult,
    CertificadoInfo,
    CertificadoUploadResult,
    CRCResource,
    LivroDResult,
    ProclamaResult,
    SegundaViaResult,
    StatusCertidao,
    TipoCertidao,
    TipoCertificado,
    VerificacaoResult,
)
from .enotariado import (
    CancelamentoResult,
    ConsultaFluxoResult,
    DownloadResult,
    ENotariadoResource,
    FluxoAssinaturaResult,
    ListaFluxosResult,
    Participante,
    StatusFluxo,
    TipoAssinatura,
    TipoDocumento,
    TipoParticipante,
    UploadResult,
)
from .onr import (
    BuscaPropriedadeResult,
    IndisponibilidadeResult,
    MatriculaInfo,
    OficioResult,
    ONRResource,
    PenhoraResult,
    ProtocoloResult,
    StatusIndisponibilidade,
    StatusProtocolo,
    TipoPenhora,
    TipoProtocolo,
)
from .onr import (
    CertidaoResult as ONRCertidaoResult,
)
from .onr import (
    StatusCertidao as ONRStatusCertidao,
)
from .onr import (
    TipoCertidao as ONRTipoCertidao,
)

__all__ = [
    # CRC Resources
    "CRCResource",
    "AsyncCRCResource",
    # CRC Enums
    "TipoCertidao",
    "StatusCertidao",
    "TipoCertificado",
    # CRC Dataclasses
    "CertidaoResult",
    "BuscaCertidaoResult",
    "VerificacaoResult",
    "ProclamaResult",
    "LivroDResult",
    "SegundaViaResult",
    "AverbacaoResult",
    "CertificadoInfo",
    "CertificadoUploadResult",
    # CENSEC Resources
    "CENSECResource",
    "AsyncCENSECResource",
    # CENSEC Enums
    "TipoTestamento",
    "TipoAtoNotarial",
    "StatusAto",
    "TipoProcuracao",
    # CENSEC Dataclasses
    "TestamentoResult",
    "BuscaTestamentoResult",
    "ProcuracaoResult",
    "BuscaProcuracaoResult",
    "EscrituraResult",
    "BuscaEscrituraResult",
    "SinalPublicoResult",
    "RegistroAtoResult",
    # e-Notariado Resources
    "ENotariadoResource",
    "AsyncENotariadoResource",
    # e-Notariado Enums
    "TipoDocumento",
    "TipoAssinatura",
    "StatusFluxo",
    "TipoParticipante",
    # e-Notariado Dataclasses
    "Participante",
    "UploadResult",
    "FluxoAssinaturaResult",
    "ConsultaFluxoResult",
    "ListaFluxosResult",
    "DownloadResult",
    "CancelamentoResult",
    # ONR/SREI Resources
    "ONRResource",
    "AsyncONRResource",
    # ONR Enums
    "ONRTipoCertidao",
    "ONRStatusCertidao",
    "TipoProtocolo",
    "StatusProtocolo",
    "TipoPenhora",
    "StatusIndisponibilidade",
    # ONR Dataclasses
    "MatriculaInfo",
    "ONRCertidaoResult",
    "BuscaPropriedadeResult",
    "ProtocoloResult",
    "PenhoraResult",
    "IndisponibilidadeResult",
    "OficioResult",
]
