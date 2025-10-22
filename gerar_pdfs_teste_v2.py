#!/usr/bin/env python3
"""
Script para gerar PDFs de teste com marcações (Versão 2)
Desenha círculos preenchidos diretamente
"""

import os
from gerador_gabarito import GeradorGabarito
from reportlab.lib.units import cm


def gerar_pdf_teste_com_marcacoes(nome_aluno, respostas, numero_teste=1):
    """
    Gera um PDF com círculos preenchidos nas respostas
    """

    nome_arquivo = f"pdfs_para_corrigir/teste_v2_{numero_teste:02d}_{nome_aluno}.pdf"

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

    # Título das respostas
    gerador.c.setFont("Helvetica-Bold", 10)
    gerador.c.drawCentredString(gerador.largura / 2, y_questoes, "RESPOSTAS - Preencha completamente o círculo")

    # Linha separadora
    gerador.c.setLineWidth(0.5)
    gerador.c.line(2*cm, y_questoes - 0.3*cm, gerador.largura - 2*cm, y_questoes - 0.3*cm)

    y_questoes -= 1*cm

    # Layout dos círculos (2 colunas x 20 linhas)
    # Coluna esquerda: Q01-Q20, Coluna direita: Q21-Q40

    # Posições base
    x_col1 = 2.5*cm
    x_col2 = 11*cm
    y_inicio = y_questoes

    # Espaçamento
    x_alt_spacing = 1.3*cm
    y_questao_spacing = 0.7*cm
    raio_circulo = 0.15*cm

    # Desenhar círculos e preenchê-los conforme respostas
    for q in range(1, 41):
        # Determinar posição
        if q <= 20:
            col = 0
            linha_em_col = q - 1
            x_base = x_col1
        else:
            col = 1
            linha_em_col = q - 21
            x_base = x_col2

        y = y_inicio - (linha_em_col * y_questao_spacing)

        # Número da questão
        gerador.c.setFont("Helvetica-Bold", 9)
        gerador.c.drawString(x_base, y, f"{q:02d}.")

        # Desenhar 5 círculos (alternativas A, B, C, D, E)
        x_alt = x_base + 1.3*cm

        for idx, alt in enumerate(['A', 'B', 'C', 'D', 'E']):
            # Desenhar círculo vazio
            gerador.c.setLineWidth(1.5)
            gerador.c.circle(x_alt, y + 0.2*cm, raio_circulo, stroke=1, fill=0)

            # Se essa questão foi respondida com essa alternativa, preencher
            if q in respostas and respostas[q] == alt:
                gerador.c.setFillColorRGB(0.1, 0.1, 0.1)  # Preto escuro
                gerador.c.circle(x_alt, y + 0.2*cm, raio_circulo * 0.8, stroke=0, fill=1)
                gerador.c.setFillColorRGB(0, 0, 0)  # Reset

            # Letra
            gerador.c.setFont("Helvetica", 7)
            gerador.c.drawCentredString(x_alt, y + 0.1*cm, alt)

            x_alt += x_alt_spacing

    # Rodapé
    gerador._desenhar_rodape(nome_aluno=nome_aluno, codigo_prova=f"TESTE{numero_teste:02d}", ra_aluno=f"000{numero_teste:05d}")

    gerador.c.save()
    print(f"  ✓ Salvo com sucesso")


def main():
    """Gera vários PDFs de teste"""

    os.makedirs('pdfs_para_corrigir', exist_ok=True)

    print("\n" + "="*70)
    print("GERANDO PDFs DE TESTE COM MARCAÇÕES (Versão 2)")
    print("="*70 + "\n")

    # Teste 1: Perfeito (100%)
    print("Teste 1: Perfeito (100%)")
    respostas_1 = {}
    for q in range(1, 41):
        indice = (q - 1) % 5
        respostas_1[q] = ['A', 'B', 'C', 'D', 'E'][indice]
    gerar_pdf_teste_com_marcacoes("PERFEITO_100", respostas_1, 1)

    # Teste 2: 50% acertos
    print("\nTeste 2: 50% de acertos")
    respostas_2 = {}
    for q in range(1, 41):
        if q % 2 == 0:
            indice = (q - 1) % 5
            respostas_2[q] = ['A', 'B', 'C', 'D', 'E'][indice]
        else:
            respostas_2[q] = 'A'  # Resposta errada
    gerar_pdf_teste_com_marcacoes("MEDIO_50", respostas_2, 2)

    # Teste 3: 75% acertos
    print("\nTeste 3: 75% de acertos")
    respostas_3 = {}
    for q in range(1, 41):
        if q % 4 != 0:
            indice = (q - 1) % 5
            respostas_3[q] = ['A', 'B', 'C', 'D', 'E'][indice]
        else:
            respostas_3[q] = 'E'  # Resposta errada
    gerar_pdf_teste_com_marcacoes("BOM_75", respostas_3, 3)

    # Teste 4: 0% acertos
    print("\nTeste 4: 0% de acertos")
    respostas_4 = {}
    for q in range(1, 41):
        respostas_4[q] = 'A'  # Sempre A (errado para maioria)
    gerar_pdf_teste_com_marcacoes("RUIM_0", respostas_4, 4)

    print("\n" + "="*70)
    print("✓ PDFs DE TESTE GERADOS COM SUCESSO!")
    print("="*70)
    print("\nArquivos criados em pdfs_para_corrigir/:")
    print("  • teste_v2_01_PERFEITO_100.pdf")
    print("  • teste_v2_02_MEDIO_50.pdf")
    print("  • teste_v2_03_BOM_75.pdf")
    print("  • teste_v2_04_RUIM_0.pdf")
    print("\nPara testar a correção:")
    print("  python3 corrigir_rapido.py pdfs_para_corrigir/teste_v2_01_PERFEITO_100.pdf")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
