import json
import time
import os
from playwright.sync_api import sync_playwright

def buscar_lista_questoes(lista_questoes, caminho_arquivo="data/resultado_busca_tec.json"):
    print(f"Iniciando automação de busca no TEC via Playwright...")
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
            print("1. Faça seu login e resolva o CAPTCHA.")
            print("2. O script avançará SOZINHO assim que você logar.")
            print("="*40 + "\n")
            
            page.goto("https://www.tecconcursos.com.br/login")
            page.wait_for_function("window.location.pathname !== '/login'", timeout=0)
            print("✅ Login detectado! Iniciando buscas...\n")
            
            total = len(lista_questoes)

            for index, texto_questao in enumerate(lista_questoes, 1):
                print(f"🔍 Processando questão {index}/{total}...")
                
                # --- NOVA LÓGICA DE BUSCA MELHORADA ---
                # 1. Remove quebras de linha e espaços duplos
                texto_limpo = " ".join(texto_questao.split())
                
                # 2. Define um limite grande, mas seguro para o TEC (ex: 350 caracteres)
                limite_chars = 350
                if len(texto_limpo) > limite_chars:
                    # Corta no limite e usa rsplit para não deixar uma palavra cortada no meio
                    trecho_busca = texto_limpo[:limite_chars].rsplit(' ', 1)[0]
                else:
                    trecho_busca = texto_limpo

                print(f"   -> Buscando por: '{trecho_busca[:100]}...' (Tamanho: {len(trecho_busca)} chars)")
                # --------------------------------------
                
                # Navega sempre para a tela limpa de busca
                page.goto("https://www.tecconcursos.com.br/questoes/busca")
                
                # Aguarda o campo de busca estar disponível
                page.wait_for_selector("input#busca", timeout=15000)
                
                # Preenche e acorda o botão de busca
                page.fill("input#busca", trecho_busca)
                page.press("input#busca", "Space")
                time.sleep(0.5) 
                
                page.click("button[type='submit'].btn.btn-tec", force=True)
                
                # Aguarda aparecer a div de resultados
                try:
                    page.wait_for_function("""
                        document.querySelector('.questoes-busca-resultado') != null || 
                        document.body.innerText.includes('Nenhuma questão encontrada')
                    """, timeout=15000)
                    time.sleep(2.0) 
                except Exception:
                    pass

                # Botão de comentário
                botao_comentario = page.locator("button[aria-label='Comentário da questao'], button[ng-click*=\"abrirComplemento('comentario')\"]").first
                
                if botao_comentario.count() > 0 and botao_comentario.is_visible():
                    print("   -> Questão encontrada! Abrindo comentários...")
                    botao_comentario.click(force=True)
                    
                    painel_comentario = page.locator(".questao-complementos-comentario")
                    try:
                        painel_comentario.wait_for(state="visible", timeout=10000)
                        time.sleep(2.0) 
                        
                        conteudo = painel_comentario.first.inner_text()
                        
                        if conteudo.strip():
                            comentario_encontrado = conteudo.strip()
                            print("   ✅ Comentário extraído com sucesso.")
                        else:
                            comentario_encontrado = "Comentário abriu, mas o texto não carregou a tempo."
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
                    if page.locator("article.questao-enunciado").count() > 0:
                        comentario_encontrado = "Questão localizada no TEC, mas não possui comentários disponíveis (ou botão oculto)."
                        print(f"   ⚠️ {comentario_encontrado}")
                        resultados.append({
                            "texto_original": texto_questao,
                            "status": "Sem comentário",
                            "comentario": comentario_encontrado
                        })
                    else:
                        print("   ❌ Questão não encontrada no TEC.")
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