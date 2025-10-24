#!/usr/bin/env python3
"""Script para testar detecção de QR code"""

import cv2
import fitz
import sys
import numpy as np

def testar_qrcode_pagina(pdf_path, page_num=0):
    """Testa detecção de QR code em uma página específica"""

    # Extrair página como imagem
    pdf = fitz.open(pdf_path)
    pagina = pdf[page_num]
    pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))
    temp_path = f'/tmp/test_qr_p{page_num}.png'
    pix.save(temp_path)
    pdf.close()

    print(f"Imagem salva em: {temp_path}")
    print(f"Testando detecção de QR code...\n")

    # Carregar imagem
    img = cv2.imread(temp_path)
    print(f"Imagem carregada: {img.shape}")

    # Criar detector de QR Code
    qr_detector = cv2.QRCodeDetector()

    # Tentar detectar em múltiplas rotações
    print("Tentando detectar QR code em diferentes rotações...\n")

    rotacoes = [
        (0, "Normal (0°)"),
        (90, "Rotação 90°"),
        (180, "Rotação 180°"),
        (270, "Rotação 270°")
    ]

    data = ""
    bbox = None
    rotacao_detectada = None

    for angulo, descricao in rotacoes:
        # Rotacionar imagem
        if angulo == 0:
            img_rotacionada = img
        elif angulo == 90:
            img_rotacionada = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif angulo == 180:
            img_rotacionada = cv2.rotate(img, cv2.ROTATE_180)
        elif angulo == 270:
            img_rotacionada = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Tentar detectar
        data_temp, bbox_temp, _ = qr_detector.detectAndDecode(img_rotacionada)

        print(f"  {descricao}: ", end="")
        if data_temp:
            print(f"✓ Detectado! Conteúdo: {data_temp}")
            data = data_temp
            bbox = bbox_temp
            rotacao_detectada = angulo
            break
        else:
            print("✗ Não detectado")

    print(f"\n=== RESULTADO ===")
    print(f"Data detectada: '{data}'")
    print(f"BBox: {bbox is not None}")
    if rotacao_detectada is not None:
        print(f"Rotação necessária: {rotacao_detectada}°")

    if data:
        print(f"✓ QR Code encontrado!")
        print(f"  Conteúdo: {data}")
        print(f"  Tamanho: {len(data)} caracteres")
        print(f"  É numérico: {data.isdigit()}")
        print(f"  Tamanho válido para RA: {10 <= len(data) <= 12}")
    else:
        print(f"✗ QR Code NÃO detectado")
        print(f"\nTentando com biblioteca pyzbar...")

        try:
            from pyzbar import pyzbar
            decoded_objects = pyzbar.decode(img)

            if decoded_objects:
                print(f"✓ pyzbar encontrou {len(decoded_objects)} código(s):")
                for obj in decoded_objects:
                    print(f"  Tipo: {obj.type}")
                    print(f"  Dados: {obj.data.decode('utf-8')}")
                    print(f"  Posição: {obj.rect}")
            else:
                print(f"✗ pyzbar também não encontrou nada")
        except ImportError:
            print(f"⚠ pyzbar não instalado (pip install pyzbar)")

if __name__ == '__main__':
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'pdfs_para_corrigir/SIMULADO_12.pdf'
    page_num = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    print(f"PDF: {pdf_path}")
    print(f"Página: {page_num + 1}\n")

    testar_qrcode_pagina(pdf_path, page_num)
