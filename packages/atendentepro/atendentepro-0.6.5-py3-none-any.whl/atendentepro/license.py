# -*- coding: utf-8 -*-
"""
AtendentePro - Sistema de Licenciamento

Este módulo gerencia a validação de tokens de acesso para uso da biblioteca.

Uso:
    from atendentepro import activate
    
    # Ativar com token
    activate("seu-token-de-acesso")
    
    # Agora pode usar a biblioteca normalmente
    from atendentepro import create_standard_network
"""

import os
import hashlib
import hmac
import time
import json
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

# Chave secreta para validação local (pode ser alterada em produção)
_SECRET_KEY = "atendentepro-bemonkai-2024"

# Estado global de ativação
_license_state = {
    "activated": False,
    "token": None,
    "expiration": None,
    "features": [],
    "organization": None,
}


@dataclass
class LicenseInfo:
    """Informações da licença ativa."""
    valid: bool
    organization: Optional[str] = None
    expiration: Optional[str] = None
    features: list = None
    message: str = ""
    
    def __post_init__(self):
        if self.features is None:
            self.features = []


class LicenseError(Exception):
    """Erro de licenciamento."""
    pass


class LicenseNotActivatedError(LicenseError):
    """Biblioteca não foi ativada com um token válido."""
    
    def __init__(self):
        super().__init__(
            "\n\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║          ATENDENTEPRO - LICENÇA NÃO ATIVADA                  ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║                                                              ║\n"
            "║  A biblioteca AtendentePro requer ativação para uso.        ║\n"
            "║                                                              ║\n"
            "║  Para ativar, use:                                          ║\n"
            "║                                                              ║\n"
            "║    from atendentepro import activate                        ║\n"
            "║    activate('seu-token-de-acesso')                          ║\n"
            "║                                                              ║\n"
            "║  Ou defina a variável de ambiente:                          ║\n"
            "║                                                              ║\n"
            "║    export ATENDENTEPRO_LICENSE_KEY='seu-token'              ║\n"
            "║                                                              ║\n"
            "║  Para obter um token, entre em contato:                     ║\n"
            "║  📧 contato@monkai.com.br                                    ║\n"
            "║                                                              ║\n"
            "╚══════════════════════════════════════════════════════════════╝\n"
        )


class LicenseExpiredError(LicenseError):
    """Token de licença expirado."""
    
    def __init__(self, expiration: str):
        super().__init__(
            f"\n\n"
            f"╔══════════════════════════════════════════════════════════════╗\n"
            f"║          ATENDENTEPRO - LICENÇA EXPIRADA                    ║\n"
            f"╠══════════════════════════════════════════════════════════════╣\n"
            f"║                                                              ║\n"
            f"║  Sua licença expirou em: {expiration:<36}║\n"
            f"║                                                              ║\n"
            f"║  Para renovar, entre em contato:                            ║\n"
            f"║  📧 contato@monkai.com.br                                    ║\n"
            f"║                                                              ║\n"
            f"╚══════════════════════════════════════════════════════════════╝\n"
        )


class InvalidTokenError(LicenseError):
    """Token inválido."""
    
    def __init__(self):
        super().__init__(
            "\n\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║          ATENDENTEPRO - TOKEN INVÁLIDO                       ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║                                                              ║\n"
            "║  O token fornecido não é válido.                            ║\n"
            "║                                                              ║\n"
            "║  Verifique se o token está correto ou entre em contato:     ║\n"
            "║  📧 contato@monkai.com.br                                    ║\n"
            "║                                                              ║\n"
            "╚══════════════════════════════════════════════════════════════╝\n"
        )


