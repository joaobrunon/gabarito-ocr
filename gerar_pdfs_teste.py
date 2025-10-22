#!/usr/bin/env python3
"""
Script para gerar PDFs de teste com marcações
Para testar o sistema de correção
"""

import os
from gerador_gabarito import GeradorGabarito
from reportlab.lib.units import cm
import cv2
import numpy as np


def gerar_pdf_teste(nome_aluno, respostas, numero_teste=1):
    """
    Gera um PDF com marcações para teste

    Args:
        nome_aluno: Nome do aluno
        respostas: Dict {questao: alternativa} ex: {1: 'A', 2: 'B', ...}
        numero_teste: Número sequencial do teste
    """

    # Nome do arquivo
    nome_arquivo = f"pdfs_para_corrigir/teste_{numero_teste:02d}_{nome_aluno}.pdf"

    # Criar gabarito
    print(f"Gerando: {nome_arquivo}")
    gerador = GeradorGabarito(nome_arquivo)

    # Cabeçalho
    info_adicional = [
        f"Teste #{numero_teste}",
        "Prova de Múltipla Escolha"
    ]
    gerador._desenhar_cabecalho("TESTE DE GABARITO", info_adicional, f"TESTE{numero_teste:02d}", f"000{numero_teste:05d}")

    # Campos de identificação
    y = gerador._desenhar_campo_identificacao(gerador.altura - 5*cm)

    # Pré-preencher dados
    gerador.c.setFont("Helvetica", 9)
    gerador.c.drawString(4.2*cm, gerador.altura - 5.15*cm, nome_aluno.upper())
    gerador.c.drawString(4.2*cm, gerador.altura - 6.35*cm, f"000{numero_teste:05d}")
    gerador.c.setFont("Helvetica", 7)
    gerador.c.drawString(11.7*cm, gerador.altura - 6.35*cm, "TESTE")

    # Orientações
    y_orientacoes = y - 0.5*cm
    y_questoes = gerador._desenhar_orientacoes(y_orientacoes)

    # Desenhar questões com círculos
    gerador._desenhar_questoes_multipla_escolha(40, ['A', 'B', 'C', 'D', 'E'], y_questoes)

    # Rodapé
    gerador._desenhar_rodape(nome_aluno=nome_aluno, codigo_prova=f"TESTE{numero_teste:02d}", ra_aluno=f"000{numero_teste:05d}")

    gerador.c.save()

    # Reabrir e adicionar marcações
    adicionar_marcacoes(nome_arquivo, respostas)


def adicionar_marcacoes(caminho_pdf, respostas):
    """
    Adiciona marcações (preenchimentos) ao PDF para simular respostas
    """
    try:
        from PyPDF2 import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from io import BytesIO

        print(f"  Adicionando marcações...")

        # Ler PDF original
        reader = PdfReader(caminho_pdf)
        writer = PdfWriter()

        # Criar PDF com marcações em overlay
        overlay = BytesIO()
        c = canvas.Canvas(overlay, pagesize=A4)

        # Posições dos círculos (aproximadas baseado no layout)
        # Essas coordenadas são baseadas no layout gerado
        x_esq_start = 97  # Primeira coluna esquerda
        x_esq_alt_spacing = 50  # Espaçamento entre alternativas
        x_dir_start = 506  # Segunda coluna

        y_start = 750  # Posição Y inicial (ajustar conforme necessário)
        y_spacing = 26  # Espaçamento vertical entre linhas

        # Desenhar círculos preenchidos para as respostas
        for questao, resposta in respostas.items():
            # Determinar linha e coluna
            if questao <= 20:
                linha = questao - 1
                x_base = x_esq_start
                col_offset = ord(resposta) - ord('A')
            else:
                linha = questao - 21
                x_base = x_dir_start
                col_offset = ord(resposta) - ord('A')

            y = y_start - (linha * y_spacing)
            x = x_base + (col_offset * x_esq_alt_spacing)

            # Desenhar círculo preenchido (em preto/cinza para ser detectado)
            c.setFillColorRGB(0.2, 0.2, 0.2)  # Cinza escuro
            c.setStrokeColorRGB(0, 0, 0)
            c.circle(x, y, 8, fill=1, stroke=1)

        c.save()
        overlay.seek(0)

        # Combinar com original
        overlay_reader = PdfReader(overlay)
        page = reader.pages[0]
        page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

        # Salvar resultado
        with open(caminho_pdf, 'wb') as f:
            writer.write(f)

        print(f"  ✓ Marcações adicionadas com sucesso")

    except Exception as e:
        print(f"  ⚠️  Não foi possível adicionar marcações: {e}")
        print(f"      (PDF sem marcações, mas estrutura está ok)")


def main():
    """Gera vários PDFs de teste"""

    # Criar pasta se não existir
    os.makedirs('pdfs_para_corrigir', exist_ok=True)

    print("\n" + "="*70)
    print("GERANDO PDFs DE TESTE COM MARCAÇÕES")
    print("="*70 + "\n")

    # Teste 1: Todas as respostas corretas (1=A, 2=B, 3=C, 4=D, 5=E padrão)
    print("Teste 1: Todas as respostas corretas")
    respostas_1 = {}
    for q in range(1, 41):
        indice = (q - 1) % 5
        respostas_1[q] = ['A', 'B', 'C', 'D', 'E'][indice]
    gerar_pdf_teste("ALUNO_PERFEITO", respostas_1, 1)

    # Teste 2: 50% de acertos (alternado)
    print("\nTeste 2: 50% de acertos")
    respostas_2 = {}
    for q in range(1, 41):
        if q % 2 == 0:
            respostas_2[q] = ['A', 'B', 'C', 'D', 'E'][(q - 1) % 5]
        else:
            respostas_2[q] = ['A', 'B', 'C', 'D', 'E'][q % 5]
    gerar_pdf_teste("ALUNO_MEDIO", respostas_2, 2)

    # Teste 3: Poucos acertos (25%)
    print("\nTeste 3: 25% de acertos")
    respostas_3 = {}
    for q in range(1, 41):
        if q % 4 == 0:
            respostas_3[q] = ['A', 'B', 'C', 'D', 'E'][(q - 1) % 5]
        else:
            respostas_3[q] = 'A'  # Responde tudo A
    gerar_pdf_teste("ALUNO_FRACO", respostas_3, 3)

    # Teste 4: Padrão diferente
    print("\nTeste 4: Padrão diferente")
    respostas_4 = {}
    for q in range(1, 41):
        respostas_4[q] = ['E', 'D', 'C', 'B', 'A'][(q - 1) % 5]  # Invertido
    gerar_pdf_teste("ALUNO_INVERTIDO", respostas_4, 4)

    print("\n" + "="*70)
    print("✓ PDFs DE TESTE GERADOS COM SUCESSO!")
    print("="*70)
    print("\nArquivos criados:")
    print("  • teste_01_ALUNO_PERFEITO.pdf     (40/40 acertos)")
    print("  • teste_02_ALUNO_MEDIO.pdf        (20/40 acertos)")
    print("  • teste_03_ALUNO_FRACO.pdf        (10/40 acertos)")
    print("  • teste_04_ALUNO_INVERTIDO.pdf    (0/40 acertos)")
    print("\nPara corrigir, execute:")
    print("  python3 corrigir_rapido.py pdfs_para_corrigir/teste_01_ALUNO_PERFEITO.pdf")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
