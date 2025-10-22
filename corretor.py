"""
Sistema de Correção de Gabaritos
Corrige gabaritos preenchidos comparando com gabarito oficial
"""

import json
from datetime import datetime
from typing import List, Dict, Tuple
import csv


class Corretor:
    """Classe para correção de gabaritos"""

    def __init__(self, gabarito_oficial: Dict[int, str] = None):
        """
        Inicializa o corretor

        Args:
            gabarito_oficial: Dicionário com as respostas corretas {questao: resposta}
        """
        self.gabarito_oficial = gabarito_oficial or {}
        self.resultados = []

    def definir_gabarito_oficial(self, gabarito: Dict[int, str]):
        """
        Define o gabarito oficial

        Args:
            gabarito: Dicionário {numero_questao: resposta_correta}
        """
        self.gabarito_oficial = gabarito
        print(f"Gabarito oficial definido com {len(gabarito)} questões")

    def carregar_gabarito_oficial(self, arquivo: str):
        """
        Carrega gabarito oficial de um arquivo

        Formatos suportados:
        - JSON: {"1": "A", "2": "B", ...}
        - TXT: cada linha com formato "questao:resposta" ou "questao resposta"
        - CSV: questao,resposta

        Args:
            arquivo: Caminho do arquivo
        """
        try:
            if arquivo.endswith('.json'):
                with open(arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    self.gabarito_oficial = {int(k): v.upper() for k, v in dados.items()}

            elif arquivo.endswith('.csv'):
                with open(arquivo, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Pular cabeçalho se existir
                    self.gabarito_oficial = {
                        int(row[0]): row[1].upper()
                        for row in reader if len(row) >= 2
                    }

            else:  # TXT
                with open(arquivo, 'r', encoding='utf-8') as f:
                    for linha in f:
                        linha = linha.strip()
                        if not linha or linha.startswith('#'):
                            continue

                        # Tentar diferentes separadores
                        if ':' in linha:
                            q, r = linha.split(':', 1)
                        elif ' ' in linha:
                            q, r = linha.split(None, 1)
                        elif ',' in linha:
                            q, r = linha.split(',', 1)
                        else:
                            continue

                        self.gabarito_oficial[int(q.strip())] = r.strip().upper()

            print(f"Gabarito oficial carregado: {len(self.gabarito_oficial)} questões")
            return True

        except Exception as e:
            print(f"Erro ao carregar gabarito oficial: {e}")
            return False

    def salvar_gabarito_oficial(self, arquivo: str):
        """
        Salva o gabarito oficial em arquivo

        Args:
            arquivo: Caminho do arquivo (JSON, CSV ou TXT)
        """
        try:
            if arquivo.endswith('.json'):
                with open(arquivo, 'w', encoding='utf-8') as f:
                    json.dump(self.gabarito_oficial, f, indent=2, ensure_ascii=False)

            elif arquivo.endswith('.csv'):
                with open(arquivo, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Questao', 'Resposta'])
                    for q in sorted(self.gabarito_oficial.keys()):
                        writer.writerow([q, self.gabarito_oficial[q]])

            else:  # TXT
                with open(arquivo, 'w', encoding='utf-8') as f:
                    f.write("# Gabarito Oficial\n")
                    f.write("# Formato: questao: resposta\n\n")
                    for q in sorted(self.gabarito_oficial.keys()):
                        f.write(f"{q}: {self.gabarito_oficial[q]}\n")

            print(f"Gabarito oficial salvo em: {arquivo}")
            return True

        except Exception as e:
            print(f"Erro ao salvar gabarito oficial: {e}")
            return False

    def corrigir_prova(self, identificacao: Dict[str, str],
                      respostas_aluno: Dict[int, str],
                      peso_questoes: Dict[int, float] = None) -> Dict:
        """
        Corrige uma prova individual

        Args:
            identificacao: Dicionário com dados do aluno (nome, matricula, etc)
            respostas_aluno: Dicionário {questao: resposta_marcada}
            peso_questoes: Dicionário com peso de cada questão (opcional)

        Returns:
            Dicionário com resultado da correção
        """
        if not self.gabarito_oficial:
            raise ValueError("Gabarito oficial não foi definido")

        # Normalizar respostas
        respostas_aluno = {k: v.upper() if v else '' for k, v in respostas_aluno.items()}

        acertos = []
        erros = []
        em_branco = []
        pontuacao = 0
        pontuacao_maxima = 0

        # Corrigir cada questão
        for questao, resposta_correta in self.gabarito_oficial.items():
            resposta_aluno = respostas_aluno.get(questao, '').strip()
            peso = peso_questoes.get(questao, 1.0) if peso_questoes else 1.0
            pontuacao_maxima += peso

            if not resposta_aluno:
                em_branco.append(questao)
            elif resposta_aluno == resposta_correta:
                acertos.append(questao)
                pontuacao += peso
            else:
                erros.append({
                    'questao': questao,
                    'resposta_aluno': resposta_aluno,
                    'resposta_correta': resposta_correta
                })

        # Calcular estatísticas
        total_questoes = len(self.gabarito_oficial)
        percentual = (pontuacao / pontuacao_maxima * 100) if pontuacao_maxima > 0 else 0

        resultado = {
            'identificacao': identificacao,
            'data_correcao': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'total_questoes': total_questoes,
            'acertos': len(acertos),
            'erros': len(erros),
            'em_branco': len(em_branco),
            'pontuacao': round(pontuacao, 2),
            'pontuacao_maxima': round(pontuacao_maxima, 2),
            'percentual': round(percentual, 2),
            'nota': round(percentual / 10, 2),  # Nota de 0 a 10
            'questoes_certas': acertos,
            'questoes_erradas': erros,
            'questoes_branco': em_branco,
            'respostas_completas': respostas_aluno
        }

        self.resultados.append(resultado)
        return resultado

    def corrigir_lote(self, arquivo_respostas: str,
                     peso_questoes: Dict[int, float] = None) -> List[Dict]:
        """
        Corrige múltiplas provas de uma vez

        Args:
            arquivo_respostas: Arquivo JSON ou CSV com respostas dos alunos
            peso_questoes: Pesos das questões (opcional)

        Formato JSON:
        [
            {
                "identificacao": {"nome": "...", "matricula": "..."},
                "respostas": {"1": "A", "2": "B", ...}
            }
        ]

        Formato CSV:
        nome,matricula,turma,q1,q2,q3,...
        João,12345,A,A,B,C,...

        Returns:
            Lista com resultados de todas as correções
        """
        resultados = []

        try:
            if arquivo_respostas.endswith('.json'):
                with open(arquivo_respostas, 'r', encoding='utf-8') as f:
                    dados = json.load(f)

                for item in dados:
                    resultado = self.corrigir_prova(
                        item['identificacao'],
                        item['respostas'],
                        peso_questoes
                    )
                    resultados.append(resultado)

            elif arquivo_respostas.endswith('.csv'):
                with open(arquivo_respostas, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)

                    for row in reader:
                        # Extrair identificação
                        identificacao = {
                            'nome': row.get('nome', ''),
                            'matricula': row.get('matricula', ''),
                            'turma': row.get('turma', '')
                        }

                        # Extrair respostas (colunas que começam com 'q')
                        respostas = {}
                        for key, value in row.items():
                            if key.startswith('q') and key[1:].isdigit():
                                num_questao = int(key[1:])
                                respostas[num_questao] = value

                        resultado = self.corrigir_prova(
                            identificacao,
                            respostas,
                            peso_questoes
                        )
                        resultados.append(resultado)

            print(f"Correção concluída: {len(resultados)} provas corrigidas")
            return resultados

        except Exception as e:
            print(f"Erro ao corrigir lote: {e}")
            return []

    def gerar_relatorio_individual(self, resultado: Dict, arquivo_saida: str = None) -> str:
        """
        Gera relatório individual de uma correção

        Args:
            resultado: Dicionário com resultado da correção
            arquivo_saida: Arquivo para salvar (opcional)

        Returns:
            String com o relatório
        """
        relatorio = []
        relatorio.append("=" * 70)
        relatorio.append("RELATÓRIO DE CORREÇÃO DE PROVA")
        relatorio.append("=" * 70)
        relatorio.append("")

        # Identificação
        relatorio.append("IDENTIFICAÇÃO:")
        for k, v in resultado['identificacao'].items():
            relatorio.append(f"  {k.capitalize()}: {v}")
        relatorio.append("")

        # Resumo
        relatorio.append("RESUMO:")
        relatorio.append(f"  Total de questões: {resultado['total_questoes']}")
        relatorio.append(f"  Acertos: {resultado['acertos']}")
        relatorio.append(f"  Erros: {resultado['erros']}")
        relatorio.append(f"  Em branco: {resultado['em_branco']}")
        relatorio.append(f"  Pontuação: {resultado['pontuacao']}/{resultado['pontuacao_maxima']}")
        relatorio.append(f"  Percentual: {resultado['percentual']:.2f}%")
        relatorio.append(f"  Nota: {resultado['nota']:.2f}")
        relatorio.append("")

        # Questões erradas
        if resultado['questoes_erradas']:
            relatorio.append("QUESTÕES ERRADAS:")
            for erro in resultado['questoes_erradas']:
                relatorio.append(
                    f"  Questão {erro['questao']:02d}: "
                    f"Marcou '{erro['resposta_aluno']}' "
                    f"(Correto: '{erro['resposta_correta']}')"
                )
            relatorio.append("")

        # Questões em branco
        if resultado['questoes_branco']:
            relatorio.append("QUESTÕES EM BRANCO:")
            relatorio.append(f"  {', '.join(map(str, resultado['questoes_branco']))}")
            relatorio.append("")

        relatorio.append(f"Data da correção: {resultado['data_correcao']}")
        relatorio.append("=" * 70)

        texto_relatorio = '\n'.join(relatorio)

        if arquivo_saida:
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                f.write(texto_relatorio)
            print(f"Relatório salvo em: {arquivo_saida}")

        return texto_relatorio

    def gerar_relatorio_turma(self, arquivo_saida: str = None) -> str:
        """
        Gera relatório consolidado da turma

        Args:
            arquivo_saida: Arquivo para salvar (opcional)

        Returns:
            String com o relatório
        """
        if not self.resultados:
            return "Nenhum resultado para gerar relatório"

        relatorio = []
        relatorio.append("=" * 70)
        relatorio.append("RELATÓRIO CONSOLIDADO DA TURMA")
        relatorio.append("=" * 70)
        relatorio.append("")

        # Estatísticas gerais
        total_alunos = len(self.resultados)
        media_acertos = sum(r['acertos'] for r in self.resultados) / total_alunos
        media_nota = sum(r['nota'] for r in self.resultados) / total_alunos
        maior_nota = max(r['nota'] for r in self.resultados)
        menor_nota = min(r['nota'] for r in self.resultados)

        relatorio.append("ESTATÍSTICAS GERAIS:")
        relatorio.append(f"  Total de alunos: {total_alunos}")
        relatorio.append(f"  Média de acertos: {media_acertos:.2f}")
        relatorio.append(f"  Média geral: {media_nota:.2f}")
        relatorio.append(f"  Maior nota: {maior_nota:.2f}")
        relatorio.append(f"  Menor nota: {menor_nota:.2f}")
        relatorio.append("")

        # Análise por questão
        relatorio.append("ANÁLISE POR QUESTÃO:")
        relatorio.append(f"{'Questão':<10} {'Acertos':<10} {'%':<10} {'Dificuldade'}")
        relatorio.append("-" * 70)

        num_questoes = self.resultados[0]['total_questoes']
        for q in range(1, num_questoes + 1):
            acertos = sum(1 for r in self.resultados if q in r['questoes_certas'])
            percentual = (acertos / total_alunos) * 100

            if percentual >= 80:
                dificuldade = "Fácil"
            elif percentual >= 50:
                dificuldade = "Média"
            else:
                dificuldade = "Difícil"

            relatorio.append(
                f"{q:<10} {acertos:<10} {percentual:>6.1f}%    {dificuldade}"
            )

        relatorio.append("")

        # Ranking
        relatorio.append("RANKING (Top 10):")
        relatorio.append(f"{'Posição':<10} {'Nome':<30} {'Nota':<10}")
        relatorio.append("-" * 70)

        ranking = sorted(self.resultados, key=lambda x: x['nota'], reverse=True)
        for i, r in enumerate(ranking[:10], 1):
            nome = r['identificacao'].get('nome', 'N/A')
            relatorio.append(f"{i:<10} {nome:<30} {r['nota']:<10.2f}")

        relatorio.append("")
        relatorio.append("=" * 70)

        texto_relatorio = '\n'.join(relatorio)

        if arquivo_saida:
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                f.write(texto_relatorio)
            print(f"Relatório da turma salvo em: {arquivo_saida}")

        return texto_relatorio

    def exportar_resultados(self, arquivo_saida: str):
        """
        Exporta resultados para arquivo

        Args:
            arquivo_saida: Caminho do arquivo (JSON ou CSV)
        """
        try:
            if arquivo_saida.endswith('.json'):
                with open(arquivo_saida, 'w', encoding='utf-8') as f:
                    json.dump(self.resultados, f, indent=2, ensure_ascii=False)

            elif arquivo_saida.endswith('.csv'):
                with open(arquivo_saida, 'w', encoding='utf-8', newline='') as f:
                    if not self.resultados:
                        return

                    writer = csv.writer(f)
                    # Cabeçalho
                    writer.writerow([
                        'Nome', 'Matrícula', 'Turma', 'Total Questões',
                        'Acertos', 'Erros', 'Em Branco',
                        'Pontuação', 'Pontuação Máxima', 'Percentual', 'Nota'
                    ])

                    # Dados
                    for r in self.resultados:
                        writer.writerow([
                            r['identificacao'].get('nome', ''),
                            r['identificacao'].get('matricula', ''),
                            r['identificacao'].get('turma', ''),
                            r['total_questoes'],
                            r['acertos'],
                            r['erros'],
                            r['em_branco'],
                            r['pontuacao'],
                            r['pontuacao_maxima'],
                            r['percentual'],
                            r['nota']
                        ])

            print(f"Resultados exportados para: {arquivo_saida}")
            return True

        except Exception as e:
            print(f"Erro ao exportar resultados: {e}")
            return False


if __name__ == '__main__':
    # Exemplo de uso
    corretor = Corretor()

    # Definir gabarito oficial
    gabarito = {
        1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E',
        6: 'A', 7: 'B', 8: 'C', 9: 'D', 10: 'E'
    }
    corretor.definir_gabarito_oficial(gabarito)

    # Corrigir uma prova
    resultado = corretor.corrigir_prova(
        identificacao={'nome': 'João Silva', 'matricula': '12345', 'turma': 'A'},
        respostas_aluno={1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E',
                        6: 'B', 7: 'B', 8: 'C', 9: 'D', 10: 'E'}
    )

    # Gerar relatório
    print(corretor.gerar_relatorio_individual(resultado))
