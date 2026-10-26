# Arquitetura e Manual Técnico Integral do SyncFrame

Este documento constitui a referência técnica exaustiva, canônica e autocontida do **SyncFrame**. Ele foi estruturado especificamente para fornecer a qualquer engenheiro de software, pesquisador, Modelo de Linguagem de Grande Porte (LLM) ou agente autônomo de IA a compreensão integral e determinística de 100% da arquitetura, motores científicos, modelos de dados, interfaces gráficas, modelos de concorrência e estratégias de empacotamento do projeto, mesmo sem executar o código ou interagir com o ambiente de execução.

---

## 1. Visão Geral, Domínio e Invariantes de Engenharia

O **SyncFrame** é uma estação de trabalho desktop e ferramenta de linha de comando voltada à automação de alta fidelidade para sincronização temporal acústica e remux não destrutivo de fluxos de vídeo e áudio provenientes de contêineres multimídia heterogêneos (.mkv, .mp4, .m4v, .mov, além de faixas de áudio isoladas como .ac3, .eac3, .flac, .opus, .dts, .wav).

O problema central resolvido pelo software é a discrepância temporal (offset estático em milissegundos) e de cadência de quadros (deriva linear / time drift) entre uma faixa de áudio dublada de alta qualidade (ou idioma secundário) e uma fonte de vídeo de referência em altíssima definição (4K UHD / 1080p Bluray com HDR/Dolby Vision).

### 1.1 Invariantes Fundamentais do Sistema
Qualquer modificação ou extensão no SyncFrame deve respeitar os seguintes invariantes invioláveis:

1. **Zero-Loss Video Passthrough:** O fluxo de vídeo de referência nunca sofre transcodificação ou recompressão sob nenhuma circunstância. Ele é copiado bit-a-bit diretamente para o contêiner final via `mkvmerge` (`--video-tracks <ID>`).
2. **Zero Recompressão de Áudio Estático:** Quando a taxa de quadros (framerate) entre as fontes for idêntica (deriva linear negligenciável, drift ≈ 1.0000), o offset em milissegundos é aplicado puramente no cabeçalho do contêiner Matroska através da diretiva `--sync <TRACK_ID>:<OFFSET_MS>`. Nenhum ciclo de recompressão acústica é desperdiçado.
3. **Proteção Térmica e de Hardware (OCP Mitigation):** O sistema implementa salvaguardas rigorosas contra desligamentos por sobrecorrente/temperatura (Over-Current Protection - OCP) em processadores multi-core legados (ex.: Intel Xeon E5-2667 v2 com 8 núcleos / 16 threads). A extração acústica é throttled no FFmpeg via `-threads 2`, as bibliotecas matemáticas operam sob limitação de threads (`OMP_NUM_THREADS=2`, `OPENBLAS_NUM_THREADS=2`, `MKL_NUM_THREADS=2`) e workers assíncronos rodam com prioridade rebaixada (`os.nice(5)`).
4. **Isolamento de Staging e Limpeza Determinística:** Todos os arquivos intermediários (áudios mono PCM 16kHz, resumos espectrais, amostras de auditoria) são gerados em um diretório oculto isolado `.syncframe_tmp/` no diretório de trabalho, com expurgo garantido no encerramento normal ou anômalo via manipuladores `atexit` e interceptação de sinais `SIGINT`/`SIGTERM`.
5. **Design System Neutro Monocromático (One UI 8.5):** A interface do usuário adere à estética One UI 8.5, com paleta estritamente monocromática neutra, zero gradientes roxos/magentas de mockup genérico, ausência total de emojis em código, logs ou telas, e continuidade geométrica curvilínea universal (banimento total de cantos retos de 90 graus).

---

## 2. Mapa Estrutural do Repositório

A estrutura de arquivos do projeto é distribuída de forma modular:

```
SyncFrame/
├── build_bin.sh                      # Script Bash para compilação em binário único ELF via PyInstaller
├── syncframe.spec                    # Arquivo de especificação PyInstaller otimizado
├── run.sh                            # Script inicializador com verificação de ambiente e restrição de threads
├── requirements.txt                  # Dependências Python obrigatórias (PySide6, numpy, scipy)
├── CHANGELOG.md                      # Histórico cronológico de modificações e versões
├── GEMINI.md                         # Protocolo autônomo de memória (Segundo Cérebro)
├── ARCHITECTURE.md                   # Este documento (manual técnico integral)
├── src/
│   ├── __init__.py
│   ├── main.py                       # Ponto de entrada CLI e inicializador da interface gráfica
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py                 # Dataclasses fundamentais, contratos de dados e formatadores
│   │   ├── inspector.py              # Motor de inspeção e probing profundo via ffprobe e mkvmerge
│   │   ├── extractor.py              # Extrator de áudio acústico filtrado (PCM 16kHz bandpass)
│   │   ├── correlator.py             # Motor de correlação acústica FFT multi-janela (PROTEGIDO)
│   │   ├── transformer.py            # Motor de compensação temporal, time-stretch e restauração tonal (PROTEGIDO)
│   │   └── remuxer.py                # Orquestrador de remux final via mkvmerge e auditoria (PROTEGIDO)
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py            # Janela principal do aplicativo, barramento de eventos e layout responsivo
│   │   ├── style.py                  # Design System One UI 8.5, tokens de cores Dark/Light e folhas QSS
│   │   ├── workspace_layout.py       # Gerenciador persistente de layout e visibilidade de cartões
│   │   ├── assets/
│   │   │   ├── check_glyph.png       # Glifo de visto verde para caixas de seleção
│   │   │   ├── switch_*.png          # Ativos para botões de alternância
│   │   │   └── icon_*.svg            # Ícones vetoriais monocromáticos da Topbar e Dock
│   │   ├── components/
│   │   │   ├── __init__.py
│   │   │   ├── unified_drop_zone.py  # Zona de ingestão unificada, máquina de estados e Review Gate
│   │   │   ├── media_inspector_view.py # Bancada de inspeção técnica detalhada para arquivos unitários
│   │   │   ├── floating_action_dock.py # Dock inferior flutuante estilizado (TiltedDock em PySide6)
│   │   │   ├── event_log_popover.py  # Console modal expandido para telemetria e registros
│   │   │   ├── version_info_popover.py # Modal informativo de diagnósticos e versões do sistema
│   │   │   ├── completion_dialog.py  # Diálogo modal pós-processamento com acionamento do explorador
│   │   │   ├── preview_player.py     # Controlador de prévia labial assíncrono (MPV / FFplay)
│   │   │   ├── sync_controls.py      # Controles de offset, slider esférico e seletores de sensibilidade
│   │   │   ├── correlation_view.py   # Renderizador vetorial da curva de correlação acústica via QPainter
│   │   │   ├── custom_combobox.py    # Comboboxes customizados com isolamento de cantos e sem scroll acidental
│   │   │   ├── preflight_dialog.py   # Modal bloqueante para auditoria e instalação de dependências
│   │   │   ├── collapsible_section.py # Container sanfonado retrátil para opções avançadas
│   │   │   └── audio_preserve_checkbox.py # Seletor customizado de preservação de trilhas originais
│   │   └── workers/
│   │       ├── __init__.py
│   │       ├── unified_pipeline_worker.py # Thread trabalhadora principal da esteira de sincronização
│   │       ├── single_file_inspection_worker.py # Thread assíncrona de probing para a bancada técnica
│   │       └── dependency_update_worker.py # Thread em baixa prioridade para auditoria de ferramentas
│   └── utils/
│       ├── __init__.py
│       ├── disk_utils.py             # Validação prévia de capacidade de armazenamento em disco
│       ├── temp_manager.py           # Ciclo de vida e purga determinística de arquivos temporários
│       └── system_check.py           # Auditoria pré-voo de binários do SO e análise de falhas de hardware
└── tests/
    ├── test_*.py                     # 187 testes automatizados unitários e de integração
    └── fixtures/                     # Amostras sintéticas e arquivos de verificação
```

