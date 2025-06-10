from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .forms import SignUpForm
from .forms import RequerenteForm
from .models import Requerente, PerfilUsuario
import json
from selenium.webdriver.support.ui import Select

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        return reverse_lazy('tela_inicial')

class CustomLogoutView(LogoutView):
    next_page = '/login/'

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

def home(request):
    # Sempre redireciona para a tela de login
    return redirect('login')

@login_required
def tela_inicial(request):
    # Obter o cliente do usuário logado
    try:
        perfil_usuario = request.user.perfilusuario
        cliente = perfil_usuario.cliente
    except PerfilUsuario.DoesNotExist:
        return redirect('login')
    
    # Estatísticas básicas
    total_requerentes = Requerente.objects.filter(cliente=cliente).count()
    
    context = {
        'total_requerentes': total_requerentes,
    }
    
    return render(request, 'tela_inicial.html', context)

@login_required
def cadastro_requerente(request):
    # Obter o cliente do usuário logado
    try:
        perfil_usuario = request.user.perfilusuario
        cliente = perfil_usuario.cliente
    except PerfilUsuario.DoesNotExist:
        # Se não tem perfil, redirecionar para login
        return redirect('login')
    
    if request.method == 'POST':
        form = RequerenteForm(request.POST)
        if form.is_valid():
            requerente = form.save(commit=False)
            requerente.cliente = cliente  # Vincular ao cliente
            requerente.save()
            return redirect('cadastro_requerente')
    else:
        form = RequerenteForm()
    
    # Mostrar apenas requerentes do cliente logado
    requerentes = Requerente.objects.filter(cliente=cliente)
    
    return render(request, 'cadastro_requerente.html', {'form': form, 'requerentes': requerentes})

# Views placeholder para as outras funcionalidades
@login_required
def certidoes_negativas(request):
    # Obter o cliente do usuário logado
    try:
        perfil_usuario = request.user.perfilusuario
        cliente = perfil_usuario.cliente
    except PerfilUsuario.DoesNotExist:
        return redirect('login')
    
    # Buscar requerentes se houver filtro
    requerentes = []
    if request.method == 'POST':
        filtro = request.POST.get('filtro', '').strip()
        if filtro:
            requerentes = Requerente.objects.filter(
                cliente=cliente
            ).filter(
                Q(nome_completo__icontains=filtro) | 
                Q(cpf__icontains=filtro)
            )
    
    context = {
        'titulo': 'Emitir Certidões Negativas',
        'requerentes': requerentes
    }
    
    return render(request, 'certidoes_negativas.html', context)