def _generate_token(
    organization: str,
    expiration_timestamp: int = None,
    features: list = None,
    secret_key: str = None
) -> str:
    """
    Gera um token de licença.
    
    USO INTERNO - Para gerar tokens para clientes.
    
    Args:
        organization: Nome da organização
        expiration_timestamp: Unix timestamp de expiração (None = sem expiração)
        features: Lista de features habilitadas
        secret_key: Chave secreta para assinatura
        
    Returns:
        Token codificado em base64
    """
    import base64
    
    if secret_key is None:
        secret_key = _SECRET_KEY
    
    if features is None:
        features = ["full"]
    
    # Payload do token
    payload = {
        "org": organization,
        "exp": expiration_timestamp,
        "feat": features,
        "v": 1,  # versão do token
    }
    
    # Serializar payload
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()
    
    # Gerar assinatura
    signature = hmac.new(
        secret_key.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    
    # Token final: payload.signature
    token = f"ATP_{payload_b64}.{signature}"
    
    return token


def _validate_token_local(token: str, secret_key: str = None) -> LicenseInfo:
    """
    Valida um token localmente.
    
    Args:
        token: Token de licença
        secret_key: Chave secreta para validação
        
    Returns:
        LicenseInfo com informações da validação
    """
    import base64
    
    if secret_key is None:
        secret_key = _SECRET_KEY
    
    try:
        # Verificar formato
        if not token.startswith("ATP_"):
            return LicenseInfo(valid=False, message="Formato de token inválido")
        
        token_body = token[4:]  # Remover "ATP_"
        
        if "." not in token_body:
            return LicenseInfo(valid=False, message="Token malformado")
        
        payload_b64, signature = token_body.rsplit(".", 1)
        
        # Verificar assinatura
        expected_signature = hmac.new(
            secret_key.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        if not hmac.compare_digest(signature, expected_signature):
            return LicenseInfo(valid=False, message="Assinatura inválida")
        
        # Decodificar payload
        try:
            payload_json = base64.urlsafe_b64decode(payload_b64).decode()
            payload = json.loads(payload_json)
        except Exception:
            return LicenseInfo(valid=False, message="Payload inválido")
        
        # Verificar expiração
        expiration = payload.get("exp")
        expiration_str = None
        
        if expiration is not None:
            expiration_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expiration))
            if time.time() > expiration:
                return LicenseInfo(
                    valid=False,
                    expiration=expiration_str,
                    message="Token expirado"
                )
        
        # Token válido
        return LicenseInfo(
            valid=True,
            organization=payload.get("org", "Unknown"),
            expiration=expiration_str,
            features=payload.get("feat", ["full"]),
            message="Token válido"
        )
        
    except Exception as e:
        return LicenseInfo(valid=False, message=f"Erro na validação: {str(e)}")


def _validate_token_online(token: str, api_url: str = None) -> LicenseInfo:
    """
    Valida um token online através de API.
    
    Args:
        token: Token de licença
        api_url: URL da API de validação
        
    Returns:
        LicenseInfo com informações da validação
    """
    # Implementação futura para validação online
    # Por enquanto, faz validação local
    return _validate_token_local(token)


def activate(
    token: str = None,
    validate_online: bool = False,
    silent: bool = False
) -> LicenseInfo:
    """
    Ativa a biblioteca AtendentePro com um token de licença.
    
    Args:
        token: Token de licença. Se não fornecido, tenta usar
               a variável de ambiente ATENDENTEPRO_LICENSE_KEY
        validate_online: Se True, valida o token online (requer internet)
        silent: Se True, não imprime mensagens de sucesso
        
    Returns:
        LicenseInfo com informações da licença
        
    Raises:
        InvalidTokenError: Se o token for inválido
        LicenseExpiredError: Se o token estiver expirado
        
    Exemplo:
        >>> from atendentepro import activate
        >>> activate("ATP_eyJvcmciOiJNaW5oYUVtcHJlc2EiLCJleHAiOm51bGwsImZlYXQiOlsiZnVsbCJdLCJ2IjoxfQ.abc123")
        ✅ AtendentePro ativado para: MinhaEmpresa
    """
    global _license_state
    
    # Tentar obter token de variável de ambiente
    if token is None:
        token = os.environ.get("ATENDENTEPRO_LICENSE_KEY")
    
    if token is None:
        raise LicenseNotActivatedError()
    
    # Validar token
    if validate_online:
        license_info = _validate_token_online(token)
    else:
        license_info = _validate_token_local(token)
    
    if not license_info.valid:
        if "expirado" in license_info.message.lower():
            raise LicenseExpiredError(license_info.expiration or "Data desconhecida")
        raise InvalidTokenError()
    
    # Atualizar estado global
    _license_state["activated"] = True
    _license_state["token"] = token
    _license_state["expiration"] = license_info.expiration
    _license_state["features"] = license_info.features
    _license_state["organization"] = license_info.organization
    
    if not silent:
        exp_msg = f" (expira: {license_info.expiration})" if license_info.expiration else " (sem expiração)"
        print(f"✅ AtendentePro ativado para: {license_info.organization}{exp_msg}")
    
    return license_info


def deactivate():
    """Desativa a biblioteca (útil para testes)."""
    global _license_state
    _license_state = {
        "activated": False,
        "token": None,
        "expiration": None,
        "features": [],
        "organization": None,
    }