---

## 3. Modelos de Dados e Contratos Fundamentais (`models.py`)

O módulo `src/core/models.py` estabelece os contratos canônicos entre as camadas de inspeção, motores matemáticos, workers assíncronos e a camada de apresentação gráfica.

### 3.1 Dataclasses Centrais

#### `StreamMetadata`
Representa as propriedades atômicas de uma trilha de mídia identificada por probing:
- `index`: Índice ordinal da trilha dentro do contêiner.
- `codec_name`: Nome canônico do codec (`hevc`, `h264`, `ac3`, `eac3`, `truehd`, `dts`, `flac`, `aac`, `subrip`, etc.).
- `codec_type`: Categoria do fluxo (`video`, `audio`, `subtitle`).
- `channels`: Quantidade numérica de canais discretos (ex.: 1, 2, 6, 8).
- `channel_layout`: Topologia de canais (`stereo`, `5.1`, `5.1(side)`, `7.1`, `7.1.4`).
- `bit_rate`: Taxa de bits teórica ou real em bps (sanitizada contra falsos positivos de cabeçalho).
- `sample_rate`: Frequência de amostragem em Hz (ex.: 48000, 44100).
- `language`: Código ISO-639-2 do idioma (ex.: `por`, `eng`, `jpn`, `und`).
- `title`: Título descritivo embutido na trilha.
- `is_default`: Sinalizador booleano de trilha primária padrão no contêiner original.
- `is_forced`: Sinalizador booleano de exibição forçada (comum em legendas para partes em idioma estrangeiro).
- `width` e `height`: Dimensões em pixels (exclusivo para vídeo).
- `fps`: Taxa de quadros por segundo como float (exclusivo para vídeo).
- `is_immersive`: Sinalizador booleano determinando se a trilha possui metadados imersivos (Dolby Atmos, DTS:X, E-AC-3 JOC).
- `immersive_description`: Descrição textual de áudio imersivo (ex.: `"Dolby Atmos (TrueHD)", "Dolby Atmos (E-AC-3 JOC)"`).
- `perceptual_score`: Escore numérico de fidelidade acústica calculado para ranqueamento automático.

#### `StreamCandidate`
Encapsula o arquivo de mídia inspecionado, listando suas trilhas atômicas e resumos técnicos:
- `file_path`: Caminho absoluto do arquivo no sistema de arquivos.
- `container_format`: Formato do contêiner (`Matroska`, `QuickTime / MOV`, `MP4`, etc.).
- `duration_sec`: Duração total do contêiner em segundos.
- `video_streams`: Lista de instâncias `StreamMetadata` do tipo vídeo.
- `audio_streams`: Lista de instâncias `StreamMetadata` do tipo áudio.
- `subtitle_streams`: Lista de instâncias `StreamMetadata` do tipo legenda.
- `start_time`: Carimbo de data/hora inicial extraído do cabeçalho do contêiner (PTS start).

#### `ConsolidatedStreamSelection`
Representa a decisão explícita e auditada das trilhas que entrarão no remux final:
- `video_source_path`: Caminho da fonte que provê a trilha de imagem selecionada.
- `video_track_id`: Índice da trilha de vídeo a ser extraída.
- `target_audio_source_path`: Caminho da fonte de onde sairá o áudio dublado principal.
- `target_audio_track_id`: Índice da trilha de áudio dublada alvo da sincronização.
- `secondary_audio_tracks`: Lista de tuplas `(source_path, track_id, language, title)` representando faixas originais mantidas como secundárias.
- `preserve_subtitles`: Sinalizador booleano para inclusão de legendas das fontes.

#### `AutoMatchVerdict`
Resultado da heurística de emparelhamento automático executada ao carregar duas fontes:
- `reference_candidate`: Candidato eleito como fonte principal de vídeo de alta fidelidade.
- `target_candidate`: Candidato eleito como provedor da melhor dublagem em português.
- `confidence_score`: Valor normalizado (0.0 a 1.0) representando a certeza do emparelhamento.
- `recommendation_reason`: Texto explicativo justificando a escolha dos arquivos.

### 3.2 Funções de Formatação e Sanitização

