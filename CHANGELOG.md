# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato segue as diretrizes do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.5.0] - 2026-10-25

### Adicionado
- **Manual Técnico Integral de Arquitetura para LLMs e Agentes de IA (`ARCHITECTURE.md`):**
  - Criação de documento canônico e exaustivo na raiz do repositório cobrindo 100% das funcionalidades, modelos, componentes de backend e de frontend.
  - 9 seções técnicas estruturadas: Invariantes de Engenharia, Mapa Estrutural do Repositório, Modelos e Dataclasses (`models.py`), Subsistemas de Backend (Probing, Extração Bandpass 300Hz-4kHz, Correlação FFT Multi-janela, Time-stretch e Restauração PAL, Remuxer DLNA e Auditoria Closed-Loop, OCP Protection e CLI), Subsistemas de Frontend (Design System One UI 8.5 Dark/Light, Sticky Topbar, Unified Drop Zone, Media Inspector, TiltedDock Flutuante, Popovers Wayland, Sync Controls com slider esférico 20x20 e sensibilidade 1ms/10ms/50ms, Lip-sync Player e Delegação de Dropdowns), Modelo de Concorrência e Sinais Assíncronos, Estratégia de Testes Automatizados (187 testes), Pipeline de Compilação em Binário Único ELF (`build_bin.sh`) e Diretrizes de Extensão para Agentes Autônomos.
  - Conformidade estrita: zero emojis, neutralidade monocromática e precisão matemática.
- **Faixa Declarativa de Especificações do Arquivo Resultante (Target Output Summary / Resulting File Specs):**
  - Substituição da linha textual estática de "Auditoria de canais" na parte inferior do painel de "Revisão de faixas" por uma barra horizontal reativa e declarativa com componentes visuais em pílulas arredondadas (`border-radius: 12px`, altura 24px) em container de cápsula contínua (`border-radius: 20px`, min-height 38px, `resultingSpecsBar`).
  - Consolidação e exibição em tempo real de 7 metadados técnicos padronizados do arquivo de saída: contêiner (`MKV Matroska` nativo ou `MKV Remux`), modo de processamento com classes cromáticas de alto contraste (`Cópia Direta (Passthrough)` com realce verde `#2fb16b` / `resultingPillGreen` ou `Re-encode [CODEC] (PAL 24fps)` com realce âmbar `#e8963a` / `resultingPillAmber`), formato comercial (`DOLBY ATMOS` com realce sinal `#4081f7` / `resultingPillSignal`, `DOLBY AUDIO 5.1`, `DTS-HD MA 7.1`, `FLAC LOSSLESS`), codec exato em caixa alta (`AC-3`, `E-AC-3`, `TRUEHD`, `DTS-HD MA`, `FLAC`, `OPUS`, `AAC`), topologia de canais decomposta com indicação explícita de surround, height/atmos e subwoofer LFE (`5.1 Surround (+Subwoofer)`, `7.1 Atmos (Surround + Height + Sub)`, `2.0 Estéreo (Sem LFE)`, `1.0 Mono (Sem LFE)`), frequência de amostragem padronizada com separador de milhar decimal (`48.000 Hz`) e taxa de bits nominal/real formatada (`640 kbps`, `3500 kbps`, `Bitrate Variável (VBR)`).
  - Reatividade bidirecional instantânea a alterações na seleção de áudio principal (`combo_target_audio`), comutação da restauração PAL (`check_pal_pitch`), seleção de codec de re-encode (`combo_audio_codec`) e seleção de vídeo de referência (`combo_video`).
  - Apresentação de fallback elegante de estado deselecionado (`Nenhum áudio selecionado`), contrato público `update_resulting_specs(self, track_info, remux_options) -> dict` e retrocompatibilidade estrita mantida com os atributos e rótulos legados (`lbl_audit_origin`, `badge_audit_layout`, `lbl_audit_specs`).
- **Dinamização da Ingestão de Fontes para $N$ Arquivos ($N \ge 2$):**
  - Substituição da estrutura estática de 2 cartões no `UnifiedDropZone` (`block_sources`) por layout flexível reativo (`self.sources_layout = QHBoxLayout()`).
  - Geração dinâmica de cartões em cápsula arredondada contínua (`.fileBox`, raio de 20px) para qualquer quantidade $N \ge 2$ de arquivos carregados (`self.dynamic_source_cards`), com limpeza determinística em `reset()`.
  - Atualização dinâmica do badge de contagem de fontes para `f"{N} / {N} FONTES"` (ex.: `3 / 3 FONTES`).
  - Identificação semântica de papéis de arquivo para todas as fontes adicionais (`VÍDEO ALTERNATIVO`, `ÁUDIO ADICIONAL` ou `FONTE ADICIONAL`).
- **Pooling Universal de Fluxos de Vídeo no Review Gate (`combo_video`):**
  - Desempacotamento recursivo em `Inspector.evaluate_media_streams` aceitando listas, tuplas e múltiplos argumentos posicionais.
  - Varredura e indexação de 100% dos fluxos de vídeo de todos os $N$ contêineres carregados, disponibilizando todas as opções com metadados técnicos completos (resolução, taxa de quadros, codec, contêiner e trilha) no seletor "Melhor Imagem" (V01).
- **Restauração dos Controles de Sensibilidade do Slider Temporal (`SensitivitySelectorWidget`):**
  - Reativação e ancoragem do seletor segmentado em pílula (`1 ms`, `10 ms`, `50 ms`) no cabeçalho de *Alinhamento temporal* ao lado do badge `Faixa A02`.
  - Conexão bidirecional mantida com o `SliderSensitivityController` e `DampedSlider` para ajuste milimétrico de offset acústico.
- **Expansão e Resiliência da Janela de Registro de Eventos (`EventLogPopover`):**
  - Expansão das dimensões do console para `820x520` (mais de 2.6x de área em relação ao layout original), proporcionando leitura técnica ampla de stack traces e saídas do FFmpeg/mkvmerge.
  - Adoção das flags `Qt.Tool | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint` com cálculo de posicionamento clampeado nos limites do monitor (`QGuiApplication.primaryScreen().availableGeometry()`), eliminando o erro de captura Wayland e impedindo que a janela seja renderizada fora da tela.
  - Fechamento imediato com a tecla `Escape` e curvatura contínua One UI de 18px (`border-radius: 18px`).
- **Micro-Interações e Profundidade no Dock Flutuante (TiltedDock Nativo):**
  - Transposição integral do comportamento do TiltedDock: o botão focado amplia para 1.35x com curva de mola `OutBack` e exibe destaque circular iluminado (`rgba(255, 255, 255, 0.14)` / `rgba(0, 0, 0, 0.08)`).
  - Profundidade de foco através de atenuação suave dos botões vizinhos (sibling dimming) para opacidade 0.45 via `QPropertyAnimation` na propriedade `buttonOpacity`.
  - Alternância de visibilidade por clique repetido (toggle) nos botões de logs e versão.
- **Transposição do Botão de Alternância de Tema para o Dock Flutuante:**
  - Remoção visual completa do botão de tema da Topbar superior, purificando totalmente o cabeçalho contra botões operacionais concorrentes.
  - Integração do botão de alternância de tema (`theme_toggle`) como o terceiro item funcional no dock flutuante desacoplado (`FloatingActionDock`), com auto-ajuste de largura para 228px.
  - Suporte visual adaptativo no dock: renderização do ícone solar SVG (`dock_theme_dark.svg`) em modo escuro (indicando ação para modo claro) e ícone lunar SVG (`dock_theme_light.svg`) em modo claro (indicando ação para modo escuro).
  - Micro-interações táteis completas: realce circular iluminado, ampliação suave de mola para 1.35x sob hover com atenuação dos irmãos vizinhos para 0.45 de opacidade, e micro-tooltip dinâmico contextual ("Modo Claro" / "Modo Escuro").
- **Desacoplamento e Fixação da Barra Superior (Sticky Detached Topbar):**
  - Desprendimento visual e estrutural completo da barra superior (`self.topbar` / `#topHeader`) da esteira de rolagem central da aplicação.
  - Fixação da altura em 76px com alinhamento vertical centrado, superfície sólida opaca (`#121316` no tema escuro e `#ffffff` no tema claro) e linha divisória sutil de 1px (`#23252b` / `#e1e4ed`), garantindo que o cabeçalho permaneça fixo no topo da janela quando a bancada é rolada para baixo.
  - Margem de respiro superior de 20px em `self.body_layout.setContentsMargins(20, 20, 20, 20)` no contêiner da bancada, permitindo que os cartões rolem suavemente por baixo da divisória sem colidir com a tipografia do título e subtítulo.
  - Propagação contínua de eventos de rolagem do mouse (`wheelEvent`) na área do cabeçalho superior diretamente para o viewport da `QScrollArea`, garantindo rolagem fluida e sem atritos em qualquer ponto da interface.

### Corrigido
- **Erradicação do Retângulo Escuro de Fundo no Painel de Faixas Secundárias:**
  - Remoção completa do container retangular opaco (`#1b1c20`) e da borda dura (`1px solid #282d34`) que envolviam as opções de faixas secundárias (`QFrame#frameSecondaryAudio`), configurando fundo 100% transparente e sem bordas (`background-color: transparent; border: none;`) em ambos os temas.
  - Alinhamento horizontal limpo dos cartões em cápsula (`secondaryTrackCard`) diretamente sobre a superfície do cartão de revisão de faixas (`blockReviewGate`), eliminando caixas ou retângulos residuais atrás das opções.
  - Ajuste idêntico em `optionsContainer` e `frameOptions`, garantindo que os seletores inferiores de preservação de áudio, restauração PAL e codec de re-encode não exibam sobreposições retangulares de fundo.
