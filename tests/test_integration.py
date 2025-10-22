"""
Testes de integração para o sistema completo
"""
import pytest
import os
import json
from gerador_gabarito import GeradorGabarito
from corretor import Corretor


class TestIntegracaoCompleta:
    """Testes de integração do fluxo completo do sistema"""

    def test_fluxo_completo_basico(self, temp_dir, sample_gabarito_dict):
        """
        Testa fluxo completo:
        1. Gerar PDF de gabarito
        2. Definir gabarito oficial
        3. Corrigir provas
        4. Gerar relatórios
        5. Exportar resultados
        """
        # 1. Gerar PDF de gabarito
        gerador = GeradorGabarito()
        arquivo_pdf = os.path.join(temp_dir, "gabarito_integracao.pdf")
        gerador.gerar_gabarito_padrao(
            num_questoes=10,
            num_alternativas=5,
            arquivo_saida=arquivo_pdf
        )
        assert os.path.exists(arquivo_pdf)

        # 2. Definir gabarito oficial
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        # Salvar gabarito oficial
        arquivo_gabarito = os.path.join(temp_dir, "gabarito_oficial.json")
        corretor.salvar_gabarito_oficial(arquivo_gabarito)
        assert os.path.exists(arquivo_gabarito)

        # 3. Corrigir prova individual
        prova1 = {
            "identificacao": {
                "nome": "João Silva",
                "matricula": "12345",
                "turma": "3A"
            },
            "respostas": sample_gabarito_dict.copy()
        }
        resultado1 = corretor.corrigir_prova(prova1)
        assert resultado1['nota'] == 10.0

        # 4. Gerar relatório individual
        arquivo_relatorio = os.path.join(temp_dir, "relatorio_individual.txt")
        corretor.gerar_relatorio_individual(resultado1, arquivo_relatorio)
        assert os.path.exists(arquivo_relatorio)

        # 5. Exportar resultado
        arquivo_export = os.path.join(temp_dir, "resultado.json")
        corretor.exportar_resultados([resultado1], arquivo_export, formato='json')
        assert os.path.exists(arquivo_export)

    def test_fluxo_correcao_lote(self, temp_dir, sample_gabarito_dict):
        """
        Testa fluxo de correção em lote:
        1. Criar arquivo com respostas de múltiplos alunos
        2. Corrigir em lote
        3. Gerar relatório de turma
        4. Exportar resultados
        """
        # 1. Criar arquivo CSV com respostas
        arquivo_respostas = os.path.join(temp_dir, "respostas_turma.csv")
        with open(arquivo_respostas, 'w', encoding='utf-8') as f:
            f.write("nome,matricula,turma,q1,q2,q3,q4,q5,q6,q7,q8,q9,q10\n")
            f.write("João Silva,12345,3A,A,B,C,D,E,A,B,C,D,E\n")
            f.write("Maria Santos,12346,3A,A,B,C,D,E,A,B,C,D,E\n")
            f.write("Pedro Costa,12347,3A,A,B,X,X,E,A,B,C,D,E\n")

        # 2. Definir gabarito e corrigir lote
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)
        resultados = corretor.corrigir_lote(arquivo_respostas)

        assert len(resultados) == 3
        assert resultados[0]['nota'] == 10.0  # João - todas corretas
        assert resultados[1]['nota'] == 10.0  # Maria - todas corretas
        assert resultados[2]['nota'] < 10.0   # Pedro - tem erros

        # 3. Gerar relatório de turma
        arquivo_relatorio = os.path.join(temp_dir, "relatorio_turma.txt")
        corretor.gerar_relatorio_turma(resultados, arquivo_relatorio)
        assert os.path.exists(arquivo_relatorio)

        # 4. Exportar resultados
        arquivo_export = os.path.join(temp_dir, "resultados_turma.csv")
        corretor.exportar_resultados(resultados, arquivo_export, formato='csv')
        assert os.path.exists(arquivo_export)

    def test_fluxo_multiplas_secoes(self, temp_dir):
        """
        Testa fluxo com gabarito personalizado (múltiplas seções)
        """
        # Gerar gabarito com múltiplas seções
        gerador = GeradorGabarito()
        arquivo_pdf = os.path.join(temp_dir, "gabarito_secoes.pdf")

        secoes = [
            {
                'tipo': 'multipla_escolha',
                'num_questoes': 15,
                'num_alternativas': 5,
                'titulo': 'Múltipla Escolha'
            },
            {
                'tipo': 'verdadeiro_falso',
                'num_questoes': 10,
                'titulo': 'Verdadeiro ou Falso'
            }
        ]

        gerador.gerar_gabarito_personalizado(
            secoes=secoes,
            arquivo_saida=arquivo_pdf
        )
        assert os.path.exists(arquivo_pdf)

        # Criar gabarito oficial correspondente
        gabarito_oficial = {}
        for i in range(1, 16):
            gabarito_oficial[str(i)] = ["A", "B", "C", "D", "E"][i % 5]
        for i in range(16, 26):
            gabarito_oficial[str(i)] = "V" if i % 2 == 0 else "F"

        # Corrigir prova com esse gabarito
        corretor = Corretor()
        corretor.definir_gabarito_oficial(gabarito_oficial)

        prova = {
            "identificacao": {"nome": "Aluno Teste", "matricula": "001"},
            "respostas": gabarito_oficial.copy()
        }

        resultado = corretor.corrigir_prova(prova)
        assert resultado['nota'] == 10.0

    def test_fluxo_diferentes_formatos_arquivo(self, temp_dir, sample_gabarito_dict):
        """
        Testa carregamento de gabarito em diferentes formatos
        """
        corretor = Corretor()

        # Teste com JSON
        arquivo_json = os.path.join(temp_dir, "gabarito.json")
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(sample_gabarito_dict, f)

        corretor.carregar_gabarito_oficial(arquivo_json)
        assert corretor.gabarito_oficial == sample_gabarito_dict

        # Teste com CSV
        arquivo_csv = os.path.join(temp_dir, "gabarito.csv")
        with open(arquivo_csv, 'w', encoding='utf-8') as f:
            f.write("Questao,Resposta\n")
            for q, r in sample_gabarito_dict.items():
                f.write(f"{q},{r}\n")

        corretor2 = Corretor()
        corretor2.carregar_gabarito_oficial(arquivo_csv)
        assert corretor2.gabarito_oficial == sample_gabarito_dict

        # Teste com TXT
        arquivo_txt = os.path.join(temp_dir, "gabarito.txt")
        with open(arquivo_txt, 'w', encoding='utf-8') as f:
            f.write("# Gabarito Oficial\n")
            for q, r in sample_gabarito_dict.items():
                f.write(f"{q}: {r}\n")

        corretor3 = Corretor()
        corretor3.carregar_gabarito_oficial(arquivo_txt)
        assert corretor3.gabarito_oficial == sample_gabarito_dict

    def test_fluxo_analise_estatisticas(self, temp_dir, sample_gabarito_dict):
        """
        Testa cálculo de estatísticas da turma
        """
        # Criar múltiplas provas com diferentes desempenhos
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        provas = []
        # Aluno com 100%
        provas.append({
            "identificacao": {"nome": "Excelente", "matricula": "001"},
            "respostas": sample_gabarito_dict.copy()
        })

        # Aluno com ~90%
        respostas_90 = sample_gabarito_dict.copy()
        respostas_90["10"] = "X"
        provas.append({
            "identificacao": {"nome": "Bom", "matricula": "002"},
            "respostas": respostas_90
        })

        # Aluno com ~70%
        respostas_70 = sample_gabarito_dict.copy()
        respostas_70["8"] = "X"
        respostas_70["9"] = "X"
        respostas_70["10"] = "X"
        provas.append({
            "identificacao": {"nome": "Regular", "matricula": "003"},
            "respostas": respostas_70
        })

        # Aluno com ~50%
        respostas_50 = {
            "1": "A", "2": "B", "3": "C", "4": "D", "5": "E",
            "6": "X", "7": "X", "8": "X", "9": "X", "10": "X"
        }
        provas.append({
            "identificacao": {"nome": "Fraco", "matricula": "004"},
            "respostas": respostas_50
        })

        # Corrigir todas as provas
        resultados = [corretor.corrigir_prova(p) for p in provas]

        # Calcular estatísticas
        notas = [r['nota'] for r in resultados]
        media = sum(notas) / len(notas)
        nota_max = max(notas)
        nota_min = min(notas)

        assert len(resultados) == 4
        assert nota_max == 10.0
        assert nota_min == 5.0
        assert 7.0 <= media <= 8.5  # Média aproximada

        # Gerar relatório de turma
        arquivo_relatorio = os.path.join(temp_dir, "relatorio_estatisticas.txt")
        corretor.gerar_relatorio_turma(resultados, arquivo_relatorio)
        assert os.path.exists(arquivo_relatorio)

    def test_fluxo_com_respostas_em_branco(self, temp_dir, sample_gabarito_dict):
        """
        Testa correção com respostas em branco
        """
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        # Prova com algumas respostas em branco
        respostas_com_branco = sample_gabarito_dict.copy()
        respostas_com_branco["3"] = ""
        respostas_com_branco["7"] = ""
        respostas_com_branco["10"] = ""

        prova = {
            "identificacao": {"nome": "Aluno Incompleto", "matricula": "999"},
            "respostas": respostas_com_branco
        }

        resultado = corretor.corrigir_prova(prova)

        assert resultado['acertos'] == 7
        assert resultado['em_branco'] == 3
        assert resultado['erros'] == 0
        assert resultado['nota'] == 7.0

    def test_fluxo_exportacao_multiplos_formatos(self, temp_dir, sample_gabarito_dict):
        """
        Testa exportação de resultados em múltiplos formatos
        """
        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        # Criar alguns resultados
        prova = {
            "identificacao": {"nome": "Teste", "matricula": "123"},
            "respostas": sample_gabarito_dict.copy()
        }
        resultado = corretor.corrigir_prova(prova)

        # Exportar em CSV
        arquivo_csv = os.path.join(temp_dir, "export.csv")
        corretor.exportar_resultados([resultado], arquivo_csv, formato='csv')
        assert os.path.exists(arquivo_csv)

        # Exportar em JSON
        arquivo_json = os.path.join(temp_dir, "export.json")
        corretor.exportar_resultados([resultado], arquivo_json, formato='json')
        assert os.path.exists(arquivo_json)

        # Verificar conteúdo do JSON
        with open(arquivo_json, 'r') as f:
            dados = json.load(f)
            assert isinstance(dados, list)
            assert len(dados) == 1
            assert dados[0]['nota'] == 10.0

    def test_fluxo_grande_volume(self, temp_dir, sample_gabarito_dict):
        """
        Testa processamento de grande volume de provas (50 alunos)
        """
        import random

        corretor = Corretor()
        corretor.definir_gabarito_oficial(sample_gabarito_dict)

        # Criar 50 provas com desempenhos variados
        arquivo_respostas = os.path.join(temp_dir, "turma_grande.csv")
        with open(arquivo_respostas, 'w', encoding='utf-8') as f:
            # Header
            f.write("nome,matricula,turma," + ",".join([f"q{i}" for i in range(1, 11)]) + "\n")

            # 50 alunos
            alternativas = ["A", "B", "C", "D", "E"]
            for i in range(1, 51):
                nome = f"Aluno{i:03d}"
                matricula = f"{1000+i}"
                turma = "3A"

                # Gerar respostas com taxa de acerto entre 50-100%
                respostas = []
                for questao in range(1, 11):
                    if random.random() > 0.25:  # 75% de chance de acertar
                        respostas.append(sample_gabarito_dict[str(questao)])
                    else:
                        respostas.append(random.choice(alternativas))

                linha = f"{nome},{matricula},{turma}," + ",".join(respostas) + "\n"
                f.write(linha)

        # Corrigir lote
        resultados = corretor.corrigir_lote(arquivo_respostas)

        assert len(resultados) == 50
        assert all(0 <= r['nota'] <= 10 for r in resultados)

        # Gerar relatório de turma
        arquivo_relatorio = os.path.join(temp_dir, "relatorio_turma_grande.txt")
        corretor.gerar_relatorio_turma(resultados, arquivo_relatorio)
        assert os.path.exists(arquivo_relatorio)

        # Exportar resultados
        arquivo_export = os.path.join(temp_dir, "resultados_turma_grande.json")
        corretor.exportar_resultados(resultados, arquivo_export, formato='json')
        assert os.path.exists(arquivo_export)
