#!/bin/bash
# Script para corrigir PDF e gerar relatório HTML automaticamente

if [ -z "$1" ]; then
    echo "Uso: ./corrigir_e_visualizar.sh <arquivo.pdf>"
    echo ""
    echo "Exemplo:"
    echo "  ./corrigir_e_visualizar.sh pdfs_para_corrigir/teste_v2_01_PERFEITO_100.pdf"
    exit 1
fi

PDF_PATH="$1"
VENV_PATH="/home/proatec/gabarito/venv"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║    SISTEMA DE CORREÇÃO COM RELATÓRIO HTML                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Ativar venv
source "$VENV_PATH/bin/activate"

# Corrigir PDF
echo "📋 Corrigindo PDF..."
python3 corrigir_rapido.py "$PDF_PATH" > /tmp/resultado_correcao.txt 2>&1

if [ $? -ne 0 ]; then
    echo "✗ Erro ao corrigir PDF"
    cat /tmp/resultado_correcao.txt
    exit 1
fi

# Extrair nome do arquivo
NOME_ARQUIVO=$(basename "$PDF_PATH" .pdf)

# Procurar relatório JSON mais recente
JSON_FILE=$(find relatorios_correcao -name "*${NOME_ARQUIVO}*relatorio.json" -type f | head -1)

if [ -z "$JSON_FILE" ]; then
    echo "✗ Relatório JSON não encontrado"
    exit 1
fi

# Gerar HTML
echo "🌐 Gerando relatório HTML..."
python3 visualizar_relatorio.py "$JSON_FILE" > /tmp/resultado_html.txt 2>&1

if [ $? -ne 0 ]; then
    echo "✗ Erro ao gerar HTML"
    cat /tmp/resultado_html.txt
    exit 1
fi

# Extrair caminho do HTML
HTML_FILE="${JSON_FILE%.json}.html"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "✅ PROCESSO CONCLUÍDO COM SUCESSO!"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📄 PDF: $PDF_PATH"
echo "📊 JSON: $JSON_FILE"
echo "🌐 HTML: $HTML_FILE"
echo ""
echo "Abra o arquivo HTML em seu navegador:"
echo "  file://$PWD/$HTML_FILE"
echo ""
