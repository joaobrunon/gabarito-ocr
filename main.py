#!/usr/bin/env python3
"""
Sistema de Geração e Correção de Gabaritos
Interface de linha de comando
"""

import sys
import os
from datetime import datetime
from gerador_gabarito import GeradorGabarito
from corretor import Corretor
import fitz  # PyMuPDF
from leitor_gabarito import LeitorFinalV2


def imprimir_menu():
    """Exibe o menu principal"""
    print("\n" + "=" * 60)
    print("SISTEMA DE GABARITOS")
    print("=" * 60)
    print("\n[1] Gerar Gabarito em PDF")
    print("[2] Definir/Carregar Gabarito Oficial")
    print("[3] Corrigir Prova Individual")
    print("[4] Corrigir Lote de Provas")
    print("[5] Gerar Relatórios")
    print("[6] Exportar Resultados")
    print("[0] Sair")
    print("\n" + "=" * 60)


def menu_gerar_gabarito():
    """Menu para geração de gabaritos"""
    print("\n--- GERAR GABARITO ---")
    print("[1] Gabarito Padrão (múltipla escolha)")
    print("[2] Gabarito Verdadeiro/Falso")
    print("[3] Gabarito Misto")
    print("[4] Gabaritos Personalizados a partir de CSV")
    print("[0] Voltar")

    opcao = input("\nEscolha uma opção: ").strip()

    if opcao == '1':
        gerar_gabarito_padrao()
    elif opcao == '2':
        gerar_gabarito_vf()
    elif opcao == '3':
        gerar_gabarito_misto()
    elif opcao == '4':
        gerar_gabaritos_csv()


def gerar_gabarito_padrao():
    """Gera um gabarito padrão de múltipla escolha"""
    print("\n--- GABARITO PADRÃO ---")

    arquivo = input("Nome do arquivo PDF (ex: prova.pdf): ").strip()
    if not arquivo.endswith('.pdf'):
        arquivo += '.pdf'

    titulo = input("Título da prova: ").strip() or "GABARITO DE PROVA"
    disciplina = input("Disciplina (opcional): ").strip() or None
    professor = input("Professor (opcional): ").strip() or None
    codigo = input("Código da prova (opcional): ").strip() or None

    num_questoes = int(input("Número de questões [30]: ").strip() or "30")

    print("\nAlternativas padrão: A, B, C, D, E")
    mudar_alt = input("Deseja mudar? (s/n): ").strip().lower()

    alternativas = ['A', 'B', 'C', 'D', 'E']
    if mudar_alt == 's':
        alt_input = input("Digite as alternativas separadas por vírgula (ex: A,B,C,D): ").strip()
        alternativas = [a.strip().upper() for a in alt_input.split(',')]

    try:
        gerador = GeradorGabarito(arquivo)
        gerador.gerar_gabarito_padrao(
            num_questoes=num_questoes,
            alternativas=alternativas,
            titulo=titulo,
            disciplina=disciplina,
            professor=professor,
            codigo_prova=codigo
        )
        print(f"\n✓ Gabarito gerado com sucesso: {arquivo}")
    except Exception as e:
        print(f"\n✗ Erro ao gerar gabarito: {e}")


def gerar_gabarito_vf():
    """Gera um gabarito de verdadeiro/falso"""
    print("\n--- GABARITO VERDADEIRO/FALSO ---")

    arquivo = input("Nome do arquivo PDF: ").strip()
    if not arquivo.endswith('.pdf'):
        arquivo += '.pdf'

    titulo = input("Título da prova: ").strip() or "GABARITO DE PROVA"
    num_questoes = int(input("Número de questões [20]: ").strip() or "20")

    try:
        gerador = GeradorGabarito(arquivo)

        configuracao = {
            'titulo': titulo,
            'secoes': [
                {
                    'tipo': 'verdadeiro_falso',
                    'num_questoes': num_questoes,
                    'colunas': 2
                }
            ]
        }

        gerador.gerar_gabarito_personalizado(configuracao)
        print(f"\n✓ Gabarito gerado com sucesso: {arquivo}")
    except Exception as e:
        print(f"\n✗ Erro ao gerar gabarito: {e}")