def is_activated() -> bool:
    """Verifica se a biblioteca está ativada."""
    return _license_state["activated"]


def get_license_info() -> LicenseInfo:
    """Retorna informações da licença atual."""
    if not _license_state["activated"]:
        return LicenseInfo(valid=False, message="Não ativado")
    
    return LicenseInfo(
        valid=True,
        organization=_license_state["organization"],
        expiration=_license_state["expiration"],
        features=_license_state["features"],
        message="Ativo"
    )


def require_activation():
    """
    Decorator/função para verificar se a biblioteca está ativada.
    
    Raises:
        LicenseNotActivatedError: Se não estiver ativada
    """
    # Primeiro, tentar ativar automaticamente via variável de ambiente
    if not _license_state["activated"]:
        env_token = os.environ.get("ATENDENTEPRO_LICENSE_KEY")
        if env_token:
            try:
                activate(env_token, silent=True)
            except LicenseError:
                pass
    
    if not _license_state["activated"]:
        raise LicenseNotActivatedError()


def has_feature(feature: str) -> bool:
    """Verifica se uma feature específica está habilitada."""
    if not _license_state["activated"]:
        return False
    
    features = _license_state.get("features", [])
    return "full" in features or feature in features


# ============================================================================
# UTILITÁRIO PARA GERAR TOKENS (USO ADMINISTRATIVO)
# ============================================================================

def generate_license_token(
    organization: str,
    days_valid: int = None,
    features: list = None
) -> str:
    """
    Gera um token de licença para uma organização.
    
    USO ADMINISTRATIVO - Para gerar tokens para clientes.
    
    Args:
        organization: Nome da organização/cliente
        days_valid: Dias de validade (None = sem expiração)
        features: Lista de features ["full", "basic", "knowledge", etc]
        
    Returns:
        Token de licença
        
    Exemplo:
        >>> generate_license_token("MinhaEmpresa", days_valid=365)
        'ATP_eyJvcmciOiJNaW5oYUVtcHJlc2EiLCJleHAiOjE3MzU2ODkw...'
    """
    expiration = None
    if days_valid is not None:
        expiration = int(time.time()) + (days_valid * 24 * 60 * 60)
    
    return _generate_token(
        organization=organization,
        expiration_timestamp=expiration,
        features=features or ["full"]
    )


# ============================================================================
# AUTO-ATIVAÇÃO VIA VARIÁVEL DE AMBIENTE
# ============================================================================

def _try_auto_activate():
    """Tenta ativar automaticamente via variável de ambiente."""
    env_token = os.environ.get("ATENDENTEPRO_LICENSE_KEY")
    if env_token and not _license_state["activated"]:
        try:
            activate(env_token, silent=True)
        except LicenseError:
            pass  # Silenciosamente ignora erros de auto-ativação


# Tentar auto-ativar ao importar o módulo
_try_auto_activate()


# ============================================================================
# CLI PARA GERAR TOKENS
# ============================================================================

def _cli_generate_token():
    """
    Ponto de entrada CLI para gerar tokens.
    
    Uso:
        atendentepro-generate-token "MinhaEmpresa" --days 365
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="atendentepro-generate-token",
        description="Gera tokens de licença para o AtendentePro"
    )
    parser.add_argument(
        "organization",
        help="Nome da organização/cliente"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Dias de validade (padrão: sem expiração)"
    )
    parser.add_argument(
        "--features",
        default="full",
        help="Features habilitadas, separadas por vírgula (padrão: full)"
    )
    
    args = parser.parse_args()
    
    # Processar features
    features = [f.strip() for f in args.features.split(",")]
    
    # Gerar token
    token = generate_license_token(
        organization=args.organization,
        days_valid=args.days,
        features=features
    )
    
    # Validar o token gerado
    info = _validate_token_local(token)
    
    print("\n" + "=" * 70)
    print("TOKEN DE LICENÇA ATENDENTEPRO")
    print("=" * 70)
    print(f"\n📋 Organização: {info.organization}")
    print(f"⏰ Expiração:   {info.expiration or 'Sem expiração'}")
    print(f"🎯 Features:    {', '.join(info.features)}")
    print(f"\n🔑 Token:\n")
    print(token)
    print("\n" + "=" * 70)
    print("\n📌 Para usar, adicione ao ambiente ou código:")
    print(f'\nexport ATENDENTEPRO_LICENSE_KEY="{token}"')
    print("\nou no código Python:")
    print(f'\nfrom atendentepro import activate')
    print(f'activate("{token}")')
    print("\n" + "=" * 70 + "\n")