O arquivo `models.py` também provê formatadores canônicos que alimentam a interface gráfica:
- `sanitize_stream_bitrate(raw_bitrate, codec, channels, file_size, duration)`: Descarta bitrates absurdos gerados por erros de muxing em MKV (ex.: metadados indicando 30 Mbps para AC-3 5.1 cujo teto teórico é 640 kbps) e recalcula valores realistas com base no tamanho do contêiner e duração.
- `format_commercial_branding(codec, channel_layout, is_immersive)`: Mapeia dados técnicos brutos para nomenclaturas comerciais reconhecidas pela indústria fonográfica (`DOLBY ATMOS`, `DOLBY AUDIO 5.1`, `DTS-HD MA 7.1`, `FLAC LOSSLESS`, `ESTÉREO CONVENCIONAL`).
- `decompose_channel_topology(channels, channel_layout, is_immersive)`: Decompõe a topologia de canais em componentes surround, height e subwoofer (`5.1 Surround (+Subwoofer)`, `7.1 Atmos (Surround + Height + Sub)`, `2.0 Estéreo (Sem LFE)`, `1.0 Mono (Sem LFE)`).

---

## 4. Subsistemas de Backend e Motores Científicos

O backend do SyncFrame é projetado sob a filosofia de processamento em etapas sequenciais com acoplamento fraco, medição estrita de integridade e tolerância a contêineres corrompidos.

### 4.1 Inspecionador de Mídia (`src/core/inspector.py`)
Responsável pelo reconhecimento profundo de formatos através de chamadas de subprocesso ao `ffprobe` e `mkvmerge`:
1. **Comandos Otimizados de Probing:** Invoca `ffprobe` com `-analyzeduration 100M -probesize 50M` e `-err_detect ignore_err`, assegurando leitura determinística mesmo em contêineres MP4 cujo átomo `moov` esteja localizado no final do arquivo.
2. **Avaliação Heurística de Vídeo (`evaluate_video_quality`):** Calcula a qualidade de cada fluxo de vídeo utilizando a fórmula ponderada:
   $$	ext{Score} = (W_{	ext{res}} \cdot 	ext{Res}) + (W_{	ext{codec}} \cdot 	ext{CodecScore}) + (W_{	ext{br}} \cdot 	ext{Bitrate})$$
   onde resoluções 4K UHD (3840x2160) superam 1080p, codecs modernos (AV1 > HEVC/H.265 > AVC/H.264) recebem multiplicadores superiores e bitrates maiores desempatam fontes idênticas.
3. **Detecção e Scoring Perceptual de Áudio (`calculate_perceptual_audio_score`):** Pontua trilhas de áudio priorizando fluxos multicanais autênticos e codecs sem perdas:
   - Tier 1: TrueHD Atmos, DTS-HD MA 7.1, DTS:X, LPCM (Score 90-100).
   - Tier 2: E-AC-3 JOC (Dolby Digital Plus Atmos), DTS-HD MA 5.1, DTS 5.1 (Score 75-89).
   - Tier 3: AC-3 5.1 convencional broadcast (Score 60-74).
   - Tier 4: AAC 2.0, MP3, Opus estéreo (Score 20-50).
   O algoritmo penaliza ativamente supostos fluxos AAC 5.1 transcodificados de baixa qualidade em detrimento de streams AC-3 5.1 originais de estúdio.
4. **Arbitragem de Faixas Duplicadas (`arbitrate_duplicate_language_streams`):** Identifica quando o arquivo de vídeo original já contém uma faixa em português de qualidade inferior (ex.: AAC 2.0 a 128 kbps) e o arquivo secundário traz uma dublagem superior (ex.: AC-3 5.1 a 640 kbps). O sistema marca automaticamente a faixa inferior com `--audio-tracks !<id>` para exclusão do contêiner final, evitando faixas redundantes.
5. **Auditoria Imersiva para Soundbars 7.1.4 (`audit_immersive_capabilities`):** Avalia se a trilha selecionada é capaz de alimentar os 7 canais horizontais, 1 subwoofer LFE e 4 canais de altura em sistemas de som de alta fidelidade (como a JBL Bar 1000 MK2), emitindo alertas contextuais se uma dublagem estéreo 2.0 for selecionada.

### 4.2 Extrator Acústico Bandpass (`src/core/extractor.py`)
Responsável pela extração das faixas de referência e alvo para consumo pelo motor de correlação matemática:
1. **Filtragem Espectral Focada:** Converte o áudio bruto para PCM 16-bit signed little-endian mono (`-ac 1`), reamostrado para exatamente 16.000 Hz (`-ar 16000`).
2. **Filtro Passa-Faixa (Bandpass 300 Hz - 4.000 Hz):**
   Utiliza a cadeia de filtros do FFmpeg:
   ```
   highpass=f=300,lowpass=f=4000
   ```
   **Justificativa Científica:** As frequências fundamentais da voz humana variam amplamente entre dubladores de idiomas distintos (inglês original vs. português dublado), o que prejudica a correlação matemática direta. Ao aplicar o passa-faixa entre 300 Hz e 4 kHz com atenuação das harmônicas primárias, o sistema foca a comparação nos ruídos de impacto foley, explosões, portas batendo, tiros e na trilha sonora incidental, que são exatamente idênticos em ambas as versões de estúdio.
3. **Throttling Compulsório:** Todas as chamadas de extração utilizam `-threads 2`, prevenindo saturação de barramento térmico.

### 4.3 Motor de Correlação Acústica FFT (`src/core/correlator.py`)
*Nota de Arquitetura: Este componente é protegido contra modificações estruturais involuntárias.*
Responsável pela detecção matemática do desvio temporal:
1. **Janelamento Multi-Ponto:** Extrai 3 segmentos temporais de 60 a 90 segundos cada em posições percentuais estratégicas do arquivo:
   - Janela 1: 5% da duração (após aberturas e logos de estúdio).
   - Janela 2: 50% da duração (ponto médio do filme).
   - Janela 3: 85% da duração (terço final da obra).
