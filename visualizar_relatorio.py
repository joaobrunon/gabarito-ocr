#!/usr/bin/env python3
"""
Script para visualizar relatórios de correção em HTML
Solução alternativa para problemas com visualização de PDF
"""

import json
import sys
import os
from datetime import datetime


def gerar_html_relatorio(caminho_json):
    """Gera HTML do relatório a partir do JSON"""

    # Carregar JSON
    try:
        with open(caminho_json, 'r') as f:
            dados = json.load(f)
    except FileNotFoundError:
        print(f"✗ Arquivo não encontrado: {caminho_json}")
        return

    # Extrair dados
    identificacao = dados.get('identificacao', {})
    acertos = dados.get('acertos', 0)
    erros = dados.get('erros', 0)
    em_branco = dados.get('em_branco', 0)
    nota = dados.get('nota', 0)
    total = dados.get('total_questoes', 40)
    data = dados.get('data_correcao', 'N/A')

    # Calcular percentual
    percentual = (acertos / total * 100) if total > 0 else 0

    # Determinar cor baseado na nota
    if nota >= 7:
        cor_nota = '#27ae60'  # Verde
        status = 'APROVADO'
    elif nota >= 5:
        cor_nota = '#f39c12'  # Laranja
        status = 'RECOMENDAÇÃO'
    else:
        cor_nota = '#e74c3c'  # Vermelho
        status = 'REPROVADO'

    # HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório de Correção</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}

            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                overflow: hidden;
            }}

            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}

            .header h1 {{
                font-size: 32px;
                margin-bottom: 10px;
            }}

            .header p {{
                opacity: 0.9;
                font-size: 14px;
            }}

            .content {{
                padding: 30px;
            }}

            .aluno-info {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                border-left: 4px solid #667eea;
            }}

            .info-linha {{
                display: flex;
                justify-content: space-between;
                margin: 10px 0;
                font-size: 16px;
            }}

            .info-label {{
                font-weight: 600;
                color: #333;
            }}

            .info-valor {{
                color: #666;
            }}

            .resultado {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }}

            .card {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }}

            .card.acertos {{
                background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);
            }}

            .card.erros {{
                background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            }}

            .card.em-branco {{
                background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            }}

            .card.nota {{
                background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            }}

            .card-numero {{
                font-size: 32px;
                font-weight: bold;
                color: #333;
                margin: 10px 0;
            }}

            .card-label {{
                font-size: 14px;
                color: #555;
                font-weight: 600;
            }}

            .nota-grande {{
                background: {cor_nota};
                color: white;
                padding: 30px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
            }}

            .nota-grande .numero {{
                font-size: 48px;
                font-weight: bold;
                margin: 10px 0;
            }}

            .nota-grande .status {{
                font-size: 20px;
                font-weight: 600;
                margin-top: 10px;
            }}

            .barra-progresso {{
                background: #ecf0f1;
                height: 30px;
                border-radius: 15px;
                overflow: hidden;
                margin: 20px 0;
            }}

            .barra-preenchida {{
                background: linear-gradient(90deg, #27ae60, #2ecc71);
                height: 100%;
                width: {percentual}%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 12px;
                transition: width 0.5s ease;
            }}

            .detalhes {{
                margin-top: 30px;
                padding-top: 30px;
                border-top: 2px solid #ecf0f1;
            }}

            .detalhes h3 {{
                margin-bottom: 15px;
                color: #333;
            }}

            .detalhes-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }}

            .detalhe-item {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                border-left: 3px solid #667eea;
            }}

            .detalhe-label {{
                font-size: 12px;
                color: #999;
                text-transform: uppercase;
                margin-bottom: 5px;
            }}

            .detalhe-valor {{
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }}

            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #999;
                font-size: 12px;
                border-top: 1px solid #ecf0f1;
            }}

            @media print {{
                body {{
                    background: white;
                }}
                .container {{
                    box-shadow: none;
                }}
            }}

            @media (max-width: 768px) {{
                .resultado {{
                    grid-template-columns: repeat(2, 1fr);
                }}
                .detalhes-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 Relatório de Correção</h1>
                <p>Sistema Automático de Gabaritos</p>
            </div>

            <div class="content">
                <!-- Informações do Aluno -->
                <div class="aluno-info">
                    <div class="info-linha">
                        <span class="info-label">👤 Nome:</span>
                        <span class="info-valor">{identificacao.get('nome', 'N/A')}</span>
                    </div>
                    <div class="info-linha">
                        <span class="info-label">📚 Matrícula:</span>
                        <span class="info-valor">{identificacao.get('matricula', 'N/A')}</span>
                    </div>
                    <div class="info-linha">
                        <span class="info-label">🏫 Turma:</span>
                        <span class="info-valor">{identificacao.get('turma', 'N/A')}</span>
                    </div>
                    <div class="info-linha">
                        <span class="info-label">📅 Data:</span>
                        <span class="info-valor">{data}</span>
                    </div>
                </div>

                <!-- Resultado em Cards -->
                <div class="resultado">
                    <div class="card acertos">
                        <div class="card-label">✓ Acertos</div>
                        <div class="card-numero">{acertos}</div>
                        <div class="card-label">de {total}</div>
                    </div>

                    <div class="card erros">
                        <div class="card-label">✗ Erros</div>
                        <div class="card-numero">{erros}</div>
                        <div class="card-label">de {total}</div>
                    </div>

                    <div class="card em-branco">
                        <div class="card-label">○ Em Branco</div>
                        <div class="card-numero">{em_branco}</div>
                        <div class="card-label">de {total}</div>
                    </div>

                    <div class="card nota">
                        <div class="card-label">🎯 Percentual</div>
                        <div class="card-numero">{percentual:.1f}%</div>
                        <div class="card-label">aproveitamento</div>
                    </div>
                </div>

                <!-- Nota Grande -->
                <div class="nota-grande">
                    <div>NOTA FINAL</div>
                    <div class="numero">{nota:.1f}</div>
                    <div class="status">{status}</div>
                </div>

                <!-- Barra de Progresso -->
                <div class="barra-progresso">
                    <div class="barra-preenchida" style="width: {percentual}%">
                        {percentual:.0f}%
                    </div>
                </div>

                <!-- Detalhes -->
                <div class="detalhes">
                    <h3>📊 Detalhes da Prova</h3>
                    <div class="detalhes-grid">
                        <div class="detalhe-item">
                            <div class="detalhe-label">Total de Questões</div>
                            <div class="detalhe-valor">{total}</div>
                        </div>
                        <div class="detalhe-item">
                            <div class="detalhe-label">Taxa de Acerto</div>
                            <div class="detalhe-valor">{percentual:.1f}%</div>
                        </div>
                        <div class="detalhe-item">
                            <div class="detalhe-label">Questões Respondidas</div>
                            <div class="detalhe-valor">{acertos + erros}</div>
                        </div>
                        <div class="detalhe-item">
                            <div class="detalhe-label">Questões Deixadas em Branco</div>
                            <div class="detalhe-valor">{em_branco}</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="footer">
                <p>Relatório gerado automaticamente pelo Sistema de Gabaritos</p>
                <p>© 2024 - Todos os direitos reservados</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Salvar HTML
    nome_html = caminho_json.replace('.json', '.html')
    with open(nome_html, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Relatório HTML gerado: {nome_html}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 visualizar_relatorio.py <arquivo.json>")
        print("\nExemplo:")
        print("  python3 visualizar_relatorio.py relatorios_correcao/teste_01_ALUNO_PERFEITO_relatorio.json")
        sys.exit(1)

    caminho_json = sys.argv[1]
    gerar_html_relatorio(caminho_json)