- **Eliminação do Bug de Desaparecimento de Ícones no Hover do Dock:**
  - Identificada e sanada a colisão de renderização no `paintEvent` do `DockItemButton`: o uso de `super().paintEvent` concorrente a um `QPainter` ativo abortava a pintura interna do Qt.
  - Renderização vetorial direta e nítida utilizando `QSvgRenderer` e `QPainter` unificado, mantendo os ícones 100% visíveis, sem recortes ou artefatos ao passar o cursor ou ampliar.
- **Erradicação de Quinas Vivas nas Faixas de Áudio Secundárias:**
  - Sanado o defeito visual onde `border-radius: 999px` em `QLabel.atomicChip` e `QLabel.atomicChipBest` revertia silenciosamente para retângulos rígidos de 90 graus no motor de QSS do Qt.
  - Implementação de raios contínuos proporcionais à meia-altura: `border-radius: 10px` com altura fixa de 20px (`min-height: 20px; max-height: 20px; padding: 0 8px;`) e alinhamento centrado em todos os chips de metadados (`ENG`, codecs, layout de canais, especificações técnicas e badge `RECOMENDADO`).
  - Transmutação do indicador de seleção (`chkSecondaryAudio::indicator`) de retângulo com cantos vivos para uma esfera perfeita de 18x18px (`border-radius: 9px;`).
  - Cartões de linha (`secondaryTrackCard`) com altura fixa de 34px e curvatura em cápsula de 16px (`border-radius: 16px;`), assegurando geometria 100% arredondada em ambos os temas.
- **Geometria 100% Circular no Slider de Alinhamento Temporal:**
  - Fixação de altura determinística de 28px no widget do slider (`min-height: 28px; height: 28px;` e `self.slider.setFixedHeight(28)`), eliminando o corte (clipping) vertical decorrente do teto de altura anterior.
  - Recalibração do handle horizontal (`::handle:horizontal`) com `width: 14px; height: 14px; margin: -6px 0; border: 3px solid #4081f7; border-radius: 10px;`.
  - Geometria esférica 1:1 resultante aferida por pixel: 20px de largura por 20px de altura, livre de achatamentos, arestas retas ou deformações nos modos Claro e Escuro.
- **Transparência de Cantos e Legibilidade em Menus Suspensos (`QComboBox` / Review Gate):**
  - Sanado o defeito de opções ilegíveis e "sobra de cantos brancos" nos seletores de imagem, faixa de áudio e codec de re-encode (`combo_audio_codec`).
  - Identificada e corrigida a causa raiz da ilegibilidade no `DropdownHighlightDelegate`: correção de acesso aos sinalizadores de estado do Qt via `QStyle.State_Selected` e `QStyle.State_MouseOver` (em vez de atributos inexistentes no `QStyleOptionViewItem`), eliminando o cancelamento prematuro da pintura de itens.
  - Eliminação definitiva dos cantos brancos opacos através do desacoplamento de transparência: configuração de `Qt.WA_TranslucentBackground` no contêiner da janela do popup (`QComboBoxPrivateContainer`) com escopo CSS restrito (`#QComboBoxPrivateContainer { background: transparent; border: none; }`), preservando a opacidade e o preenchimento de fundo sólido (`#1b1c20` / `#ffffff`) da superfície interna com raio de curvatura de 16px.
  - Promoção do seletor `combo_audio_codec` para `HighlightComboBox` com `DropdownHighlightDelegate` e bloqueio de rolagem acidental (`install_wheel_blocker`).

## [1.4.0] - 2026-10-25

### Adicionado
- **Reconstrução do Dock Inferior como Hub de Ações Flutuante (TiltedDock Nativo PySide6/Qt6):**
  - Transposição nativa dos princípios ergonômicos e micro-interações do TiltedDock sem dependências externas (zero Node/React).
  - Hub desacoplado com auto-dimensionamento restrito ao conteúdo (`fit-content`), curvatura contínua semicircular (`border-radius: 26px`), superfície translúcida (`rgba(27, 28, 32, 0.85)` / `rgba(255, 255, 255, 0.85)`), borda cirúrgica de 1px e sombra suave de elevação.
  - Micro-interações táteis de hover: ampliação fluida via `QPropertyAnimation` com curva de mola `QEasingCurve.OutBack` e micro-tooltip em pílula posicionado acima do botão ativo com fade de opacidade de 120ms.
  - Reposicionamento dinâmico em `resizeEvent` e `showEvent` ancorado a 20px da borda inferior:
    $$X = \frac{\text{Largura da Janela} - \text{Largura do Dock}}{2}, \quad Y = \text{Altura da Janela} - \text{Altura do Dock} - 20$$
  - **Popover de Registro de Eventos (`EventLogPopover`):** Janela flutuante suspensa sem bordas (`Qt.Popup | Qt.FramelessWindowHint`) com micro-badge contador, botão "Limpar" em pílula e console técnico monoespacado com retenção estrita limitada às últimas 1.000 linhas para prevenção de consumo de RAM.
  - **Auditoria de Atualizações Assíncrona Integrada:** Acionamento sob demanda do `DependencyUpdateWorker` em segundo plano com indicador sutil de atividade e notificação toast flutuante temporária.
  - **Popover de Diagnóstico e Versão (`VersionInfoPopover`):** Janela suspensa compacta exibindo tags em pílula atômicas com a versão do SyncFrame (`v1.2.0`), ambiente operacional (`Nobara Linux x86_64`) e status dos motores (`FFmpeg`, `MKVToolNix`, `MPV`).
- **Nova Suíte de Testes Automatizados (`tests/test_floating_action_dock.py`):**
  - Testes unitários para `DockItemConfig`, `FloatingActionDock`, `EventLogPopover`, `VersionInfoPopover`, limites de memória de logs, cálculos de posicionamento e isolamento da Topbar (179 testes globais passando).

### Modificado
- **Higienização e Simplificação da Topbar Superior:**
  - Isolamento exclusivo no canto superior direito do botão comutador de tema (`#btnTheme`), formatado em pílula semicircular contínua (`border-radius: 17px`), dimensionado dinamicamente via `QFontMetrics` + 14px de padding simétrico com rótulos contextuais "Modo Claro" / "Modo Escuro" e zero truncamento.
  - Remoção visual permanente da tag "Espaço de trabalho local" e do badge de versão do container superior direito, mantendo atributos internos para compatibilidade estrita com contratos legados.
  - Transferência definitiva da ação de "Verificar Atualizações" para o novo dock de ações inferior.

## [1.3.1] - 2026-10-25

### Adicionado
- **Heurística Qualitativa de Seleção de Áudio Secundário (4 Tiers de Fidelidade Acústica):**
  - Implementação de modelo determinístico de pontuação em 4 patamares (`compute_stream_quality_score` e `Inspector.rank_secondary_audio_streams`):
    - *Tier 1 (Lossless/Imersivo, Score 100):* TrueHD Atmos, DTS-HD MA 7.1, DTS:X, LPCM 7.1.
    - *Tier 2 (Imersivo Broadcast/Multicanal Full, Score 80):* E-AC-3 JOC (Dolby Digital Plus com Atmos), DTS-HD MA 5.1, DTS 5.1.
    - *Tier 3 (Multicanal Convencional, Score 65):* AC-3 5.1 (Dolby Digital legado).
    - *Tier 4 (Estéreo/Compactado, Score 40):* AAC 2.0, MP3, Opus 2.0.
  - Pré-seleção automática e exclusiva (checked) restrita à trilha original de maior escore do Tier 1. Trilhas redundantes ou de menor fidelidade (ex.: faixa AC-3 5.1 de compatibilidade quando TrueHD Atmos está presente) vêm desmarcadas por padrão.
- **Resumo Técnico Estruturado em "Auditoria de canais":**
  - Implementação do método contratual `StreamReviewGate.update_channel_audit_summary(primary_audio, container_format)` renderizando:
    - Badge Pill Contêiner: `MKV Nativo` ou `<FMT> -> MKV Remux`.
    - Badge Pill Perfil Imersivo: `DOLBY ATMOS`, `DOLBY AUDIO 5.1`, `DTS-HD MA 7.1`, `DTS SURROUND` ou `ESTÉREO CONVENCIONAL`.
    - Rótulo de Especificação Unificada em tipografia monospace de alta densidade: `Codec: <CODEC> • Canais: <LAYOUT> • Frequência: <HZ> Hz • Taxa de Bits: <KBPS> kbps`.
- **Conformidade Estrita de Metadados Matroska para Renderizadores DLNA/UPnP:**
  - Implementação de `Remuxer.generate_dlna_track_args(track, is_primary)` gerando parâmetros certificados para players DLNA e TVs (BubbleUPnP, Smart TVs Samsung/LG):
    - `--track-name`: `Português (Dublagem Oficial - <Codec> <Canais>)` (primária) e `Inglês (Original - <Perfil_Audio>)` (secundária original).
    - `--language`: `por` (primária) e `eng` (secundária original).
    - `--enabled-track-flag <id>:1` para todas as faixas ativas.
    - `--default-track-flag <id>:1` (primária) e `<id>:0` (secundárias).
    - `--forced-display-flag <id>:0` para faixas de áudio convencionais.
- **Contador Dinâmico de Fontes Ingeridas ($N$ Fontes):**
  - Implementação de `IngestPanel.update_source_count_badge(count)` desacoplando o contador estático para suportar dinamicamente `f"{count} / {count} FONTES"`.

### Corrigido
- **Correção da Quebra de Contraste no Modo Claro (Seleção Múltipla de Secundárias):**
  - Erradicação de estilos inline hardcoded em `unified_drop_zone.py` (`lbl_fsa_title`, `chip_fsa_status`, `chk.setStyleSheet`, `lbl_audit_specs`).
  - Introdução de seletores semânticos em `src/ui/style.py` para Modo Claro (`#16181d` sobre `#ffffff` e indicador `#e1e4ed`) e Modo Escuro (`#f2f3f7` sobre `#1b1c20`), com estado checked em verde neutro do sistema (`#2fb16b`).
