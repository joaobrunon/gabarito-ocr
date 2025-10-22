#!/usr/bin/env python3
"""
Script para listar PDFs na pasta de correção
"""

import os
import sys

pasta_pdfs = 'pdfs_para_corrigir'

if not os.path.isdir(pasta_pdfs):
    print(f"✗ Pasta não encontrada: {pasta_pdfs}")
    sys.exit(1)

pdfs = [f for f in os.listdir(pasta_pdfs) if f.lower().endswith('.pdf')]

if not pdfs:
    print(f"Nenhum PDF encontrado em {pasta_pdfs}/")
    sys.exit(0)

print("\n" + "="*60)
print(f"PDFs DISPONÍVEIS PARA CORREÇÃO ({len(pdfs)})")
print("="*60 + "\n")

for i, pdf in enumerate(pdfs, 1):
    tamanho = os.path.getsize(os.path.join(pasta_pdfs, pdf))
    tamanho_mb = tamanho / (1024 * 1024)
    print(f"[{i}] {pdf:<40} ({tamanho_mb:.1f} MB)")

print("\n" + "="*60)
print("Use o caminho completo ao corrigir:")
print(f"Exemplo: pdfs_para_corrigir/{pdfs[0]}")
print("="*60 + "\n")