def gerar_gabarito_misto():
    """Gera um gabarito com múltiplas seções"""
    print("\n--- GABARITO MISTO ---")

    arquivo = input("Nome do arquivo PDF: ").strip()
    if not arquivo.endswith('.pdf'):
        arquivo += '.pdf'

    titulo = input("Título da prova: ").strip() or "GABARITO DE PROVA"

    secoes = []

    print("\nQuantas seções diferentes? ")
    num_secoes = int(input("Número de seções [2]: ").strip() or "2")

    for i in range(num_secoes):
        print(f"\n--- Seção {i+1} ---")
        print("[1] Múltipla escolha")
        print("[2] Verdadeiro/Falso")
        tipo_secao = input("Tipo: ").strip()

        num_q = int(input("Número de questões: ").strip())

        if tipo_secao == '1':
            secoes.append({
                'tipo': 'multipla_escolha',
                'num_questoes': num_q,
                'alternativas': ['A', 'B', 'C', 'D', 'E'],
                'colunas': 2
            })
        elif tipo_secao == '2':
            secoes.append({
                'tipo': 'verdadeiro_falso',
                'num_questoes': num_q,
                'colunas': 2
            })

    try:
        gerador = GeradorGabarito(arquivo)
        configuracao = {'titulo': titulo, 'secoes': secoes}
        gerador.gerar_gabarito_personalizado(configuracao)
        print(f"\n✓ Gabarito gerado com sucesso: {arquivo}")
    except Exception as e:
        print(f"\n✗ Erro ao gerar gabarito: {e}")


def menu_gabarito_oficial(corretor):
    """Menu para definir gabarito oficial"""
    print("\n--- GABARITO OFICIAL ---")
    print("[1] Digitar gabarito manualmente")
    print("[2] Carregar de arquivo")
    print("[3] Salvar gabarito oficial")
    print("[0] Voltar")

    opcao = input("\nEscolha uma opção: ").strip()

    if opcao == '1':
        definir_gabarito_manual(corretor)
    elif opcao == '2':
        carregar_gabarito_arquivo(corretor)
    elif opcao == '3':
        salvar_gabarito_oficial(corretor)


def definir_gabarito_manual(corretor):
    """Define o gabarito oficial manualmente"""
    print("\n--- DEFINIR GABARITO MANUALMENTE ---")
    print("Digite as respostas no formato: 1:A 2:B 3:C ...")
    print("Ou linha por linha (pressione Enter vazio para finalizar)")

    gabarito = {}

    # Opção 1: uma linha
    print("\n[1] Tudo em uma linha")
    print("[2] Linha por linha")
    opcao = input("Escolha: ").strip()

    if opcao == '1':
        entrada = input("\nDigite o gabarito: ").strip()
        partes = entrada.split()
        for parte in partes:
            if ':' in parte:
                q, r = parte.split(':', 1)
                gabarito[int(q)] = r.upper()
    else:
        print("\nDigite linha por linha (formato: questao:resposta)")
        print("Pressione Enter vazio para finalizar")
        questao_num = 1
        while True:
            entrada = input(f"Questão {questao_num}: ").strip()
            if not entrada:
                break

            if ':' in entrada:
                q, r = entrada.split(':', 1)
                gabarito[int(q)] = r.strip().upper()
            else:
                gabarito[questao_num] = entrada.upper()

            questao_num += 1

    if gabarito:
        corretor.definir_gabarito_oficial(gabarito)
        print(f"\n✓ Gabarito definido com {len(gabarito)} questões")
    else:
        print("\n✗ Nenhuma questão definida")


def carregar_gabarito_arquivo(corretor):
    """Carrega gabarito oficial de arquivo"""
    print("\n--- CARREGAR GABARITO ---")
    arquivo = input("Caminho do arquivo (JSON, CSV ou TXT): ").strip()

    if os.path.exists(arquivo):
        if corretor.carregar_gabarito_oficial(arquivo):
            print(f"\n✓ Gabarito carregado com sucesso")
    else:
        print(f"\n✗ Arquivo não encontrado: {arquivo}")


def salvar_gabarito_oficial(corretor):
    """Salva o gabarito oficial em arquivo"""
    if not corretor.gabarito_oficial:
        print("\n✗ Nenhum gabarito oficial definido")
        return

    print("\n--- SALVAR GABARITO OFICIAL ---")
    arquivo = input("Nome do arquivo (ex: gabarito.json): ").strip()

    if corretor.salvar_gabarito_oficial(arquivo):
        print(f"\n✓ Gabarito salvo com sucesso")


