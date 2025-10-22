"""
Configurações e fixtures compartilhadas para os testes
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Cria um diretório temporário para testes"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_gabarito_dict():
    """Gabarito oficial de exemplo como dicionário"""
    return {
        "1": "A",
        "2": "B",
        "3": "C",
        "4": "D",
        "5": "E",
        "6": "A",
        "7": "B",
        "8": "C",
        "9": "D",
        "10": "E"
    }


@pytest.fixture
def sample_gabarito_json(temp_dir, sample_gabarito_dict):
    """Cria arquivo JSON com gabarito oficial"""
    import json
    file_path = os.path.join(temp_dir, "gabarito_oficial.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(sample_gabarito_dict, f, indent=2)
    return file_path


@pytest.fixture
def sample_gabarito_csv(temp_dir, sample_gabarito_dict):
    """Cria arquivo CSV com gabarito oficial"""
    file_path = os.path.join(temp_dir, "gabarito_oficial.csv")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("Questao,Resposta\n")
        for questao, resposta in sample_gabarito_dict.items():
            f.write(f"{questao},{resposta}\n")
    return file_path


@pytest.fixture
def sample_gabarito_txt(temp_dir, sample_gabarito_dict):
    """Cria arquivo TXT com gabarito oficial"""
    file_path = os.path.join(temp_dir, "gabarito_oficial.txt")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("# Gabarito Oficial\n")
        f.write("# Formato: questao: resposta\n\n")
        for questao, resposta in sample_gabarito_dict.items():
            f.write(f"{questao}: {resposta}\n")
    return file_path


@pytest.fixture
def sample_student_answers():
    """Respostas de exemplo de um aluno"""
    return {
        "identificacao": {
            "nome": "João Silva",
            "matricula": "12345",
            "turma": "3A"
        },
        "respostas": {
            "1": "A",  # Correto
            "2": "B",  # Correto
            "3": "C",  # Correto
            "4": "A",  # Errado
            "5": "E",  # Correto
            "6": "A",  # Correto
            "7": "B",  # Correto
            "8": "C",  # Correto
            "9": "D",  # Correto
            "10": ""   # Em branco
        }
    }


@pytest.fixture
def sample_students_csv(temp_dir):
    """Cria arquivo CSV com respostas de múltiplos alunos"""
    file_path = os.path.join(temp_dir, "respostas_alunos.csv")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("nome,matricula,turma,q1,q2,q3,q4,q5,q6,q7,q8,q9,q10\n")
        f.write("João Silva,12345,3A,A,B,C,A,E,A,B,C,D,\n")
        f.write("Maria Santos,12346,3A,A,B,C,D,E,A,B,C,D,E\n")
        f.write("Pedro Costa,12347,3A,B,C,D,E,A,B,C,D,E,A\n")
    return file_path


@pytest.fixture
def sample_students_json(temp_dir):
    """Cria arquivo JSON com respostas de múltiplos alunos"""
    import json
    file_path = os.path.join(temp_dir, "respostas_alunos.json")
    students = [
        {
            "identificacao": {
                "nome": "João Silva",
                "matricula": "12345",
                "turma": "3A"
            },
            "respostas": {
                "1": "A", "2": "B", "3": "C", "4": "A", "5": "E",
                "6": "A", "7": "B", "8": "C", "9": "D", "10": ""
            }
        },
        {
            "identificacao": {
                "nome": "Maria Santos",
                "matricula": "12346",
                "turma": "3A"
            },
            "respostas": {
                "1": "A", "2": "B", "3": "C", "4": "D", "5": "E",
                "6": "A", "7": "B", "8": "C", "9": "D", "10": "E"
            }
        }
    ]
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(students, f, indent=2)
    return file_path
