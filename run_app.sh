#!/bin/bash
# Script para rodar a aplicação web

cd /home/proatec/gabarito

# Ativar venv
source venv/bin/activate

# Instalar dependências se necessário
pip install -q flask

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║    SISTEMA WEB DE CORREÇÃO DE GABARITOS                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Acessível em: http://localhost:5000"
echo ""
echo "✅ Funcionalidades:"
echo "   • Upload e correção de PDFs"
echo "   • Criar e gerenciar gabaritos"
echo "   • Visualizar relatórios"
echo "   • Estatísticas em tempo real"
echo ""
echo "Pressione CTRL+C para parar"
echo ""

# Rodar app
python3 app.py
