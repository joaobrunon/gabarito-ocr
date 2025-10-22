#!/usr/bin/env python3
"""
Aplicação Web para Correção de Gabaritos
Sistema completo de upload, correção e visualização de relatórios
"""

from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import json
import os
from pathlib import Path
from datetime import datetime
import subprocess
import sys
from gerador_gabarito import GeradorGabarito
from gerar_gabaritos_personalizados import ler_csv_alunos, listar_turmas, gerar_gabaritos_turma
import csv

# Configuração
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['UPLOAD_FOLDER'] = 'pdfs_para_corrigir'
app.config['REPORTS_FOLDER'] = 'relatorios_correcao'
app.config['GABARITOS_FOLDER'] = 'gabaritos'
app.config['GABARITOS_PDF_FOLDER'] = 'gabaritos_gerados'
app.config['CSV_UPLOAD_FOLDER'] = 'uploads_csv'

# Criar pastas se não existirem
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['REPORTS_FOLDER']).mkdir(exist_ok=True)
Path(app.config['GABARITOS_FOLDER']).mkdir(exist_ok=True)
Path(app.config['GABARITOS_PDF_FOLDER']).mkdir(exist_ok=True)
Path(app.config['CSV_UPLOAD_FOLDER']).mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}
ALLOWED_CSV_EXTENSIONS = {'csv'}
GABARITO_OFICIAL = 'gabarito_oficial.json'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_csv_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_CSV_EXTENSIONS

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/reports', methods=['GET'])
def get_reports():
    """Retorna lista de relatórios"""
    reports = []
    reports_path = Path(app.config['REPORTS_FOLDER'])

    for json_file in sorted(reports_path.glob('*_relatorio.json'), reverse=True):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            reports.append({
                'nome': data.get('identificacao', {}).get('nome', 'Desconhecido'),
                'data': data.get('data_correcao', 'N/A'),
                'nota': data.get('nota', 0),
                'acertos': data.get('acertos', 0),
                'erros': data.get('erros', 0),
                'total': data.get('total_questoes', 40),
                'json_file': json_file.name,
                'html_file': json_file.with_suffix('.html').name
            })
        except:
            pass

    return jsonify(reports)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Recebe PDF e começa a corrigir"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Arquivo vazio'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Apenas arquivos PDF são permitidos'}), 400

    # Salvar arquivo
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Corrigir PDF
    try:
        venv_path = '/home/proatec/gabarito/venv'
        result = subprocess.run(
            [f'{venv_path}/bin/python3', 'corrigir_rapido.py', filepath],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return jsonify({'error': 'Erro ao corrigir PDF'}), 500

        # Procurar relatório gerado
        base_name = Path(filename).stem
        json_files = list(Path(app.config['REPORTS_FOLDER']).glob(f'*{base_name}*relatorio.json'))

        if not json_files:
            return jsonify({'error': 'Relatório não gerado'}), 500

        json_file = json_files[0]

        # Carregar dados do relatório
        with open(json_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        return jsonify({
            'success': True,
            'message': 'PDF corrigido com sucesso!',
            'report': {
                'nome': report_data.get('identificacao', {}).get('nome', 'Desconhecido'),
                'data': report_data.get('data_correcao', 'N/A'),
                'nota': report_data.get('nota', 0),
                'acertos': report_data.get('acertos', 0),
                'erros': report_data.get('erros', 0),
                'em_branco': report_data.get('em_branco', 0),
                'total': report_data.get('total_questoes', 40),
                'percentual': report_data.get('percentual', 0),
                'json_file': json_file.name
            }
        })

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timeout ao corrigir PDF'}), 500
    except Exception as e:
        return jsonify({'error': f'Erro: {str(e)}'}), 500

@app.route('/api/report/<filename>')
def get_report(filename):
    """Retorna dados de um relatório específico"""
    json_path = Path(app.config['REPORTS_FOLDER']) / filename

    if not json_path.exists():
        return jsonify({'error': 'Relatório não encontrado'}), 404

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        return jsonify(report)
    except:
        return jsonify({'error': 'Erro ao ler relatório'}), 500

@app.route('/api/stats')
def get_stats():
    """Retorna estatísticas gerais"""
    stats = {
        'total_relatorios': 0,
        'media_nota': 0,
        'maior_nota': 0,
        'menor_nota': 10
    }

    reports_path = Path(app.config['REPORTS_FOLDER'])
    notas = []

    for json_file in reports_path.glob('*_relatorio.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            nota = data.get('nota', 0)
            notas.append(nota)
        except:
            pass

    if notas:
        stats['total_relatorios'] = len(notas)
        stats['media_nota'] = round(sum(notas) / len(notas), 2)
        stats['maior_nota'] = max(notas)
        stats['menor_nota'] = min(notas)

    return jsonify(stats)

@app.route('/relatorio/<filename>')
def view_report(filename):
    """Retorna o HTML do relatório"""
    html_path = Path(app.config['REPORTS_FOLDER']) / filename.replace('.json', '.html')

    if not html_path.exists():
        return "Relatório não encontrado", 404

    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()

# APIs de Gabarito
@app.route('/api/gabaritos', methods=['GET'])
def list_gabaritos():
    """Lista todos os gabaritos disponíveis"""
    gabaritos = []
    gabaritos_path = Path(app.config['GABARITOS_FOLDER'])

    for json_file in sorted(gabaritos_path.glob('*.json')):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            is_oficial = json_file.name == GABARITO_OFICIAL
            gabaritos.append({
                'nome': json_file.stem,
                'arquivo': json_file.name,
                'questoes': len(data),
                'oficial': is_oficial
            })
        except:
            pass

    return jsonify(gabaritos)

@app.route('/api/gabarito/atual', methods=['GET'])
def get_gabarito_atual():
    """Retorna o gabarito oficial atual"""
    gabarito_path = Path(GABARITO_OFICIAL)

    if not gabarito_path.exists():
        return jsonify({'error': 'Nenhum gabarito selecionado'}), 404

    try:
        with open(gabarito_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except:
        return jsonify({'error': 'Erro ao ler gabarito'}), 500

@app.route('/api/gabarito/criar', methods=['POST'])
def criar_gabarito():
    """Cria um novo gabarito"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    nome = data.get('nome', '').strip()
    questoes = data.get('questoes', [])

    if not nome:
        return jsonify({'error': 'Nome do gabarito é obrigatório'}), 400

    if not questoes or len(questoes) == 0:
        return jsonify({'error': 'Adicione pelo menos uma questão'}), 400

    # Validar questões
    gabarito_dict = {}
    try:
        for i, resp in enumerate(questoes, 1):
            if resp.upper() not in ['A', 'B', 'C', 'D', 'E']:
                return jsonify({'error': f'Resposta inválida na questão {i}'}), 400
            gabarito_dict[i] = resp.upper()
    except:
        return jsonify({'error': 'Formato inválido nas questões'}), 400

    # Salvar gabarito
    gabarito_path = Path(app.config['GABARITOS_FOLDER']) / f"{nome}.json"

    try:
        with open(gabarito_path, 'w', encoding='utf-8') as f:
            json.dump(gabarito_dict, f, indent=2)
        return jsonify({'success': True, 'message': f'Gabarito "{nome}" criado com {len(gabarito_dict)} questões'})
    except Exception as e:
        return jsonify({'error': f'Erro ao salvar gabarito: {str(e)}'}), 500

@app.route('/api/gabarito/selecionar/<nome>', methods=['POST'])
def selecionar_gabarito(nome):
    """Seleciona um gabarito como oficial"""
    gabarito_path = Path(app.config['GABARITOS_FOLDER']) / f"{nome}.json"

    if not gabarito_path.exists():
        return jsonify({'error': 'Gabarito não encontrado'}), 404

    try:
        # Copiar para gabarito_oficial.json
        with open(gabarito_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        with open(GABARITO_OFICIAL, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return jsonify({'success': True, 'message': f'Gabarito "{nome}" selecionado como oficial'})
    except Exception as e:
        return jsonify({'error': f'Erro ao selecionar gabarito: {str(e)}'}), 500

@app.route('/api/gabarito/deletar/<nome>', methods=['DELETE'])
def deletar_gabarito(nome):
    """Deleta um gabarito"""
    gabarito_path = Path(app.config['GABARITOS_FOLDER']) / f"{nome}.json"

    if not gabarito_path.exists():
        return jsonify({'error': 'Gabarito não encontrado'}), 404

    try:
        gabarito_path.unlink()
        return jsonify({'success': True, 'message': f'Gabarito "{nome}" deletado'})
    except Exception as e:
        return jsonify({'error': f'Erro ao deletar gabarito: {str(e)}'}), 500

@app.route('/api/gabarito/gerar-pdf', methods=['POST'])
def gerar_gabarito_pdf():
    """Gera um gabarito em PDF"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    # Extrair parâmetros
    nome_arquivo = data.get('nome_arquivo', '').strip()
    titulo = data.get('titulo', 'GABARITO DE PROVA').strip()
    disciplina = data.get('disciplina', '').strip() or None
    professor = data.get('professor', '').strip() or None
    codigo_prova = data.get('codigo_prova', '').strip() or None
    num_questoes = int(data.get('num_questoes', 40))
    alternativas_str = data.get('alternativas', 'A,B,C,D,E').strip()

    # Validações
    if not nome_arquivo:
        return jsonify({'error': 'Nome do arquivo é obrigatório'}), 400

    if num_questoes < 1 or num_questoes > 200:
        return jsonify({'error': 'Número de questões deve estar entre 1 e 200'}), 400

    # Processar alternativas
    alternativas = [a.strip().upper() for a in alternativas_str.split(',') if a.strip()]
    if not alternativas:
        alternativas = ['A', 'B', 'C', 'D', 'E']

    # Adicionar .pdf se não tiver
    if not nome_arquivo.endswith('.pdf'):
        nome_arquivo += '.pdf'

    # Caminho completo
    pdf_path = Path(app.config['GABARITOS_PDF_FOLDER']) / nome_arquivo

    try:
        # Gerar PDF
        gerador = GeradorGabarito(str(pdf_path))
        gerador.gerar_gabarito_padrao(
            num_questoes=num_questoes,
            alternativas=alternativas,
            titulo=titulo,
            disciplina=disciplina,
            professor=professor,
            codigo_prova=codigo_prova
        )

        return jsonify({
            'success': True,
            'message': f'Gabarito PDF "{nome_arquivo}" gerado com sucesso!',
            'arquivo': nome_arquivo,
            'caminho': str(pdf_path)
        })

    except Exception as e:
        return jsonify({'error': f'Erro ao gerar PDF: {str(e)}'}), 500

@app.route('/api/gabarito/download-pdf/<path:filename>')
def download_gabarito_pdf(filename):
    """Faz download de um gabarito PDF gerado"""
    pdf_path = Path(app.config['GABARITOS_PDF_FOLDER']) / filename

    if not pdf_path.exists():
        return jsonify({'error': 'PDF não encontrado'}), 404

    # Nome do arquivo para download (sem o caminho)
    download_name = Path(filename).name

    return send_file(pdf_path, as_attachment=True, download_name=download_name)

@app.route('/api/gabaritos-pdf', methods=['GET'])
def list_gabaritos_pdf():
    """Lista todos os gabaritos PDF gerados (incluindo subpastas)"""
    gabaritos_pdf = []
    gabaritos_pdf_path = Path(app.config['GABARITOS_PDF_FOLDER'])

    # PDFs diretos na pasta principal
    for pdf_file in gabaritos_pdf_path.glob('*.pdf'):
        stat = pdf_file.stat()
        gabaritos_pdf.append({
            'nome': pdf_file.name,
            'caminho_relativo': pdf_file.name,
            'tamanho': round(stat.st_size / 1024, 2),  # KB
            'data_criacao': datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M')
        })

    # PDFs em subpastas (gabaritos personalizados)
    for pdf_file in gabaritos_pdf_path.glob('*/*.pdf'):
        stat = pdf_file.stat()
        caminho_relativo = f"{pdf_file.parent.name}/{pdf_file.name}"
        gabaritos_pdf.append({
            'nome': f"{pdf_file.parent.name}",  # Nome da turma
            'caminho_relativo': caminho_relativo,
            'tamanho': round(stat.st_size / 1024, 2),  # KB
            'data_criacao': datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M')
        })

    # Ordenar por data (mais recentes primeiro)
    gabaritos_pdf.sort(key=lambda x: x['data_criacao'], reverse=True)

    return jsonify(gabaritos_pdf)

@app.route('/api/csv/upload', methods=['POST'])
def upload_csv():
    """Faz upload de CSV e analisa turmas"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Arquivo vazio'}), 400

    if not allowed_csv_file(file.filename):
        return jsonify({'error': 'Apenas arquivos CSV são permitidos'}), 400

    # Salvar arquivo
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['CSV_UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Ler alunos do CSV
        alunos = ler_csv_alunos(filepath)

        # Organizar por turmas
        turmas = listar_turmas(alunos)

        # Preparar resposta
        turmas_info = []
        for turma, alunos_turma in sorted(turmas.items()):
            turmas_info.append({
                'nome': turma,
                'num_alunos': len(alunos_turma)
            })

        return jsonify({
            'success': True,
            'arquivo': filename,
            'total_alunos': len(alunos),
            'total_turmas': len(turmas),
            'turmas': turmas_info
        })

    except Exception as e:
        return jsonify({'error': f'Erro ao processar CSV: {str(e)}'}), 500

@app.route('/api/csv/gerar-gabaritos', methods=['POST'])
def gerar_gabaritos_csv():
    """Gera gabaritos personalizados a partir do CSV"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    # Extrair parâmetros
    csv_filename = data.get('csv_filename', '').strip()
    turmas_selecionadas = data.get('turmas', [])
    titulo = data.get('titulo', 'GABARITO DE PROVA').strip()
    disciplina = data.get('disciplina', '').strip() or None
    professor = data.get('professor', '').strip() or None
    codigo_prova = data.get('codigo_prova', '').strip() or None
    num_questoes = int(data.get('num_questoes', 40))
    alternativas_str = data.get('alternativas', 'A,B,C,D,E').strip()

    # Validações
    if not csv_filename:
        return jsonify({'error': 'Nome do arquivo CSV é obrigatório'}), 400

    if not turmas_selecionadas or len(turmas_selecionadas) == 0:
        return jsonify({'error': 'Selecione pelo menos uma turma'}), 400

    csv_path = Path(app.config['CSV_UPLOAD_FOLDER']) / csv_filename
    if not csv_path.exists():
        return jsonify({'error': 'Arquivo CSV não encontrado'}), 404

    # Processar alternativas
    alternativas = [a.strip().upper() for a in alternativas_str.split(',') if a.strip()]
    if not alternativas:
        alternativas = ['A', 'B', 'C', 'D', 'E']

    try:
        # Ler alunos do CSV
        alunos = ler_csv_alunos(str(csv_path))

        # Organizar por turmas
        turmas = listar_turmas(alunos)

        # Configuração
        config = {
            'titulo': titulo,
            'disciplina': disciplina,
            'professor': professor,
            'codigo_prova': codigo_prova,
            'num_questoes': num_questoes,
            'alternativas': alternativas
        }

        # Pasta de saída
        pasta_saida = app.config['GABARITOS_PDF_FOLDER']

        # Gerar gabaritos para as turmas selecionadas
        total_alunos = 0
        pdfs_gerados = []

        for turma_nome in turmas_selecionadas:
            if turma_nome in turmas:
                alunos_turma = turmas[turma_nome]
                total_alunos += len(alunos_turma)

                # Gerar gabarito para a turma
                gerar_gabaritos_turma(alunos_turma, turma_nome, pasta_saida, config)

                # Nome do PDF gerado
                import re
                nome_pasta_limpo = re.sub(r'[/\\:*?"<>|]', '', turma_nome).strip()
                nome_pasta_limpo = re.sub(r'\s+', '_', nome_pasta_limpo)
                pdf_nome = f"{nome_pasta_limpo}/{nome_pasta_limpo}.pdf"
                pdfs_gerados.append({
                    'turma': turma_nome,
                    'arquivo': pdf_nome,
                    'num_alunos': len(alunos_turma)
                })

        return jsonify({
            'success': True,
            'message': f'Gabaritos gerados com sucesso para {len(turmas_selecionadas)} turma(s)!',
            'total_alunos': total_alunos,
            'total_turmas': len(turmas_selecionadas),
            'pdfs': pdfs_gerados
        })

    except Exception as e:
        return jsonify({'error': f'Erro ao gerar gabaritos: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