@login_required
def gerar_certidao(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        requerente_id = data.get('requerente_id')
        tipo_certidao = data.get('tipo_certidao')
        
        try:
            # Obter o cliente do usuário logado
            perfil_usuario = request.user.perfilusuario
            cliente = perfil_usuario.cliente
            
            # Verificar se o requerente pertence ao cliente
            requerente = Requerente.objects.get(id=requerente_id, cliente=cliente)
            
            # Aqui implementaremos a automação com Selenium
            resultado = automatizar_certidao(requerente, tipo_certidao)
            
            return JsonResponse({
                'success': True,
                'message': f'Certidão {tipo_certidao} gerada com sucesso!',
                'resultado': resultado
            })
            
        except Requerente.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Requerente não encontrado.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao gerar certidão: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido.'})

def automatizar_certidao(requerente, tipo_certidao):
    """
    Função para automatizar a geração de certidões usando Selenium
    """
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    import time
    
    # Configurar Chrome em modo headless
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    urls = {
        'federal': 'https://web.trf3.jus.br/certidao-regional/',
        'estadual': 'https://esaj.tjsp.jus.br/sco/abrirCadastro.do',
        'militar': 'https://www.stm.jus.br/servicos-stm/certidao-negativa/emitir-certidao-negativa',
        'eleitoral': 'https://www.tse.jus.br/servicos-eleitorais/autoatendimento-eleitoral#/certidoes-eleitor'
    }
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        if tipo_certidao == 'todas':
            resultados = {}
            for tipo, url in urls.items():
                resultados[tipo] = processar_site(driver, url, requerente, tipo)
            return resultados
        else:
            url = urls.get(tipo_certidao)
            if url:
                return processar_site(driver, url, requerente, tipo_certidao)
            else:
                return {'erro': 'Tipo de certidão inválido'}
                
    except Exception as e:
        return {'erro': f'Erro na automação: {str(e)}'}
    finally:
        if 'driver' in locals():
            driver.quit()

def processar_site(driver, url, requerente, tipo):
    """
    Processa um site específico para gerar a certidão
    """
    try:
        driver.get(url)
        time.sleep(3)
        
        # Implementar lógica específica para cada site
        if 'trf3.jus.br' in url:  # Federal
            return processar_certidao_federal(driver, requerente)
        elif 'tjsp.jus.br' in url:  # Estadual
            return processar_certidao_estadual(driver, requerente)
        elif 'stm.jus.br' in url:  # Militar
            return processar_certidao_militar(driver, requerente)
        elif 'tse.jus.br' in url:  # Eleitoral
            return processar_certidao_eleitoral(driver, requerente)
        else:
            return {'status': 'Site não implementado'}
            
    except Exception as e:
        return {'erro': f'Erro ao processar {tipo}: {str(e)}'}

def processar_certidao_federal(driver, requerente):
    # Implementar automação específica para TRF3
    return {'status': 'Processado - Federal', 'site': 'TRF3'}

def processar_certidao_estadual(driver, requerente):
    # Implementar automação específica para TJSP
    return {'status': 'Processado - Estadual', 'site': 'TJSP'}

def processar_certidao_militar(driver, requerente):
    # Implementar automação específica para STM
    return {'status': 'Processado - Militar', 'site': 'STM'}

def processar_certidao_eleitoral(driver, requerente):
    # Implementar automação específica para TSE
    return {'status': 'Processado - Eleitoral', 'site': 'TSE'}

@login_required
def concessao_cr(request):
    return render(request, 'em_desenvolvimento.html', {'titulo': 'Concessão de CR'})

@login_required
def requisicao_compra(request):
    return render(request, 'em_desenvolvimento.html', {'titulo': 'Requisição de Compra'})

@login_required
def registro_craf(request):
    return render(request, 'em_desenvolvimento.html', {'titulo': 'Registro (CRAF)'})

@login_required
def guia_trafego(request):
    return render(request, 'em_desenvolvimento.html', {'titulo': 'Guia de Tráfego (GT)'})

@login_required
def emitir_gru(request):
    return render(request, 'em_desenvolvimento.html', {'titulo': 'Emitir Guia GRU'})

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import json
from django.http import JsonResponse
from .models import Requerente
import os
from django.conf import settings
from django.http import HttpResponse, FileResponse
import requests
from datetime import datetime

def automatizar_justica_federal(requerente_data, nome_certidao="Justiça Federal"):
    """
    Automatiza a geração de certidão negativa na Justiça Federal
    """
    try:
        print(f"🚀 INICIANDO AUTOMAÇÃO DA JUSTIÇA FEDERAL")
        print(f"📋 Requerente: {requerente_data['nome']}")
        print(f"📄 CPF: {requerente_data['cpf']}")
        
        # Configurar Chrome para download automático
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Configurar pasta de download
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        print(f"📁 Pasta de download configurada: {download_dir}")
        
        # Inicializar o driver
        print("🔧 Inicializando Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Chrome WebDriver inicializado com sucesso")
        
        # IMPORTANTE: Acessar diretamente a URL do formulário
        target_url = 'https://web.trf3.jus.br/certidao-regional/CertidaoCivelEleitoralCriminal/SolicitarDadosCertidao'
        print(f"🎯 ACESSANDO DIRETAMENTE: {target_url}")
        
        driver.get(target_url)
        print("⏳ Aguardando carregamento da página...")
        
        # Aguardar carregamento
        time.sleep(5)
        
        # Verificar URL atual
        current_url = driver.current_url
        print(f"📍 URL ATUAL APÓS ACESSO: {current_url}")
        
        if current_url != target_url and "SolicitarDadosCertidao" not in current_url:
            print(f"❌ ERRO: Foi redirecionado para: {current_url}")
            print("❌ Deveria estar em: SolicitarDadosCertidao")
            driver.quit()
            return JsonResponse({
                'success': False, 
                'message': f'Redirecionado incorretamente para: {current_url}'
            })
        
        print("✅ SUCESSO: Está na página do formulário!")
        
        # Aguardar carregamento do formulário
        wait = WebDriverWait(driver, 20)
        time.sleep(3)
        
        print("📝 INICIANDO PREENCHIMENTO DO FORMULÁRIO...")
        
        # 1. Selecionar tipo de certidão (CIVEL por padrão)
        print("🔍 Procurando campo 'Tipo de Certidão'...")
        try:
            tipo_select = wait.until(EC.presence_of_element_located((By.ID, "Tipo")))
            print("✅ Campo 'Tipo' encontrado")
            Select(tipo_select).select_by_value("CIVEL")
            time.sleep(1)
            print("✅ Tipo de certidão 'CIVEL' selecionado")
        except Exception as e:
            print(f"❌ Erro ao selecionar tipo de certidão: {e}")
            print("🔍 Tentando localizar elemento por outros métodos...")
            try:
                # Tentar outros seletores
                tipo_select = driver.find_element(By.NAME, "Tipo")
                Select(tipo_select).select_by_value("CIVEL")
                print("✅ Tipo selecionado via NAME")
            except Exception as e2:
                print(f"❌ Erro com seletor NAME: {e2}")
                # Continuar mesmo com erro
        
        # 2. Selecionar tipo de documento (CPF)
        print("🔍 Procurando campo 'Tipo de Documento'...")
        try:
            tipo_doc_select = wait.until(EC.presence_of_element_located((By.ID, "TipoDeDocumento")))
            print("✅ Campo 'TipoDeDocumento' encontrado")
            Select(tipo_doc_select).select_by_value("CPF")
            print("✅ Tipo de documento 'CPF' selecionado")
        except Exception as e:
            print(f"❌ Erro ao selecionar tipo de documento: {e}")
            driver.quit()
            return JsonResponse({'success': False, 'message': f'Erro no tipo de documento: {e}'})
        
        # 3. Preencher campo Documento (CPF)
        print(f"🔍 Preenchendo CPF: {requerente_data['cpf']}")
        try:
            documento_field = wait.until(EC.presence_of_element_located((By.ID, "Documento")))
            print("✅ Campo 'Documento' encontrado")
            documento_field.clear()
            documento_field.send_keys(requerente_data['cpf'])
            print(f"✅ CPF preenchido: {requerente_data['cpf']}")
        except Exception as e:
            print(f"❌ Erro ao preencher CPF: {e}")
            driver.quit()
            return JsonResponse({'success': False, 'message': f'Erro no CPF: {e}'})
        
        # 4. Preencher Nome Social
        print(f"🔍 Preenchendo Nome: {requerente_data['nome']}")
        try:
            nome_social_field = wait.until(EC.presence_of_element_located((By.ID, "NomeSocial")))
            print("✅ Campo 'NomeSocial' encontrado")
            nome_social_field.clear()
            nome_social_field.send_keys(requerente_data['nome'])
            print(f"✅ Nome preenchido: {requerente_data['nome']}")
        except Exception as e:
            print(f"❌ Erro ao preencher nome: {e}")
            driver.quit()
            return JsonResponse({'success': False, 'message': f'Erro no nome: {e}'})
        
        print("✅ FORMULÁRIO PREENCHIDO COM SUCESSO!")
        
        # 5. Verificar reCAPTCHA
        print("🔍 Verificando presença do reCAPTCHA...")
        time.sleep(2)
        
        try:
            # Procurar por diferentes elementos do reCAPTCHA
            recaptcha_frame = driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            print("🤖 reCAPTCHA detectado! Aguardando resolução manual...")
            print("⏰ Você tem 60 segundos para resolver o reCAPTCHA")
            print("👆 Clique no reCAPTCHA e complete o desafio")
            
            # Aguardar resolução manual
            WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit'] | //input[@type='submit']"))
            )
            print("✅ reCAPTCHA resolvido!")
            
        except Exception as e:
            print(f"⚠️ reCAPTCHA não encontrado ou já resolvido: {e}")
        
        # 6. Submeter formulário
        print("📤 Submetendo formulário...")
        try:
            submit_btn = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[@type='submit'] | //input[@type='submit']"
            )))
            print("✅ Botão de submit encontrado")
            submit_btn.click()
            print("✅ Formulário submetido!")
        except Exception as e:
            print(f"❌ Erro ao submeter formulário: {e}")
            driver.quit()
            return JsonResponse({'success': False, 'message': f'Erro na submissão: {e}'})
        
        # Aguardar processamento
        print("⏳ Aguardando processamento...")
        time.sleep(5)
        
        # 7. Procurar download
        print("🔍 Procurando link de download...")
        try:
            download_element = wait.until(EC.presence_of_element_located((
                By.XPATH, "//a[contains(@href, '.pdf')] | //button[contains(@onclick, '.pdf')] | //a[contains(text(), 'Download')] | //a[contains(text(), 'Baixar')]"
            )))
            
            download_url = download_element.get_attribute('href')
            print(f"✅ Link de download encontrado: {download_url}")
            
            if download_url:
                if download_url.startswith('/'):
                    download_url = 'https://web.trf3.jus.br' + download_url
                
                print(f"📥 Iniciando download: {download_url}")
                download_element.click()
                time.sleep(3)
                print("✅ Download iniciado!")
            
        except Exception as e:
            print(f"❌ Erro no download: {e}")
            print("⚠️ Tentando manter navegador aberto para download manual")
            time.sleep(10)  # Dar tempo para download manual
        
        print("🎉 AUTOMAÇÃO CONCLUÍDA!")
        time.sleep(5)  # Aguardar antes de fechar
        driver.quit()
        
        return JsonResponse({
            'success': True, 
            'message': f'Certidão da Justiça Federal processada para {requerente_data["nome"]}'
        })
        
    except Exception as e:
        print(f"💥 ERRO GERAL NA AUTOMAÇÃO: {e}")
        print(f"📍 Tipo do erro: {type(e).__name__}")
        try:
            driver.quit()
        except:
            pass
        return JsonResponse({'success': False, 'message': f'Erro na automação: {str(e)}'})