2. **Correlação Cruzada Normalizada no Domínio da Frequência via FFT:**
   Para dois sinais discretos de áudio $x[n]$ e $y[n]$, a correlação cruzada circular é computada via Transformada Rápida de Fourier (SciPy / NumPy):
   $$R_{xy}[k] = \mathcal{F}^{-1}\left\{ \mathcal{F}\{x\} \cdot \mathcal{F}\{y\}^* ight\}$$
   Onde $*$ denota o conjugado complexo.
3. **Métrica de Confiança Estatística (PSLR & Escore Z):**
   A confiabilidade do pico de correlação é mensurada pela Razão entre o Pico e o Lóbulo Lateral (Peak-to-Side-Lobe Ratio - PSLR):
   $$	ext{Confidence} = rac{	ext{Pico} - \mu_{	ext{ruído}}}{\sigma_{	ext{ruído}}}$$
   Onde $\mu_{	ext{ruído}}$ e $\sigma_{	ext{ruído}}$ são a média e o desvio padrão da energia acústica fora do intervalo do pico. Picos com $	ext{PSLR} < 3.5$ ou confiança $< 0.40$ são sinalizados como inconclusivos.
4. **Detecção de Deriva Linear (Time Drift Ratio):**
   Compara os offsets temporais obtidos nas 3 janelas ($t_1, t_2, t_3$).
   $$	ext{Drift Ratio} = rac{\Delta t_{	ext{alvo}}}{\Delta t_{	ext{ref}}}$$
   Permite detectar variações de framerate conhecidas:
   - $23.976	ext{ fps} \leftrightarrow 24.000	ext{ fps}$ (deriva de telecine $1001/1000 pprox +0.1001\%$).
   - $24.000	ext{ fps} \leftrightarrow 25.000	ext{ fps}$ (deriva PAL $25/24 pprox +4.167\%$).
