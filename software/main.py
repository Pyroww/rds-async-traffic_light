import customtkinter as ctk
import serial
import serial.tools.list_ports
from datetime import datetime
import threading
import time

# ==========================================
# CONFIGURAÇÃO ESTÉTICA (Light Mode)
# ==========================================
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


COR_VERDE = "#009600"      # Verde escuro
COR_AMARELA = "#B8860B"    # GoldenRod
COR_VERMELHA = "#C80000"   # Vermelho acadêmico
COR_AZUL_RX = "#0000CD"    # MediumBlue para modo Receptor
COR_FUNDO_LOG = "#F5F5F5"  # Cinza bem claro (WhiteSmoke)

class CommandCenterRDS(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações da Janela Principal
        self.title("Command Center RDS - Protocolo V4 (Python Edition)")
        self.geometry("450x480")
        self.minsize(450, 480)

        # Variáveis de Estado
        self.porta_serial = None
        self.modo_atual = "DESCONHECIDO"
        self.estado_teste_rapido = 0

        # Layout Principal (Grid Config)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # O log expande

        # --- PAINEL 1: CONEXÃO ---
        self.create_conexao_panel()

        # --- PAINEL 2: CONTROLES MANUAIS ---
        self.create_manual_panel()

        # --- PAINEL 3: CONFIGURADOR DE CICLO ---
        self.create_auto_panel()

        # --- PAINEL 4: LOG ---
        self.create_log_panel()

        # Inicialização
        self.bloquear_controles(False)
        self.log_dinamico("=== Sistema Iniciado. Aguardando Conexão ===")

    # ==========================================
    # CRIAÇÃO DA INTERFACE (UI)
    # ==========================================

    def create_conexao_panel(self):
        self.frame_conexao = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_conexao.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.frame_conexao, text="Porta COM:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        
        self.combo_portas = ctk.CTkComboBox(self.frame_conexao, values=self.listar_portas(), width=200)
        self.combo_portas.pack(side="left", padx=5)

        self.btn_conectar = ctk.CTkButton(self.frame_conexao, text="CONECTAR", command=self.conectar_serial, fg_color="#3b8ed0")
        self.btn_conectar.pack(side="left", padx=10)

    def create_manual_panel(self):
        self.frame_manual = ctk.CTkFrame(self)
        self.frame_manual.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.frame_manual.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(self.frame_manual, text="Overrides Manuais", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, pady=5)

        self.btn_verde = ctk.CTkButton(self.frame_manual, text="🟢 VERDE", text_color=COR_VERDE, fg_color="#f9f9f9", hover_color="#e0e0e0", border_width=1, border_color="#d0d0d0", command=lambda: self.injetar_comando("110000"))
        self.btn_verde.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.btn_amarelo = ctk.CTkButton(self.frame_manual, text="🟡 AMARELO", text_color=COR_AMARELA, fg_color="#f9f9f9", hover_color="#e0e0e0", border_width=1, border_color="#d0d0d0", command=lambda: self.injetar_comando("001100"))
        self.btn_amarelo.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.btn_vermelho = ctk.CTkButton(self.frame_manual, text="🔴 VERMELHO", text_color=COR_VERMELHA, fg_color="#f9f9f9", hover_color="#e0e0e0", border_width=1, border_color="#d0d0d0", command=lambda: self.injetar_comando("000011"))
        self.btn_vermelho.grid(row=1, column=2, padx=10, pady=10, sticky="ew")

        self.btn_desativar = ctk.CTkButton(self.frame_manual, text="⏹ DESLIGAR TUDO", fg_color="#555555", hover_color="#333333", command=lambda: self.injetar_comando("000000"))
        self.btn_desativar.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.btn_alerta_geral = ctk.CTkButton(self.frame_manual, text="⚠️ ALERTA GERAL", fg_color="#FF4500", hover_color="#CC3700", command=lambda: self.injetar_comando("020202"))
        self.btn_alerta_geral.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        self.btn_alerta_padrao = ctk.CTkButton(self.frame_manual, text="⚠️ ALERTA PADRÃO", fg_color=COR_AMARELA, hover_color="#8B6508", text_color="white", command=lambda: self.injetar_comando("000300"))
        self.btn_alerta_padrao.grid(row=2, column=2, padx=10, pady=10, sticky="ew")

        self.btn_teste_rapido = ctk.CTkButton(self.frame_manual, text="⚡ TESTE RÁPIDO", fg_color="#777777", hover_color="#555555", command=self.action_teste_rapido)
        self.btn_teste_rapido.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

    def create_auto_panel(self):
        self.frame_auto = ctk.CTkFrame(self)
        self.frame_auto.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.frame_auto.grid_columnconfigure((1, 2, 4, 5), weight=1)

        ctk.CTkLabel(self.frame_auto, text="Configurador do Ciclo Automático (No Hardware)", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=6, pady=5)

        # Verde
        self.chk_verde = ctk.CTkCheckBox(self.frame_auto, text="🟢 VERDE", text_color=COR_VERDE)
        self.chk_verde.select()
        self.chk_verde.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(self.frame_auto, text="Tempo (seg):", text_color=COR_VERDE).grid(row=1, column=1, sticky="e")
        self.txt_verde = ctk.CTkEntry(self.frame_auto, width=50, justify="center")
        self.txt_verde.insert(0, "3")
        self.txt_verde.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        # Amarelo
        self.chk_amarelo = ctk.CTkCheckBox(self.frame_auto, text="🟡 AMARELO", text_color=COR_AMARELA)
        self.chk_amarelo.select()
        self.chk_amarelo.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(self.frame_auto, text="Tempo (seg):", text_color=COR_AMARELA).grid(row=2, column=1, sticky="e")
        self.txt_amarelo = ctk.CTkEntry(self.frame_auto, width=50, justify="center")
        self.txt_amarelo.insert(0, "1")
        self.txt_amarelo.grid(row=2, column=2, padx=5, pady=5, sticky="w")

        # Vermelho
        self.chk_vermelho = ctk.CTkCheckBox(self.frame_auto, text="🔴 VERMELHO", text_color=COR_VERMELHA)
        self.chk_vermelho.select()
        self.chk_vermelho.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(self.frame_auto, text="Tempo (seg):", text_color=COR_VERMELHA).grid(row=3, column=1, sticky="e")
        self.txt_vermelho = ctk.CTkEntry(self.frame_auto, width=50, justify="center")
        self.txt_vermelho.insert(0, "3")
        self.txt_vermelho.grid(row=3, column=2, padx=5, pady=5, sticky="w")

        self.btn_enviar_ciclo = ctk.CTkButton(self.frame_auto, text="🚀 INJETAR CICLO NO RDS", fg_color="#228B22", hover_color="#006400", command=self.action_enviar_ciclo)
        self.btn_enviar_ciclo.grid(row=2, column=4, columnspan=2, padx=20, sticky="ew")

    def create_log_panel(self):
        self.log_area = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12), state="disabled", wrap="word", fg_color=COR_FUNDO_LOG, text_color="black", border_width=1, border_color="#d0d0d0")
        self.log_area.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

    

    def listar_portas(self):
        portas = serial.tools.list_ports.comports()
        return [p.device for p in portas] or ["Nenhuma porta encontrada"]

    def log_dinamico(self, mensagem, color="black"):
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        
        self.log_area.configure(state="normal")
        
        self.log_area.configure(text_color=color) 
        self.log_area.insert("end", timestamp + mensagem + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def bloquear_controles(self, status):
        state = "normal" if status else "disabled"
        
        for child in self.frame_manual.winfo_children():
            if isinstance(child, ctk.CTkButton):
                child.configure(state=state)
        
        for child in self.frame_auto.winfo_children():
            if isinstance(child, (ctk.CTkButton, ctk.CTkCheckBox, ctk.CTkEntry)):
                child.configure(state=state)

    def injetar_comando(self, comando):
        if self.porta_serial and self.porta_serial.is_open:
            try:
                msg = (comando + "\n").encode('utf-8')
                self.porta_serial.write(msg)
                self.porta_serial.flush() 
                self.log_dinamico(f"📡 RDS [Protocolo V4]: {comando}")
            except Exception as e:
                self.log_dinamico(f"❌ Erro ao enviar: {e}", "red")

    def formata_tempo_segundos(self, entry_widget):
        texto = entry_widget.get().strip()
        try:
            tempo_segundos = int(texto)
            tempo_limitado = max(1, min(tempo_segundos, 99)) 
            return f"{tempo_limitado:02d}"
        except ValueError:
            return "03" 

    # --- Ações ---

    def action_teste_rapido(self):
        if self.estado_teste_rapido == 0:
            self.injetar_comando("020202"); self.estado_teste_rapido = 1
        elif self.estado_teste_rapido == 1:
            self.injetar_comando("030303"); self.estado_teste_rapido = 2
        else:
            self.injetar_comando("111111"); self.estado_teste_rapido = 0

    def action_enviar_ciclo(self):
        v = self.formata_tempo_segundos(self.txt_verde) if self.chk_verde.get() else "00"
        a = self.formata_tempo_segundos(self.txt_amarelo) if self.chk_amarelo.get() else "00"
        r = self.formata_tempo_segundos(self.txt_vermelho) if self.chk_vermelho.get() else "00"
        
        payload = "t" + v + a + r
        self.injetar_comando(payload)

    

    def conectar_serial(self):
        
        if self.porta_serial and self.porta_serial.is_open:
            self.porta_serial.close()
            self.log_dinamico("Conexão encerrada.")
            self.btn_conectar.configure(state="normal", text="CONECTAR", fg_color="#3b8ed0", hover_color="#36719F")
            self.combo_portas.configure(state="normal")
            self.modo_atual = "DESCONHECIDO"
            self.frame_conexao.configure(fg_color="transparent")
            self.bloquear_controles(False) 
            return
        

        porta_nome = self.combo_portas.get()
        if porta_nome == "Nenhuma porta encontrada" or not porta_nome:
            self.log_dinamico("⚠️ Selecione uma porta COM válida.", "orange")
            return

        try:
            # Configuração base
            self.porta_serial = serial.Serial()
            self.porta_serial.port = porta_nome
            self.porta_serial.baudrate = 115200
            self.porta_serial.timeout = 0.1 

            
            self.porta_serial.open()
            
            
            self.porta_serial.setDTR(False)
            self.porta_serial.setRTS(False)

            self.btn_conectar.configure(state="disabled", text="CONECTANDO...")
            self.combo_portas.configure(state="disabled")
            self.log_dinamico(f"✅ Interrogando placa USB na porta {porta_nome}...")

            # Inicia thread de leitura
            self.thread_leitura = threading.Thread(target=self.ler_serial_thread, daemon=True)
            self.thread_leitura.start()

            # BLINDAGEM 3 (Correção do PING): Usar Thread para delay de boot
            threading.Thread(target=self.enviar_ping_id, daemon=True).start()

        except Exception as e:
            self.log_dinamico(f"❌ Falha ao tentar abrir a {porta_nome}: {e}", "red")
            self.btn_conectar.configure(state="normal", text="CONECTAR")
            self.combo_portas.configure(state="normal")

    def enviar_ping_id(self):
        time.sleep(2.0) # Espera o ESP32 dar boot
        
        # BLINDAGEM 4 (Flush): Limpa o buffer de sujeira do Bootloader
        if self.porta_serial and self.porta_serial.is_open:
            self.porta_serial.reset_input_buffer()
            self.porta_serial.reset_output_buffer()
            
            # Dispara a requisição
            self.porta_serial.write("PING_ID\n".encode('utf-8'))
            self.porta_serial.flush()

    def ler_serial_thread(self):
        while self.porta_serial and self.porta_serial.is_open:
            try:
                if self.porta_serial.in_waiting > 0:
                    linha = self.porta_serial.readline().decode('utf-8', errors='ignore').strip()
                    if linha:
                        
                        self.after(0, self.processar_linha_serial, linha)
            except Exception as e:
                
                if not self.porta_serial or not self.porta_serial.is_open:
                    break
                # Se for erro real, loga
                self.after(0, self.log_dinamico, f"⚠️ Erro de leitura: {e}", "red")

    def processar_linha_serial(self, linha):
        if self.modo_atual == "DESCONHECIDO":
            
            if "SYS_ID:TRANSMISSOR" in linha or "TX: Comando" in linha:
                self.modo_atual = "TRANSMISSOR"
                self.frame_conexao.configure(fg_color="#e6ffed") # Fundo esverdeado suave
                self.bloquear_controles(True)
                
                
                self.log_dinamico("🚀 TX: Controles Ciber-Físicos Liberados.", COR_VERDE)
                
                # --- ATUALIZA O BOTÃO PARA DESCONECTAR ---
                self.btn_conectar.configure(state="normal", text="DESCONECTAR", fg_color=COR_VERMELHA, hover_color="#FF0000")
                return 
            
            elif "SYS_ID:RECEPTOR" in linha:
                self.modo_atual = "RECEPTOR"
                self.frame_conexao.configure(fg_color="#e6f7ff") # Fundo azulado suave
                
                # Ajuste de cores para fundo claro (MediumBlue)
                self.log_dinamico("🎧 RX: Monitorando LEDs.", COR_AZUL_RX)
                
                # --- ATUALIZA O BOTÃO PARA DESCONECTAR ---
                self.btn_conectar.configure(state="normal", text="DESCONECTAR", fg_color=COR_VERMELHA, hover_color="#FF0000")
                return

        prefixo = "ESP32: " if self.modo_atual == "TRANSMISSOR" else ""
        self.log_dinamico(prefixo + linha)

if __name__ == "__main__":
    app = CommandCenterRDS()
    app.mainloop()
