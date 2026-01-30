# Changelog

All notable changes to AtendentePro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.5] - 2025-01-21

### Added
- **Scripts de teste de licença**: Novos scripts em `scripts/` para testar o comportamento da biblioteca sem credencial
  - `scripts/test_without_license.py`: Script para verificar se a biblioteca bloqueia corretamente o uso sem licença
  - `scripts/TESTE_SEM_CREDENCIAL.md`: Documentação do teste de licença

### Documentation
- Documentação sobre verificação de licença e comportamento sem credencial

## [0.6.4] - 2025-01-14

### Added
- **Filtros de Acesso (Role/User)**: Novo sistema de controle de acesso baseado em roles e usuários
  - `UserContext`: Contexto do usuário com user_id, role e metadata
  - `AccessFilter`: Filtros whitelist/blacklist para roles e users
  - `FilteredPromptSection`: Seções de prompt condicionais por role/user
  - `FilteredTool`: Tools com filtro de acesso
- **Novos parâmetros em `create_standard_network`**:
  - `user_context`: Contexto do usuário para filtragem
  - `agent_filters`: Filtros de agente por role/user
  - `conditional_prompts`: Prompts condicionais por role/user
  - `filtered_tools`: Tools filtradas por role/user
- **Configuração via YAML** (`access_config.yaml`): Suporte a configuração de filtros via arquivo
- **Exemplos completos**: Pasta `docs/examples/access_filters/` com casos de uso

### Documentation
- README atualizado com seção completa de Filtros de Acesso
- Exemplos de código e YAML para diferentes cenários

## [0.6.3] - 2025-01-12

### Changed
- **Dependências otimizadas**: numpy e scikit-learn movidos para opcional `[rag]`
- **Versões com limites**: Todas as dependências agora têm limites máximos de versão
- **CI mais rápido**: Cache de pip adicionado e matriz reduzida para Python 3.9 e 3.12
- Instalação base reduzida de ~300MB para ~50MB

### Added
- **Exemplos de Single Reply Mode**: Pasta `docs/examples/single_reply/` com exemplos completos
- Documentação expandida no README com casos de uso práticos (FAQ Bot, Bot de Leads)

### Fixed
- Warnings de instalação eliminados com pinagem de versões
- Tempo de deploy reduzido de ~40min para ~8-10min
- Verificação clara quando RAG dependencies não estão instaladas

### Migration
- Se você usa RAG/Knowledge Agent, agora precisa: `pip install atendentepro[rag]`

## [0.6.2] - 2025-01-12

### Added
- **Single Reply Mode**: Novo parâmetro `single_reply` para todos os agentes
  - Quando ativado, agente responde uma vez e transfere automaticamente para Triage
  - Evita que conversas fiquem "presas" em agentes específicos
  - `global_single_reply`: Ativa para todos os agentes
  - `single_reply_agents`: Dict para configurar por agente
- `single_reply_config.yaml`: Novo arquivo YAML para configurar via template
- `SingleReplyConfig`: Model Pydantic para configuração
- `load_single_reply_config()`: Função para carregar configurações

### Changed
- Todos os agentes agora aceitam parâmetro `single_reply: bool = False`
- `create_standard_network()` aceita `global_single_reply` e `single_reply_agents`
- Documentação atualizada com exemplos de Single Reply Mode

## [0.6.1] - 2025-01-08

### Fixed
- Documentação PyPI atualizada com AgentStyle e changelog completo

## [0.6.0] - 2025-01-08

### Added
- **AgentStyle**: Nova classe para configurar tom e estilo de comunicação dos agentes
  - `tone`: Tom da conversa (ex: "profissional", "empático", "consultivo")
  - `language_style`: Nível de formalidade ("formal", "informal", "neutro")
  - `response_length`: Tamanho das respostas ("conciso", "moderado", "detalhado")
  - `custom_rules`: Regras personalizadas em texto livre
- `style_config.yaml`: Novo arquivo YAML para configurar estilos via template
- `load_style_config()`: Função para carregar configurações de estilo
- `StyleConfig` e `AgentStyleConfig`: Models Pydantic para configuração
- Parâmetros `global_style` e `agent_styles` em `create_standard_network()`
- Parâmetro `style_instructions` em todos os create_*_agent()

### Changed
- Todos os agentes agora aceitam `style_instructions` para personalização de tom
- Documentação atualizada com exemplos de uso do AgentStyle

## [0.5.9] - 2025-01-07

### Changed
- Descrição PyPI formal: "Framework de orquestração de agentes IA"
- README profissional com foco em capacidades corporativas
- Tabela de capacidades técnicas no README

## [0.5.8] - 2025-01-07

### Changed
- Updated PyPI description to highlight all agent types
- Added new keywords: triage, handoff, escalation, feedback, knowledge-base, interview
- Changed `tracing` optional dependency to use `monkai-trace`
- Added `azure` optional dependency for Application Insights

## [0.5.7] - 2025-01-07

### Added
- MonkAI Trace integration for comprehensive agent monitoring
- New functions: `configure_monkai_trace`, `run_with_monkai_tracking`
- Session management with `set_monkai_user`, `set_monkai_input`
- Token segmentation support (input, output, process, memory)
- Multi-user session tracking for WhatsApp/chat bots
- Documentation for tracing setup in README

### Changed
- Renamed `configure_tracing` to `configure_application_insights` (legacy alias kept)

## [0.5.6] - 2025-01-07

### Added
- New parameters in `create_standard_network` to enable/disable individual agents:
  - `include_flow`, `include_interview`, `include_answer`
  - `include_knowledge`, `include_confirmation`, `include_usage`