5. **Detecção de Descontinuidade Temporal Não Linear (Cortes de Montagem):**
   Se o offset medido for idêntico nas janelas 1 e 2 ($t_1 pprox t_2$), mas apresentar um degrau abrupto e inexplicável na janela 3 ($t_3 \gg t_2$), o sistema diagnostica corte de montagem (versão de cinema vs. versão estendida/director's cut), emitindo código semântico de erro e alertando a impossibilidade de sincronização por estiramento temporal linear simples.
6. **Contrato Matemático de Sinal de Offset:**
   - Se a dublagem está atrasada em relação ao vídeo: $	ext{offset} > 0$. Para adiantar o áudio no contêiner `mkvmerge`, utiliza-se `--sync 0:-offset_ms`.
   - Se a dublagem está adiantada em relação ao vídeo: $	ext{offset} < 0$. No `mkvmerge`, utiliza-se `--sync 0:+|offset_ms|`.
   - No miniplayer de prévia MPV, o atraso é compensado via parâmetro `--audio-delay`.

### 4.4 Motor de Transformação Temporal e Restauração Tonal (`src/core/transformer.py`)
*Nota de Arquitetura: Este componente é protegido contra modificações estruturais involuntárias.*
Quando o drift ratio for diferente de 1.0000 (exigindo estiramento ou compressão temporal):
1. **Time-Stretch sem Alteração de Altura Tonal (Pitch-Neutral):** Utiliza o filtro `atempo` do FFmpeg encadeado quando a alteração de velocidade não envolve fontes em padrão PAL europeu.
2. **Restauração Analógica de Pitch PAL (25 fps -> 24/23.976 fps):**
   Filmes dublados transmitidos em emissoras europeias ou ripados de DVDs PAL sofrem aceleração de 4,167% (PAL Speedup), o que torna as vozes dos atores agudas e artificiais. O SyncFrame aplica o filtro:
   ```
   asetrate=r=48000*24000/25000,aresample=resampler=soxr:osr=48000
   ```
   Esse algoritmo restaura a velocidade e o tom analógico autêntico da gravação cinematográfica original via reamostragem de alta precisão (libsoxr).
3. **Parametrização de Codecs de Saída:**
   Se a transcodificação for obrigatória devido a time-stretch, o usuário pode selecionar o formato no Review Gate:
   - FLAC: 24-bit ou 16-bit Lossless bit-perfect.
   - Opus: 160 kbps (estéreo) ou 450 kbps (multicanal 5.1).
   - E-AC-3: Dolby Digital Plus a 640 kbps.
   - AC-3: Dolby Digital clássico a 640 kbps.
   - AAC: Advanced Audio Coding a 256 kbps.

### 4.5 Motor de Remux e Auditoria em Malha Fechada (`src/core/remuxer.py`)
*Nota de Arquitetura: Este componente é protegido contra modificações estruturais involuntárias.*
1. **Injeção Não Destrutiva via `mkvmerge`:** Monta a linha de comando determinística do MKVToolNix combinando o vídeo da referência com a faixa dublada alvo sincronizada e as faixas originais selecionadas.
2. **Padronização Estrita de Metadados DLNA / UPnP (BubbleUPnP Fix):**
   Para evitar falhas de identificação de faixas em Smart TVs Samsung/LG e media servers DLNA, o remuxer gera explicitamente:
   - `--track-name <id>:"Português (Dublagem Oficial - [Codec] [Canais])"`
   - `--language <id>:por`
   - `--default-track-flag <id>:1` (para a dublagem principal)
   - `--track-name <id_sec>:"Inglês (Original - [Codec] [Canais])"`
   - `--language <id_sec>:eng`
   - `--default-track-flag <id_sec>:0`
   - `--enabled-track-flag <id>:1`
3. **Compensação de Atrasos do Contêiner (`start_time` / Edit Lists):**
   Calcula o offset líquido real somando atrasos de cabeçalho do MP4/MKV de origem:
   $$	ext{Offset}_{	ext{líquido}} = 	ext{Offset}_{	ext{acústico}} + (	ext{PTS\_start}_{	ext{ref}} - 	ext{PTS\_start}_{	ext{alvo}})$$
4. **Auditoria Acústica em Malha Fechada (Closed-Loop Post-Remux Audit):**
   Após a geração do arquivo final `.mkv`:
   - Extrai um segmento de 30 segundos do arquivo resultante recém-criado.
   - Executa correlação FFT com a trilha de referência original.
   - Se o resíduo de sincronia for $\le 5	ext{ ms}$, a integridade é validada com sucesso.
   - Se o resíduo for superior a $15	ext{ ms}$ (falha grave de muxing), o arquivo final é renomeado para `<nome>.failed_audit.mkv` e o usuário é notificado imediatamente.

### 4.6 Utilitários do Sistema e Hardware (`src/utils/`)
- `disk_utils.py`: Analisa se o diretório de destino possui espaço livre suficiente (mínimo: tamanho do vídeo original + tamanho das trilhas de áudio + 2 GB de margem).
- `temp_manager.py`: Cria diretórios seguros sob `.syncframe_tmp/` com nomes aleatórios e registra hooks de encerramento em `atexit` e no sinal `SIGTERM`.
- `system_check.py`:
  - `PreFlightChecker.verify_system_binaries()`: Audita a presença dos executáveis obrigatórios no sistema (`ffmpeg`, `ffprobe`, `mkvmerge`, `mpv`).
  - `diagnose_system_crash_logs()`: Inspeciona os registros do `journalctl` e dmesg em busca de quedas por MCE (Machine Check Exception) e desarmes térmicos no host.

### 4.7 Modo Headless de Linha de Comando (`src/main.py`)
O SyncFrame pode ser operado inteiramente via terminal em servidores ou pipelines CI/CD:
```bash
python3 -m src.main --video "filme_4k.mkv" --dub "filme_dublado.mp4" --output "filme_final.mkv" [opções]
```
Códigos de retorno semânticos da CLI:
- `0`: Sucesso total com remux e auditoria aprovados.
- `1`: Erro operacional ou dependência ausente.
- `2`: Descontinuidade temporal não linear detectada (corte de montagem entre as versões).
- `3`: Baixa confiança estatística na correlação acústica (pico não discernível).

---

## 5. Subsistemas de Frontend e Arquitetura de Interface

A camada visual do SyncFrame é construída 100% nativa em **PySide6 (Qt6)** com aceleração por hardware e adere aos princípios ergonômicos do Samsung One UI 8.5.

### 5.1 Design System One UI 8.5 e Tokens Cromáticos (`src/ui/style.py`)
O sistema suporta alternância dinâmica e atômica entre **Modo Escuro (Dark)** e **Modo Claro (Light)** sem resíduos gráficos:
- **Tokens Dark Mode:**
  - Fundo da janela: `#0d0e11`
  - Fundo de cartões (`card`): `#16181d` com borda fina `#23252b`
  - Fundo de contêineres de arquivo (`fileBox`): `#1b1c20`
  - Texto primário: `#ffffff`
  - Texto secundário: `#9496a1`
  - Acento verde esmeralda: `#2fb16b`
  - Acento âmbar funcional: `#e8963a`
  - Acento azul de foco: `#4081f7`
- **Tokens Light Mode:**
  - Fundo da janela: `#f4f5f8`
  - Fundo de cartões: `#ffffff` com borda fina `#e1e4ed`
  - Fundo de contêineres de arquivo: `#ebedf4`
  - Texto primário: `#16181d`
  - Texto secundário: `#686b78`
- **Banimento Estrito de Cantos Retos (Ergonomia Geométrica Contínua):**
  Todos os elementos visuais obedecem a curvaturas contínuas proporcionais:
  - Janelas modais e diálogos: `border-radius: 28px`
  - Cartões principais de superfície: `border-radius: 24px` a `32px`
  - Menus e popups: `border-radius: 16px` a `18px`
  - Badges e chips: `border-radius: 10px` a `14px`
  - Botões de ação e campos de texto: curvatura exata de meia-altura (`border-radius: 17px` para altura 34px, `border-radius: 22px` para altura 44px).

### 5.2 Barra Superior Desconectada Fixa (`Sticky Detached Topbar`)
- Localizada em `src/ui/main_window.py` (`#topHeader`).
- Altura rígida de 76px, fixada no topo da janela fora da área de rolagem central.
- Título principal em tipografia bold de 34px e subtítulo técnico monospace.
- Totalmente desobstruída de botões dispersos: as ações de sistema foram transferidas para a Doca Flutuante inferior.
- Propagação transparente de eventos de scroll do mouse (`wheelEvent`) diretamente para a esteira central `QScrollArea`.

### 5.3 Zona Central de Ingestão Unificada (`UnifiedDropZone`)
Implementada em `src/ui/components/unified_drop_zone.py`. Opera sob uma máquina de estados visual:
1. **Estado Vazio (Empty State):** Exibe área de arraste minimalista com altura contida (240px) e borda pontilhada suave.
2. **Estado de Ingestão Unitária (1 arquivo inserido):** Dispara automaticamente a transição para a Bancada de Inspeção Técnica (`MediaInspectorView`).
3. **Estado de Revisão de Faixas (Stream Review Gate - 2 ou mais arquivos inseridos):**
   - **Cartões de Fontes Dinâmicas ($N$ Fontes):** Gera automaticamente cápsulas horizontais (`fileBox`) para qualquer quantidade de arquivos ingeridos, identificando determinística e visualmente papéis ("REFERÊNCIA DE VÍDEO", "ÁUDIO DUBLADO", "VÍDEO ALTERNATIVO", etc.).
   - **Pooling Universal de Imagem (`combo_video`):** Disponibiliza 100% dos fluxos de vídeo de todas as fontes inseridas no seletor de vídeo principal.
   - **Seletor de Áudio Dublado Alvo (`combo_target_audio`):** Exibe todas as trilhas de áudio disponíveis com metadados detalhados e prevenção de seleções conflitantes.
   - **Painel de Áudios Secundários (`frameSecondaryAudio`):** Lista estruturada com checkboxes circulares (`border-radius: 9px`) pré-selecionando a melhor trilha original e desmarcando trilhas secundárias redundantes.
   - **Faixa de Especificações do Arquivo Resultante (`resultingSpecsBar`):**
     Barra horizontal reativa de badges pílula (`border-radius: 12px`, altura 24px) que consolida em tempo real as especificações técnicas da saída antes do remux:
     - Badge de Contêiner: `MKV Matroska` ou `MKV Remux`.
     - Badge de Modo: `Cópia Direta (Passthrough)` em verde `#2fb16b` ou `Re-encode [CODEC] (PAL 24fps)` em âmbar `#e8963a`.
     - Badge de Formato Comercial: `DOLBY ATMOS`, `DOLBY AUDIO 5.1`, `DTS-HD MA 7.1`, `FLAC LOSSLESS`, etc.
     - Badge de Codec: Caixa alta padronizada (`AC-3`, `E-AC-3`, `TRUEHD`, `FLAC`, etc.).
     - Badge de Topologia de Canais Decomposta: Indicando canais surround, de teto e LFE (`5.1 Surround (+Subwoofer)`, `7.1 Atmos (Surround + Height + Sub)`).
     - Badge de Frequência de Amostragem: `48.000 Hz`.
     - Badge de Taxa de Bits: Taxa sanitizada (ex.: `640 kbps` ou `Bitrate Variável (VBR)`).
     Contrato público auditado via `update_resulting_specs(self, track_info, remux_options) -> dict`.

### 5.4 Bancada de Inspeção Técnica Unitária (`MediaInspectorView`)
Componente em `src/ui/components/media_inspector_view.py`. Quando exatamente 1 arquivo é arrastado para o programa:
- A interface suspende correlatores vazios e ativa o modo inspeção profunda via `SingleFileInspectionWorker`.
- Apresenta cartões estruturados decompondo fluxos de vídeo (resolução, FPS, bit depth, HDR/Dolby Vision), áudio (codecs, layout de canais, frequências), legendas e capítulos.
- Exibe o botão de ação tracejado (`#btnConnectiveAction`, raio contínuo de 22px), permitindo que o usuário adicione o segundo arquivo e transite suavemente para o Review Gate sem reiniciar a aplicação.

### 5.5 Doca de Ações Flutuante (`FloatingActionDock`)
Implementada em `src/ui/components/floating_action_dock.py`. Transposição nativa em PySide6/Qt6 inspirada no conceito TiltedDock:
- Barra em cápsula flutuante (`border-radius: 26px; height: 52px;`) ancorada a 20px da borda inferior e auto-centralizada dinamicamente no `resizeEvent`.
- Quatro ferramentas operacionais integradas:
  1. `event_log`: Abre o Console de Telemetria Técnica (`EventLogPopover`).
  2. `check_updates`: Dispara auditoria silenciosa de dependências via `DependencyUpdateWorker`.
  3. `theme_toggle`: Alternador atômico de tema com ícone dinâmico do Sol (no escuro) e da Lua (no claro).
  4. `version_info`: Abre o modal de diagnósticos de ambiente (`VersionInfoPopover`).
- **Micro-interações de Dinâmica de Mola:**
  - O ícone sob foco do mouse (hover) é escalado para 1.35x de seu tamanho normal através de `QPropertyAnimation` e curva de amortecimento `QEasingCurve.OutBack`.
  - Exibe um anel sutil de realce luminoso pintado por trás do ícone via `QPainter`.
  - Os botões irmãos não focados esmaecem suavemente para 0.45 de opacidade (`buttonOpacity`).
  - Renderização estritamente vetorial via `QSvgRenderer`.

### 5.6 Popovers Flutuantes com Resiliência Wayland
- `EventLogPopover`: Modal de 820x520 pixels com cantos curvos de 18px, buffer circular de 1.000 eventos, contagem viva de linhas, botão "Limpar" e fechamento instantâneo via tecla Escape. Clampeado contra os limites da tela gráfica para nunca vazar fora do monitor.
- `VersionInfoPopover`: Diálogo compacto com tags de diagnóstico indicando versões instaladas de `FFmpeg`, `MKVToolNix`, `MPV` e do sistema operacional.

### 5.7 Painel de Alinhamento Temporal e Controles de Offset (`SyncControls`)
Implementado em `src/ui/components/sync_controls.py`:
- **Visor Numérico de Offset:** Caixa em cápsula contínua com tipografia bold de 38px (`+0,0 ms`).
- **Seletor de Sensibilidade (`SensitivitySelectorWidget`):** Pílula segmentada com 3 passos selecionáveis (`1 ms`, `10 ms`, `50 ms`) conectados ao `SliderSensitivityController`.
- **Slider Esférico Proporcional (`DampedSlider`):**
  Elimina o achatamento vertical de sliders tradicionais. O thumb é um círculo matematicamente perfeito de 20x20px (`border-radius: 10px; border: 3px solid;`) com trilho de 8px e altura de container travada em 28px.
- **Grade 2x4 de Micro-Passos Rápidos:** 8 botões em cápsula arredondada (`-500 ms`, `-100 ms`, `-50 ms`, `-10 ms`, `+10 ms`, `+50 ms`, `+100 ms`, `+500 ms`).
- **Caixas de Telemetria:** Indicam o desvio temporal contínuo (drift) e a confiança estatística da correlação.
- **Pílula de Diagnóstico:** Badge inferior com ponto verde utilitário e parecer descritivo neutro sem emojis.

### 5.8 Miniplayer de Inspeção Labial (`PreviewPlayer` & `LipSyncController`)
Implementado em `src/ui/components/preview_player.py`:
- Orquestra um processo isolado `QProcess` rodando `mpv` (com fallback automático para `ffplay`).
- Permite validação visual e auditiva imediata da sincronia labial sem gerar arquivos temporários no disco.
- Botões seletores em cápsula de 40px para 3 marcos temporais do filme: `5% (Abertura)`, `50% (Meio)` e `90% (Final)`.
- Aplica compensação temporal inversa via `--audio-delay=-offset_sec`.
- Garante terminação atômica sem deixar processos órfãos na memória.

### 5.9 Renderizador Vetorial da Curva de Correlação (`CorrelationView`)
Implementado em `src/ui/components/correlation_view.py`:
- Renderiza em alta resolução a energia acústica da correlação FFT utilizando `QPainter` e `QPainterPath`.
- Recorta a pintura dentro de uma curva contínua de 28px (`clipPath`), impedindo que a grade e a onda vazem para fora dos cantos arredondados do cartão.
- Desenha linhas de grade discretas, indicador vertical do pico e marcação de limiar de confiança.

### 5.10 Menus Suspensos e Delegação de Renderização (`custom_combobox.py`)
- `NoWheelComboBox`: Bloqueia eventos da roda do mouse (`wheelEvent`) quando o dropdown está fechado, prevenindo alterações acidentais de parâmetros durante a rolagem da página.
- `DropdownHighlightDelegate`: Delegado customizado que desenha itens internos com cantos arredondados de 10px e fundo destacado em verde ou cinza neutro sem cortar bordas.
- `HighlightComboBox`: Configura o container da janela suspensa com `Qt.WA_TranslucentBackground`, erradicando sobras brancas retangulares de 90 graus nas quinas da lista suspensa.

### 5.11 Diálogo Modal de Conclusão (`CompletionDialog`)
Substituto estético de alta fidelidade para o `QMessageBox.information` nativo:
- Diálogo modal estilizado com cantos arredondados de 28px e fundo semi-translúcido.
- Glifo minimalista de confirmação em verde esmeralda.
- Rótulo de caminho do arquivo MKV final em tipografia monospace mono-espaçada.
- Botão "Abrir Diretório" que aciona o gerenciador de arquivos nativo do usuário (`xdg-open`, `dolphin`, `nautilus`) em thread separada para não bloquear a UI, com fallback para cópia do caminho na área de transferência.
- Fechamento instantâneo via teclas Enter ou Escape.

---

## 6. Modelo de Concorrência, Threads e Sinais Assíncronos

Para manter a interface gráfica a 60 fps constantes e sem engasgos (jank-free), todas as operações pesadas de I/O de disco, subprocessos do FFmpeg/MKVToolNix e cálculos matemáticos da FFT rodam estritamente fora da thread principal da interface gráfica (`Main GUI Thread`).

### 6.1 Diagrama de Sequência da Esteira Unificada

```
[ Usuário ]       [ MainWindow ]       [ UnifiedDropZone ]       [ UnifiedPipelineWorker ]       [ Subprocessos (ffmpeg/mkvmerge) ]
     |                   |                      |                               |                                      |
     |-- Arraste 2x ---->|                      |                               |                                      |
     |                   |--- Dispara Ingestão ->|                              |                                      |
     |                   |<-- AutoMatchVerdict -|                              |                                      |
     |                   |--- Exibe Review Gate >                               |                                      |
     |                                                                          |                                      |
     |-- Clica "Sincronizar e Concluir" ------->|                               |                                      |
     |                   |                      |--- Instancia e inicia ------->|                                      |
     |                   |                      |<-- analysis_started ----------|                                      |
     |                   |                      |                               |--- Extrai ref audio (16kHz PCM) ---->|
     |                   |                      |<-- step_progress(1/4) --------|                                      |
     |                   |                      |                               |--- Extrai dub audio (16kHz PCM) ---->|
     |                   |                      |<-- step_progress(2/4) --------|                                      |
     |                   |                      |                               |--- Executa FFT Multi-Janela -------->|
     |                   |                      |<-- correlation_ready(peak) ---|                                      |
     |                   |                      |<-- step_progress(3/4) --------|                                      |
     |                   |                      |                               |--- Executa mkvmerge remux ---------->|
     |                   |                      |<-- remux_progress(0..100) ----|                                      |
     |                   |                      |                               |--- Executa Closed-Loop Audit ------->|
     |                   |                      |<-- finished_success(out_path)-|                                      |
     |                   |<-- Exibe Modal ------|                               |                                      |
     |                   |    CompletionDialog                                  |                                      |
```

### 6.2 Tabela de Sinais e Contratos dos Workers

| Worker | Sinal (PySide6 Signal) | Parâmetros | Descrição / Efeito na Interface |
|---|---|---|---|
| `UnifiedPipelineWorker` | `analysis_started` | Nenhum | Desativa botões de ação e exibe cursor de espera (`WaitCursor`). |
| `UnifiedPipelineWorker` | `step_progress` | `step: int, total: int, msg: str` | Atualiza o texto de status e a barra de progresso horizontal superior. |
| `UnifiedPipelineWorker` | `correlation_ready` | `dict` (dados de pico, offset, ruído) | Atualiza o visor numérico de offset e a curva de correlação do `CorrelationView`. |
| `UnifiedPipelineWorker` | `preview_segments_ready` | `dict` (caminhos dos segmentos de prévia) | Habilita os botões de reprodução instantânea no miniplayer `PreviewPlayer`. |
| `UnifiedPipelineWorker` | `remux_progress` | `percent: int` | Atualiza a barra de progresso percentual no cartão de saída do remux. |
| `UnifiedPipelineWorker` | `finished_success` | `output_path: str` | Restaura cursores, emite som do sistema e abre o `CompletionDialog`. |
| `UnifiedPipelineWorker` | `execution_failed` | `error_msg: str` | Registra erro no console de telemetria e exibe alerta contextual ao usuário. |
| `SingleFileInspectionWorker` | `inspection_completed` | `StreamCandidate` | Alimenta os cartões de metadados da Bancada de Inspeção Técnica. |
| `SingleFileInspectionWorker` | `inspection_failed` | `str` | Notifica falha na leitura do arquivo unitário ingerido. |
| `DependencyUpdateWorker` | `audit_finished` | `dict` (ferramentas e versões) | Atualiza os badges de versão no `VersionInfoPopover` e notifica o dock. |
| `DependencyUpdateWorker` | `update_available` | `tool_name: str, version: str` | Notifica existência de nova versão identificada via comparação semântica. |
| `DependencyUpdateWorker` | `status_message` | `msg: str` | Registra mensagens no `EventLogPopover` com telemetria detalhada de execução. |
| `DependencyUpdateWorker` | `update_completed` | `item: str, success: bool, msg: str` | Sinaliza término da execução do auto-updater (git pull, download ou dnf). |

---

## 7. Estratégia de Testes Automatizados

A robustez do SyncFrame é garantida por uma suíte de **187 testes automatizados** distribuídos no diretório `tests/`.

### 7.1 Categorias e Cobertura de Testes

1. **Testes de Algoritmos Acústicos e Matemáticos (`test_correlator.py`, `test_transformer.py`):**
   - Validação da correlação FFT com sinais senoidais puros com offsets conhecidos de $\pm 120	ext{ ms}$, $\pm 550	ext{ ms}$, $\pm 2400	ext{ ms}$.
   - Verificação da precisão da taxa de deriva temporal (drift ratio) em conversões de $23.976 \leftrightarrow 24.000$ fps e $24.000 \leftrightarrow 25.000$ fps.
   - Detecção determinística de cortes de montagem e descontinuidades não lineares.
   - Validação da fórmula de PSLR e descarte de picos sob ruído branco gaussiano.
2. **Testes de Inspeção e Heurísticas de Seleção (`test_inspector.py`, `test_secondary_ranking_and_dlna.py`):**
   - Sanitização de bitrates impossíveis de cabeçalhos MKV.
   - Identificação determinística de metadados de Dolby Atmos e canais de teto.
   - Ranqueamento de áudios secundários pelos 4 tiers qualitativos.
   - Validação dos argumentos DLNA/UPnP gerados para o `mkvmerge`.
   - Teste de especificação da barra de saída do arquivo resultante (`test_resulting_output_specs_pills_and_topology`).
3. **Testes de Interface Gráfica e Design System (`test_ui_*.py`, `test_all_rounded_corners.py`, `test_floating_action_dock.py`):**
   - Execução offscreen via `QT_QPA_PLATFORM=offscreen`.
   - Validação universal de cantos arredondados contínuos (proibição de cantos retos em 100% dos widgets).
   - Validação cromática estrita em escala de cinza neutra (banimento de `#f59e0b` ou roxo/magenta).
   - Testes de comutação atômica Dark Mode / Light Mode.
   - Testes de colapso responsivo da janela (mudança de 2 colunas para 1 coluna vertical em larguras < 960px).
   - Micro-interações do Dock Flutuante e abertura de popovers.
   - Geometria esférica do slider e seletores de sensibilidade (1ms, 10ms, 50ms).
4. **Testes de Segurança de Hardware e Concorrência (`test_system_check.py`, `test_workers.py`):**
   - Verificação de throttling de threads (`-threads 2`).
   - Verificação de expurgo atômico de arquivos em `.syncframe_tmp/`.

### 7.2 Execução da Suíte de Testes
Para rodar a totalidade dos 187 testes sem abrir janelas gráficas no desktop:
```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -p "test_*.py"
```
Todos os 187 testes devem ser executados com resultado `OK` e zero falhas (`failures=0, errors=0`).

---

## 8. Compilação e Empacotamento em Binário Único ELF

O SyncFrame pode ser compilado em um único arquivo binário executável autocontido para plataformas Linux x86_64 através do script `build_bin.sh` e da especificação PyInstaller `syncframe.spec`.

### 8.1 Pipeline de Compilação (`build_bin.sh`)
O script executa as seguintes fases:
1. Validação do ambiente Python virtual (`.venv`) e instalação de dependências de compilação (`pyinstaller`).
2. Limpeza prévia de diretórios `build/` e `dist/`.
3. Inclusão dos ativos estáticos (`src/ui/assets/*`) mapeados para o diretório interno do pacote.
4. Resolução das bibliotecas dinâmicas do FlexiBLAS / OpenBLAS necessárias para o SciPy e NumPy.
5. Exclusão explícita de módulos pesados não utilizados do Qt (ex.: `QtNetwork`, `QtQml`, `QtQuick`, `QtPdf`, `QtWebEngine`) para manter o executável final compacto e com inicialização instantânea.
6. Geração do executável final em `dist/SyncFrame`.

### 8.2 Resolução de Ativos em Runtime (`sys._MEIPASS`)
Todos os componentes de interface que carregam arquivos estáticos (ícones vetoriais SVG e glifos PNG) utilizam resolução dinâmica:
```python
import sys
from pathlib import Path

def get_asset_path(relative_name: str) -> str:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_dir = Path(sys._MEIPASS) / "src" / "ui" / "assets"
    else:
        base_dir = Path(__file__).resolve().parent.parent / "ui" / "assets"
    return str(base_dir / relative_name)
```
Isso garante funcionamento transparente tanto em modo interpretado (`python3 -m src.main`) quanto empacotado no binário ELF.

---

## 9. Diretrizes de Extensão para Agentes de IA e LLMs

Quando um modelo de linguagem ou agente de automação for solicitado a realizar alterações, melhorias ou refatorações no SyncFrame, as seguintes regras devem ser cumpridas sem exceção:

1. **Arquivos Protegidos:**
   - **NÃO altere** a lógica matemática central de `src/core/remuxer.py`, `src/core/correlator.py` ou `src/core/transformer.py` a menos que o usuário solicite explicitamente uma mudança de algoritmo matemático. O contrato dessas classes está calibrado e homologado.
2. **Proibição de Emojis:**
   - Nunca insira emojis em nomes de variáveis, comentários de código, docstrings, arquivos markdown, saídas de log do sistema ou respostas textuais direcionadas ao usuário. Use glifos vetoriais monocromáticos limpos ou tipografia técnica em texto claro.
3. **Conformidade de Design One UI:**
   - Ao criar novos componentes visuais, herde a estética descrita em `src/ui/style.py`.
   - Aplique sempre bordas arredondadas proporcionais à meia-altura em botões e badges (`border-radius = height / 2`).
   - Utilize a paleta monocromática neutra com os acentos funcionais permitidos (`#2fb16b` para verde esmeralda, `#e8963a` para âmbar e `#4081f7` para azul safira de seleção).
   - O uso de gradientes roxos ou violetas é estritamente proibido.
4. **Verificação de Regressão Obrigatória:**
   - Após qualquer alteração no código-fonte, execute imediatamente a suíte completa de testes offscreen:
     ```bash
     QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -p "test_*.py"
     ```
   - Nenhuma entrega é considerada válida se houver qualquer regressão nos 187 testes existentes.
