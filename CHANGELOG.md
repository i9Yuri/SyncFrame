# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato segue as diretrizes do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.2.0] - 2026-10-24

### Corrigido
- **Disparo e Encadeamento Assíncrono do Botão "Sincronizar e Concluir":**
  - Resolução definitiva da inércia visual na esteira unificada de alinhamento acústico e multiplexação.
  - Correção de exceção fatal de assinatura (`TypeError`) no construtor de `UnifiedPipelineWorker` com suporte a `parent: Optional[object] = None`.
  - Compatibilização de campos no modelo `RemuxJob`, sincronizando bidirecionalmente `target_track_id` e `target_audio_track_id` para prevenir falhas de inicialização em chamadas da interface.
  - Correção de atributo inconsistente `metrics.correlation_points` substituído pelo vetor matemático real `metrics.correlation_curve`.
  - Implementação e amarração do contrato completo de sinais assíncronos: `analysis_started`, `step_progress`, `correlation_ready`, `correlation_completed`, `preview_ready`, `finished_success`, `execution_failed` e `log_message`.
  - Máquina de estados de acionamento do botão primário: desativação temporária (`setEnabled(False)`), atualização de rótulo para "Processando sincronização...", ativação de cursor de espera (`Qt.WaitCursor`) e restauração atômica (`_restore_action_button()`) ao concluir ou cancelar a operação.
  - Emissão dinâmica de status e telemetria gráfica no visualizador de correlação espectral FFT e no player de spot check.

### Adicionado
- **Sistema Didático de Recomendação Acústica (Audiophile Badges):**
  - Implementação das funções `format_audiophile_recommendation_badge` e `format_audiophile_discard_notice` no módulo de inspeção (`src/core/inspector.py`).
  - Identificação e destaque intuitivo de faixas de estúdio: classificação `ÁUDIO DE MAIOR FIDELIDADE` para fluxos bit-perfect sem perdas (TrueHD, FLAC, DTS-HD MA) e `MELHOR OPÇÃO RECOMENDADA` para fluxos imersivos multicanais (Dolby Atmos, Surround 5.1/7.1 AC-3/E-AC-3/DTS).
  - Justificativa educativa contextual no card de arbitragem explicando em linguagem acessível o motivo da priorização de faixas de alta fidelidade e alertando contra perdas de dinâmica em faixas comprimidas.
- **Cobertura de Testes de Sinais e Controles:**
  - Criação da suíte `tests/test_pipeline_signals.py` com 10 testes dedicados validando contratos de sinais, cancelamento resiliente, formatação de badges audiófilos e classes CSS de contêineres arredondados (elevando a suíte do projeto para 94 testes 100% aprovados).

### Refatorado
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
