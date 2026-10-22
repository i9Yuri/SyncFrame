# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato segue as diretrizes do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [0.1.0] - 2026-10-22

### Adicionado
- **Core Engine & Pipeline de Sincronia:**
  - Contratos estruturados de dados em `src/core/models.py`: `StreamMetadata`, `InspectionResult`, `SyncMetrics`, `RemuxJob`.
  - Módulo de inspeção de metadados em `src/core/inspector.py` utilizando `mkvmerge -J` e `ffprobe` com cálculo de durações e taxas fracionárias exatas (ex.: 24000/1001 para 23.976 fps).
  - Módulo de extração acústica em `src/core/extractor.py` gerando faixas mono PCM 16kHz com filtro passa-faixa (300Hz-4000Hz) para destacar efeitos, foley e transientes musicais.
  - Motor de correlação acústica FFT em `src/core/correlator.py` com cálculo normalizado de Pearson (suporte a SciPy e fallback vetorizado nativo em NumPy) e análise multi-janela (5%, 50%, 85%) para diagnóstico de drift e desalinhamentos de framerate (23.976 fps, 24.000 fps, 25.000 fps PAL).
  - Módulo de time-stretch lossless sem alteração de pitch em `src/core/transformer.py` utilizando o filtro `atempo` do FFmpeg em formato FLAC intermediário.
  - Orquestrador de remux lossless em `src/core/remuxer.py` via `mkvmerge`: zero reencodamento de vídeo (stream copy direta), sincronização por cabeçalho (`--sync <ID>:<OFFSET>`), tags de idioma e monitoramento de progresso em tempo real.
  - Gerenciamento isolado de staging em `src/core/temp_manager.py` (`.syncframe_tmp/`) com expurgo automático ao término do processo ou em sinais de cancelamento (`SIGINT`/`SIGTERM`/`atexit`).
  - Validador pré-voo de capacidade em disco em `src/core/disk_utils.py`.
  - Validação de dependências do sistema host em `src/utils/system_check.py` (`ffmpeg`, `ffprobe`, `mkvmerge`, `mpv`).

- **Interface Gráfica Desktop (PySide6):**
  - Layout assimétrico Bento Grid em `src/ui/main_window.py`.
  - Estilização completa Pro Max v4 Anti-Slop em `src/ui/style.py` (Dark Slate `#090d16`, superfícies `#0f172a`, Ciano Cirúrgico `#06b6d4`, Verde Esmeralda `#10b981`, Âmbar `#f59e0b`, Azul Safira `#0ea5e9`, sem tons roxo/magenta).
  - Card de upload com drag-and-drop e seletores de streams em `src/ui/components/file_drop_card.py`.
  - Visualizador gráfico de onda e pico de correlação via QPainter em `src/ui/components/correlation_view.py`.
  - Controles de micro-ajuste de offset (passos de $\pm 50\text{ ms}$, botões de salto rápido, slider e badges de métricas) em `src/ui/components/sync_controls.py`.
  - Player de inspeção em tempo real nos marcadores temporais 5%, 50% e 90% via `mpv` com áudio compensado em `src/ui/components/preview_player.py`.
  - Gaveta retrátil de logs do terminal em `src/ui/components/log_drawer.py`.
  - Execução assíncrona desacoplada da GUI com suporte a cancelamento imediato em `src/ui/workers/analyze_worker.py` e `src/ui/workers/remux_worker.py`.

- **Launcher & Ambiente:**
  - Script executável por duplo clique `run.sh` com checagem de binários de sistema, bootstrap de `.venv` com `--system-site-packages` e sincronização silenciosa de `requirements.txt`.
  - Suporte a modo CLI `--cli-check` e `--version`.

- **Testes Unitários Automatizados:**
  - Suíte de 9 testes unitários em `tests/` cobrindo modelos, precisão matemática da correlação FFT com sinais sintéticos atrasados, diagnósticos de frame rate, ciclo de vida de diretórios temporários e parsing de metadados.

- **Auto-Matching Heurístico & Review Gate Assistido:**
  - Dataclasses `StreamCandidate` e `AutoMatchVerdict` em `src/core/models.py`.
  - Heurística determinística de ranqueamento de fidelidade de vídeo em `src/core/inspector.py`: fórmula de pontuação considerando área de resolução, pesos de codec (`AV1 > HEVC > AVC > MPEG`) e taxa de bits/tamanho em disco para eleição automática da melhor imagem.
  - Varredura e mapeamento inteligente de áudio em `src/core/inspector.py`: detecção de tags e termos de dublagem em português (`por`, `pt`, `pt-br`, `pob`, `"Dublado"`) e eleição do áudio original de referência no arquivo primário de vídeo.
  - Componente modal `StreamSelectorModal` (`src/ui/components/stream_selector_modal.py`) como estágio de confirmação assistida (Review Gate) com foco padrão no botão "Confirmar e Sincronizar Tudo" para aprovação instantânea via Enter.
  - Suporte a drag-and-drop simultâneo de múltiplos arquivos MKV na janela principal ou nos cards, separando e avaliando ambos automaticamente sem necessidade de adivinhar slots.
  - Encadeamento de execução autônoma pós-confirmação (extração mono passa-faixa -> cálculo FFT -> remux lossless mkvmerge) sem requerer novas interações manuais.
  - Testes unitários dedicados em `tests/test_stream_evaluator.py` cobrindo cenários 4K vs 1080p, desempate por codec e fallback seguro para metadados ambíguos.

- **Redesign Neutro Monocromático & Unified Drop Zone (v0.1.1):**
  - Eliminação completa de matizes saturados (azuis/cianocromáticos) em prol de uma estética neutra, minimalista e limpa em escala de cinza (`#121212`, `#1e1e1e`, `#2e2e2e`, `#e5e5e5`, `#ffffff`).
  - Suporte estruturado e reativo a temas Claro e Escuro Neutros com alternador dinâmico (`🌓`) no cabeçalho via `apply_theme` e `get_theme_qss`.
  - Remoção de insígnias e textos descontextualizados ("Anti-Slop Engine"), mantendo cabeçalho puramente técnico com numeração de versão.
  - Resolução definitiva de achatamento e sobreposição de widgets em modo janela via envelopamento do layout em `QScrollArea` com `setWidgetResizable(True)` e barra de rolagem vertical sob demanda.
  - Substituição dos cards duplos de drop por um componente central unificado (`UnifiedDropZone`) com máquina de estados (vazio -> 1 arquivo -> Review Gate tabular inline).
  - Testes automatizados offscreen em `tests/test_unified_drop_zone.py` e `tests/test_ui_layout_responsiveness.py` validando resizes para `1280x800`, `1024x650`, `900x550` e `800x540`.