- **Erradicação de Quinas Retangulares Vivas nos Popups Dropdown:**
  - Aplicação de `border-radius: 16px`, borda `1px solid #282d34` / `#dcdfe8`, padding de 6px e itens com `border-radius: 10px` nos popups `QComboBox QAbstractItemView`.
  - Configuração de `Qt.WA_TranslucentBackground`, `Qt.Popup` e `Qt.FramelessWindowHint` em `NoWheelComboBox`, eliminando qualquer moldura retangular de fundo de 90 graus no compositor X11/Wayland.
- **Ergonomia Espacial no Card de Alinhamento Temporal (03A):**
  - Inserção de espaçamento vertical contínuo de 16px (`layout.addSpacing(16)`) entre a grade de passos rápidos (`grid_steps`) e a linha de telemetria acústica (`row_mets`).

## [1.3.0] - 2026-10-25

### Adicionado
- **Modo Inspeção / Visualizador de Mídia (Single-File Media Inspector):**
  - Transmutação automática e fluida da interface ao ingerir exatamente 1 arquivo — contêiner de vídeo (.mkv, .mp4, .m4v, .mov) ou faixa de áudio isolada (.ac3, .eac3, .aac, .dts, .flac, .m4a, .mp3, .wav, .opus) —, apresentando bancada de auditoria técnica estruturada sem necessidade de arquivos secundários.
  - Probing profundo assíncrono e não-bloqueante via `SingleFileInspectionWorker` (QThread) e `inspect_single_media`, extraindo formato do contêiner, taxa de quadros, HDR/Dolby Vision, profundidade de bits, layout e canais de áudio, legendas e capítulos com tolerância a cabeçalhos truncados (`-err_detect ignore_err`).
  - Apresentação estruturada e modular em `MediaInspectorView`:
    - Cabeçalho com identificador em pílula do contêiner, tamanho formatado em bytes, duração e contagem de fluxos.
    - Bloco de especificações de vídeo (resolução UHD/HD, codec, taxa de quadros, formato HDR/Dolby Vision, perfil, bit depth) com supressão inteligente para faixas de áudio isoladas.
    - Bloco de faixas de áudio com pílulas de trilha (A01, A02), idioma, codec, layout de canais (2.0, 5.1, 7.1 Atmos), taxa de amostragem e bitrate real.
    - Bloco de legendas e capítulos com destaque para faixas forçadas e contagem estruturada.
    - Card de aviso contextual para áudios isolados orientando a adição de fonte de vídeo de referência.
    - Botão conectivo de rodapé (`btnConnectiveAction`, contorno tracejado com 22px de curvatura contínua) viabilizando a transição imediata para sincronização ao arrastar ou selecionar uma segunda fonte sem reiniciar o estado.
