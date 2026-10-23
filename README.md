# SyncFrame

**SyncFrame** é uma aplicação desktop de alta fidelidade voltada para a automação de remux e sincronização precisa de áudio dublado e vídeo de alta definição a partir de arquivos MKV, MP4, M4V e MOV distintos.

Projetado com uma interface neutra, minimalista e de alta densidade de informação, o sistema soluciona desalinhamentos temporais causados por atrasos estáticos iniciais, discrepâncias de frame rate (23.976 fps vs. 24.000 fps vs. 25.000 fps PAL) e deriva contínua através de inspeção matemática de metadados e correlação acústica por FFT, realizando multiplexação direta no contêiner MKV sem reencodamento de vídeo.

---

## ⚡ Características Principais

- **Fidelidade Visual 100% Intocada (Zero-Loss Passthrough):** O vídeo de referência **nunca** é reencodificado; o fluxo é transmitido diretamente bit-a-bit via `mkvmerge`.
- **Suporte Agnóstico a Múltiplos Contêineres (MKV, MP4, M4V, MOV):** Ingestão transparente e combinação híbrida de fontes (ex.: Vídeo 4K de um MKV + Áudio dublado de um MP4/MOV de torrent).
- **Probing Profundo & Resiliente:** Análise não bloqueante via `ffprobe` com flags de análise profunda (`-analyzeduration 100M -probesize 50M`) e tolerância a erros (`-err_detect ignore_err`), garantindo leitura imediata mesmo de arquivos MP4 com átomo `moov` alocado ao final ou cabeçalhos imperfeitos.
- **Demuxing Lossless Direto (Zero Recompressão de Áudio):** Extração de faixas em modo cópia de stream (`ffmpeg -c:a copy`) preservando os codecs nativos (AAC, AC3, E-AC3, MP3, Opus, DTS, FLAC) sem perdas nem downmix/upmix forçado.
- **Card de Auditoria Acústica no Review Gate:** Apresentação clara de layout de canais (Mono 1.0, Estéreo 2.0, Surround 5.1, Surround 7.1), codec, taxa de amostragem em Hz e bitrate, acompanhado de alerta contextual neutro quando a dublagem for estéreo e o original for multicanal surround.
- **Zero Recompressão para Offsets Estáticos:** Se as taxas de quadros forem congruentes, o atraso/adiantamento é aplicado nativamente no cabeçalho do contêiner MKV (`--sync <TRACK_ID>:<OFFSET_MS>`).
- **Detecção de Framerate & Correlação FFT Multi-Janela:** Extrai trechos acústicos filtrados (bandpass 300Hz-4000Hz mono PCM) no início (5%), meio (50%) e fim (85%) para isolar transientes, trilhas incidentais e foley idênticos entre idiomas, diagnosticando divergências de frame rate conhecidas:
  - `23.976 fps ↔ 24.000 fps` (deriva telecine NTSC de $1001/1000 \approx +0.1001\%$)
  - `24.000 fps ↔ 25.000 fps` (PAL Speedup/Slowdown de $25/24 \approx +4.167\%$)
- **Zona Unificada de Entrada (Unified Drop Zone) & Review Gate Tabular:** Zona central inteligente que aceita 1 ou 2 arquivos simultaneamente (.mkv, .mp4, .m4v, .mov), com aprovação instantânea em 1 clique ou via tecla **Enter**.
- **Estética Neutra Monocromática & Modo Escuro/Claro:** Design refinado em escala de cinza neutra, preto e branco, com alternador dinâmico de tema (`🌓`) no cabeçalho.
- **Layout Totalmente Responsivo com Scroll Vertical:** Estrutura envelopada em `QScrollArea` que garante perfeita usabilidade em modo janela (`1024x650`, `900x550`), eliminando achatamento ou sobreposição de widgets.
- **Time-Stretch Inteligente sem Alteração de Pitch:** Se e somente se houver deriva contínua significativa ($\text{drift} \neq 1.0$), o filtro `atempo` do FFmpeg é aplicado em cópia temporária de alta precisão (FLAC lossless).
- **Player de Inspeção Instantânea:** Teste de reprodução em tempo real nos marcadores 5%, 50% e 90% via `mpv` com compensação de atraso instantânea para validação labial antes do remux.
- **Isolamento e Limpeza Compulsória de Staging:** Todos os artefatos temporários de PCM e áudios intermediários em `.syncframe_tmp/` são descartados automaticamente ao término do trabalho ou em caso de encerramento do processo (`SIGINT`/`SIGTERM`/`atexit`).

---

## 🛠 Pré-requisitos de Sistema

O SyncFrame requer utilitários nativos de mídia no sistema operacional do host:

| Ferramenta | Papel no Pipeline | Obrigatório |
| :--- | :--- | :---: |
| `ffmpeg` | Extração de trechos mono PCM e filtro passa-faixa | **Sim** |
| `ffprobe` | Análise de metadados, taxas de quadros e durações | **Sim** |
| `mkvmerge` | Inspeção de faixas do container e multiplexação lossless | **Sim** |
| `mpv` | Player de inspeção em tempo real com delay dinâmico | *Recomendado* (fallback `ffplay`) |
| `Python 3.10+` | Runtime da aplicação e bibliotecas científicas | **Sim** |

### Instalação no Linux

```bash
# Nobara Linux / Fedora / RHEL
sudo dnf install ffmpeg mkvtoolnix mpv

# Ubuntu / Debian / Linux Mint
sudo apt update && sudo apt install ffmpeg mkvtoolnix mpv

# Arch Linux / Manjaro
sudo pacman -S ffmpeg mkvtoolnix-cli mpv
```

---

## 🚀 Modos de Execução

O **SyncFrame** oferece dois métodos de execução no Linux:

