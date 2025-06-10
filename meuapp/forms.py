from django import forms
from .models import Requerente, Cliente, PerfilUsuario

class RequerenteForm(forms.ModelForm):
    class Meta:
        model = Requerente
        fields = '__all__'
        exclude = ['cliente']  # Excluir cliente do formulário
        
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    nome_razao_social = forms.CharField(label='Nome ou Razão Social', max_length=150)
    cpf_cnpj = forms.CharField(label='CPF ou CNPJ', max_length=18)
    cep = forms.CharField(label='CEP', max_length=9)
    endereco = forms.CharField(label='Endereço Completo', max_length=255)
    email = forms.EmailField(label='E-mail')

    class Meta:
        model = User
        fields = ('nome_razao_social', 'cpf_cnpj', 'cep', 'endereco', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Criar cliente automaticamente
            cliente = Cliente.objects.create(
                nome=self.cleaned_data['nome_razao_social'],
                email=self.cleaned_data['email'],
                cnpj=self.cleaned_data['cpf_cnpj']
            )
            # Criar perfil do usuário
            PerfilUsuario.objects.create(
                user=user,
                cliente=cliente
            )
        return user