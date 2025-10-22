#!/bin/bash
# Script para executar testes do Sistema de Gabaritos

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Sistema de Gabaritos - Suite de Testes ===${NC}\n"

# Verificar se ambiente virtual existe
if [ ! -d "venv" ]; then
    echo -e "${RED}Erro: Ambiente virtual não encontrado!${NC}"
    echo "Execute primeiro:"
    echo "  sudo apt install python3.11-venv"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  pip install pytest pytest-cov"
    exit 1
fi

# Ativar ambiente virtual
echo -e "${YELLOW}Ativando ambiente virtual...${NC}"
source venv/bin/activate

# Verificar se pytest está instalado
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Erro: pytest não está instalado!${NC}"
    echo "Execute: pip install pytest pytest-cov"
    exit 1
fi

# Menu de opções
echo -e "\nEscolha o tipo de teste:"
echo "1) Todos os testes"
echo "2) Apenas testes unitários"
echo "3) Apenas testes de integração"
echo "4) Testes com cobertura de código"
echo "5) Teste rápido (teste_rapido.py)"
echo "6) Testes específicos (você escolhe o arquivo)"
echo ""
read -p "Opção [1-6]: " opcao

case $opcao in
    1)
        echo -e "\n${GREEN}Executando TODOS os testes...${NC}\n"
        pytest tests/ -v
        ;;
    2)
        echo -e "\n${GREEN}Executando testes UNITÁRIOS...${NC}\n"
        pytest tests/test_gerador_gabarito.py tests/test_corretor.py -v
        ;;
    3)
        echo -e "\n${GREEN}Executando testes de INTEGRAÇÃO...${NC}\n"
        pytest tests/test_integration.py -v
        ;;
    4)
        echo -e "\n${GREEN}Executando testes com COBERTURA...${NC}\n"
        pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
        echo -e "\n${YELLOW}Relatório HTML gerado em: htmlcov/index.html${NC}"
        ;;
    5)
        echo -e "\n${GREEN}Executando TESTE RÁPIDO (integração básica)...${NC}\n"
        python3 teste_rapido.py
        ;;
    6)
        echo -e "\nArquivos de teste disponíveis:"
        ls tests/test_*.py
        echo ""
        read -p "Digite o nome do arquivo (ex: test_corretor.py): " arquivo
        echo -e "\n${GREEN}Executando testes de: $arquivo${NC}\n"
        pytest tests/$arquivo -v
        ;;
    *)
        echo -e "${RED}Opção inválida!${NC}"
        exit 1
        ;;
esac

# Status de saída
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Testes concluídos com sucesso!${NC}\n"
else
    echo -e "\n${RED}✗ Alguns testes falharam!${NC}\n"
    exit 1
fi
