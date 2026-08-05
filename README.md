# 🚦 Orquestração Semafórica via Protocolo RDS (Out-of-Band IoT)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![C++](https://img.shields.io/badge/C%2B%2B-Arduino-00979D?logo=arduino)](https://www.arduino.cc/)

Este repositório contém o código-fonte integral, esquemáticos e a documentação técnica da arquitetura analógica baseada em **Radio Data System (RDS)** para controle remoto de semáforos, apresentada ao Simpósio Brasileiro de Sistemas Multimídia e Web (WebMedia).

O objetivo deste projeto é demonstrar a viabilidade de operar infraestruturas urbanas críticas utilizando radiodifusão FM (VHF) como canal de contingência ou principal, garantindo a resiliência do sistema de trânsito independente de redes IP (Wi-Fi, 4G/5G, Fibra Óptica).

Este repositório contém o código-fonte (software e firmware), diagramas e as instruções de replicação de hardware para o projeto de pesquisa **"Usando a Infraestrutura FM como Canal de Controle por RDS"**, submetido à SBC WEBMEDIA.
---

## ⚙️ Arquitetura do Sistema

O ecossistema é dividido em três camadas principais:
1. **Orquestrador (Python):** Interface gráfica que converte as ações de controle de tráfego em cargas úteis (*payloads*) otimizadas.
2. **Nó Transmissor / Gateway (ESP32 + Si4713):** Recebe os comandos via USB/Serial e os irradia na subportadora inaudível de 57 kHz da frequência FM (106.1 MHz).
3. **Nó Receptor / Atuador (ESP8266 + Si4703):** Ouve a frequência, extrai as *strings* RDS, processa-as em um Motor de Estados finito e atua sobre os LEDs do semáforo.

---

## 🛠️ Material Necessário

Para replicar este experimento em bancada, você precisará de:

**Transmissor (TX):**
- 1x Microcontrolador ESP32
- 1x Módulo Transmissor FM Si4713 (Adafruit)
- Jumpers e protoboard

**Receptor (RX):**
- 1x Microcontrolador ESP8266 (NodeMCU)
- 1x Módulo Receptor FM Si4703 (SparkFun)
- 1x Led de Arduino Amarelo
- 1x Led de Arduino Verde
- 1x Led de Arduino Vermelho
- Fone de ouvido barato (o fio atua como antena receptora no conector P2 do Si4703)

---

## 🔌 Esquema de Ligação (Pinagem)

Importante ressaltar, que para melhor visualização e didática, fizemos um diagrama ilustrativo visual no diretório `Data/`, contendo cada um das tabelas de esquemas abaixo, bem como as suas respectivas tabelas neste manual de replicação, ambos os módulos de rádio utilizam o barramento **I2C**. Conecte conforme a tabela:

| Módulo Rádio | Pino ESP32 (TX) | Pino ESP8266 (RX) |
| :--- | :--- | :--- |
| **VCC / 3.3V** | 3V3 | 3V3 |
| **GND** | GND | GND |
| **SDA** | GPIO 21 | D2 (GPIO 4) |
| **SCL** | GPIO 22 | D1 (GPIO 5) |
| **RST** | GPIO 17 (opcional) | D3 (GPIO 0) |

> **Atenção:** Os módulos Si4703 e Si4713 operam em 3.3V. **Não** conecte no pino de 5V (VIN), sob risco de queimar os CIs.

---

## 🚀 Tutorial de Replicação

### 1. Preparando o Hardware (Firmware C/C++)
1. Instale a [Arduino IDE](https://www.arduino.cc/en/software).
2. Adicione as placas ESP32 e ESP8266 no Gerenciador de Placas.
3. Instale as seguintes bibliotecas através do `Library Manager`:
   - `Adafruit Si4713 Library` (Para o Transmissor)
   - `PU2CLR SI470X` ou `SparkFun Si4703` (Para o Receptor)
4. Abra o arquivo `firmware/tx_gateway_esp32/tx_gateway_esp32.ino`, compile e grave no ESP32.
5. Abra o arquivo `firmware/rx_atuador_esp8266/rx_atuador_esp8266.ino`, compile e grave no ESP8266.

### 2. Rodando o Orquestrador (Software Python)
Recomenda-se o uso de um ambiente virtual (venv).
```bash
# Clone o repositório
git clone [https://github.com/SEU-USUARIO/rds-async-traffic_light.git](https://github.com/SEU-USUARIO/rds-async-traffic_light.git)
cd rds-async-traffic_light/software

# Instale as dependências
pip install -r requirements.txt
# (As dependências são: pyserial e customtkinter)

# Execute o orquestrador
python orquestrador.py
