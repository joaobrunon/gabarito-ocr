#!/usr/bin/env python3
"""
Script para gerar gabaritos personalizados com nome dos alunos
A partir de arquivo CSV da secretaria
Usa ReportLab com marcadores OCR para velocidade e compatibilidade
"""

import csv
import os
from collections import defaultdict
import re
from gerador_gabarito import GeradorGabarito
from reportlab.lib.units import cm


def ler_csv_alunos(arquivo_csv):
    """
    Lê o arquivo CSV e retorna lista de alunos (removendo duplicatas)
    Mantém apenas o primeiro registro de cada RA (primeira turma)

    Returns:
        list: Lista de dicionários com dados dos alunos únicos
    """
    alunos = []
    alunos_vistos = set()  # Para rastrear alunos únicos (por RA)

    with open(arquivo_csv, 'r', encoding='utf-8-sig') as f:
        # Pular primeira linha (cabeçalho de data)
        next(f)
        next(f)  # Linha em branco

        # Ler CSV com delimitador ";"
        reader = csv.DictReader(f, delimiter=';')

        for row in reader:
            if row.get('Aluno'):  # Só adicionar se tiver nome
                ra = row['RA'].strip()
                # Evitar duplicatas - manter apenas primeira ocorrência de cada RA
                if ra not in alunos_vistos:
                    alunos_vistos.add(ra)
                    alunos.append({
                        'nome': row['Aluno'].strip(),
                        'ra': ra,
                        'turma': row['Turma'].strip(),
                        'ano_letivo': row['Ano Letivo'].strip(),
                        'escola': row['Escola'].strip()
                    })

    return alunos


def listar_turmas(alunos):
    """
    Lista todas as turmas disponíveis no CSV

    Args:
        alunos: Lista de alunos

    Returns:
        dict: {turma: [alunos]}
    """
    turmas = defaultdict(list)

    for aluno in alunos:
        turmas[aluno['turma']].append(aluno)

    return dict(turmas)


def selecionar_turmas(turmas_disponiveis):
    """
    Permite selecionar quais turmas processar

    Args:
        turmas_disponiveis: Dict com turmas disponíveis

    Returns:
        list: Lista de turmas selecionadas
    """
    print("\n" + "=" * 70)
    print("TURMAS DISPONÍVEIS:")
    print("=" * 70)

    turmas_list = sorted(turmas_disponiveis.keys())

    for idx, turma in enumerate(turmas_list, 1):
        num_alunos = len(turmas_disponiveis[turma])
        print(f"  [{idx:2d}] {turma:<50} ({num_alunos} alunos)")

    print("\n" + "=" * 70)
    print("OPÇÕES DE SELEÇÃO:")
    print("  - Digite números separados por vírgula (ex: 1,3,5)")
    print("  - Digite 'todas' para selecionar todas as turmas")
    print("  - Digite 'sair' para cancelar")
    print("=" * 70)

    while True:
        escolha = input("\nSelecione as turmas: ").strip().lower()

        if escolha == 'sair':
            return []

        if escolha == 'todas':
            return turmas_list

        try:
            # Parse dos números
            indices = [int(x.strip()) for x in escolha.split(',')]
            turmas_selecionadas = []

            for idx in indices:
                if 1 <= idx <= len(turmas_list):
                    turmas_selecionadas.append(turmas_list[idx - 1])
                else:
                    print(f"  ⚠️  Número {idx} inválido (deve estar entre 1 e {len(turmas_list)})")
                    turmas_selecionadas = []
                    break

            if turmas_selecionadas:
                return turmas_selecionadas

        except ValueError:
            print("  ❌ Formato inválido! Use números separados por vírgula.")


