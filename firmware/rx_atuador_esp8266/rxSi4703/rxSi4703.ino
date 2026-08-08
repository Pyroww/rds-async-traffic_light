#include <Wire.h>
#include <SI470X.h>

#define PINO_RESET 14 // D5

SI470X rx;

char ultimaMensagem[65] = ""; 

// Pinos do Semáforo
const int pinoVermelho = 15; // D8
const int pinoAmarelo = 13;  // D6
const int pinoVerde = 12;    // D7

// Variáveis do Motor de Estado
int modoAtual = 0; // 0=OFF, 1=Estatico, 2=Piscar Rápido, 3=Piscar Lento, 4=Ciclo
unsigned long ultimoPiscar = 0;
bool estadoPiscar = false;

// Tempos do Ciclo (agora armazenados em milissegundos internamente)
unsigned long tempoVerde = 0;
unsigned long tempoAmarelo = 0;
unsigned long tempoVermelho = 0;

// 0 = Verde, 1 = Amarelo, 2 = Vermelho
int faseCiclo = 0; 
unsigned long ultimaMudancaCiclo = 0;

void limparTexto(char* texto) {
  if (texto == NULL) return;
  for (int i = 0; i < strlen(texto); i++) {
    if (!isprint(texto[i])) texto[i] = ' '; 
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(pinoVermelho, OUTPUT); pinMode(pinoAmarelo, OUTPUT); pinMode(pinoVerde, OUTPUT);
  desligarLeds();

  pinMode(PINO_RESET, OUTPUT);
  digitalWrite(PINO_RESET, LOW); delay(100); 
  digitalWrite(PINO_RESET, HIGH); delay(100); 

  Wire.begin(4, 5); 
  rx.setup(PINO_RESET, 4); 
  rx.setFrequency(10610); 
  rx.setVolume(0); 
  rx.setRDS(true);

  Serial.println("✅ Receptor Ciber-Físico V4.0 (Protocolo 't') Ativo");
}

void desligarLeds() {
  digitalWrite(pinoVerde, LOW); digitalWrite(pinoAmarelo, LOW); digitalWrite(pinoVermelho, LOW);
}

void processarPayload(String payload) {
  // Se o comando começa com 't' ou 'T', é o Configurador de Tempo!
  if (payload.charAt(0) == 't' || payload.charAt(0) == 'T') {
    // Extrai pares de segundos e converte para milissegundos (x 1000)
    tempoVerde = payload.substring(1, 3).toInt() * 1000UL;
    tempoAmarelo = payload.substring(3, 5).toInt() * 1000UL;
    tempoVermelho = payload.substring(5, 7).toInt() * 1000UL;
    
    modoAtual = 4; // Entra no modo ciclo
    faseCiclo = 0;
    ultimaMudancaCiclo = millis();
    Serial.println("[RDS] Novo Ciclo: V=" + String(tempoVerde/1000) + "s, A=" + String(tempoAmarelo/1000) + "s, R=" + String(tempoVermelho/1000) + "s");
  } 
  else {
    // Comandos de Override Manual (Padrões Puros)
    String cmd = payload.substring(0, 6);
    if (cmd == "000000") { modoAtual = 0; desligarLeds(); Serial.println("[RDS] Comando: OFF"); }
    else if (cmd == "111111") { modoAtual = 1; digitalWrite(pinoVerde, HIGH); digitalWrite(pinoAmarelo, HIGH); digitalWrite(pinoVermelho, HIGH); Serial.println("[RDS] Comando: TODOS ON"); }
    else if (cmd == "110000") { modoAtual = 1; digitalWrite(pinoVerde, HIGH); digitalWrite(pinoAmarelo, LOW); digitalWrite(pinoVermelho, LOW); Serial.println("[RDS] Comando: VERDE ON"); }
    else if (cmd == "001100") { modoAtual = 1; digitalWrite(pinoVerde, LOW); digitalWrite(pinoAmarelo, HIGH); digitalWrite(pinoVermelho, LOW); Serial.println("[RDS] Comando: AMARELO ON"); }
    else if (cmd == "000011") { modoAtual = 1; digitalWrite(pinoVerde, LOW); digitalWrite(pinoAmarelo, LOW); digitalWrite(pinoVermelho, HIGH); Serial.println("[RDS] Comando: VERMELHO ON"); }
    else if (cmd == "020202") { modoAtual = 2; Serial.println("[RDS] Comando: PISCAR RÁPIDO"); }
    else if (cmd == "030303") { modoAtual = 3; Serial.println("[RDS] Comando: PISCAR LENTO"); }
    else if (cmd == "000300") { modoAtual = 5; Serial.println("[RDS] Comando: ALERTA AMARELO"); }
  }
}

void rodarMotorHardware() {
  unsigned long agora = millis();

  // Piscar Rápido e Lento
  if (modoAtual == 2 && (agora - ultimoPiscar >= 150)) {
    estadoPiscar = !estadoPiscar;
    digitalWrite(pinoVerde, estadoPiscar); digitalWrite(pinoAmarelo, estadoPiscar); digitalWrite(pinoVermelho, estadoPiscar);
    ultimoPiscar = agora;
  } else if (modoAtual == 3 && (agora - ultimoPiscar >= 800)) {
    estadoPiscar = !estadoPiscar;
    digitalWrite(pinoVerde, estadoPiscar); digitalWrite(pinoAmarelo, estadoPiscar); digitalWrite(pinoVermelho, estadoPiscar);
    ultimoPiscar = agora;
  } 
  // Ciclo Automático Independente
  else if (modoAtual == 4) {
    unsigned long tempoAtualDaFase = (faseCiclo == 0) ? tempoVerde : (faseCiclo == 1) ? tempoAmarelo : tempoVermelho;
    
    digitalWrite(pinoVerde, faseCiclo == 0 ? HIGH : LOW);
    digitalWrite(pinoAmarelo, faseCiclo == 1 ? HIGH : LOW);
    digitalWrite(pinoVermelho, faseCiclo == 2 ? HIGH : LOW);

    // Salta a fase ou muda quando o tempo acaba
    if (tempoAtualDaFase == 0 || (agora - ultimaMudancaCiclo >= tempoAtualDaFase)) {
      do {
        faseCiclo = (faseCiclo + 1) % 3; 
        tempoAtualDaFase = (faseCiclo == 0) ? tempoVerde : (faseCiclo == 1) ? tempoAmarelo : tempoVermelho;
      } while (tempoAtualDaFase == 0 && (tempoVerde > 0 || tempoAmarelo > 0 || tempoVermelho > 0)); 
      
      ultimaMudancaCiclo = agora;
    }
  }

  else if (modoAtual == 5 && (agora - ultimoPiscar >= 800)) {
    estadoPiscar = !estadoPiscar;
    digitalWrite(pinoVerde, LOW); // Garante o verde desligado
    digitalWrite(pinoAmarelo, estadoPiscar); // Pisca só o amarelo
    digitalWrite(pinoVermelho, LOW); // Garante o vermelho desligado
    ultimoPiscar = agora;
  }

}

void loop() {
  if (Serial.available()) {
    String comandoUsb = Serial.readStringUntil('\n');
    comandoUsb.trim();
    if (comandoUsb.equals("PING_ID")) Serial.println("SYS_ID:RECEPTOR"); 
  }

  rodarMotorHardware();

  if (rx.getRdsReady()) { 
    char* radioText = rx.getRdsText2A();
    if (radioText != NULL) {
      limparTexto(radioText);
      if (strcmp(radioText, ultimaMensagem) != 0) {
        strcpy(ultimaMensagem, radioText);
        String msg = String(ultimaMensagem);
        // Agora verifica se tem pelo menos 6 ou 7 chars (t + 6 numeros)
        if (msg.length() >= 6) {
          processarPayload(msg);
        }
      }
    }
  }
}