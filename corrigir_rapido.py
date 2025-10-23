#!/usr/bin/env python3
"""
Script Rápido para Corrigir PDFs
Sem menu interativo - direto ao ponto
"""

import sys
import json
import fitz
import csv
import cv2
import numpy as np
from leitor_gabarito import LeitorFinalV2
from corretor import Corretor
from visualizar_relatorio import gerar_html_relatorio


def carregar_csv_alunos(caminho_csv='csv_alunos_referencia/alunos_referencia.csv'):
    """Carrega CSV com dados dos alunos e retorna dicionário {RA: dados}"""
    alunos = {}
    try:
        with open(caminho_csv, 'r', encoding='utf-8') as f:
            # Pular primeira linha (cabeçalho de data)
            f.readline()
            # Pular linha em branco
            f.readline()
            # Agora processar o CSV
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                ra = row.get('RA', '').strip()
                digito = row.get('Digito', '').strip()

                # RA completo = RA + Digito
                ra_completo = ra + digito

                if ra_completo:
                    alunos[ra_completo] = {
                        'nome': row.get('Aluno', '').strip(),
                        'turma': row.get('Turma', '').strip(),
                        'email': row.get('E-Mail Microsoft', '').strip()
                    }
    except Exception as e:
        print(f"⚠ Erro ao carregar CSV: {e}")
        import traceback
        traceback.print_exc()

    return alunos


def extrair_ra_da_imagem(imagem_path):
    """Extrai RA do QR code usando OpenCV"""
    try:
        # Carregar imagem
        img = cv2.imread(imagem_path)

        # Criar detector de QR Code
        qr_detector = cv2.QRCodeDetector()

        # Detectar e decodificar QR code
        data, bbox, _ = qr_detector.detectAndDecode(img)

        if data:
            ra = data.strip()
            # Validar se parece com um RA (numérico, 10-12 dígitos)
            if ra.isdigit() and 10 <= len(ra) <= 12:
                return ra

        # Se não encontrou QR code, tentar procurar barcode com OpenCV
        # (barcode é mais difícil, então vamos apenas tentar QR por enquanto)

        return None
    except Exception as e:
        print(f"⚠ Erro ao extrair RA: {e}")
        return None


def corrigir_rapido(caminho_pdf, caminho_gabarito='gabarito_oficial.json'):
    """Corrige um PDF de forma rápida e automática - TODAS AS PÁGINAS"""

    # 1. Carregar gabarito oficial
    print(f"Carregando gabarito: {caminho_gabarito}")
    corretor = Corretor()
    if not corretor.carregar_gabarito_oficial(caminho_gabarito):
        print(f"✗ Erro ao carregar gabarito: {caminho_gabarito}")
        return

    # 1.5 Carregar CSV de alunos
    print(f"Carregando dados dos alunos...")
    alunos_dict = carregar_csv_alunos()
    print(f"✓ {len(alunos_dict)} alunos carregados do CSV\n")

    # 2. Abrir PDF e processar TODAS as páginas
    print(f"Processando PDF: {caminho_pdf}")
    try:
        pdf = fitz.open(caminho_pdf)
        num_paginas = len(pdf)
        print(f"📄 {num_paginas} páginas detectadas\n")

        num_questoes = len(corretor.gabarito_oficial)
        leitor = LeitorFinalV2(num_questoes=num_questoes)

        # Processar cada página
        for page_num in range(num_paginas):
            print(f"\n{'='*70}")
            print(f"PROCESSANDO PÁGINA {page_num + 1}/{num_paginas}")
            print(f"{'='*70}")

            # Converter página em imagem
            pagina = pdf[page_num]
            pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))
            temp_path = f'/tmp/corrigir_scan_p{page_num}.png'
            pix.save(temp_path)

            # 3. Ler respostas com OCR
            print("Detectando respostas...")
            respostas = leitor.ler_gabarito(temp_path)
            print(f"✓ {len(respostas)}/{num_questoes} questões detectadas")

            # 4. Converter para formato esperado
            respostas = {int(q): r for q, r in respostas.items()}

            # 5. Identificação do aluno - extrair do QR code/barcode
            print("Extraindo identificação do aluno...")
            ra = extrair_ra_da_imagem(temp_path)

            # Nome do PDF para usar no nome do arquivo de relatório
            nome_pdf = caminho_pdf.split('/')[-1].replace('.pdf', '')

            # Tentar encontrar aluno no CSV
            dados_aluno = None
            if ra:
                # Primeiro tentar com RA completo
                if ra in alunos_dict:
                    dados_aluno = alunos_dict[ra]
                else:
                    # O QR code pode ter apenas os 12 primeiros dígitos (sem o dígito verificador)
                    # Procurar por RA que comece com os 12 dígitos
                    for ra_completo, aluno in alunos_dict.items():
                        if ra_completo.startswith(ra):
                            dados_aluno = aluno
                            break

            if dados_aluno:
                # Encontrou o aluno no CSV
                identificacao = {
                    'nome': dados_aluno['nome'],
                    'matricula': ra,
                    'turma': dados_aluno['turma']
                }
                print(f"✓ Aluno identificado: {dados_aluno['nome']} (RA: {ra})")
            else:
                # Fallback: usar nome do arquivo
                identificacao = {
                    'nome': f"{nome_pdf}_pagina_{page_num + 1}",
                    'matricula': ra if ra else '',
                    'turma': ''
                }
                if ra:
                    print(f"⚠ RA {ra} encontrado mas não está no CSV")
                else:
                    print(f"⚠ QR/Barcode não detectado, usando nome do arquivo")

            # 6. Corrigir
            print("Corrigindo prova...")
            resultado = corretor.corrigir_prova(identificacao, respostas)

            # 6.5 Adicionar informação de múltiplas marcações
            resultado['questoes_multiplas_marcacoes'] = leitor.questoes_multiplas

            # 7. Exibir resultado resumido
            acertos = resultado['acertos']
            total = resultado['total_questoes']
            nota = resultado['nota']

            print(f"✓ Acertos: {acertos}/{total}")
            print(f"🎯 Nota: {nota:.1f}/100")
            if leitor.questoes_multiplas:
                print(f"⚠️  Múltiplas marcações detectadas em: {leitor.questoes_multiplas}")

            # 8. Salvar relatório
            relatorio_path = f"relatorios_correcao/{nome_pdf}_pag{page_num + 1:03d}_relatorio.json"
            with open(relatorio_path, 'w') as f:
                json.dump(resultado, f, indent=2)

            print(f"✓ Relatório salvo: {relatorio_path}")

            # 9. Gerar HTML
            gerar_html_relatorio(relatorio_path)

        pdf.close()

        print(f"\n{'='*70}")
        print(f"✅ CONCLUÍDO! {num_paginas} páginas processadas")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"✗ Erro ao processar PDF: {e}")
        return


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 corrigir_rapido.py <arquivo.pdf> [gabarito.json]")
        print("\nExemplo:")
        print("  python3 corrigir_rapido.py pdfs_para_corrigir/Documento35.pdf")
        print("  python3 corrigir_rapido.py pdfs_para_corrigir/Documento35.pdf gabaritos/prova_A.json")
        sys.exit(1)

    caminho_pdf = sys.argv[1]
    caminho_gabarito = sys.argv[2] if len(sys.argv) > 2 else 'gabarito_oficial.json'
    corrigir_rapido(caminho_pdf, caminho_gabarito)
