#!/bin/bash
# Script para iniciar a aplicação web de correção de gabaritos

VENV_PATH="/home/proatec/gabarito/venv"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       SISTEMA WEB DE CORREÇÃO DE GABARITOS                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Ativar venv
source "$VENV_PATH/bin/activate"

# Verificar dependências
echo "📦 Verificando dependências..."
pip install -q flask

echo ""
echo "🚀 Iniciando aplicação web..."
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Acesse em: http://localhost:5000"
echo ""
echo "📋 Funcionalidades:"
echo "  • Upload de PDFs"
echo "  • Correção automática com OCR"
echo "  • Visualização de relatórios"
echo "  • Estatísticas de desempenho"
echo "  • Histórico de correções"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Pressione CTRL+C para parar o servidor"
echo ""

# Iniciar aplicação
python3 app.py
