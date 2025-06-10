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