def corrigir_prova_individual(corretor):
    """Corrige uma prova individual"""
    if not corretor.gabarito_oficial:
        print("\n✗ Defina o gabarito oficial primeiro!")
        return

    print("\n--- CORRIGIR PROVA INDIVIDUAL ---")
    print("[1] Digitar respostas manualmente")
    print("[2] Carregar de arquivo PDF escaneado")
    opcao_entrada = input("\nEscolha: ").strip()

    # Identificação
    nome = input("Nome do aluno: ").strip()
    matricula = input("Matrícula: ").strip()
    turma = input("Turma: ").strip()

    identificacao = {'nome': nome, 'matricula': matricula, 'turma': turma}

    respostas = {}

    if opcao_entrada == '2':
        # Carregar de PDF
        print("\n--- CARREGAR DE PDF ---")
        caminho_pdf = input("Caminho do PDF: ").strip()

        if not os.path.exists(caminho_pdf):
            print(f"\n✗ Arquivo não encontrado: {caminho_pdf}")
            return

        try:
            print("Processando PDF...")
            pdf = fitz.open(caminho_pdf)
            pagina = pdf[0]
            pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))
            temp_path = '/tmp/prova_scan.png'
            pix.save(temp_path)

            # Ler respostas com OCR
            leitor = LeitorFinalV2()
            respostas = leitor.ler_gabarito(temp_path)

            # Converter para formato esperado
            respostas = {int(q): r for q, r in respostas.items()}

            print(f"✓ {len(respostas)}/40 questões detectadas do PDF")

            pdf.close()

        except Exception as e:
            print(f"\n✗ Erro ao processar PDF: {e}")
            return

    else:
        # Entrada manual
        print("\nDigite as respostas do aluno:")
        print("Formato: 1:A 2:B 3:C ... (ou linha por linha)")

        print("\n[1] Tudo em uma linha")
        print("[2] Linha por linha")
        opcao = input("Escolha: ").strip()

        if opcao == '1':
            entrada = input("\nRespostas: ").strip()
            partes = entrada.split()
            for parte in partes:
                if ':' in parte:
                    q, r = parte.split(':', 1)
                    respostas[int(q)] = r.upper()
        else:
            print("\nDigite as respostas (Enter vazio para questão em branco)")
            for q in sorted(corretor.gabarito_oficial.keys()):
                resp = input(f"Questão {q}: ").strip().upper()
                if resp:
                    respostas[int(q)] = resp

    try:
        resultado = corretor.corrigir_prova(identificacao, respostas)
        print("\n" + corretor.gerar_relatorio_individual(resultado))

        salvar = input("\nSalvar relatório? (s/n): ").strip().lower()
        if salvar == 's':
            arquivo = input("Nome do arquivo: ").strip()
            corretor.gerar_relatorio_individual(resultado, arquivo)

    except Exception as e:
        print(f"\n✗ Erro ao corrigir: {e}")


def corrigir_lote(corretor):
    """Corrige lote de provas"""
    if not corretor.gabarito_oficial:
        print("\n✗ Defina o gabarito oficial primeiro!")
        return

    print("\n--- CORRIGIR LOTE ---")
    arquivo = input("Arquivo com respostas (JSON ou CSV): ").strip()

    if not os.path.exists(arquivo):
        print(f"\n✗ Arquivo não encontrado: {arquivo}")
        return

    try:
        resultados = corretor.corrigir_lote(arquivo)
        print(f"\n✓ {len(resultados)} provas corrigidas com sucesso")
    except Exception as e:
        print(f"\n✗ Erro ao corrigir lote: {e}")


def menu_relatorios(corretor):
    """Menu de relatórios"""
    print("\n--- RELATÓRIOS ---")
    print("[1] Relatório Individual")
    print("[2] Relatório da Turma")
    print("[0] Voltar")

    opcao = input("\nEscolha uma opção: ").strip()

    if opcao == '1':
        if not corretor.resultados:
            print("\n✗ Nenhuma correção realizada ainda")
            return

        print("\nProvas corrigidas:")
        for i, r in enumerate(corretor.resultados, 1):
            nome = r['identificacao'].get('nome', 'N/A')
            print(f"[{i}] {nome} - Nota: {r['nota']:.2f}")

        escolha = int(input("\nEscolha uma prova: ").strip()) - 1
        if 0 <= escolha < len(corretor.resultados):
            print("\n" + corretor.gerar_relatorio_individual(corretor.resultados[escolha]))

            salvar = input("\nSalvar relatório? (s/n): ").strip().lower()
            if salvar == 's':
                arquivo = input("Nome do arquivo: ").strip()
                corretor.gerar_relatorio_individual(corretor.resultados[escolha], arquivo)

    elif opcao == '2':
        if not corretor.resultados:
            print("\n✗ Nenhuma correção realizada ainda")
            return

        print("\n" + corretor.gerar_relatorio_turma())

        salvar = input("\nSalvar relatório? (s/n): ").strip().lower()
        if salvar == 's':
            arquivo = input("Nome do arquivo: ").strip()
            corretor.gerar_relatorio_turma(arquivo)


