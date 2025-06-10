from django.db import models
from django.contrib.auth.models import User

class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    cnpj = models.CharField(max_length=18, unique=True, blank=True, null=True)  # Adicionar CNPJ
    # Adicione outros campos relevantes para o clube/despachante

    def __str__(self):
        return self.nome

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    # Adicione outros campos de perfil, se necessário

    def __str__(self):
        return self.user.username

# Create your models here.
from django.db import models

class Requerente(models.Model):
    # NOVO CAMPO: Vincular ao cliente
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    
    nome_completo = models.CharField(max_length=150)
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')])
    cpf = models.CharField(max_length=14)  # Remover unique=True
    identidade = models.CharField(max_length=20)
    data_expedicao = models.DateField()
    orgao_emissor = models.CharField(max_length=20)
    uf_identidade = models.CharField(max_length=2)
    data_nascimento = models.DateField()
    pais = models.CharField(max_length=50)
    titulo_eleitor = models.CharField(max_length=20)
    profissao = models.CharField(max_length=50)
    outra_profissao = models.CharField(max_length=50, blank=True, null=True)
    telefone1 = models.CharField(max_length=20)
    telefone2 = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField()
    nome_mae = models.CharField(max_length=150)
    nome_pai = models.CharField(max_length=150, blank=True, null=True)
    # Endereço residencial
    cep_residencial = models.CharField(max_length=9)
    endereco_residencial = models.CharField(max_length=255)
    numero_residencial = models.CharField(max_length=10)
    bairro_residencial = models.CharField(max_length=100)
    cidade_residencial = models.CharField(max_length=100)
    uf_residencial = models.CharField(max_length=2)
    complemento_residencial = models.CharField(max_length=100, blank=True, null=True)
    latitude_residencial = models.CharField(max_length=30, blank=True, null=True)
    longitude_residencial = models.CharField(max_length=30, blank=True, null=True)
    # Segundo endereço do acervo
    cep_acervo = models.CharField(max_length=9, blank=True, null=True)
    endereco_acervo = models.CharField(max_length=255, blank=True, null=True)
    numero_acervo = models.CharField(max_length=10, blank=True, null=True)
    bairro_acervo = models.CharField(max_length=100, blank=True, null=True)
    cidade_acervo = models.CharField(max_length=100, blank=True, null=True)
    uf_acervo = models.CharField(max_length=2, blank=True, null=True)
    complemento_acervo = models.CharField(max_length=100, blank=True, null=True)
    latitude_acervo = models.CharField(max_length=30, blank=True, null=True)
    longitude_acervo = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        # CPF único apenas dentro do mesmo cliente
        unique_together = ['cliente', 'cpf']

    def __str__(self):
        return f"{self.nome_completo} - {self.cliente.nome}"
