# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato segue as diretrizes do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [2.0.0] - 2026-10-25

### Adicionado
- **Faixa Declarativa de Especificações do Arquivo Resultante (Target Output Summary / Resulting File Specs):**
  - Substituição da antiga linha de auditoria estática por uma barra horizontal reativa e declarativa com componentes visuais em pílulas arredondadas (`resultingSpecsBar`, `border-radius: 20px`, altura mínima 38px).
  - Exibição e consolidação em tempo real de 7 metadados técnicos padronizados do arquivo de saída: contêiner (`MKV Matroska` nativo ou `MKV Remux`), modo de processamento com classes cromáticas de alto contraste (`Cópia Direta (Passthrough)` com realce verde `#2fb16b` / `resultingPillGreen` ou `Re-encode [CODEC] (PAL 24fps)` com realce âmbar `#e8963a` / `resultingPillAmber`), formato comercial (`DOLBY ATMOS` em cápsula monocromática de alto contraste / `resultingPillSignal`, `DOLBY AUDIO 5.1`, `DTS-HD MA 7.1`, `FLAC LOSSLESS`), codec exato em caixa alta (`AC-3`, `E-AC-3`, `TRUEHD`, `DTS-HD MA`, `FLAC`, `OPUS`, `AAC`), topologia de canais decomposta com indicação explícita de surround, height/atmos e subwoofer LFE (`5.1 Surround (+Subwoofer)`, `7.1 Atmos (Surround + Height + Sub)`, `2.0 Estéreo (Sem LFE)`, `1.0 Mono (Sem LFE)`), frequência de amostragem padronizada com separador de milhar decimal (`48.000 Hz`) e taxa de bits nominal/real formatada (`640 kbps`, `3500 kbps`, `Bitrate Variável (VBR)`).
  - Reatividade bidirecional instantânea a alterações na seleção de áudio principal (`combo_target_audio`), comutação da restauração PAL (`check_pal_pitch`), seleção de codec de re-encode (`combo_audio_codec`) e seleção de vídeo de referência (`combo_video`).
  - Apresentação de fallback elegante de estado deselecionado (`Nenhum áudio selecionado`), contrato público `update_resulting_specs(self, track_info, remux_options) -> dict` e retrocompatibilidade estrita mantida com os atributos legados (`lbl_audit_origin`, `badge_audit_layout`, `lbl_audit_specs`).
- **Modo Inspeção de Mídia Única (Single-File Media Inspector):**
  - Transmutação automática e fluida da interface ao ingerir exatamente 1 arquivo — contêiner de vídeo (.mkv, .mp4, .m4v, .mov) ou faixa de áudio isolada (.ac3, .eac3, .aac, .dts, .flac, .m4a, .mp3, .wav, .opus) —, atuando como bancada técnica aprofundada sem requerer uma segunda fonte.
  - Probing profundo assíncrono e não-bloqueante via `SingleFileInspectionWorker` (QThread) e `inspect_single_media`, extraindo formato do contêiner, taxa de quadros, HDR/Dolby Vision, profundidade de bits, layout e canais de áudio, legendas e capítulos com tolerância a cabeçalhos truncados (`-err_detect ignore_err`).
  - Botão conectivo de rodapé (`btnConnectiveAction`, contorno tracejado com 22px de curvatura contínua) viabilizando a transição imediata para sincronização ao arrastar ou selecionar uma segunda fonte sem reiniciar o estado.
- **Review Gate Dinâmico para Múltiplas Fontes Ingeridas ($N \ge 2$) e Pooling Universal de Vídeo:**
  - Substituição da estrutura estática de 2 cartões no `UnifiedDropZone` (`block_sources`) por layout flexível reativo (`self.sources_layout = QHBoxLayout()`).
  - Geração dinâmica de cartões em cápsula arredondada contínua (`.fileBox`, raio de 20px) para qualquer quantidade $N \ge 2$ de arquivos carregados (`self.dynamic_source_cards`), com limpeza determinística em `reset()`.
  - Atualização dinâmica do badge de contagem de fontes para `f"{N} / {N} FONTES"` (ex.: `3 / 3 FONTES`).
  - Indexação e disponibilização de 100% dos fluxos de vídeo de todos os $N$ contêineres carregados no seletor "Melhor Imagem" (V01) com metadados técnicos completos (resolução, taxa de quadros, codec, contêiner e trilha).
