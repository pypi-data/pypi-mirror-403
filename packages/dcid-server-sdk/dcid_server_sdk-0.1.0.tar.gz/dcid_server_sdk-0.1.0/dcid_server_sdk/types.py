"""Type definitions for DCID Server SDK"""

from typing import Optional, Dict, Any, Union, List, Literal, TypedDict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DCIDServerSDKConfig:
    """Configuration options for the DCID Server SDK"""
    api_key: str
    environment: Literal["dev", "prod"] = "prod"
    timeout: int = 30000
    default_headers: Optional[Dict[str, str]] = None
    logger: Optional[Any] = None
    enable_request_logging: bool = False


@dataclass
class InitiateOTPResponse:
    """Response from OTP initiation"""
    otp: Optional[str] = None


@dataclass
class TokenResponse:
    """Response from OTP confirmation or token refresh"""
    access_token: str
    refresh_token: str
    expires_in: Optional[int] = None


@dataclass
class InitiateOTPOptions:
    """Options for initiating OTP registration/sign-in"""
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class ConfirmOTPOptions:
    """Options for confirming OTP"""
    otp: str
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class RefreshTokenOptions:
    """Options for refreshing token"""
    refresh_token: str


@dataclass
class GenerateEncryptionKeyOptions:
    """Options for generating encryption key"""
    did: str
    owner_email: str


@dataclass
class GenerateEncryptionKeyResponse:
    """Response from generating encryption key"""
    encrypted_key: str
    did: str
    owner_email: str
    message: str


@dataclass
class GetEncryptedKeyOptions:
    """Options for getting encrypted key"""
    did: str


@dataclass
class GetEncryptedKeyResponse:
    """Response from getting encrypted key"""
    encrypted_key: str
    did: str
    message: str


@dataclass
class IssueCredentialOptions:
    """Options for issuing a credential"""
    did: str
    credential_name: str
    values: Dict[str, Any]
    owner_email: str


class IssueCredentialResponseSIG(TypedDict):
    """Response from issuing a SIG credential"""
    qr_code_link: str
    schema_type: str


class IssueCredentialResponseMTP(TypedDict):
    """Response from issuing an MTP credential"""
    tx_id: str
    claim_id: str


IssueCredentialResponse = Union[IssueCredentialResponseSIG, IssueCredentialResponseMTP]


@dataclass
class GetCredentialOfferOptions:
    """Options for getting credential offer"""
    claim_id: str
    tx_id: str


@dataclass
class GetCredentialOfferResponse:
    """Response from getting credential offer"""
    status: Literal["published", "pending"]
    tx_id: str
    claim_id: str
    offer_available: bool
    qr_code_link: Optional[str] = None
    offer: Optional[Any] = None
    message: Optional[str] = None


@dataclass
class StoreCredentialOptions:
    """Options for storing a credential to IPFS"""
    did: str
    credential_type: str
    credential: Union[str, Dict[str, Any]]
    encrypted: bool = True


@dataclass
class StoreCredentialResponse:
    """Response from storing a credential to IPFS"""
    cid: str
    did: str
    credential_type: str
    message: str
    encrypted: bool


@dataclass
class RetrieveUserCredentialOptions:
    """Options for retrieving a user credential from IPFS"""
    did: str
    credential_type: str
    include_cid_only: bool = False


@dataclass
class RetrieveUserCredentialResponse:
    """Response from retrieving a user credential from IPFS"""
    cid: str
    did: str
    credential_type: str
    message: str
    credential: Optional[Union[str, Dict[str, Any]]] = None
    encrypted: Optional[bool] = None


@dataclass
class GetAllUserCredentialsOptions:
    """Options for getting all user credentials from IPFS"""
    did: str
    include_credential_data: bool = False


@dataclass
class GetAllUserCredentialsResponse:
    """Response from getting all user credentials from IPFS"""
    credentials: Dict[str, Union[str, Dict[str, Any]]]
    did: str
    count: int
    message: str


@dataclass
class VerifySignInOptions:
    """Options for initiating sign-in verification"""
    credential_name: str


@dataclass
class VerifySignInResponse:
    """Response from initiating sign-in verification"""
    proof_request_url: str
    iden3comm_url: str
    session_id: str


class PostLinkStoreBodyScope(TypedDict, total=False):
    """Scope item for PostLinkStoreBody"""
    id: Union[int, str]
    circuit_id: str
    query: Dict[str, Any]


class PostLinkStoreBody(TypedDict):
    """Body for PostLinkStoreOptions"""
    reason: str
    message: str
    callback_url: str
    scope: List[PostLinkStoreBodyScope]


@dataclass
class PostLinkStoreOptions:
    """Options for storing proof request in link store"""
    id: str
    thid: str
    type: str
    from_did: str
    typ: str
    body: PostLinkStoreBody


@dataclass
class PostLinkStoreResponse:
    """Response from storing proof request in link store"""
    proof_request_url: str
    iden3comm_url: str


@dataclass
class GetLinkStoreOptions:
    """Options for getting proof request from link store"""
    id: str


@dataclass
class GetLinkStoreResponse:
    """Response from getting proof request from link store"""
    id: str
    thid: str
    type: str
    from_did: str
    typ: str
    body: PostLinkStoreBody


@dataclass
class VerifyCallbackOptions:
    """Options for verification callback"""
    session_id: str
    token: str


class VerifyCallbackProof(TypedDict):
    """Proof data in VerifyCallbackResponse"""
    pi_a: List[str]
    pi_b: List[List[str]]
    pi_c: List[str]
    protocol: str
    curve: str


class VerifyCallbackScopeItem(TypedDict):
    """Scope item in VerifyCallbackResponse"""
    id: Union[int, str]
    circuit_id: str
    proof: VerifyCallbackProof
    pub_signals: List[str]


class VerifyCallbackBody(TypedDict):
    """Body data in VerifyCallbackResponse"""
    message: str
    scope: List[VerifyCallbackScopeItem]


@dataclass
class VerifyCallbackResponse:
    """Response from verification callback"""
    id: str
    typ: str
    type: str
    thid: str
    body: VerifyCallbackBody
    from_did: str
    to: str


@dataclass
class ErrorContext:
    """Error context information for debugging"""
    timestamp: str
    url: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    status_text: Optional[str] = None
    response_headers: Optional[Dict[str, Any]] = None
    request_headers: Optional[Dict[str, str]] = None
    request_id: Optional[str] = None
    is_krakend_error: bool = False
    error_source: Optional[Literal["krakend", "backend", "network"]] = None


class DCIDServerSDKError(Exception):
    """Custom error class for SDK errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
        context: Optional[ErrorContext] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response
        self.context = context


class NetworkError(DCIDServerSDKError):
    """Network error (connectivity issues, timeouts, etc.)"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ):
        super().__init__(message, 0, {"code": code}, context)
        self.code = code


class AuthenticationError(DCIDServerSDKError):
    """Authentication error (API-KEY or JWT token issues)"""

    def __init__(
        self,
        message: str,
        is_api_key_error: bool,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
        context: Optional[ErrorContext] = None,
    ):
        super().__init__(message, status_code, response, context)
        self.is_api_key_error = is_api_key_error


class ServerError(DCIDServerSDKError):
    """Server error (backend or gateway errors)"""

    def __init__(
        self,
        message: str,
        is_backend_connectivity_error: bool,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
        context: Optional[ErrorContext] = None,
    ):
        super().__init__(message, status_code, response, context)
        self.is_backend_connectivity_error = is_backend_connectivity_error