- Allows creating custom networks without specific agents (e.g., without Knowledge)

### Changed
- Handoffs are now dynamically configured based on which agents are enabled
- Documentation updated with examples of minimal network configurations

## [0.5.5] - 2025-01-06

### Fixed
- GitHub Actions workflow now only triggers PyPI publish on version tags

## [0.5.4] - 2025-01-06

### Changed
- Complete standalone documentation in README.md for PyPI
- All documentation now visible directly on PyPI page
- No external links to private repository

## [0.5.3] - 2025-01-06

### Fixed
- Documentation links now use absolute GitHub URLs for PyPI compatibility
- Removed reference to private `examples/` folder

## [0.5.2] - 2025-01-06

### Changed
- Updated contact information:
  - Email: contato@monkai.com.br
  - Website: https://www.monkai.com.br

## [0.5.1] - 2025-01-06

### Changed
- **Documentation**: Updated all diagrams and READMEs
  - Added prompts files for Escalation and Feedback agents (`prompts/escalation.py`, `prompts/feedback.py`)
  - Moved `templates/standard/` out of `client_templates/` (now included in repository)
  - Removed unnecessary Answer → Interview handoff
  - Fixed inconsistencies in handoff diagrams
  - Improved YAML configuration documentation

### Fixed
- Removed circular handoff from Answer Agent to Interview Agent
- Fixed docstrings and diagrams referencing old handoff structure

## [0.5.0] - 2025-01-06

### Added
- **Feedback Agent**: New module for ticket-based user feedback
  - `create_feedback_agent()` factory function
  - `FEEDBACK_TOOLS` with ticket creation and management tools:
    - `criar_ticket` - Create feedback tickets (dúvida, feedback, reclamação, sugestão, elogio, problema)
    - `enviar_email_confirmacao` - Send confirmation email to user
    - `consultar_ticket` - Query ticket status by protocol
    - `listar_meus_tickets` - List user's tickets by email
    - `atualizar_ticket` - Update ticket status or add response
  - Protocol generation with customizable prefix (TKT, SAC, SUP)
  - Email templates with brand customization
  - Priority auto-classification (reclamações = alta)
  - Team notification support
- **Network Integration**: Feedback Agent added to standard network
  - `include_feedback` parameter in `create_standard_network()`
  - `feedback_protocol_prefix`, `feedback_brand_color`, `feedback_brand_name` parameters
  - `add_feedback_to_all()` method in AgentNetwork
  - Feedback added as handoff to ALL agents by default
- **Template Configuration**: New `feedback_config.yaml` template
  - Ticket types configuration
  - Priority levels and SLA
  - Email branding options
  - Auto-priority rules
- **Configuration Function**: `configure_feedback_storage()` for runtime config

### Changed
- `AgentNetwork` now includes `feedback` attribute
- Network handoffs updated to include feedback option
- README updated with Feedback Agent documentation
- Version bump to 0.5.0

## [0.4.0] - 2025-01-06

### Added
- **Escalation Agent**: New module for human support transfer
  - `create_escalation_agent()` factory function
  - `ESCALATION_TOOLS` with registration and consultation tools
  - Automatic activation triggers (explicit request, frustration, out-of-scope topics)
  - Business hours verification
  - Protocol generation and tracking
  - Priority auto-classification (urgent, high, normal, low)
  - Webhook notification support
- **Network Integration**: Escalation Agent added to standard network
  - `include_escalation` parameter in `create_standard_network()`
  - `escalation_channels` parameter for channel description
  - `add_escalation_to_all()` method in AgentNetwork
  - Escalation added as handoff to ALL agents by default
- **Template Configuration**: New `escalation_config.yaml` template
  - Customizable triggers, channels, and business hours
  - Priority classification rules
  - Custom messages
- **Client Updates**: Vivo and EasyDr networks support Escalation Agent
- **Examples**: New `main_escalation()` demo in `run_vivo.py`

### Changed
- `AgentNetwork` now includes `escalation` attribute
- Network handoffs updated to include escalation option
- README updated with Escalation Agent documentation
- Version bump to 0.4.0

## [0.3.0] - 2025-01-04

### Added
- **License System**: New token-based licensing system
  - `activate()` function to activate the library
  - Auto-activation via `ATENDENTEPRO_LICENSE_KEY` environment variable
  - `atendentepro-generate-token` CLI command for administrators
  - License expiration support
  - Feature-based licensing
- **CLI Tools**: Command-line interface for token generation
- **Improved Documentation**: Enhanced README with activation instructions

### Changed
- Library now requires activation before use
- Version bump to 0.3.0
- Updated pyproject.toml with new metadata

### Security
- Added HMAC-SHA256 token validation
- Proprietary license enforcement

## [0.2.0] - 2025-01-03

### Added
- **Modular Architecture**: Complete refactoring into independent library
- **Agent Network**: Configurable multi-agent system
  - Triage Agent - Intent classification
  - Flow Agent - Options presentation
  - Interview Agent - Information collection
  - Answer Agent - Response synthesis
  - Knowledge Agent - RAG and structured data queries
  - Confirmation Agent - Yes/no validation
  - Usage Agent - System help
  - Onboarding Agent - User registration
- **Template System**: YAML-based client configuration
- **Guardrails**: Scope validation and forbidden topics
- **Custom Tools**: Support for function_tool integrations
- **Multiple Data Sources**: CSV, database, API support

### Changed
- Extracted from monkai monorepo into standalone package
- Standardized configuration format

## [0.1.0] - 2024-12-01

### Added
- Initial release
- Basic multi-agent functionality
- OpenAI Agents SDK integration

