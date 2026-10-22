# SyncFrame

**SyncFrame** é uma aplicação desktop de alta fidelidade voltada para a automação de remux e sincronização precisa de áudio dublado e vídeo de alta definição a partir de arquivos MKV distintos.

Projetado com uma interface neutra, minimalista e de alta densidade de informação, o sistema soluciona desalinhamentos temporais causados por atrasos estáticos iniciais, discrepâncias de frame rate (23.976 fps vs. 24.000 fps vs. 25.000 fps PAL) e deriva contínua através de inspeção matemática de metadados e correlação acústica por FFT, realizando multiplexação direta sem reencodamento de vídeo.

---

## ⚡ Características Principais

- **Fidelidade Visual 100% Intocada (Zero-Loss Passthrough):** O vídeo de referência **nunca** é reencodificado; o fluxo é transmitido diretamente bit-a-bit via `mkvmerge`.
- **Zero Recompressão de Áudio para Offsets Estáticos:** Se as taxas de quadros forem congruentes, o atraso/adiantamento é aplicado nativamente no cabeçalho do contêiner MKV (`--sync <TRACK_ID>:<OFFSET_MS>`), preservando a qualidade de áudio original sem perda de geração.
- **Detecção de Framerate & Correlação FFT Multi-Janela:** Extrai trechos acústicos filtrados (bandpass 300Hz-4000Hz mono PCM) no início (5%), meio (50%) e fim (85%) para isolar transientes, trilhas incidentais e foley idênticos entre idiomas, diagnosticando divergências de frame rate conhecidas:
  - `23.976 fps ↔ 24.000 fps` (deriva telecine NTSC de $1001/1000 \approx +0.1001\%$)
  - `24.000 fps ↔ 25.000 fps` (PAL Speedup/Slowdown de $25/24 \approx +4.167\%$)
- **Zona Unificada de Entrada (Unified Drop Zone) & Review Gate Tabular:** Zona central inteligente que aceita 1 ou 2 arquivos MKV simultaneamente ou seleção via diálogo nativo de arquivos:
  - Ingestão simultânea de fontes com avaliação heurística imediata em segundo plano.
  - Painel de confirmação assistida inline com seleção de faixas recomendadas (vídeo de melhor imagem, áudio dublado em português e áudio de referência original).
  - Aprovação instantânea em 1 clique ou via tecla **Enter**, deflagrando autonomamente todo o pipeline de extração, cálculo de offset e multiplexação sem perdas.
- **Estética Neutra Monocromática & Modo Escuro/Claro:** Design refinado em escala de cinza neutra, preto e branco, sem cores temáticas saturadas ou invasivas, com alternador dinâmico de tema (`🌓`) no cabeçalho.
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

## 🚀 Inicialização Rápida

O projeto inclui um launcher de inicialização rápida executável por duplo clique ou terminal:

```bash
# Permissão de execução (já configurada no repositório)
chmod +x run.sh

# Execução direta
./run.sh
```

O script `run.sh` valida as dependências do sistema, configura ou reutiliza o ambiente virtual isolado (`.venv`), sincroniza dependências de `requirements.txt` silenciosamente e inicia a aplicação.

### Modos Adicionais

```bash
# Diagnóstico de ferramentas do sistema via CLI (sem GUI)
./run.sh --cli-check

# Exibir versão
./run.sh --version
```

---

## 🏗 Arquitetura Modular

```
SyncFrame/
├── run.sh                          # Launcher Bash executável por duplo clique
├── requirements.txt                # Dependências Python (NumPy, SciPy, PySide6)
├── src/
│   ├── main.py                     # Ponto de entrada CLI/GUI
│   ├── core/                       # Motor de processamento desacoplado
│   │   ├── models.py               # Contratos de dados e schemas tipados
│   │   ├── inspector.py            # Inspeção de streams via mkvmerge -J e ffprobe
│   │   ├── extractor.py            # Extração mono 16kHz PCM com filtro passa-faixa 300-4000Hz
│   │   ├── correlator.py           # FFT Cross-Correlation e estimador de deriva/framerate
│   │   ├── transformer.py          # Time-stretch lossless sem alteração de tom via atempo
│   │   ├── remuxer.py              # Orquestrador mkvmerge com passthrough e tags de sync
│   │   ├── temp_manager.py         # Gerenciamento de diretórios temporários e expurgo atômico
│   │   └── disk_utils.py           # Validação pré-voo de capacidade em disco
│   ├── ui/                         # Interface Gráfica desktop (PySide6)
│   │   ├── app.py                  # Factory de instanciação do QApplication
│   │   ├── main_window.py          # Janela principal responsiva com QScrollArea e tema alternável
│   │   ├── style.py                # Design system neutro monocromático (Dark/Light QSS)
│   │   ├── components/             # Componentes modulares de UI
│   │   │   ├── unified_drop_zone.py # Zona unificada de ingestão e Review Gate tabular inline
│   │   │   ├── stream_selector_modal.py # Modal assistido de confirmação de faixas
│   │   │   ├── correlation_view.py # Gráfico de correlação desenhado em QPainter
│   │   │   ├── sync_controls.py    # Controles de micro-ajuste (±50ms) e métricas
│   │   │   ├── preview_player.py   # Spot-check player nos marcadores 5%, 50%, 90%
│   │   │   ├── log_drawer.py       # Gaveta retrátil de logs do terminal
│   │   │   └── file_drop_card.py   # Card modular legado de drop
│   │   └── workers/                # Threads de segundo plano (QThread)
│   │       ├── analyze_worker.py   # Análise espectral assíncrona multi-janela
│   │       └── remux_worker.py     # Multiplexação com suporte a cancelamento
│   └── utils/
│       └── system_check.py         # Validador de utilitários do SO host
└── tests/                          # Suíte de testes unitários automatizados
    ├── test_models.py
    ├── test_correlator.py
    ├── test_inspector.py
    ├── test_temp_manager.py
    ├── test_stream_evaluator.py
    ├── test_unified_drop_zone.py
    └── test_ui_layout_responsiveness.py
```

---

## 🧪 Suíte de Testes

Para executar os testes unitários da esteira matemática e dos modelos:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📜 Licença

Distribuído sob licença MIT. Consulte `LICENSE` para mais detalhes.