def gerar_gabaritos_turma(alunos_turma, turma, pasta_saida, config):
    """
    Gera um único PDF com gabaritos para todos os alunos de uma turma em ordem alfabética

    Args:
        alunos_turma: Lista de alunos da turma
        turma: Nome da turma
        pasta_saida: Pasta onde salvar o PDF
        config: Configurações da prova
    """
    # Criar subpasta para a turma (preservando acentos, normalizando espaços)
    nome_pasta_limpo = re.sub(r'[/\\:*?"<>|]', '', turma).strip()
    nome_pasta_limpo = re.sub(r'\s+', '_', nome_pasta_limpo)  # Normalizar múltiplos espaços em um underscore
    pasta_turma = os.path.join(pasta_saida, nome_pasta_limpo)
    os.makedirs(pasta_turma, exist_ok=True)

    print(f"\n  📁 Pasta: {pasta_turma}")
    print(f"  👥 Alunos: {len(alunos_turma)}")
    print(f"  📄 Gerando PDF consolidado...")

    # Ordenar alunos alfabeticamente por nome
    alunos_ordenados = sorted(alunos_turma, key=lambda x: x['nome'].upper())

    # Nome do arquivo consolidado
    nome_arquivo = f"{nome_pasta_limpo}.pdf"
    caminho_pdf = os.path.join(pasta_turma, nome_arquivo)

    # Gerar gabarito consolidado com ReportLab
    gerador = GeradorGabarito(caminho_pdf)

    # Informações adicionais
    info_adicional = []
    if config['disciplina']:
        info_adicional.append(f"Disciplina: {config['disciplina']}")
    if config['professor']:
        info_adicional.append(f"Professor(a): {config['professor']}")
    if config['codigo_prova']:
        info_adicional.append(f"Código: {config['codigo_prova']}")

    # Gerar gabarito para cada aluno (múltiplas páginas)
    for idx, aluno in enumerate(alunos_ordenados, 1):
        # Cabeçalho (com marcadores OCR automaticamente)
        gerador._desenhar_cabecalho(config['titulo'], info_adicional if info_adicional else None, config['codigo_prova'], aluno['ra'])

        # Campos de identificação
        y = gerador._desenhar_campo_identificacao(gerador.altura - 5*cm)

        # Pré-preencher nome, RA e turma (dentro dos retângulos)
        gerador.c.setFont("Helvetica", 9)
        gerador.c.drawString(4.2*cm, gerador.altura - 5.15*cm, aluno['nome'].upper())
        gerador.c.drawString(4.2*cm, gerador.altura - 6.35*cm, aluno['ra'])
        gerador.c.setFont("Helvetica", 7)  # Fonte menor para turma
        gerador.c.drawString(11.7*cm, gerador.altura - 6.35*cm, turma)

        # Orientações
        y_orientacoes = y - 0.5*cm
        y_questoes = gerador._desenhar_orientacoes(y_orientacoes)

        # Questões (descem mais para baixo)
        gerador._desenhar_questoes_multipla_escolha(config['num_questoes'], config['alternativas'], y_questoes)

        # Rodapé com QR Code e nome do aluno
        gerador._desenhar_rodape(nome_aluno=aluno['nome'], codigo_prova=config['codigo_prova'], ra_aluno=aluno['ra'])

        # Adicionar nova página se não for o último aluno
        if idx < len(alunos_ordenados):
            gerador.c.showPage()

        # Mostrar progresso
        if idx % 10 == 0 or idx == len(alunos_turma):
            print(f"    ✓ {idx}/{len(alunos_turma)} páginas criadas")

    # Salvar arquivo consolidado
    gerador.c.save()
    print(f"  ✅ Turma {turma} concluída! PDF: {nome_arquivo} ({len(alunos_ordenados)} páginas)")


def main():
    """Função principal"""
    print("=" * 70)
    print("GERADOR DE GABARITOS PERSONALIZADOS")
    print("=" * 70)

    # 1. Localizar arquivo CSV
    arquivo_csv = 'Dados(12).csv'

    if not os.path.exists(arquivo_csv):
        print(f"\n❌ Arquivo {arquivo_csv} não encontrado!")
        print("   Coloque o arquivo CSV na pasta do projeto.")
        return

    print(f"\n✓ Arquivo encontrado: {arquivo_csv}")

    # 2. Ler alunos do CSV
    print("\n📖 Lendo dados dos alunos...")
    alunos = ler_csv_alunos(arquivo_csv)
    print(f"   ✓ {len(alunos)} alunos encontrados")

    # 3. Organizar por turmas
    turmas = listar_turmas(alunos)
    print(f"   ✓ {len(turmas)} turmas encontradas")

    # 4. Selecionar turmas
    turmas_selecionadas = selecionar_turmas(turmas)

    if not turmas_selecionadas:
        print("\n❌ Operação cancelada.")
        return

    # 5. Configurar prova
    print("\n" + "=" * 70)
    print("CONFIGURAÇÃO DA PROVA:")
    print("=" * 70)

    titulo = input("Título da prova [GABARITO DE PROVA]: ").strip() or "GABARITO DE PROVA"
    disciplina = input("Disciplina: ").strip()
    professor = input("Professor(a): ").strip()
    codigo_prova = input("Código da prova: ").strip()
    num_questoes = int(input("Número de questões [40]: ").strip() or "40")

    config = {
        'titulo': titulo,
        'disciplina': disciplina or None,
        'professor': professor or None,
        'codigo_prova': codigo_prova or None,
        'num_questoes': num_questoes,
        'alternativas': ['A', 'B', 'C', 'D', 'E']
    }

    # 6. Pasta de saída
    pasta_saida = input("\nPasta de saída [gabaritos_personalizados]: ").strip() or "gabaritos_personalizados"
    os.makedirs(pasta_saida, exist_ok=True)

    # 7. Gerar gabaritos
    print("\n" + "=" * 70)
    print("GERANDO GABARITOS PERSONALIZADOS...")
    print("=" * 70)

    total_alunos = 0
    for turma in turmas_selecionadas:
        alunos_turma = turmas[turma]
        total_alunos += len(alunos_turma)

        print(f"\n📚 Processando: {turma}")
        gerar_gabaritos_turma(alunos_turma, turma, pasta_saida, config)

    # 8. Resumo final
    print("\n" + "=" * 70)
    print("✅ CONCLUÍDO!")
    print("=" * 70)
    print(f"  📊 Turmas processadas: {len(turmas_selecionadas)}")
    print(f"  👥 Total de alunos: {total_alunos}")
    print(f"  📁 PDFs salvos em: {pasta_saida}/")
    print("=" * 70)


if __name__ == '__main__':
    main()
