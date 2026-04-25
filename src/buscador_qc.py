import json
import time
import os
from playwright.sync_api import sync_playwright

def buscar_lista_questoes_qc(lista_questoes, caminho_arquivo="data/resultado_busca_qc.json"):
    print(f"Iniciando automação de busca no QConcursos via Playwright...")
    resultados = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"]
        ) 
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("\n" + "="*40)
            print("🛑 PAUSA PARA LOGIN E CAPTCHA 🛑")
            print("1. O navegador abrirá a página de login do QConcursos.")
            print("2. Faça seu login e resolva o CAPTCHA.")
            print("3. APÓS LOGAR, CLIQUE EM 'Questões' no menu (ou navegue até a página de questões).")
            print("4. O script assumirá o controle SOZINHO assim que reconhecer a página de questões.")
            print("="*40 + "\n")
            
            # Vai para a página de login do QC
            page.goto("https://www.qconcursos.com/#!/signin-email")
            
            # Aguarda a ação do usuário de navegar para a tela de questões
            page.wait_for_url("**/questoes-de-concursos/questoes*", timeout=0)
            print("✅ Página de questões detectada! Iniciando as buscas...\n")
            
            total = len(lista_questoes)

            for index, texto_questao in enumerate(lista_questoes, 1):
                print(f"🔍 Processando questão {index}/{total}...")
                
                # --- NOVA LÓGICA DE BUSCA MELHORADA ---
                # 1. Remove quebras de linha e espaços duplos
                texto_limpo = " ".join(texto_questao.split())
                
                # 2. Como vimos, o input do QC tem maxlength="250". 
                # Vamos usar 240 caracteres de margem de segurança.
                limite_chars = 240
                if len(texto_limpo) > limite_chars:
                    trecho_busca = texto_limpo[:limite_chars].rsplit(' ', 1)[0]
                else:
                    trecho_busca = texto_limpo

                print(f"   -> Buscando por: '{trecho_busca[:100]}...' (Tamanho: {len(trecho_busca)} chars)")
                # --------------------------------------
                
                # Navega sempre para a tela limpa de busca de questões do QC
                page.goto("https://www.qconcursos.com/questoes-de-concursos/questoes")
                
                # Aguarda o campo de busca estar disponível
                page.wait_for_selector("input#questions-keywords-search", timeout=15000)
                
                # Preenche e aciona espaço
                page.fill("input#questions-keywords-search", trecho_busca)
                page.press("input#questions-keywords-search", "Space")
                time.sleep(0.5)
                
                # Clica no botão de buscar
                page.click('button[aria-label="Buscar por Palavra chave"]', force=True)
                
                try:
                    page.wait_for_function("""
                        document.querySelector('.q-page-results-title') != null || 
                        document.body.innerText.includes('Não encontramos questões') ||
                        document.body.innerText.includes('Nenhuma questão')
                    """, timeout=15000)
                    time.sleep(2.0) 
                except Exception:
                    pass

                titulo_resultados = page.locator('.q-page-results-title')
                
                if titulo_resultados.count() > 0 and "0" not in titulo_resultados.first.inner_text():
                    print("   -> Questão encontrada! Abrindo comentários...")
                    
                    botao_comentario = page.locator('a[data-component-name="question_teacher"]').first
                    
                    if botao_comentario.count() > 0 and botao_comentario.is_visible():
                        botao_comentario.click(force=True)
                        
                        painel_comentario = page.locator('div[id*="-teacher-tab"].active .q-text, .q-text').first
                        
                        try:
                            painel_comentario.wait_for(state="visible", timeout=10000)
                            time.sleep(1.5) 
                            
                            conteudo = painel_comentario.inner_text()
                            
                            if conteudo.strip():
                                comentario_encontrado = conteudo.strip()
                                print("   ✅ Comentário do Professor extraído com sucesso.")
                            else:
                                comentario_encontrado = "Aba de comentários abriu, mas o texto do professor estava vazio."
                                print(f"   ⚠️ {comentario_encontrado}")
                                
                            resultados.append({
                                "texto_original": texto_questao,
                                "status": "Encontrada",
                                "comentario": comentario_encontrado
                            })
                            
                        except Exception as e:
                            comentario_encontrado = f"Erro ao tentar ler o texto do comentário: {e}"
                            print(f"   ❌ {comentario_encontrado}")
                            resultados.append({
                                "texto_original": texto_questao,
                                "status": "Encontrada com erro",
                                "comentario": comentario_encontrado
                            })
                    else:
                        comentario_encontrado = "Questão localizada, mas não possui 'Gabarito Comentado' pelo professor."
                        print(f"   ⚠️ {comentario_encontrado}")
                        resultados.append({
                            "texto_original": texto_questao,
                            "status": "Sem comentário",
                            "comentario": comentario_encontrado
                        })
                else:
                    print("   ❌ Questão não encontrada no QConcursos.")
                    resultados.append({
                        "texto_original": texto_questao,
                        "status": "Não encontrada",
                        "comentario": "A questão não foi localizada na base de dados (Busca não retornou resultados)."
                    })

        except Exception as e:
            print(f"Ocorreu um erro geral durante a execução: {e}")
            
        finally:
            try:
                browser.close()
            except Exception:
                pass

    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=4)
        
    print(f"\nFeito! Busca finalizada e salva em '{caminho_arquivo}'.")
    return True