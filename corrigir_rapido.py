#!/usr/bin/env python3
"""
Script Rápido para Corrigir PDFs
Sem menu interativo - direto ao ponto
"""

import sys
import json
import fitz
from leitor_gabarito import LeitorFinalV2
from corretor import Corretor


def corrigir_rapido(caminho_pdf):
    """Corrige um PDF de forma rápida e automática"""

    # 1. Carregar gabarito oficial
    print("Carregando gabarito oficial...")
    corretor = Corretor()
    if not corretor.carregar_gabarito_oficial('gabarito_oficial.json'):
        print("✗ Erro ao carregar gabarito oficial")
        return

    # 2. Converter PDF em imagem
    print(f"Processando PDF: {caminho_pdf}")
    try:
        pdf = fitz.open(caminho_pdf)
        pagina = pdf[0]
        pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))
        temp_path = '/tmp/corrigir_scan.png'
        pix.save(temp_path)
        pdf.close()
    except Exception as e:
        print(f"✗ Erro ao processar PDF: {e}")
        return

    # 3. Ler respostas com OCR
    print("Detectando respostas...")
    num_questoes = len(corretor.gabarito_oficial)
    leitor = LeitorFinalV2(num_questoes=num_questoes)
    respostas = leitor.ler_gabarito(temp_path)
    print(f"✓ {len(respostas)}/{num_questoes} questões detectadas")

    # 4. Converter para formato esperado (inteiros para compatibilidade com corretor)
    respostas = {int(q): r for q, r in respostas.items()}

    # 5. Identificação do aluno
    nome_pdf = caminho_pdf.split('/')[-1].replace('.pdf', '')
    identificacao = {
        'nome': nome_pdf,
        'matricula': '',
        'turma': ''
    }

    # 6. Corrigir
    print("\nCorrigindo prova...")
    resultado = corretor.corrigir_prova(identificacao, respostas)

    # 7. Exibir resultado
    print("\n" + "="*70)
    print("RESULTADO DA CORREÇÃO")
    print("="*70)

    acertos = resultado['acertos']
    total = resultado['total_questoes']
    nota = resultado['nota']

    print(f"\n✓ Acertos:     {acertos}/{total}")
    print(f"✗ Erros:       {total - acertos}/{total}")
    print(f"\n🎯 NOTA FINAL: {nota:.1f}/100")

    # Mostrar respostas
    print("\n" + "-"*70)
    print("RESPOSTAS:")
    print("-"*70)

    for q in range(1, total + 1):
        resposta_aluno = respostas.get(q, '?')
        resposta_correta = corretor.gabarito_oficial.get(q, '?')

        if resposta_aluno == resposta_correta:
            status = "✓"
        else:
            status = "✗"

        if (q - 1) % 5 == 0:
            print()

        print(f"{status} Q{q:02d}:{resposta_aluno}", end="  ")

    print("\n\n" + "="*70)

    # 8. Salvar relatório
    relatorio_path = f"relatorios_correcao/{nome_pdf}_relatorio.json"
    with open(relatorio_path, 'w') as f:
        json.dump(resultado, f, indent=2)

    print(f"✓ Relatório salvo: {relatorio_path}")
    print("="*70 + "\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 corrigir_rapido.py <arquivo.pdf>")
        print("\nExemplo:")
        print("  python3 corrigir_rapido.py pdfs_para_corrigir/Documento35.pdf")
        sys.exit(1)

    caminho_pdf = sys.argv[1]
    corrigir_rapido(caminho_pdf)