def gerar_certidao_justica_federal(request, requerente_id):
    """
    View para gerar certidão da Justiça Federal
    """
    if request.method == 'POST':
        try:
            requerente = Requerente.objects.get(id=requerente_id)
            
            # Preparar dados completos do requerente
            requerente_data = {
                # Dados pessoais básicos
                'nome': requerente.nome_completo,
                'cpf': requerente.cpf.replace('.', '').replace('-', ''),  # Remover formatação
                'rg': requerente.identidade,
                'data_nascimento': requerente.data_nascimento.strftime('%d/%m/%Y'),
                'sexo': requerente.sexo,
                'orgao_emissor': requerente.orgao_emissor,
                'uf_identidade': requerente.uf_identidade,
                'data_expedicao': requerente.data_expedicao.strftime('%d/%m/%Y'),
                'pais': requerente.pais,
                'titulo_eleitor': requerente.titulo_eleitor,
                'profissao': requerente.profissao,
                'outra_profissao': requerente.outra_profissao or '',
                
                # Contatos
                'telefone1': requerente.telefone1,
                'telefone2': requerente.telefone2 or '',
                'email': requerente.email,
                
                # Filiação
                'nome_mae': requerente.nome_mae,
                'nome_pai': requerente.nome_pai or '',
                
                # Endereço residencial
                'cep_residencial': requerente.cep_residencial,
                'endereco_residencial': requerente.endereco_residencial,
                'numero_residencial': requerente.numero_residencial,
                'bairro_residencial': requerente.bairro_residencial,
                'cidade_residencial': requerente.cidade_residencial,
                'uf_residencial': requerente.uf_residencial,
                'complemento_residencial': requerente.complemento_residencial or '',
                
                # Endereço do acervo (se disponível)
                'cep_acervo': requerente.cep_acervo or '',
                'endereco_acervo': requerente.endereco_acervo or '',
                'numero_acervo': requerente.numero_acervo or '',
                'bairro_acervo': requerente.bairro_acervo or '',
                'cidade_acervo': requerente.cidade_acervo or '',
                'uf_acervo': requerente.uf_acervo or '',
                'complemento_acervo': requerente.complemento_acervo or '',
                
                # Dados do cliente
                'cliente_nome': requerente.cliente.nome,
                'cliente_cnpj': requerente.cliente.cnpj or '',
                
                # Endereço completo formatado
                'endereco_completo': f"{requerente.endereco_residencial}, {requerente.numero_residencial} - {requerente.bairro_residencial}, {requerente.cidade_residencial} - {requerente.uf_residencial}, CEP: {requerente.cep_residencial}"
            }
            
            # Executar automação com nome da certidão
            resultado = automatizar_justica_federal(requerente_data, "Justiça_Federal")
            
            return JsonResponse(resultado)
            
        except Requerente.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Requerente não encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro interno: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

# Adicionar view para servir arquivos de download
def download_certidao(request, nome_arquivo):
    """
    View para fazer download de certidões
    """
    try:
        caminho_arquivo = os.path.join(settings.MEDIA_ROOT, 'certidoes', nome_arquivo)
        
        if os.path.exists(caminho_arquivo):
            response = FileResponse(
                open(caminho_arquivo, 'rb'),
                as_attachment=True,
                filename=nome_arquivo
            )
            response['Content-Type'] = 'application/pdf'
            return response
        else:
            return HttpResponse('Arquivo não encontrado', status=404)
            
    except Exception as e:
        return HttpResponse(f'Erro ao baixar arquivo: {str(e)}', status=500)