### 1. Executável Binário Standalone (Recomendado)
A aplicação pode ser executada diretamente como um único arquivo executável ELF autônomo, sem requerer instalação de Python ou dependências virtuais adicionais:

```bash
# Execução direta via terminal ou duplo clique
./dist/SyncFrame

# Diagnóstico de ferramentas do sistema via CLI
./dist/SyncFrame --cli-check

# Exibir versão oficial
./dist/SyncFrame --version
```

### 2. Modo de Desenvolvimento Local (`run.sh`)
Para desenvolvimento e inspeção do código-fonte:

```bash
# Permissão de execução (já configurada no repositório)
chmod +x run.sh

# Inicialização com bootstrap automático de virtualenv
./run.sh
```

---

## 📦 Compilação do Binário Único (`build_bin.sh`)

Para compilar o binário único ELF autônomo com exclusão seletiva de footprints desnecessários:

```bash
# Executa o pipeline automatizado de empacotamento com PyInstaller
chmod +x build_bin.sh
./build_bin.sh
```

O script limpa builds anteriores, compila o binário em `dist/SyncFrame` usando `syncframe.spec`, atribui permissões de execução e roda testes automatizados pré-voo.

---

## 🎛 Tabela de Compatibilidade de Mídias e Codecs

| Componente | Formatos / Codecs Suportados | Método de Processamento |
| :--- | :--- | :--- |
| **Contêineres** | `.mkv`, `.mp4`, `.m4v`, `.mov` | Probing profundo não-destrutivo (`ffprobe`) |
| **Vídeo** | AV1, HEVC (H.265), AVC (H.264), VP9 | **100% Passthrough Bit-a-Bit** (zero recompressão) |
| **Áudio Alvo (Dublagem)** | AAC, AC3, E-AC3, MP3, Opus, DTS, FLAC | Demuxing direto de stream copy (`-c:a copy`) |
| **Layouts de Canal** | Mono 1.0, Estéreo 2.0, Surround 5.1, Surround 7.1 | Preservação nativa de canais com auditoria visual |
| **Sincronia Estática** | Qualquer offset em milissegundos ($\pm\text{ms}$) | Cabeçalho do contêiner MKV via `--sync` |
| **Sincronia Dinâmica** | Desvios de framerate (23.976, 24.0, 25.0 fps) | Time-stretch FLAC sem alteração de tom via `atempo` |

---

## 🏗 Arquitetura Modular

```
SyncFrame/
├── build_bin.sh                    # Pipeline de compilação em binário único ELF
├── syncframe.spec                  # Especificação PyInstaller otimizada para Linux
├── run.sh                          # Launcher Bash para desenvolvimento local
├── requirements.txt                # Dependências científicas (NumPy, SciPy, PySide6)
├── src/
│   ├── main.py                     # Ponto de entrada CLI/GUI com guardas de display
│   ├── core/                       # Motores de processamento multimídia desacoplados
│   │   ├── models.py               # Contratos de dados e schemas tipados
│   │   ├── inspector.py            # Inspeção de streams via mkvmerge -J e ffprobe
│   │   ├── extractor.py            # Extração mono PCM com passa-faixa e demux lossless
│   │   ├── correlator.py           # FFT Cross-Correlation com normalização matemática de sinal
│   │   ├── transformer.py          # Time-stretch lossless sem alteração de tom via atempo
│   │   ├── remuxer.py              # Orquestrador mkvmerge com passthrough e tags de sync
│   │   ├── temp_manager.py         # Gerenciamento de diretórios temporários e expurgo
│   │   └── disk_utils.py           # Validação pré-voo de capacidade em disco
│   ├── ui/                         # Interface Gráfica desktop (PySide6)
│   │   ├── app.py                  # Factory de instanciação do QApplication (v1.0.0)
│   │   ├── main_window.py          # Janela principal responsiva com esteira de ação única
│   │   ├── style.py                # Design system neutro monocromático (Dark/Light QSS)
│   │   ├── components/             # Componentes de interface modulares
│   │   │   ├── unified_drop_zone.py # Zona central unificada e Review Gate tabular
│   │   │   ├── completion_dialog.py # Modal de conclusão estilizado com zero-latency
│   │   │   ├── audio_preserve_checkbox.py # Seletor de preservação de alto contraste
│   │   │   ├── collapsible_section.py # Gaveta retrátil para ferramentas secundárias
│   │   │   ├── correlation_view.py # Visualizador do pico de correlação acústica
│   │   │   ├── sync_controls.py    # Controles de micro-ajuste e badges de métricas
│   │   │   ├── preview_player.py   # Spot-check player labial (5%, 50%, 90%)
│   │   │   └── log_drawer.py       # Gaveta de logs em tempo real
│   │   └── workers/                # Threads de segundo plano (QThread)
│   │       ├── unified_pipeline_worker.py # Orquestrador de ação única ininterrupta
│   │       ├── analyze_worker.py   # Análise espectral assíncrona
│   │       └── remux_worker.py     # Multiplexação com cancelamento gracioso
│   └── utils/
│       └── system_check.py         # Diagnóstico de integridade e logs de crash
└── tests/                          # Suíte de 53 testes unitários automatizados
    ├── test_completion_dialog.py
    ├── test_ui_components.py
    ├── test_system_diagnostics.py
    ├── test_container_handling.py
    ├── test_ui_layout_responsiveness.py
    ├── test_unified_drop_zone.py
    ├── test_stream_evaluator.py
    ├── test_correlator.py
    ├── test_models.py
    ├── test_inspector.py
    └── test_temp_manager.py
```

---

## 🧪 Suíte de Testes

Para executar os 53 testes unitários da esteira matemática, interface e modelos:

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📜 Licença

Distribuído sob licença MIT. Consulte `LICENSE` para mais detalhes.
