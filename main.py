import customtkinter as ctk
import threading
import os
import sys
import datetime
import re

# Importando os dois buscadores criados
from src.buscador_tec import buscar_lista_questoes
from src.buscador_qc import buscar_lista_questoes_qc
from src.gerador_docs import formatar_documento_comentarios

def obter_caminho_base():
    """Retorna o caminho correto quer esteja rodando no VS Code ou no .exe final."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppBuscador(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Buscador Automático de Comentários")
        self.geometry("700x650") # Aumentado um pouco para caber os botões de seleção
        self.resizable(False, False)

        self.lbl_titulo = ctk.CTkLabel(self, text="Busca Automática de Comentários", font=("Arial", 22, "bold"))
        self.lbl_titulo.pack(pady=(20, 5))

        self.lbl_subtitulo = ctk.CTkLabel(self, text="Cole o bloco XML com as questões (<enunciado_questao>...):", font=("Arial", 13), text_color="gray")
        self.lbl_subtitulo.pack(pady=(0, 10))

        # Caixa de texto para colar as questões
        self.textbox_questoes = ctk.CTkTextbox(self, width=600, height=250, font=("Arial", 13))
        self.textbox_questoes.pack(pady=5)

        # --- SELEÇÃO DE PLATAFORMA ---
        self.frame_plataforma = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_plataforma.pack(pady=10)
        
        self.lbl_plataforma = ctk.CTkLabel(self.frame_plataforma, text="Selecione a Plataforma:", font=("Arial", 14, "bold"))
        self.lbl_plataforma.grid(row=0, column=0, columnspan=2, pady=(0, 5))
        
        self.plataforma_var = ctk.StringVar(value="TEC") # Plataforma padrão selecionada
        
        self.rb_tec = ctk.CTkRadioButton(self.frame_plataforma, text="TEC Concursos", variable=self.plataforma_var, value="TEC")
        self.rb_tec.grid(row=1, column=0, padx=20)
        
        self.rb_qc = ctk.CTkRadioButton(self.frame_plataforma, text="QConcursos", variable=self.plataforma_var, value="QC")
        self.rb_qc.grid(row=1, column=1, padx=20)
        # -----------------------------

        self.btn_buscar = ctk.CTkButton(self, text="Buscar Comentários", width=250, height=45, font=("Arial", 15, "bold"), command=self.iniciar_busca)
        self.btn_buscar.pack(pady=10)

        self.lbl_status = ctk.CTkLabel(self, text="", font=("Arial", 13))
        self.lbl_status.pack(pady=5)

        self.btn_abrir_doc = ctk.CTkButton(
            self, text="📄 Abrir Documento Gerado", width=250, height=45, 
            font=("Arial", 15, "bold"), fg_color="#10b981", hover_color="#059669", 
            state="disabled", command=self.abrir_documento
        )
        self.btn_abrir_doc.pack(pady=10)

        self.caminho_doc_gerado = "" 

    def iniciar_busca(self):
        texto_bruto = self.textbox_questoes.get("1.0", "end-1c").strip()
        
        if not texto_bruto:
            self.lbl_status.configure(text="Por favor, cole as questões na caixa de texto.", text_color="#ef4444") 
            return

        # LÓGICA DE EXTRAÇÃO VIA REGEX (Tags XML/HTML)
        padrao = re.compile(r'<enunciado_questao>(.*?)</enunciado_questao>', re.IGNORECASE | re.DOTALL)
        questoes_lista = [q.strip() for q in padrao.findall(texto_bruto) if q.strip()]

        if not questoes_lista:
            self.lbl_status.configure(text="Nenhuma questão válida encontrada nas tags <enunciado_questao>.", text_color="#ef4444") 
            return

        plataforma = self.plataforma_var.get()
        self.btn_buscar.configure(state="disabled", text="Buscando... Aguarde")
        self.lbl_status.configure(text=f"Abrindo navegador para buscar {len(questoes_lista)} questões no {plataforma}...", text_color="#eab308") 
        self.btn_abrir_doc.configure(state="disabled")

        threading.Thread(target=self.tarefa_em_segundo_plano, args=(questoes_lista, plataforma), daemon=True).start()

    def tarefa_em_segundo_plano(self, questoes_lista, plataforma):
        try:
            caminho_base = obter_caminho_base()
            pasta_data = os.path.join(caminho_base, "data")
            os.makedirs(pasta_data, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
            caminho_novo_doc = os.path.join(pasta_data, f"Comentarios_{plataforma}_{timestamp}.docx")
            caminho_json = os.path.join(pasta_data, f"resultado_busca_{plataforma.lower()}.json")

            # Executa a automação baseada na escolha feita na interface
            if plataforma == "TEC":
                buscar_lista_questoes(questoes_lista, caminho_json)
            elif plataforma == "QC":
                buscar_lista_questoes_qc(questoes_lista, caminho_json)
            
            self.lbl_status.configure(text="Formatando documento do Word...", text_color="#eab308")
            
            # Formata o documento (Usamos a mesma função geradora!)
            sucesso = formatar_documento_comentarios(caminho_json=caminho_json, caminho_saida=caminho_novo_doc)
            
            if sucesso:
                self.caminho_doc_gerado = caminho_novo_doc 
                self.lbl_status.configure(text="✅ Processo finalizado com sucesso!", text_color="#10b981") 
                self.btn_abrir_doc.configure(state="normal") 
            else:
                self.lbl_status.configure(text="❌ Falha na geração do documento.", text_color="#ef4444")
                
        except Exception as e:
            self.lbl_status.configure(text="❌ Erro durante a execução. Verifique o terminal.", text_color="#ef4444")
            print(f"Erro detalhado: {e}")
            
        finally:
            self.btn_buscar.configure(state="normal", text="Buscar Novas Questões")

    def abrir_documento(self):
        if not self.caminho_doc_gerado: return
        caminho_absoluto = os.path.abspath(self.caminho_doc_gerado)
        if os.path.exists(caminho_absoluto):
            os.startfile(caminho_absoluto)
            self.lbl_status.configure(text="Documento aberto!", text_color="#10b981")

if __name__ == "__main__":
    app = AppBuscador()
    app.mainloop()