def exportar_resultados(corretor):
    """Exporta resultados"""
    if not corretor.resultados:
        print("\n✗ Nenhuma correção realizada ainda")
        return

    print("\n--- EXPORTAR RESULTADOS ---")
    arquivo = input("Nome do arquivo (JSON ou CSV): ").strip()

    if corretor.exportar_resultados(arquivo):
        print(f"\n✓ Resultados exportados com sucesso")


def gerar_gabaritos_csv():
    """Gera gabaritos personalizados a partir de CSV com dados dos alunos"""
    from gerar_gabaritos_personalizados import ler_csv_alunos, listar_turmas, selecionar_turmas, gerar_gabaritos_turma

    print("\n--- GABARITOS PERSONALIZADOS A PARTIR DE CSV ---")

    # Verificar se o CSV existe
    if not os.path.exists('Dados(12).csv'):
        print("\n✗ Arquivo 'Dados(12).csv' não encontrado!")
        return

    try:
        # Ler alunos do CSV
        print("\n📖 Lendo dados dos alunos...")
        alunos = ler_csv_alunos('Dados(12).csv')
        print(f"   ✓ {len(alunos)} alunos encontrados")

        # Organizar por turmas
        turmas = listar_turmas(alunos)
        print(f"   ✓ {len(turmas)} turmas encontradas")

        # Selecionar turmas (mostra lista primeiro)
        turmas_selecionadas = selecionar_turmas(turmas)

        if not turmas_selecionadas:
            print("\n❌ Operação cancelada.")
            return

        # Configurar prova
        print("\n" + "=" * 70)
        print("CONFIGURAÇÃO DA PROVA:")
        print("=" * 70)

        titulo = input("Título da prova [GABARITO DE PROVA]: ").strip() or "GABARITO DE PROVA"
        disciplina = input("Disciplina: ").strip()
        professor = input("Professor(a): ").strip()
        codigo_prova = input("Código da prova [AUTO]: ").strip() or f"PROVA_{datetime.now().strftime('%d%m%Y_%H%M')}"
        num_questoes = int(input("Número de questões [40]: ").strip() or "40")

        config = {
            'titulo': titulo,
            'disciplina': disciplina or None,
            'professor': professor or None,
            'codigo_prova': codigo_prova,
            'num_questoes': num_questoes,
            'alternativas': ['A', 'B', 'C', 'D', 'E']
        }

        # Pasta de saída
        pasta_saida = input("\nPasta de saída [gabaritos_personalizados]: ").strip() or "gabaritos_personalizados"
        os.makedirs(pasta_saida, exist_ok=True)

        # Gerar gabaritos
        print("\n" + "=" * 70)
        print("GERANDO GABARITOS PERSONALIZADOS...")
        print("=" * 70)

        total_alunos = 0
        for turma in turmas_selecionadas:
            alunos_turma = turmas[turma]
            total_alunos += len(alunos_turma)

            print(f"\n📚 Processando: {turma}")
            gerar_gabaritos_turma(alunos_turma, turma, pasta_saida, config)

        # Resumo final
        print("\n" + "=" * 70)
        print("✅ CONCLUÍDO!")
        print("=" * 70)
        print(f"  📊 Turmas processadas: {len(turmas_selecionadas)}")
        print(f"  👥 Total de alunos: {total_alunos}")
        print(f"  📁 PDFs salvos em: {pasta_saida}/")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Erro ao gerar gabaritos: {e}")


def main():
    """Função principal"""
    corretor = Corretor()

    while True:
        imprimir_menu()
        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == '1':
            menu_gerar_gabarito()
        elif opcao == '2':
            menu_gabarito_oficial(corretor)
        elif opcao == '3':
            corrigir_prova_individual(corretor)
        elif opcao == '4':
            corrigir_lote(corretor)
        elif opcao == '5':
            menu_relatorios(corretor)
        elif opcao == '6':
            exportar_resultados(corretor)
        elif opcao == '0':
            print("\nSaindo...")
            sys.exit(0)
        else:
            print("\n✗ Opção inválida!")


if __name__ == '__main__':
    main()