- **Heurística de Pontuação e Ranqueamento em 4 Tiers para Áudio Secundário:**
  - Implementação de modelo determinístico de pontuação em 4 patamares (`compute_stream_quality_score` e `Inspector.rank_secondary_audio_streams`):
    - *Tier 1 (Lossless/Imersivo, Score 100):* TrueHD Atmos, DTS-HD MA 7.1, DTS:X, LPCM 7.1.
    - *Tier 2 (Imersivo Broadcast/Multicanal Full, Score 80):* E-AC-3 JOC (Dolby Digital Plus com Atmos), DTS-HD MA 5.1, DTS 5.1.
    - *Tier 3 (Multicanal Convencional, Score 65):* AC-3 5.1 (Dolby Digital legado).
    - *Tier 4 (Estéreo/Compactado, Score 40):* AAC 2.0, MP3, Opus 2.0.
  - Pré-seleção automática e exclusiva (checked) restrita à trilha original de maior escore do Tier 1. Trilhas redundantes ou de menor fidelidade (ex.: faixa AC-3 5.1 de compatibilidade quando TrueHD Atmos está presente) vêm desmarcadas por padrão.
- **Reconstrução do Dock Inferior como Hub de Ações Flutuante (TiltedDock Nativo PySide6/Qt6):**
  - Hub desacoplado com auto-dimensionamento restrito ao conteúdo (`fit-content`), curvatura contínua semicircular (`border-radius: 26px`), superfície translúcida (`rgba(27, 28, 32, 0.85)` / `rgba(255, 255, 255, 0.85)`), borda cirúrgica de 1px e sombra suave de elevação.
  - Micro-interações táteis de hover: ampliação fluida via `QPropertyAnimation` com curva de mola `QEasingCurve.OutBack` para 1.35x com destaque circular iluminado (`rgba(255, 255, 255, 0.14)` / `rgba(0, 0, 0, 0.08)`) e atenuação dos irmãos vizinhos (sibling dimming) para opacidade 0.45.
  - Integração do botão de alternância de tema (`theme_toggle`) no dock com ícones vetoriais sol/lua SVG adaptativos e micro-tooltip dinâmico contextual.
  - Reposicionamento dinâmico ancorado a 20px da borda inferior em `resizeEvent` e `showEvent`.
- **Popovers Wayland-Resilientes (`EventLogPopover` e `VersionInfoPopover`):**
  - Janelas suspensas com flags `Qt.Tool | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint` com cálculo de posicionamento clampeado nos limites da tela disponível (`QGuiApplication.primaryScreen().availableGeometry()`), eliminando falhas de captura em compositores Wayland.
  - Expansão das dimensões do console de logs para `820x520` (mais de 2.6x de área útil), retenção restrita a 1.000 linhas para prevenção de consumo de memória e fechamento imediato pela tecla `Escape`.
- **Esteira de Atualização Ativa e Comparação Semântica de Versões (`DependencyUpdateWorker`):**
  - Substituição da checagem ingênua (`!=`) por análise semântica estrita (`parse_semantic_version`), impedindo falsos positivos de atualização com versões remotas anteriores.
  - Disparo ativo de atualizações via Git (`git pull --ff-only`), download de releases binárias do GitHub ou pacotes de sistema (`pkexec dnf upgrade -y ffmpeg mkvtoolnix mpv`), com transmissão de telemetria linha a linha para o `EventLogPopover` e notificação toast no dock.
- **Topbar Desacoplada e Fixa (Sticky Detached Topbar):**
  - Desprendimento visual e estrutural do cabeçalho superior (`self.topbar`) da esteira de rolagem central, fixando a altura em 76px com superfície sólida opaca e linha divisória sutil de 1px.
  - Propagação contínua de eventos de rolagem (`wheelEvent`) na área do cabeçalho superior diretamente para o viewport da `QScrollArea`.
- **Controles de Sensibilidade do Slider Temporal (`SensitivitySelectorWidget`):**
  - Seletor segmentado em pílula (`1 ms`, `10 ms`, `50 ms`) no cabeçalho de *Alinhamento temporal* conectado ao `SliderSensitivityController` e `DampedSlider` para ajuste milimétrico de offset acústico.
- **Controlador Robusto de Inspeção Labial (`LipSyncController` & `PreviewPlayer`):**
  - Controlador desacoplado baseado em `QProcess` com terminação atômica e prevenção estrita de processos órfãos (`mpv` e fallback para `ffplay`).
  - Suporte a marcadores temporais (5% Abertura, 50% Meio, 90% Ato final) com compensação instantânea de delay (`--audio-delay`).
