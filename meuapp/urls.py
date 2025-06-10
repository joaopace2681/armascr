from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.tela_inicial, name='tela_inicial'),
    path('cadastro-requerente/', views.cadastro_requerente, name='cadastro_requerente'),
    path('certidoes-negativas/', views.certidoes_negativas, name='certidoes_negativas'),
    path('gerar-certidao/', views.gerar_certidao, name='gerar_certidao'),
    path('concessao-cr/', views.concessao_cr, name='concessao_cr'),
    path('requisicao-compra/', views.requisicao_compra, name='requisicao_compra'),
    path('registro-craf/', views.registro_craf, name='registro_craf'),
    path('guia-trafego/', views.guia_trafego, name='guia_trafego'),
    path('emitir-gru/', views.emitir_gru, name='emitir_gru'),
    path('gerar-certidao-federal/<int:requerente_id>/', views.gerar_certidao_justica_federal, name='gerar_certidao_federal'),
    path('download-certidao/<str:nome_arquivo>/', views.download_certidao, name='download_certidao'),
]