- **Modo Sincronização e Remux Híbrido com Review Gate Consolidado:**
  - Review Gate estruturado em 3 seções determinísticas:
    (a) Dropdown de Vídeo de Referência Principal (`[Melhor Imagem Detectada]`).
    (b) Dropdown de Áudio Dublado Principal (`[Áudio Recomendado]`).
    (c) Painel de Fluxos Secundários de Áudio (`frameSecondaryAudio`) com checkboxes individuais dedicados (`chkSecondaryAudio`), indicador com cantos arredondados de 4px e glifo de visto verde (#2fb16b), mantendo o áudio original em inglês marcado por padrão e trilhas redundantes/inferiores desmarcadas.
  - Formalização do contrato de seleção consolidada (`ConsolidatedStreamSelection`) e persistência no `RemuxJob`.
  - Processamento determinístico em `build_mkvmerge_hybrid_command`: fluxo de vídeo bit-a-bit, áudio dublado principal alinhado por FFT e faixas secundárias marcadas incorporadas em modo stream copy passthrough com `--default-track-flag <id>:no`, omitindo faixas desmarcadas.
  - Transições atômicas na janela principal (`transition_to_inspector_mode` e `transition_to_sync_mode`) coordenando a disponibilidade dos painéis da esteira.
- **Verificação Pré-Voo de Dependências do Sistema (`PreFlightChecker` & `PreFlightDialog`):**
  - Auditoria estrita pré-inicialização das ferramentas mandatórias de sistema (`ffmpeg`, `ffprobe`, `mkvmerge`, `mpv`) via `PreFlightChecker.verify_system_binaries()`.
  - Exibição de diálogo modal One UI com cantos arredondados contínuos de 28px (`PreFlightDialog`) suspendendo a inicialização caso algum binário obrigatório esteja ausente, oferecendo instalação guiada com elevação de privilégios (`pkexec`) e opção de saída limpa.
  - Atualização do script de inicialização `run.sh` incluindo validação explícita de `mpv`.
- **Auditoria Silenciosa em Background e Botão de Atualização na Topbar (`DependencyUpdateWorker`):**
  - Worker em thread assíncrona desacoplada (`DependencyUpdateWorker`, `QThread.LowPriority`) para consulta tolerante a falhas e sem bloqueios na GUI das versões locais e lançamentos remotos via GitHub API.
  - Botão em pílula semicircular de 34px (`#btnCheckUpdates`, `border-radius: 17px`) integrado à barra superior com estados transitórios ("Verificar Atualizações" -> "Verificando..." -> resultado temporizado por 4 segundos).
  - Tratamento resiliente offline (`Verificação remota ignorada: offline`) sem popups intrusivos.
- **Controlador Robusto de Inspeção Labial (`LipSyncController` & `PreviewPlayer`):**
  - Implementação do controlador de reprodução desacoplado `LipSyncController` baseado em `QProcess` com terminação atômica e prevenção estrita de processos órfãos (`mpv` e fallback para `ffplay`).
  - Suporte a flags de reprodução pontual (`--start`, `--length=12`, `--audio-delay`) e mapeamento determinístico de atraso temporal via `map_offset_to_player_delay`.
  - Disparo de marcadores segmentados (5% · Abertura, 50% · Meio, 90% · Ato final) calculados dinamicamente com base na duração total da mídia e botão "Parar" sincronizado com o ciclo de vida do processo.
  - Atualização em tempo real de timecodes e mensagens de status sem emojis.
- **Auditoria Acústica Imersiva e Badge Reativo de Compatibilidade com Soundbars 7.1.4:**
  - Implementação do motor de auditoria de som imersivo multicanal (`audit_immersive_capabilities` em `src/core/inspector.py`), com calibração de referência para soundbars de 7.1.4 canais com suporte a Dolby Atmos e caixas surround desacopláveis (JBL Bar 1000 MK2).
  - Classificação determinística em estados `optimal` (círculo verde com visto ✓ para Dolby Atmos, TrueHD Atmos, E-AC-3 JOC, DTS:X, 7.1 discreto) e `suboptimal` (círculo âmbar com exclamação ! para 5.1 convencional, estéreo 2.0 ou transcodificação comprimida).
  - Implementação do componente visual `SoundbarAuditBadge` com renderização vetorial anti-aliased em 24x24px inserido no cabeçalho do card de saída do remux.
  - Implementação do `SmoothFadeTooltip` com transição suave em fade de opacidade (120ms, `QEasingCurve.OutQuad`), geometria curva contínua (`border-radius: 12px`), dimensionamento dinâmico via `QFontMetrics` e orientação diagnóstica sucinta em 3 linhas.
  - Reatividade atômica via sinal `primary_audio_changed` atualizando instantaneamente o status do badge a cada mudança de seleção no Review Gate.

### Alterado
- **Comutador de Tema com Ícones Vetoriais de Sol e Lua na Topbar (`#btnTheme`):**
  - Substituição dos rótulos de texto estáticos ("Modo Claro" / "Modo Escuro") por botão em pílula circular perfeita de 34x34px (`border-radius: 17px`) com ícones vetoriais SVG nítidos e centralizados (`icon_sun.svg` no tema Dark para transição à luz, `icon_moon.svg` no tema Light para transição ao escuro).
  - Remoção de margens internas de texto (`padding: 0px`) com dimensionamento fixo 34x34px, `qproperty-iconSize: 18px 18px`, tooltips contextuais ("Modo Claro" / "Modo Escuro") e suporte dinâmico a estados `:hover` e `:pressed` sem regressões geométricas.

### Corrigido
- **Erradicação de Quinas Vivas e Caixas Retangulares na Zona de Ingestão e Botões Primários:**
  - Substituição de `border-radius: 999px` por raios matemáticos contínuos de meia-altura (`22px` para botões primários de 44px, `17px` para botões secundários de 34px e `14px` para badges de 28px) em `DARK_THEME_QSS` e `LIGHT_THEME_QSS`.
  - Correção da geometria do botão "Selecionar Arquivos..." (`#btnBrowse`), botão de segundo arquivo (`#btnBrowseSecond`) e botão de confirmação (`#btnConfirm`) transformando-os em pílulas orgânicas perfeitas com `border-radius: 22px`.
  - Fixação de altura explícita (28px), `border: none` e `border-radius: 14px` no chip indicador de etapa "01 INGESTÃO DE FONTES" (`#tagIngest`) e badge de espera (`#badgeWaiting`), eliminando a renderização de caixas retangulares retas de 90 graus.
- **Padronização e Erradicação de Arestas Rígidas no Card de Alinhamento Temporal:**
  - Substituição da diretiva `border-radius: 999px` por raios matemáticos contínuos proporcionais à meia-altura exata (13px, 14px, 17px, 18px) nos temas Dark e Light, sanando a reversão do Qt QSS para quinas retangulares de 90 graus.
  - Eliminação de cantos vivos na pílula do seletor de sensibilidade (`SensitivitySelectorWidget`), no chip de faixa ativa (`Faixa A02`), nos 8 botões da matriz de micro-passo (`stepBtn`) e na barra de diagnóstico de cadência (`frameNote`).
  - Ativação visual nítida do botão de sensibilidade ativo (`QPushButton.pillSegmentBtn[active="true"]`) em contraste alto e adição de pseudo-estados `:pressed` e `:disabled` com bordas curvas contínuas.
- **Erradicação de Quinas Vivas e Estiramento Vertical no Card de Saída do Remux:**
  - Fixação determinística de altura de 44px e raio contínuo de meia-altura (`border-radius: 22px; height: 44px;`) no seletor de caminho de destino (`#frameOutPath`), eliminando o estiramento vertical indesejado de 160px e revertendo quinas retangulares vivas.
  - Integração transparente do campo de texto (`#txtOutputPath`, `background: transparent; border: none; padding: 0 4px;`) sem molduras retangulares internas colidindo com o contorno da pílula.
  - Transformação dos botões "Procurar..." (`#btnBrowseDest`) e "Cancelar" (`#btnCancel`) em botões de pílula contínua de 34px de altura (`border-radius: 17px; height: 34px; min-height: 34px; max-height: 34px; padding: 0 16px;`).
  - Arredondamento contínuo da barra de progresso (`QProgressBar` e `QProgressBar::chunk`) com altura fixa de 14px e `border-radius: 7px;`.
  - Inserção de espaçador vertical (`cre_layout.addStretch()`) preservando a proporção orgânica compacta dos controles sem distorções geométricas.
- **Erradicação de Quinas Vivas e Padronização da Doca Flutuante de Eventos (`FloatingDockWidget`):**
  - Ajuste do raio de curvatura da doca inferior (`#floatingDock`) de `34px` para `border-radius: 28px;`, eliminando a falha do Qt QSS que descartava o raio por exceder a meia-altura de 56px (56 / 2 = 28px) e revertia para um retângulo de cantos retos.
  - Padronização do badge de contagem de eventos (`#badgeEventCount`) com altura fixa de 28px, alinhamento centralizado e `border-radius: 14px;`, eliminando arestas rígidas retangulares.
  - Transformação dos botões "Limpar" (`#btnDockClear`) e "Expandir" / "Recolher" (`#btnDockToggle`) em botões de pílula contínua de 34px de altura (`border-radius: 17px; height: 34px; padding: 0 14px; border: none;`) em ambos os temas Dark e Light.
  - Padronização da doca flutuante em 28px de curvatura contínua e botões retráteis em 36px com `border-radius: 18px;`.
- **Erradicação de Quinas Vivas e Geometria Orgânica no Player de Inspeção Labial (`PreviewPlayer`):**
  - Padronização dos botões seletores de marcos temporais (`#btnMarkerP05`, `#btnMarkerP50`, `#btnMarkerP90`) em cápsulas pílula contínuas de 40px com `border-radius: 20px;`, altura fixa explícita e tratamento completo de estados (`:hover`, `:pressed`, `:checked`, `:disabled`).
  - Formatação do chip de timecode (`#lblTimecodeChip`) como cápsula semicircular de 26px (`border-radius: 13px; height: 26px; border: none;`), eliminando caixas retangulares duras no visor do monitor.
  - Fixação da altura de 34px no botão "Parar" (`#btnStopPreview`) e badge de backend (`#badgeBackendMpv`), com contorno pílula visível no estado desativado (`border-radius: 17px; background: #222329` em Dark, `#f1f2f6` em Light).
- **Erradicação de Quinas Vivas nas Fontes Ingeridas e Auditoria Acústica FFT:**
  - Padronização dos badges de formato de contêiner (`#badgeVFmt`, `#badgeAFmt`, `formatChip`) como cápsulas pílula de 24px com `border-radius: 12px; height: 22px; min-height: 22px; max-height: 22px; border: 1px solid`, eliminando as caixas retangulares duras de 90 graus nos cartões de vídeo de referência e áudio dublado.
  - Correção da geometria do chip de status FFT (`#chipFFT`, `statusPill`) com altura física de 28px e `border-radius: 14px; height: 26px; min-height: 26px; max-height: 26px; border: 1px solid`, sanando o descarte de raio do Qt QSS que revertia para um retângulo pontiagudo.
  - Padronização do indicador de fontes (`#chipSourcesCount`) em pílula de 28px de altura (`border-radius: 14px;`) e botão de ação secundária "Trocar arquivos" (`#btnChangeFiles`) com altura fixa de 28px (`border-radius: 14px;`) e cursor de mão nos temas Dark e Light.

## [1.2.0] - 2026-10-24

### Corrigido
- **Padronização Universal de Cantos Arredondados e Eliminação Irrestrita de Retângulos Rígidos:**
  - Aplicação estrita de geometria curva contínua e pílulas ovais (`border-radius: 999px`) em 100% dos botões, chips, badges, campos e pseudo-estados (`:hover`, `:pressed`, `:disabled`, `:focus`), erradicando qualquer aresta reta ou quina de 90 graus residual na interface.
  - Arredondamento contínuo irrestrito em 100% dos widgets da aplicação em ambos os temas (Dark e Light): `QFrame` (`24px`), `QDialog`, `QMessageBox` e `CompletionDialog` (`28px`), `QToolTip` (`12px`), `QMenu` (`18px`, itens `10px`), barras de rolagem `QScrollBar` horizontal e vertical (`4px`), listas suspensas `QComboBox QAbstractItemView` (`16px`, itens `10px`), campos de entrada `QLineEdit`, `QDoubleSpinBox` e `QSpinBox` (`999px`), áreas de texto `QPlainTextEdit` e agrupamentos `QGroupBox` (`20px`), subcards de arquivo (`fileBox`, `cardFileV`, `cardFileA`) e container do slider (`20px`).
  - Preservação mandatória de curvatura arredondada contínua (`border-radius: 32px;`) ao alternar o modo de edição no gerenciador de layout (`WorkspaceLayoutManager.toggle_edit_mode`), impedindo a regressão para bordas quadradas durante o reposicionamento dos cards.
  - Recorte geométrico arredondado contínuo via `QPainterPath` (`clip_path.addRoundedRect(0, 0, w, h, 28, 28)`) no `CorrelationView.paintEvent`, prevenindo vazamento de linhas de grade e curvas espectrais fora dos cantos arredondados do cartão.
  - Padronização geométrica e cromática do modal de seleção de trilhas (`StreamSelectorModal`) com cantos de 28px no diálogo, 24px nos cards internos, pílulas ovais nos controles e paleta monocromática neutra (`badgeNeutral`).
  - Implementação da classe `StyleEngine` com método utilitário estático `apply_universal_rounded_tokens(theme_mode)` e exportação de helpers modulares para geração determinística de estilos curvos.
- **Depuração e Higienização da Topbar e Expurgo de Elementos Inoperantes:**
  - Padronização determinística dos botões e pills do cabeçalho via `MainWindow.setup_topbar_actions()`: altura uniforme e compacta de 34px, geometria em pílula semicircular matematicamente exata (`border-radius: 17px;` proporcional à meia-altura de 34px) sanando a falha do Qt QSS que revertia `border-radius: 999px` para retângulos rígidos de 90 graus.
  - Eliminação de truncamento no badge de versão (`v1.2.0`), com centralização explícita (`qproperty-alignment: AlignCenter;`), alinhamento `Qt.AlignCenter` e dimensionamento com margem generosa de segurança (`max(76, text_w + 38)`).
  - Prevenção de duplicidade de padding em `pillWorkspace` (`padding: 0px;` no QSS delegando espaçamentos internos ao layout), exibindo integralmente "Espaço de trabalho" e "Modo Claro" / "Modo Escuro".
  - Expurgo sumário do botão inoperante "Modo Edição" da Topbar visível, consolidando o layout estático proporcional e sem elementos residuais.
  - Confinamento estrito do grid técnico de cruzes ortogonais (+) do `paintEvent` à área útil de conteúdo abaixo da Topbar (`start_y >= topbar_bottom + 24px`), impedindo que cruzamentos decorativos vazem ou sobreponham elementos de navegação do cabeçalho.
- **Refatoração do Seletor de Sensibilidade e Botões em Pílula Orgânica:**
  - Implementação do componente `SensitivitySelectorWidget` (`src/ui/components/sync_controls.py`) com container segmentado em pílula (`border-radius: 999px; background-color: #26272d` em Dark e `#eceef4` em Light), botões internos ovais de 26px de altura e destaque da opção ativa em alto contraste.
  - Disponibilização do contrato `SensitivitySelectorWidget.set_sensitivity_step(step_ms: int)` e sinal `step_changed`.
  - Padronização do botão "Resetar" (`#btnResetOffset`) como pílula contínua (`border-radius: 999px;`) com padding simétrico.
  - Estilização de botões desativados (`:disabled`) em `src/ui/style.py` com `border-radius: 999px;` explícito, eliminando quinas cinzas retangulares em `#btnStopPreview` e outros controles.
  - Refinamento do slider temporal com `QSlider { background: transparent; border: none; }` para erradicar qualquer borda intermediária quadrada.
- **Ativação e Ancoragem da Esteira Assíncrona ("Sincronizar e Concluir"):**
  - Implementação da interface pública `MainWindow.start_sync_pipeline()` com despacho determinístico da esteira.
  - Ancoragem persistente mandatória da instância da thread trabalhadora em `self.active_pipeline_worker = worker`, prevenindo coleta prematura pelo garbage collector do Python.
  - Fortalecimento de `UnifiedDropZone._on_confirm_clicked()` com inspeção automática de contingência sobre fontes ingeridas, prevenindo retornos silenciosos inertes.
  - Validação ponta a ponta com as mídias reais de Os Vingadores (`test_live_avengers_pipeline.py`) confirmando extração PCM mono 16kHz via FFmpeg, correlação FFT com pico em -829 ms, atualização espectral no card 03, movimentação do slider e ativação dos marcadores de lip-sync (5%, 50%, 90%).
- **Contrato `CustomStyleEngine`:**
  - Implementação da classe `CustomStyleEngine` em `src/ui/style.py` com o método estático `enforce_universal_pill_radius(theme_mode: Literal["dark", "light"] = "dark") -> str` e função de conveniência modular.
- **Contorno Recortado na Área de Drop (Dropzone Corner Clipping):**
  - Isolamento estrito da borda pontilhada no `#dropFrameEmpty` e neutralização do contorno recortado no container raiz (`UnifiedDropZone`), eliminando o vazamento de borda interna sob a linha tracejada com cantos arredondados (`border-radius: 24px`).
  - Configuração de fundo transparente em `QStackedWidget` nas folhas de estilo de ambos os temas para evitar artefatos de herança de estilo sobre os componentes filhos.
- **Geometria de Cantos Arredondados Contínuos (One UI / Modern Card Ergonomics):**
  - Sanado o defeito de renderização do Qt QSS onde a especificação `border-radius: 999px` em elementos com altura inferior a 1998px falhava silenciosamente e revertia para cantos retangulares de 90 graus.
  - Aplicação de raios exatos proporcionais à metade da altura dos componentes: 12px para chips/badges, 16px-18px para botões secundários e botões de micro-passo (`-250 ms`, `+250 ms`), 20px para caixas de telemetria (`metBox`), 22px para botões primários ("Selecionar Arquivos..."), 24px para o monitor de prévia labial e 34px para o dock flutuante.
- **Harmonização Cromática e Visual do Modo Claro:**
  - Erradicação de caixas pretas duras residuais no miniplayer de inspeção labial e caixas de contraste, mapeando o fundo do visor para `#eceef4`, chips de timecode para `#ffffff` com texto `#16181d`, barra de progresso para `#e1e4ed`/`#3e82f7` e bordas para `#dcdfe8`.
  - Alinhamento vertical centralizado do badge de passthrough ("Zero re-encode") no cabeçalho do card de saída do remux.
- **Otimização Dimensional da Dropzone Vazia e Expansão Dinâmica:**
  - Compactação da Dropzone vazia para altura máxima de 240px (`QSizePolicy.Fixed`), garantindo que tanto a área de drop quanto o card "Saída do remux" caibam simultaneamente no viewport padrão (800px) sem gerar barras de rolagem verticais.
  - Implementação de transição dinâmica via `update_dropzone_state(has_files: bool)` expandindo a área para dimensão fluida (`QSizePolicy.Preferred`, sem restrição de altura) quando os arquivos de mídia forem carregados.
- **Disparo e Encadeamento Assíncrono do Botão "Sincronizar e Concluir":**
  - Resolução definitiva da inércia visual na esteira unificada de alinhamento acústico e multiplexação.
  - Correção de exceção fatal de assinatura (`TypeError`) no construtor de `UnifiedPipelineWorker` com suporte a `parent: Optional[object] = None`.
  - Compatibilização de campos no modelo `RemuxJob`, sincronizando bidirecionalmente `target_track_id` e `target_audio_track_id` para prevenir falhas de inicialização em chamadas da interface, além da extração correta de áudio de referência via `ref_audio_file`.
  - Correção de atributo inconsistente `metrics.correlation_points` substituído pelo vetor matemático real `metrics.correlation_curve`.
  - Implementação e amarração do contrato completo de sinais assíncronos: `analysis_started`, `step_progress`, `correlation_ready`, `correlation_completed`, `preview_segments_ready`, `preview_ready`, `remux_progress`, `remux_completed`, `finished_success`, `execution_failed` e `log_message`.
  - Máquina de estados de acionamento do botão primário: desativação temporária (`setEnabled(False)`), atualização de rótulo para "Processando sincronização...", ativação de cursor de espera (`Qt.WaitCursor`) e restauração atômica (`_restore_action_button()`) ao concluir ou cancelar a operação.
  - Emissão dinâmica de telemetria espectral no visualizador FFT e ativação imediata dos marcadores de lip-sync no player spot check, com fallback transparente para `ffplay` quando `mpv` não estiver instalado e tratamento neutro de baixa confiança (< 0.40) preservando o pico estático detectado.
- **Compactação Dimensional da Coluna Esquerda e Prevenção de Overflow:**
  - Reestruturação das opções secundárias do Review Gate em linha horizontal compacta (`options_row`) e redução de padding vertical nas linhas de trilha (`trackRow`) para 8px e identificadores (`tid`) para 32px de altura, assegurando que o card "Saída do remux" e botões de ação fiquem simultaneamente visíveis em viewports padrão (>= 1366x768 e 1280x800) sem barras de rolagem.
- **Bloqueio de Scroll Acidental nos Seletores de Trilha:**
  - Implementação de `install_wheel_blocker(combobox)` e componente `NoWheelComboBox`, bloqueando alterações inadvertidas de faixa ao rolar a roda do mouse sobre comboboxes e repassando o evento de rolagem diretamente à área de rolagem pai (`QScrollArea`).
- **Clareza Semântica dos Chips de Ação das Faixas:**
  - Substituição de termos técnicos opacos "Copy" e "Align" por rótulos autoexplicativos: "Vídeo Intocado (Cópia Direta)" (V01), "Sincronizar e Alinhar" (A02) e "Manter como Secundária" (A01), com cálculo de largura dinâmica via `QFontMetrics` para prevenir corte textual.
- **Restauração Rápida de Recomendação e Heurísticas Preditivas:**
  - Adição do botão pílula "Restaurar Recomendação" no cabeçalho do Review Gate (`reset_to_recommended_state`), permitindo reverter instantaneamente qualquer ajuste manual para a arbitragem ótima original.
  - Implementação de `determine_smart_defaults(video, audio) -> SmartDefaultsConfig`, detectando automaticamente cadência PAL (25 fps áudio vs <= 24.2 fps vídeo) para marcar restauração de pitch e parametrizando o codec ideal (FLAC para lossless, E-AC3 para multicanais, Opus/AAC para estéreo).
  - Disponibilização do componente unificado `StreamReviewGate` (`src/ui/components/stream_review_gate.py`) e contrato de estado `StreamReviewState`.

### Adicionado
- **Gerenciador de Layout do Espaço de Trabalho (WorkspaceLayoutManager):**
  - Implementação de `WorkspaceLayoutManager` em `src/ui/workspace_layout.py` permitindo reorganização e redimensionamento persistente dos cards de trabalho via `QSettings`, com checagem de limites de coordenadas e restauração determinística para o layout padrão em caso de configurações corrompidas.
  - Adição do botão "Modo Edição" / "Concluir Layout" no cabeçalho superior e integração com o grid principal.
- **Controle de Sensibilidade e Amortecimento do Slider de Offset (DampedSlider & SliderSensitivityController):**
  - Implementação de `SliderSensitivityController` e `DampedSlider` em `src/ui/components/sync_controls.py` com modos de resolução granular: `Fino` (1 ms / 0.25x), `Normal` (10 ms / 1.0x) e `Amplo` (50 ms / 2.5x).
  - Segmented pill group (`btn_sens_fine`, `btn_sens_normal`, `btn_sens_coarse`) para comutação dinâmica de granularidade.
- **Dock Flutuante de Telemetria com Animação Fluida (FloatingDockWidget):**
  - Implementação de `FloatingDockWidget` em `src/ui/components/log_drawer.py` com expansão e recolhimento animados via `QPropertyAnimation` (140 ms, `QEasingCurve.InOutQuad`), indicador visual de pulso para novos eventos, contador dinâmico e botões de ação dedicados ("Limpar", "Expandir"/"Recolher").
- **Grade Modular de Fundo com Cruzes Ortogonais:**
  - Renderização geométrica em `paintEvent` da janela principal desenhando cruzes discretas (+) com espaçamento simétrico de 48px na paleta monocromática neutra (`#1f2329` em Dark e `#e2e5eb` em Light).
- **Esteira Completa de Sincronização e Multiplexação Ponta a Ponta:**
  - Implementação e validação do método público `execute_end_to_end_pipeline()`, disparando o pipeline assíncrono real de ponta a ponta com extração de amostras acústicas mono PCM via FFmpeg, correlação cruzada espectral FFT com detecção determinística de pico, injeção de atraso no contêiner MKV via `--sync` sem recodificação de vídeo (`mkvmerge`), e atualização visual dos marcadores de lip-sync no miniplayer (5%, 50%, 90%).
- **Sistema Didático de Recomendação Acústica (Audiophile Badges):**
  - Implementação das funções `format_audiophile_recommendation_badge` e `format_audiophile_discard_notice` no módulo de inspeção (`src/core/inspector.py`).
  - Identificação e destaque intuitivo de faixas de estúdio: classificação `ÁUDIO DE MAIOR FIDELIDADE` para fluxos bit-perfect sem perdas (TrueHD, FLAC, DTS-HD MA) e `MELHOR OPÇÃO RECOMENDADA` para fluxos imersivos multicanais (Dolby Atmos, Surround 5.1/7.1 AC-3/E-AC-3/DTS).
  - Justificativa educativa contextual no card de arbitragem explicando em linguagem acessível o motivo da priorização de faixas de alta fidelidade e alertando contra perdas de dinâmica em faixas comprimidas.
- **Cobertura de Testes de Sinais e Controles:**
  - Criação da suíte `tests/test_pipeline_signals.py` com 10 testes dedicados validando contratos de sinais, cancelamento resiliente, formatação de badges audiófilos e classes CSS de contêineres arredondados (elevando a suíte do projeto para 94 testes 100% aprovados).

- **Contratos e Geradores de Estilo para Ergonomia de Interface:**
  - Implementação das funções utilitárias `get_pill_button_style`, `get_compact_dropzone_style` e `get_telemetry_card_style` em `src/ui/style.py`.
  - Disponibilização dos métodos públicos `apply_theme(theme_name)`, `update_dropzone_state(has_files)` e `set_manual_offset(offset_ms)` em `SyncFrameMainWindow`, `UnifiedDropZone` e `SyncControls`.
- **Refatoração Estrutural de Apresentação com One UI e Ergonomia de Superfícies Contínuas:**
  - Transposição completa da geometria visual da interface para o paradigma de superfícies contínuas e cantos arredondados generosos (border-radius de 28px nos painéis/cartões principais `panelCard` e `bentoCard`, 22px em subcartões `subCard`, `fileCardWorkbench`, `streamRowCard`, `arbitrationCard`, `offsetCallout`, `metricCallout`, `viewportScreen`).
  - Formato de pílula contínua oval (border-radius de 999px) aplicado universalmente a todos os botões (`QPushButton`), caixas de seleção suspensa (`QComboBox`), campos de texto (`QLineEdit`), barras de progresso (`QProgressBar`), manípulos deslizantes (`QSlider::handle`) e chips de estado (`roleBadge`, `streamActionChip`, `streamIdTag`, `systemChip`, `badgeNeutral`, `badgeSignal`, `badgeGreen`, `badgeAmber`, `timecodeChip`).
  - Transformação da barra de eventos em dock flutuante inferior (`floatingDock`, border-radius de 34px) com margens laterais elevadas (24, 0, 24, 14) e alinhamento centralizado, integrando botões pílula e etiqueta contadora de eventos.
  - Implementação de colapso responsivo vertical no `resizeEvent`: reorganização automática das colunas em pilha única vertical (`QBoxLayout.TopToBottom`) quando a largura da janela for inferior a 960px e retorno para layout lado a lado (`QBoxLayout.LeftToRight`) em larguras superiores ou iguais a 960px.
  - Formalização das funções de estilo `get_theme_tokens(mode)` e `apply_one_ui_monochrome_theme(app, mode)` garantindo fidelidade estrita à paleta monocromática neutra (Dark: `#000000`, `#1b1c20`, `#26272d`, `#33343b`, `#f2f3f7`, `#9a9eac`, `#2d2f36`; Light: `#f1f2f6`, `#ffffff`, `#eceef4`, `#e1e4ed`, `#16181d`, `#6a7080`, `#dcdfe8`).
  - Expansão da suíte de testes unitários para 97 testes (100% aprovados), validando tokens, colapso responsivo e geometria da dock flutuante.
- **Estética dos Seletores de Opção (Checkboxes com Visto Verde Nítido):**
  - Substituição de caixas sólidas monocromáticas ambíguas por indicadores com cantos arredondados contendo um glifo de visto/check verde esmeralda nítido (`check_glyph.png`, vetor anti-aliased renderizado dinamicamente via `QPainter` com stroke de 2.4px).
  - Conformidade estrita com o design system monocromático nos temas Dark e Light, integrando o glifo visual através do seletor `QCheckBox::indicator:checked`.
- **Erradicação de Placas Retangulares Duras em Contêineres de Opções e Deslizante:**
  - Envelopamento da linha de opções do Review Gate no contêiner estilizado `optionsContainer` (`#frameOptions`, `border-radius: 6px`, borda cirúrgica de 1px).
  - Envelopamento do controle deslizante e rótulos de amplitude temporal no contêiner estilizado `sliderContainer` (`#frameSlider`, `border-radius: 8px`, borda cirúrgica de 1px).

---

## [1.1.3] - 2026-10-24

### Corrigido
- **Erradicação Definitiva do Truncamento de Badges e Chips no Stream Review Gate:**
  - Substituição dos layouts horizontais monolíticos comprimidos por cartões estruturados em dois níveis (`streamRowCard`), eliminando o estrangulamento espacial entre seletores e rótulos na coluna esquerda.
  - Linha superior com respiração visual ampla para identificador monoespacado (`streamIdTag`), badge de classificação com auto-fit dinâmico (`roleBadge`) e chip de ação/estado alinhado à direita (`streamActionChip` com largura mínima >= 64px), extinguindo cortes visuais em "Melhor Imagem", "Português Oficial", "Referência Fixa", "Copy" e "Align".
  - Linha inferior dedicada com menu suspenso expansivo (`streamCombo`) ou descrição técnica (`streamDesc`) ocupando toda a largura horizontal do cartão.
  - Implementação da função `update_role_badge` com cálculo dinâmico de largura via `QFontMetrics` e folga proporcional (`minWidth >= 88px`), garantindo acomodação integral do texto mesmo com variações tipográficas do sistema.
  - Disponibilização dos métodos utilitários `get_role_badge_style` e `get_action_chip_style` em `src/ui/style.py`.

### Refatorado
- **Decomposição Modular e Desobstrução da Coluna Esquerda:**
  - Reestruturação da coluna de trabalho em 3 blocos visuais autônomos com separação simétrica (12px–16px): Bloco de Fontes Ingeridas (`block_sources`), Bloco de Diagnóstico e Arbitragem de Dublagem (`frame_arbitration`) e Bloco de Stream Review Gate (`block_review`).
  - Implementação do contrato formal de instanciação `configure_stream_row(track_id, role_badge, description, action_chip, combo=None) -> QWidget`.
  - Implementação do algoritmo de elisão central de nomes de arquivo `elide_filename` (ex.: `The.Avengers...1-DTOne.mkv`), preservando prefixo, sufixo do tronco e extensão original para garantir legibilidade técnica sem desbordamento horizontal nos menus e mantendo o caminho integral disponível via tooltip (`Qt.ToolTipRole`).

### Adicionado
- **Cobertura de Testes de Layout e Anti-Truncamento:**
  - Adição de testes unitários em `tests/test_ui_ingestion_and_themes.py` validando os contratos de `configure_stream_row`, middle elision de `elide_filename`, largura dinâmica anti-truncamento de `update_role_badge`, estilizações de badges/chips e existência dos 3 recipientes autônomos (elevando a suíte para 77 testes 100% aprovados).

---

## [1.1.2] - 2026-10-23

### Corrigido
- **Restauração da Transição de Estado na Ingestão de Arquivos:**
  - Resolução definitiva do desacoplamento onde o arrasto de arquivos ou seleção via diálogo nativo registrava telemetria mas mantinha a interface estática no estado vazio (Página 0).
  - Implementação do contrato formal `handle_files_ingested(file_paths: List[str]) -> None` no `UnifiedDropZone` e na `MainWindow`, gerenciando a transição determinística: 1 arquivo direciona para aguardo do segundo na Página 1, e 2 arquivos acionam a inspeção técnica de streams e o avanço para o Review Gate (Página 2).
  - Implementação do método `update_sources_view(media_sources: List[MediaSourceInfo]) -> None` renderizando metadados estruturados de forma robusta e defensiva nos cartões emparelhados de mídia.
  - Correção de resiliência em `evaluate_media_streams` para aceitar tanto caminhos em string quanto listas pré-inspecionadas de metadados, eliminando exceções não tratadas durante o auto-matching.
- **Erradicação de Regressões de Contraste e Quebra de Herança no Modo Claro:**
  - Expulso qualquer estilo inline residual que impunha fundos escuros estáticos (`#141414`, `#1c1c1c`) durante eventos de arrasto (`dragEnterEvent`/`dragLeaveEvent`), substituídos por propriedades dinâmicas do Qt (`dragOver`) integradas ao motor QSS.
  - Removido estilo inline escuro no título da gaveta de registros de eventos (`LogDrawer`), garantindo legibilidade perfeita com tipografia `#191c1a` sobre superfícies neutras `#f1f3ef` no modo claro.
  - Implementação do método `apply_application_theme(theme_mode: Literal['dark', 'light']) -> None` executando repolimento atômico e recursivo de estilos em todos os nós filhos (`unpolish`/`polish`), eliminando vazamentos de especificidade CSS e colisões preto-no-preto ou branco-no-branco.
  - Fidelidade estrita à paleta 100% monocromática neutra sem cores saturadas (Dark: `#0a0b0d` / `#111317` / `#eef0f2`; Light: `#f2f3f1` / `#ffffff` / `#191c1a`).

### Adicionado
- **Suíte de Testes Automatizados de Ingestão e Temas:**
  - Criação de `tests/test_ui_ingestion_and_themes.py` cobrindo transições de estado (Página 0 -> 1 -> 2), validação de contratos de `MediaSourceInfo`, comutação atômica de temas e contraste de elementos de interface (totalizando 72 testes aprovados).

---

## [1.1.1] - 2026-10-23

### Adicionado
- **Arbitragem Determinística de Faixas de Áudio Duplicadas (Substituição de Áudio PT Inferior):**
  - Heurística determinística de 3 níveis para arbitrar trilhas no mesmo idioma (dublagem PT pré-existente no vídeo base vs. dublagem externa):
    - Prioridade 1: Quantidade de canais (7.1 > 5.1 > 2.0 > 1.0).
    - Prioridade 2: Hierarquia de codecs de preservação (Lossless FLAC/TrueHD > E-AC3/AC3/Opus/DTS > AAC > MP3).
    - Prioridade 3: Bitrate nominal (kbps).
  - Descarte automático da faixa embutida inferior do arquivo de base via flags de exclusao `--audio-tracks !<id>` no `mkvmerge` quando a externa for superior.
  - Banner contextual explicito no Review Gate com opcao de reversao manual pelo operador antes da multiplexacao.
- **Suíte de Testes para Arbitragem de Streams:**
  - Adicao de `tests/test_stream_arbitration.py` com cobertura completa de canais, codecs, taxas de bits, reversao e comandos mkvmerge (totalizando 67 testes unitarios).

### Corrigido
- **Responsividade e Modo Janela:**
  - Resolucao de truncamento e corte lateral em dimensoes compactas (1024x600, 1280x720) atraves de flexibilizacao de larguras e `QScrollArea` com rolagem sob demanda.
  - Remocao definitiva da barra residual horizontal sob a topbar (`pipeline_ruler`).
- **Motor de Temas 100% Monocromatico (Dark e Light Mode):**
  - Restauracao da comutacao dinamica e funcional entre Modo Escuro e Modo Claro.
  - Erradicacao total de cores saturadas (verde, azul, ciano, limao) em prol de paleta neutra preto-e-branco e escala de cinza cirurgica em ambos os modos.
  - Correcao de contraste e legibilidade de textos no modo claro atraves da remocao de estilos inline rigidos.

---

## [1.1.0] - 2026-10-23

### Adicionado
- **Detecção de Descontinuidade Temporal Não Linear (Cortes de Montagem vs. Deriva Linear):**
  - Algoritmo de diferenciação multi-janela identificando variações abruptas em degrau ($\Delta\text{Step}$) geradas por logos de distribuidora, cortes de montagem ou aberturas ausentes ($T_1 \approx T_2 \ll T_3$).
  - Bloqueio automático de time-stretch cego com emissão de relatório de corte `DiscontinuityReport`, aviso contextual visual na interface e código de saída 2 na CLI.
- **Métrica de Confiança Acústica Robusta (PSLR & Piso de Ruído):**
  - Cálculo de Peak-to-Side-Lobe Ratio (PSLR) e escore Z estatístico contra o piso de ruído ($\text{Confidence} = (\text{Peak} - \mu_{\text{noise}}) / \sigma_{\text{noise}}$).
  - Bloqueio de alinhamento cego e exigência de intervenção quando $\text{PSLR} < 3.5$ ou confiança $< 0.45$.
- **Compensação Determinística de Carimbos de Contêiner (`start_time` e Edit Lists):**
  - Probing profundo de carimbos `format.start_time`, `stream.start_time` e metadados de listas de edição (`elst`) em contêineres MP4/MOV/MKV.
  - Cálculo do offset líquido: $\text{Offset}_{\text{net}} = \text{Offset}_{\text{acústico}} + (\text{PTS\_start}_{\text{ref}} - \text{PTS\_start}_{\text{target}})$, injetado diretamente no `--sync` do `mkvmerge`.
- **Desaceleração com Restauração Tonal para Masters PAL (25 fps):**
  - Filtro dedicado para restauração analógica de pitch drop: `asetrate=r=48000*24000/25000,aresample=resampler=soxr:osr=48000`.
  - Checkbox na interface gráfica e flag `--pal-pitch-restore` na CLI.
- **Parametrização de Codec de Recompressão de Áudio:**
  - Suporte à seleção explícita de formato para casos onde o time-stretch ou restauração de tom seja mandatório: FLAC (Lossless bit-perfect), Opus (160k/450k), E-AC3/AC3 (640k) e AAC (256k).
- **Verificação Acústica Pós-Remux em Malha Fechada (Closed-Loop Audit):**
  - Validação acústica automatizada do contêiner `.mkv` de saída extraindo amostra do áudio multiplexado e correlacionando com o áudio de referência ($|\text{Resíduo}| \le 5\text{ ms}$).
  - Renomeação para `.failed_audit.mkv` e aborto em caso de falha crítica ($> 15\text{ ms}$).
  - Selo visual de verificação no modal de término e logs detalhados.
- **Interface de Linha de Comando (CLI) Headless Completa:**
  - Execução no terminal sem display via flags `--video`, `--dub`, `--output`, `--keep-original`, `--pal-pitch-restore`, `--audio-codec`, `--ignore-cuts`, `--no-audit`.
  - Códigos de saída semânticos: `0` (sucesso auditado), `1` (dependência/erro de sistema), `2` (corte detectado), `3` (baixa confiança/piso de ruído).
- **Refinamento Ergonômico e Estético da Interface (Responsividade e Player Lip-Sync):**
  - Resolução definitiva de truncamento vertical no modo janela através de hierarquia de dimensionamento flexível em `QScrollArea`, eliminando cortes no card de Remux e na barra inferior.
  - Modernização das caixas de contraste e badges de telemetria (`.offsetCallout` e `.metricCallout`): substituição do formato sólido cru por molduras com cantos arredondados (`border-radius: 8px`), borda sutil de 1px e padding proporcional.
  - Redesenho da seção *03B Lip-Sync Spot Check & Player*: visor de sinal estilizado (`.viewportScreen`), display de timecode monoespacado e botões de marcadores de inspeção (`05%`, `50%`, `90%`) com destaque de estado ativo em Signal verde (`#d9f56b`).
  - Consolidação do stepper superior em indicador linear de status com separadores discretos, otimizando o aproveitamento vertical de tela.
  - Implementação de métodos auxiliares `get_telemetry_badge_style()`, `get_player_viewport_style()` e `get_stepper_style()` em `src/ui/style.py`.
- **Suíte de Testes Expandida:**
  - Inclusão de `tests/test_discontinuity.py` elevando a suíte de testes para 59 testes unitários (100% aprovados).

### Corrigido
- **Erradicação de Artefatos Visuais e Caixas Pretas Duras:**
  - Aplicação universal de `background: transparent; border: none;` no seletor base de `QLabel` nos temas Dark e Light, eliminando caixas retangulares escuras sobrepostas aos cards e seções.
  - Remoção de sobrescritas pontuais de folhas de estilo em `UnifiedDropZone`, `PreviewPlayer`, `SyncControls` e diálogos modais que provocavam queda de herança de fundo.
  - Correção do contraste, tipografia e contenção espacial em tags, badges, chips de dados e indicadores de telemetria.

### Modificado
- **Consolidação do Stepper em Linha de Progresso Contínua:**
  - Substituição do container segmentado de botões e caixas do stepper por uma régua de progresso linear contínua e minimalista de 2px (`QProgressBar#pipelineRuler`) integrada à borda inferior da barra superior.
  - Liberação de espaço vertical na bancada de trabalho mantendo total compatibilidade retroativa de controle de fases da pipeline.
- **Harmonização do Bloco de Identidade e Topbar:**
  - Integração do título da aplicação, subtítulo técnico e breadcrumb em layout com transparência contínua e separador vertical sutil de 1px.
- **Novas Funções Auxiliares de Estilização em `style.py`:**
  - Implementação e exportação de `get_clean_badge_style()`, `get_telemetry_display_style()` e `get_topbar_brand_style()` para padronização de micro-badges com cantos arredondados e visores monoespacados.

---

## [1.0.0] - 2026-10-22

### Primeira Versão Estável (Release Oficial)
- **Reestruturação Visual da Interface Gráfica — Precision Bench (Media Alignment Workbench):**
  - Implementação da linguagem estética industrial inspirada no protótipo de bancada de precisão:
    - Paleta de alta densidade no modo escuro (`#0a0b0d` base, `#111317` painéis, `#282d34` divisórias) com realce no acento Signal verde-limão cirúrgico (`#d9f56b`) e texto de alto contraste (`#15190b`).
    - Paleta correspondente no modo claro (`#f2f3f1` base, `#fbfcfa` painéis, `#d9ddd7` linhas) com acento chartreuse (`#c1df50`).
  - Topbar técnica compacta (~54px) com marca "SyncFrame", subtítulo "MEDIA ALIGNMENT WORKBENCH", breadcrumb de sessão, chip de status "LOCAL WORKSPACE", alternador de tema dinâmico e indicador de versão.
  - Stepper de pipeline segmentado na barra superior ilustrando as 4 fases do processo: 01 Ingestão, 02 Auditoria, 03 Sincronização, 04 Remux.
  - Distribuição assimétrica em duas colunas responsivas envelopadas em `QScrollArea` com rolagem fluida e sem achatamento de widgets:
    - Coluna Esquerda (Operacional e Decisório): Ingestão unificada com subcards horizontais em par (vídeo de referência + dublagem), tabela de auditoria (Review Gate) com chips de codecs e ações (`Copy` / `Align`), e card de saída do remux sem perdas com botão primário Signal.
    - Coluna Direita (Auditoria Acústica e Instrumentação): Auditoria de canais nativos com avisos contextuais, tela de correlação FFT via `QPainter` com pico destacado em Signal, micro-ajuste temporal com grande display monoespacado, slider linear e botões de nudge (±1, ±10, ±50, ±250 ms), e player de validação labial (05%, 50%, 90%).
  - Gaveta de logs inferior estilo console (`Event log`) com contagem de eventos e formatação alinhada.
  - Preservação estrita de 100% dos fluxos de backend, chamadas de subprocessos e contratos matemáticos existentes.
- **Modal de Conclusão Estilizado com Custo Zero de Latência:**
  - Substituição do `QMessageBox.information` nativo pelo componente `CompletionDialog` (`src/ui/components/completion_dialog.py`), integrado à estética neutra monocromática.
  - Glifo discreto em verde utilitário, caixa de texto delimitada em tipografia monospace exibindo o caminho absoluto do arquivo MKV final.
  - Botão secundário *"Abrir Diretório"* com lançamento não-bloqueante do gerenciador de arquivos nativo do host (Dolphin, Nautilus, xdg-open) e fallback inteligente com cópia instantânea para a área de transferência (`QClipboard`).
  - Botão primário *"OK / Fechar"* com acionamento padrão imediato via tecla **Enter** ou **Esc**.
  - Montagem estática sem animações ou blur (latência imperceptível de 0ms).
- **Distribuição em Binário Único Autônomo (Standalone Linux ELF):**
  - Script automatizado de compilação `build_bin.sh` e especificação otimizada `syncframe.spec` para PyInstaller.
  - Empacotamento em arquivo único ELF (`dist/SyncFrame`) compatível com Nobara Linux e distribuições x86_64 baseadas em glibc.
  - Exclusão seletiva de módulos e bibliotecas não utilizadas do Qt (`QtWebEngine`, `QtQml`, `QtQuick`, `Qt3D`, `QtDesigner`, `tkinter`) para otimização de footprint e redução expressiva do tempo de inicialização.
  - Consumo dinâmico não invasivo de `ffmpeg`, `ffprobe` e `mkvmerge` do `$PATH` do sistema operacional host.
  - Blindagem de execução headless com mensagem instrutiva em `sys.stderr` caso `$DISPLAY` ou `$WAYLAND_DISPLAY` estejam ausentes.
- **Ingestão Agnóstica de Contêineres:**
  - Suporte completo a arquivos `.mkv`, `.mp4`, `.m4v` e `.mov`, com demuxing lossless em cópia direta (`-c:a copy`) para AAC, AC3, E-AC3, MP3, Opus, DTS e FLAC.
  - Probing resiliente com tratamento de átomo `moov` tardio e contêineres malformados.
- **Auto-Seleção Heurística Determinística:**
  - Análise comparativa imediata por pontuação de fidelidade de vídeo (resolução, codec, bitrate) e detecção autônoma de faixas de dublagem em português (`por`, `pt-br`, `pob`).
- **Auditoria Acústica no Review Gate:**
  - Verificação determinística de canais (Mono 1.0, Estéreo 2.0, Surround 5.1, Surround 7.1) e alerta contextual preventivo quando a dublagem for estéreo e a fonte original for multicanal surround.
- **Motor Acústico por Correlação FFT & Normalização de Sinal:**
  - Cálculo de desalinhamento temporal por correlação cruzada FFT multi-janela (5%, 50%, 85%) com filtro passa-faixa (300Hz-4000Hz).
  - Normalização estrita do contrato de sinal de offset: delay negativo no cabeçalho MKV (`--sync 0:-offset_ms`) e adiantamento no player (`--audio-delay=-offset_sec`) para dublagens atrasadas.
  - Time-stretch lossless sem alteração de tom via filtro `atempo` exclusivamente quando diagnosticada deriva contínua de framerate ($23.976 \leftrightarrow 24.000 \leftrightarrow 25.000$ fps).
- **Pipeline de Ação Única ("Jogou -> Confirmou -> Concluiu"):**
  - Eliminação de botões concorrentes em favor do fluxo linear de aprovação assistida em 1 clique via `UnifiedPipelineWorker`.
  - Botão contextual *"Cancelar Operação"* durante a execução.
  - Gaveta retrátil `CollapsibleSection` (*"Ajustes Avançados e Inspeção Labial"*) encapsulando waveform, micro-ajustes manuais ($\pm 50\text{ ms}$, $\pm 250\text{ ms}$, slider) e miniplayer labial (`mpv`).
- **Proteção e Estabilidade de Hardware:**
  - Throttling compulsório de subprocessos (`-threads 2`) e limitação de variáveis de ambiente (`OMP_NUM_THREADS=2`, `OPENBLAS_NUM_THREADS=2`) blindando o host (Intel Xeon E5-2667 v2) contra desarmes de proteção térmica/elétrica (OCP).
- **Suíte de Testes Automatizados:**
  - Cobertura expandida para 53 testes unitários automatizados (100% aprovados).

---

## [0.3.0] - 2026-10-22

### Adicionado
- **Diagnóstico do Sistema & Mitigação de Quedas de Hardware:**
  - Utilitário `diagnose_system_crash_logs()` em `src/utils/system_check.py` para inspeção automatizada dos logs anteriores do sistema operacional (`journalctl -b -1`).
  - Diagnóstico da causa-raiz do desligamento abrupto no host (Intel Xeon E5-2667 v2 + AMD RX 580 no Nobara Linux): desarme elétrico/térmico (OCP) sob concorrência desenfreada de 16 threads de FFmpeg em 4K UHD Atmos somada a reprodução acelerada por hardware no mpv.
  - Mitigação de sobrecarga em `run.sh` e `src/main.py`: fixação estrita das variáveis de ambiente de concorrência (`OMP_NUM_THREADS=2`, `OPENBLAS_NUM_THREADS=2`, `MKL_NUM_THREADS=2`, `VECLIB_MAXIMUM_THREADS=2`, `NUMEXPR_NUM_THREADS=2`).
  - Throttling de processos em `src/core/extractor.py` e `src/core/transformer.py`: injeção compulsória de `-threads 2` em todas as invocações de FFmpeg (`extract_reference_channel`, `extract_audio_lossless`, `apply_temporal_transform`).
  - Execução de esteira em baixa prioridade (`os.nice(5)`) no worker de background.

- **Formalização Matemática do Contrato de Sinal de Offset:**
  - Implementação de `calculate_signed_offset` e `map_offset_to_player_delay` em `src/core/correlator.py`.
  - Resolução da divergência de convenções de sinal:
    - Se o áudio dublado inicia *depois* do vídeo (atrasado), `offset_ms > 0` ($+\text{ms}$); exige avanço no contêiner (`mkvmerge --sync 0:-offset_ms`) e adiantamento no player (`mpv --audio-delay=-offset_sec`).
    - Se o áudio dublado inicia *antes* do vídeo (adiantado), `offset_ms < 0` ($-\text{ms}$); exige atraso positivo no contêiner e player.
  - Blindagem contra exaustão de RAM em arquivos longos (`load_wav_mono` com teto padrão de leitura de 600 segundos).

- **Fluxo de Ação Única & Simplificação Radical da Interface:**
  - Consolidação dos fluxos dispersos no modelo de ação linear ("Jogou -> Confirmou -> Concluiu") orquestrado por `UnifiedPipelineWorker` (`src/ui/workers/unified_pipeline_worker.py`).
  - Eliminação de botões concorrentes e redundantes ("Calcular Sincronia", "Iniciar Sincronização e Remux", "Executar Lossless Remux") em favor de um botão único principal: `"Sincronizar e Concluir"`.
  - Botão contextual `"Cancelar Operação"` acionável durante a execução com cancelamento gracioso de subprocessos.
  - Novo componente de gaveta retrátil `CollapsibleSection` (`src/ui/components/collapsible_section.py`) recolhido por padrão com alternador `[+] / [-]`, encapsulando a curva de correlação (`CorrelationView`), micro-ajustes manuais ($\pm 50\text{ ms}$, $\pm 250\text{ ms}$, slider) e o miniplayer de inspeção labial (`PreviewPlayer`).
  - Novo controle de alto contraste `AudioPreserveCheckbox` (`src/ui/components/audio_preserve_checkbox.py`) com fundo esmeralda `#10b981`, ícone SVG de checkmark nítido quando ativo, e texto dinâmico inequívoco (`"Preservar áudio original em inglês: Sim (Faixa Secundária)"` vs `"Não"`).
  - Auditoria e saneamento completo de herança visual no tema claro, eliminando cores escuras inline fixadas (`#141414`, `#121212`, `#ffffff`) em favor de classes semânticas QSS neutras.

- **Expansão da Suíte de Testes Automatizados:**
  - Criação de `tests/test_system_diagnostics.py` e `tests/test_ui_components.py`.
  - Novos testes de cálculo de offset com sinal e mapeamento de atraso em `tests/test_correlator.py`.
  - Total de 44 testes unitários automatizados (100% aprovados).

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
  - Suporte estruturado e reativo a temas Claro e Escuro Neutros com alternador dinâmico no cabeçalho via `apply_theme` e `get_theme_qss`.
  - Remoção de insígnias e textos descontextualizados ("Anti-Slop Engine"), mantendo cabeçalho puramente técnico com numeração de versão.
  - Resolução definitiva de achatamento e sobreposição de widgets em modo janela via envelopamento do layout em `QScrollArea` com `setWidgetResizable(True)` e barra de rolagem vertical sob demanda.
  - Substituição dos cards duplos de drop por um componente central unificado (`UnifiedDropZone`) com máquina de estados (vazio -> 1 arquivo -> Review Gate tabular inline).
  - Testes automatizados offscreen em `tests/test_unified_drop_zone.py` e `tests/test_ui_layout_responsiveness.py` validando resizes para `1280x800`, `1024x650`, `900x550` e `800x540`.

- **Suporte Agnóstico a Contêineres (MP4, M4V, MOV, MKV) & Auditoria Acústica (v0.2.0):**
  - Probing profundo e resiliente em `src/core/inspector.py` via `probe_media_file` (`ffprobe -analyzeduration 100M -probesize 50M` com fallback automático `-err_detect ignore_err`), garantindo leitura íntegra de arquivos com átomo `moov` no final ou cabeçalhos truncados.
  - Dataclasses enriquecidas em `src/core/models.py`: `AudioProfile`, `MediaContainerInfo`, `ExtractedAudioResult` e função `format_channel_layout_label` (Mono 1.0, Estéreo 2.0, Surround 5.1, Surround 7.1).
  - Extração não destrutiva de áudio em `src/core/extractor.py` via `extract_audio_lossless` em modo cópia direta de stream (`ffmpeg -c:a copy`), preservando os codecs nativos (AAC, AC3, EAC3, MP3, Opus, DTS, FLAC) e fallback para FLAC multicanal sem perdas para formatos exóticos.
  - Montagem de comando de remux híbrido em `src/core/remuxer.py` (`build_mkvmerge_hybrid_command`) e demuxing automático em staging para contêineres MP4/MOV, blindando o `mkvmerge` contra inconsistências de empacotamento.
  - Card de Auditoria Acústica no Review Gate de `src/ui/components/unified_drop_zone.py` com badges de origem (`MP4 -> MKV Remux`), layout de canais, especificação acústica (`AAC • 48.000 Hz`) e alerta contextual neutro quando a dublagem for Estéreo 2.0 e o áudio original for 5.1/7.1.
  - Suporte formal a `.mkv`, `.mp4`, `.m4v`, `.mov` nos diálogos de arquivos e validação do drag-and-drop.
  - Suíte de testes em `tests/test_container_handling.py` elevando a suíte para 30 testes unitários automatizados (100% aprovados).
