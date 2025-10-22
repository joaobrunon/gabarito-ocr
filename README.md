# Sistema de Correção de Gabaritos com OCR

Um sistema web completo para criar gabaritos, fazer upload de PDFs e corrigir automaticamente usando OCR.

## ✨ Funcionalidades

- 📝 **Criar Gabaritos**: Interface intuitiva com círculos clicáveis para definir as respostas
- 📤 **Upload de PDFs**: Envie arquivos PDF para serem corrigidos automaticamente
- 🤖 **OCR Automático**: Detecta e reconhece respostas marcadas nos PDFs
- 📊 **Relatórios**: Gera relatórios detalhados em HTML e JSON
- 📈 **Estatísticas**: Acompanhe notas, acertos e erros
- 🌐 **Interface Web**: Dashboard moderno e responsivo

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.8+
- pip

### Instalação

1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/gabarito-ocr.git
cd gabarito-ocr
```

2. Crie um ambiente virtual
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências
```bash
pip install -r requirements.txt
```

4. Inicie a aplicação
```bash
bash run_app.sh
```

5. Acesse no navegador
```
http://localhost:5000
```

## 📋 Como Usar

### 1. Criar um Gabarito

1. Acesse a aba "Gabaritos"
2. Digite o nome do gabarito
3. Defina o número de questões
4. Clique nos círculos para selecionar as respostas (A, B, C, D ou E)
5. Clique em "Criar Gabarito"

### 2. Corrigir PDFs

1. Acesse a aba "Correção"
2. Arraste um PDF ou clique para selecionar
3. O sistema corrige automaticamente
4. Visualize o relatório em HTML ou JSON

## 🛠️ Estrutura do Projeto

```
.
├── app.py                    # Aplicação Flask (backend)
├── corrigir_rapido.py       # Script de correção rápida
├── leitor_gabarito.py       # OCR com detecção de círculos
├── visualizar_relatorio.py  # Gerador de relatórios HTML
├── templates/
│   └── index.html           # Interface web
├── static/
│   ├── css/style.css        # Estilos
│   └── js/app.js            # Lógica frontend
├── gabaritos/               # Gabaritos salvos (JSON)
├── pdfs_para_corrigir/      # PDFs para processar
└── relatorios_correcao/     # Relatórios gerados
```

## 📚 API Endpoints

### Gabaritos
- `GET /api/gabaritos` - Lista todos os gabaritos
- `GET /api/gabarito/atual` - Retorna gabarito oficial atual
- `POST /api/gabarito/criar` - Cria novo gabarito
- `POST /api/gabarito/selecionar/<nome>` - Seleciona como oficial
- `DELETE /api/gabarito/deletar/<nome>` - Deleta um gabarito

### Correção
- `GET /api/reports` - Lista todos os relatórios
- `POST /api/upload` - Corrige um PDF
- `GET /api/stats` - Estatísticas gerais

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` se necessário:

```
FLASK_ENV=production
FLASK_DEBUG=False
```

### Portas

- Aplicação web: `5000`
- Servidor padrão: `localhost`

## 📦 Dependências

- Flask: Framework web
- PyMuPDF (fitz): Processamento de PDFs
- OpenCV: Processamento de imagens
- Pillow: Manipulação de imagens

Veja `requirements.txt` para a lista completa.

## 🐛 Troubleshooting

### Aplicação não inicia
```bash
# Verifique se a porta 5000 está disponível
lsof -i :5000

# Ou use outra porta editando app.py
```

### Erro ao processar PDF
```bash
# Verifique se o PDF é válido
file seu_arquivo.pdf

# Tente processar novamente
bash run_app.sh
```

## 📄 Licença

Este projeto está sob a licença MIT. Veja `LICENSE` para mais detalhes.

## 👤 Autor

Desenvolvido como sistema de correção automática de gabaritos com OCR.

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Notas

- O OCR funciona melhor com PDFs de alta qualidade
- Círculos bem preenchidos são reconhecidos com precisão
- Suporta gabaritos com qualquer número de questões (1-200)