- **Auditoria Acústica Imersiva e Badge Reativo de Compatibilidade com Soundbars 7.1.4:**
  - Classificação determinística em estados `optimal` (verde para Atmos / 7.1 discreto) e `suboptimal` (âmbar para 5.1/estéreo) com `SmoothFadeTooltip` em fade suave de opacidade.
- **Conformidade Estrita de Metadados Matroska para Renderizadores DLNA/UPnP:**
  - Geração automatizada de argumentos certificados para Smart TVs e servidores DLNA (`--track-name`, `--language`, `--default-track-flag`, `--forced-display-flag`).
- **Manual Técnico Integral de Arquitetura (`ARCHITECTURE.md`):**
  - Documentação canônica exaustiva na raiz do repositório cobrindo 100% das funcionalidades, modelos, componentes de backend e de frontend.

### Modificado
- **Design System One UI 8.5 Curvo Contínuo:**
  - Erradicação de 100% dos cantos retos (90 graus) em toda a aplicação (botões, cards, dialogs, menus suspensos, sliders e tooltips) com padronização de raios contínuos de meia-altura (10px a 26px e pílulas ovais contínuas).
- **Paleta Monocromática Neutra no Review Gate:**
  - Substituição de contornos e realces azuis por tons monocromáticos neutros (`#50535e` no escuro, `#a3a8b8` no claro) e adaptação de badges de alto contraste sem tons azuis.
- **Purificação da Barra Superior:**
  - Transferência dos botões operacionais concorrentes (tema, versão, atualizações) para o dock flutuante desacoplado, mantendo a Topbar limpa e focada exclusivamente na identidade da bancada.

### Corrigido
- **Remoção de Elementos Decorativos de Fundo (Cruzes / Símbolos de +):**
  - Remoção completa da rotina matricial de pintura de grade em `paintEvent` da janela principal, garantindo superfícies sólidas e limpas em ambos os temas.
- **Erradicação do Retângulo Escuro de Fundo no Painel de Faixas Secundárias:**
  - Configuração de transparência integral em `frameSecondaryAudio`, `secondaryContainer` e `secondaryTrackCard`, permitindo que as opções assentem-se diretamente na superfície do cartão.
- **Transparência de Cantos e Legibilidade em Menus Suspensos (`QComboBox` / Review Gate):**
  - Desacoplamento de transparência em `QComboBoxPrivateContainer` com `Qt.WA_TranslucentBackground`, eliminando cantos brancos opacos, e correção de acesso aos sinalizadores de seleção no `DropdownHighlightDelegate`.
- **Eliminação de Bug de Desaparecimento de Ícones no Hover do Dock:**
  - Substituição de chamadas concorrentes por renderização vetorial estável direta via `QSvgRenderer` e `QPainter` unificado.
- **Geometria Esférica 1:1 no Slider de Alinhamento Temporal:**
  - Recalibração de altura fixa de 28px e manipulador horizontal esférico de 20x20px sem cortes ou distorções.

### Segurança e Performance
- **Proteção Térmica e de Hardware contra Desarme de Sistema (OCP Protection):**
  - Diagnóstico automatizado em `src/utils/system_check.py` (`diagnose_system_crash_logs`) e mitigação ativa contra desligamentos por sobrecorrente/desarme térmico em processadores com alto TDP (Intel Xeon E5-2667 v2).
  - Throttling compulsório de threads no FFmpeg (`-threads 2`), contenção em runtime (`OMP_NUM_THREADS=2`, `OPENBLAS_NUM_THREADS=2`, `MKL_NUM_THREADS=2`) e execução dos workers em baixa prioridade (`os.nice(5)`).
- **Auditoria de Pré-Voo e Provisionamento de Dependências do Sistema:**
  - Verificação síncrona pré-inicialização via `PreFlightChecker` auditando `ffmpeg`, `ffprobe`, `mkvmerge` e `mpv`, com modal One UI (`PreFlightDialog`) e instalação guiada com elevação de privilégios (`pkexec`).
- **Probing Assíncrono Profundo e Resiliente:**
  - Análise não-bloqueante profunda via `ffprobe` (`-analyzeduration 100M -probesize 50M`) com tolerância a erros (`-err_detect ignore_err`), viabilizando a ingestão de contêineres MP4 com átomo `moov` tardio e cabeçalhos truncados.

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
