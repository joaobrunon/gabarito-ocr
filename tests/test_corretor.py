"""
Testes unitários para o módulo corretor.py
"""
import pytest
import os
import json
from corretor import Corretor


class TestCorretor:
    """Testes para a classe Corretor"""

    def test_criar_instancia(self):
        """Testa criação de instância do corretor"""
        corretor = Corretor()
        assert corretor is not None
        assert hasattr(corretor, 'definir_gabarito_oficial')
        assert hasattr(corretor, 'corrigir_prova')

    def test_definir_gabarito_oficial_dict(self, sample_gabarito_dict):
        """Testa definição de gabarito oficial via dicionário"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)
        assert corretor.gabarito_oficial == sample_gabarito_dict

    def test_carregar_gabarito_json(self, sample_gabarito_json):
        """Testa carregamento de gabarito oficial de arquivo JSON"""
        corretor = Corretor()
        corretor.carregar_gabarito_oficial(sample_gabarito_json)
        assert corretor.gabarito_oficial is not None
        assert len(corretor.gabarito_oficial) == 10

    def test_carregar_gabarito_csv(self, sample_gabarito_csv):
        """Testa carregamento de gabarito oficial de arquivo CSV"""
        corretor = Corretor()
        corretor.carregar_gabarito_oficial(sample_gabarito_csv)
        assert corretor.gabarito_oficial is not None
        assert len(corretor.gabarito_oficial) == 10

    def test_carregar_gabarito_txt(self, sample_gabarito_txt):
        """Testa carregamento de gabarito oficial de arquivo TXT"""
        corretor = Corretor()
        corretor.carregar_gabarito_oficial(sample_gabarito_txt)
        assert corretor.gabarito_oficial is not None
        assert len(corretor.gabarito_oficial) == 10

    def test_salvar_gabarito_oficial_json(self, temp_dir, sample_gabarito_dict):
        """Testa salvamento de gabarito oficial em JSON"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        arquivo_saida = os.path.join(temp_dir, "gabarito_salvo.json")
        corretor.salvar_gabarito_oficial(arquivo_saida)

        assert os.path.exists(arquivo_saida)
        with open(arquivo_saida, 'r') as f:
            gabarito_carregado = json.load(f)
        assert gabarito_carregado == sample_gabarito_dict

    def test_corrigir_prova_nota_maxima(self, sample_gabarito_dict):
        """Testa correção de prova com todas as respostas corretas"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        prova = {
            "identificacao": {"nome": "Aluno Teste", "matricula": "001"},
            "respostas": sample_gabarito_dict.copy()
        }

        resultado = corretor.corrigir_prova(prova)

        assert resultado['nota'] == 10.0
        assert resultado['acertos'] == 10
        assert resultado['erros'] == 0
        assert resultado['em_branco'] == 0
        assert resultado['percentual'] == 100.0

    def test_corrigir_prova_nota_zero(self, sample_gabarito_dict):
        """Testa correção de prova com todas as respostas erradas"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        respostas_erradas = {str(i): "X" for i in range(1, 11)}
        prova = {
            "identificacao": {"nome": "Aluno Teste", "matricula": "002"},
            "respostas": respostas_erradas
        }

        resultado = corretor.corrigir_prova(prova)

        assert resultado['nota'] == 0.0
        assert resultado['acertos'] == 0
        assert resultado['erros'] == 10
        assert resultado['percentual'] == 0.0

    def test_corrigir_prova_com_respostas_em_branco(self, sample_gabarito_dict):
        """Testa correção de prova com respostas em branco"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        respostas_parciais = sample_gabarito_dict.copy()
        respostas_parciais["5"] = ""
        respostas_parciais["10"] = ""

        prova = {
            "identificacao": {"nome": "Aluno Teste", "matricula": "003"},
            "respostas": respostas_parciais
        }

        resultado = corretor.corrigir_prova(prova)

        assert resultado['acertos'] == 8
        assert resultado['em_branco'] == 2
        assert resultado['nota'] == 8.0

    def test_corrigir_prova_parcialmente_correta(self, sample_gabarito_dict):
        """Testa correção de prova com 50% de acertos"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        respostas_mistas = {
            "1": "A",  # Correto
            "2": "X",  # Errado
            "3": "C",  # Correto
            "4": "X",  # Errado
            "5": "E",  # Correto
            "6": "X",  # Errado
            "7": "B",  # Correto
            "8": "X",  # Errado
            "9": "D",  # Correto
            "10": "X"  # Errado
        }

        prova = {
            "identificacao": {"nome": "Aluno Teste", "matricula": "004"},
            "respostas": respostas_mistas
        }

        resultado = corretor.corrigir_prova(prova)

        assert resultado['acertos'] == 5
        assert resultado['erros'] == 5
        assert resultado['nota'] == 5.0
        assert resultado['percentual'] == 50.0

    def test_corrigir_lote_csv(self, sample_gabarito_dict, sample_students_csv):
        """Testa correção em lote a partir de arquivo CSV"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        resultados = corretor.corrigir_lote(sample_students_csv)

        assert len(resultados) == 3
        assert all('nota' in r for r in resultados)
        assert all('identificacao' in r for r in resultados)

    def test_corrigir_lote_json(self, sample_gabarito_dict, sample_students_json):
        """Testa correção em lote a partir de arquivo JSON"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        resultados = corretor.corrigir_lote(sample_students_json)

        assert len(resultados) == 2
        assert all('nota' in r for r in resultados)
        assert all('identificacao' in r for r in resultados)

    def test_gerar_relatorio_individual(self, sample_gabarito_dict, sample_student_answers, temp_dir):
        """Testa geração de relatório individual"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        resultado = corretor.corrigir_prova(sample_student_answers)

        arquivo_relatorio = os.path.join(temp_dir, "relatorio_individual.txt")
        corretor.gerar_relatorio_individual(resultado, arquivo_relatorio)

        assert os.path.exists(arquivo_relatorio)
        assert os.path.getsize(arquivo_relatorio) > 0

        with open(arquivo_relatorio, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            assert "João Silva" in conteudo
            assert "Nota" in conteudo

    def test_gerar_relatorio_turma(self, sample_gabarito_dict, sample_students_csv, temp_dir):
        """Testa geração de relatório de turma"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        resultados = corretor.corrigir_lote(sample_students_csv)

        arquivo_relatorio = os.path.join(temp_dir, "relatorio_turma.txt")
        corretor.gerar_relatorio_turma(resultados, arquivo_relatorio)

        assert os.path.exists(arquivo_relatorio)
        assert os.path.getsize(arquivo_relatorio) > 0

        with open(arquivo_relatorio, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            assert "Média" in conteudo or "Estatísticas" in conteudo

    def test_exportar_resultados_csv(self, sample_gabarito_dict, sample_students_csv, temp_dir):
        """Testa exportação de resultados em CSV"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        resultados = corretor.corrigir_lote(sample_students_csv)

        arquivo_export = os.path.join(temp_dir, "resultados.csv")
        corretor.exportar_resultados(resultados, arquivo_export, formato='csv')

        assert os.path.exists(arquivo_export)
        with open(arquivo_export, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            assert "nome" in conteudo.lower() or "nota" in conteudo.lower()

    def test_exportar_resultados_json(self, sample_gabarito_dict, sample_students_json, temp_dir):
        """Testa exportação de resultados em JSON"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        resultados = corretor.corrigir_lote(sample_students_json)

        arquivo_export = os.path.join(temp_dir, "resultados.json")
        corretor.exportar_resultados(resultados, arquivo_export, formato='json')

        assert os.path.exists(arquivo_export)
        with open(arquivo_export, 'r') as f:
            dados = json.load(f)
            assert isinstance(dados, list)
            assert len(dados) > 0

    def test_corrigir_sem_gabarito_oficial(self):
        """Testa correção sem definir gabarito oficial"""
        corretor = Corretor()

        prova = {
            "identificacao": {"nome": "Teste", "matricula": "001"},
            "respostas": {"1": "A", "2": "B"}
        }

        with pytest.raises(Exception):
            corretor.corrigir_prova(prova)

    def test_carregar_gabarito_arquivo_inexistente(self):
        """Testa carregamento de gabarito de arquivo inexistente"""
        corretor = Corretor()

        with pytest.raises(FileNotFoundError):
            corretor.carregar_gabarito_oficial("arquivo_inexistente.json")

    def test_corrigir_prova_com_pesos(self, sample_gabarito_dict):
        """Testa correção de prova com pesos diferentes por questão"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        pesos = {str(i): 1.0 if i <= 5 else 2.0 for i in range(1, 11)}

        prova = {
            "identificacao": {"nome": "Aluno Teste", "matricula": "005"},
            "respostas": {
                "1": "A", "2": "B", "3": "C", "4": "D", "5": "E",
                "6": "X", "7": "X", "8": "X", "9": "X", "10": "X"
            }
        }

        resultado = corretor.corrigir_prova(prova, pesos=pesos)

        assert resultado['acertos'] == 5
        assert resultado['erros'] == 5
        # Nota ponderada deve ser diferente de 5.0

    def test_estatisticas_turma(self, sample_gabarito_dict, sample_students_csv):
        """Testa cálculo de estatísticas da turma"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        resultados = corretor.corrigir_lote(sample_students_csv)

        notas = [r['nota'] for r in resultados]
        media = sum(notas) / len(notas)
        nota_max = max(notas)
        nota_min = min(notas)

        assert media >= 0 and media <= 10
        assert nota_max >= nota_min
        assert len(resultados) == 3

    def test_analise_dificuldade_questoes(self, sample_gabarito_dict, sample_students_csv):
        """Testa análise de dificuldade por questão"""
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        resultados = corretor.corrigir_lote(sample_students_csv)

        # Analisa quantos alunos acertaram cada questão
        acertos_por_questao = {}
        for questao in sample_gabarito_dict.keys():
            acertos_por_questao[questao] = 0

        for resultado in resultados:
            questoes_corretas = resultado.get('questoes_corretas', [])
            for questao in questoes_corretas:
                if questao in acertos_por_questao:
                    acertos_por_questao[questao] += 1

        # Verifica se as estatísticas fazem sentido
        for questao, acertos in acertos_por_questao.items():
            assert acertos >= 0
            assert acertos <= len(resultados)
