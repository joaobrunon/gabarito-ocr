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


def corrigir_inclinacao(img):
    """Detecta e corrige pequenas inclinações na imagem"""
    try:
        # Converter para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detectar bordas
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detectar linhas usando Hough Transform
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)

        if lines is not None:
            # Calcular ângulos dominantes
            angles = []
            for rho, theta in lines[:20]:  # Usar apenas as 20 linhas mais fortes
                angle = np.degrees(theta) - 90
                angles.append(angle)

            if angles:
                # Usar a mediana dos ângulos para evitar outliers
                median_angle = np.median(angles)

                # Se a inclinação for significativa (> 0.5°), corrigir
                if abs(median_angle) > 0.5:
                    # Rotacionar imagem
                    (h, w) = img.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    img_corrigida = cv2.warpAffine(img, M, (w, h),
                                                   flags=cv2.INTER_CUBIC,
                                                   borderMode=cv2.BORDER_REPLICATE)
                    return img_corrigida, median_angle

        return img, 0
    except:
        return img, 0


def preprocessar_imagem_para_codigo(img):
    """Aplica múltiplos pré-processamentos para melhorar detecção de códigos (ordem otimizada)"""
    processadas = []

    # Converter para escala de cinza uma vez (usado em vários métodos)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Ordem otimizada: métodos mais rápidos e eficazes primeiro

    # 1. Imagem original (mais rápido)
    processadas.append(("original", img))

    # 2. Escala de cinza simples (rápido)
    processadas.append(("gray", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))

    # 3. Blur + threshold OTSU (muito eficaz para códigos)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processadas.append(("otsu", cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)))

    # 4. CLAHE - equalização adaptativa (muito bom para iluminação desigual)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    clahe_img = clahe.apply(gray)
    processadas.append(("clahe", cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2BGR)))

    # 5. Adaptive threshold (bom para fundos variados)
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
    processadas.append(("adaptive", cv2.cvtColor(adaptive, cv2.COLOR_GRAY2BGR)))

    # Apenas se necessário (mais lentos):
    # 6. Sharpen (aumenta processamento)
    # kernel_sharpen = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    # sharpened = cv2.filter2D(gray, -1, kernel_sharpen)
    # processadas.append(("sharp", cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)))

    return processadas


def detectar_barcode(img):
    """Tenta detectar código de barras usando pyzbar com múltiplos pré-processamentos"""
    try:
        from pyzbar import pyzbar

        # Tentar com diferentes pré-processamentos
        imagens_processadas = preprocessar_imagem_para_codigo(img)

        for nome_proc, img_proc in imagens_processadas:
            decoded_objects = pyzbar.decode(img_proc)

            for obj in decoded_objects:
                data = obj.data.decode('utf-8').strip()
                # Validar se parece com um RA (numérico, 10-12 dígitos)
                if data.isdigit() and 10 <= len(data) <= 12:
                    return data, f"{obj.type} ({nome_proc})"

        return None, None
    except ImportError:
        # pyzbar não instalado, retornar None
        return None, None
    except Exception:
        return None, None


def detectar_qrcode_multiplas_tentativas(img, qr_detector):
    """Tenta detectar QR code com múltiplos pré-processamentos"""
    # Tentar com a imagem original primeiro
    data, bbox, _ = qr_detector.detectAndDecode(img)
    if data and data.strip().isdigit() and 10 <= len(data.strip()) <= 12:
        return data.strip(), "original"

    # Tentar com diferentes pré-processamentos
    imagens_processadas = preprocessar_imagem_para_codigo(img)

    for nome_proc, img_proc in imagens_processadas:
        data, bbox, _ = qr_detector.detectAndDecode(img_proc)
        if data and data.strip().isdigit() and 10 <= len(data.strip()) <= 12:
            return data.strip(), nome_proc

    return None, None


def extrair_ra_da_imagem(imagem_path):
    """Extrai RA do QR code/Barcode usando OpenCV - com suporte a rotações e correção de inclinação"""
    try:
        # Carregar imagem
        img = cv2.imread(imagem_path)

        # Criar detector de QR Code
        qr_detector = cv2.QRCodeDetector()

        # 1. Tentar detectar QR code com múltiplos pré-processamentos
        qr_data, qr_method = detectar_qrcode_multiplas_tentativas(img, qr_detector)
        if qr_data:
            if qr_method != "original":
                print(f"  (QR code detectado com pré-processamento: {qr_method})")
            return qr_data

        # 2. Tentar detectar barcode com múltiplos pré-processamentos
        barcode_data, barcode_type = detectar_barcode(img)
        if barcode_data:
            print(f"  (Código de barras detectado - tipo: {barcode_type})")
            return barcode_data

        # 3. Tentar corrigir inclinação leve
        img_corrigida, angulo_correcao = corrigir_inclinacao(img)
        if abs(angulo_correcao) > 0.5:
            # Tentar QR code na imagem corrigida
            qr_data, qr_method = detectar_qrcode_multiplas_tentativas(img_corrigida, qr_detector)
            if qr_data:
                print(f"  (QR code detectado após correção de inclinação: {angulo_correcao:.1f}° + {qr_method})")
                return qr_data

            # Tentar barcode na imagem corrigida
            barcode_data, barcode_type = detectar_barcode(img_corrigida)
            if barcode_data:
                print(f"  (Código de barras detectado após correção de inclinação: {angulo_correcao:.1f}° - tipo: {barcode_type})")
                return barcode_data

        # 4. Tentar com rotações de 90° (para páginas muito tortas)
        rotacoes = [
            (90, cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)),
            (180, cv2.rotate(img, cv2.ROTATE_180)),
            (270, cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE))
        ]

        for angulo, img_rotacionada in rotacoes:
            # Tentar QR code com múltiplos pré-processamentos
            qr_data, qr_method = detectar_qrcode_multiplas_tentativas(img_rotacionada, qr_detector)
            if qr_data:
                print(f"  (QR code detectado com rotação {angulo}° + {qr_method})")
                return qr_data

            # Tentar barcode
            barcode_data, barcode_type = detectar_barcode(img_rotacionada)
            if barcode_data:
                print(f"  (Código de barras detectado com rotação de {angulo}° - tipo: {barcode_type})")
                return barcode_data

            # Tentar também corrigir inclinação após rotação
            img_rot_corrigida, angulo_correcao = corrigir_inclinacao(img_rotacionada)
            if abs(angulo_correcao) > 0.5:
                # Tentar QR code com múltiplos pré-processamentos
                qr_data, qr_method = detectar_qrcode_multiplas_tentativas(img_rot_corrigida, qr_detector)
                if qr_data:
                    print(f"  (QR code detectado com rotação {angulo}° + inclinação {angulo_correcao:.1f}° + {qr_method})")
                    return qr_data

                # Tentar barcode
                barcode_data, barcode_type = detectar_barcode(img_rot_corrigida)
                if barcode_data:
                    print(f"  (Código de barras detectado com rotação {angulo}° + inclinação {angulo_correcao:.1f}° - tipo: {barcode_type})")
                    return barcode_data

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
