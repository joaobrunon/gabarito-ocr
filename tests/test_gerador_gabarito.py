"""
Testes unitários para o módulo gerador_gabarito.py
"""
import pytest
import os
from gerador_gabarito import GeradorGabarito


class TestGeradorGabarito:
    """Testes para a classe GeradorGabarito"""

    def test_criar_instancia(self):
        """Testa criação de instância do gerador"""
        gerador = GeradorGabarito()
        assert gerador is not None
        assert hasattr(gerador, 'gerar_gabarito_padrao')
        assert hasattr(gerador, 'gerar_gabarito_personalizado')

    def test_gerar_gabarito_padrao_10_questoes(self, temp_dir):
        """Testa geração de gabarito padrão com 10 questões"""
        gerador = GeradorGabarito()
        arquivo_saida = os.path.join(temp_dir, "gabarito_10q.pdf")

        gerador.gerar_gabarito_padrao(
            num_questoes=10,
            num_alternativas=5,
            arquivo_saida=arquivo_saida
        )

        assert os.path.exists(arquivo_saida)
        assert os.path.getsize(arquivo_saida) > 0

    def test_gerar_gabarito_padrao_50_questoes(self, temp_dir):
        """Testa geração de gabarito com 50 questões"""
        gerador = GeradorGabarito()
        arquivo_saida = os.path.join(temp_dir, "gabarito_50q.pdf")

        gerador.gerar_gabarito_padrao(
            num_questoes=50,
            num_alternativas=4,
            arquivo_saida=arquivo_saida
        )

        assert os.path.exists(arquivo_saida)
        assert os.path.getsize(arquivo_saida) > 0

    def test_gerar_gabarito_com_4_alternativas(self, temp_dir):
        """Testa geração de gabarito com 4 alternativas (A-D)"""
        gerador = GeradorGabarito()
        arquivo_saida = os.path.join(temp_dir, "gabarito_4alt.pdf")

        gerador.gerar_gabarito_padrao(
            num_questoes=20,
            num_alternativas=4,
            arquivo_saida=arquivo_saida
        )

        assert os.path.exists(arquivo_saida)
        assert os.path.getsize(arquivo_saida) > 0

    def test_gerar_gabarito_com_qrcode(self, temp_dir):
        """Testa geração de gabarito com QR code"""
        gerador = GeradorGabarito()
        arquivo_saida = os.path.join(temp_dir, "gabarito_qr.pdf")

        gerador.gerar_gabarito_padrao(
            num_questoes=10,
            num_alternativas=5,
            arquivo_saida=arquivo_saida,
            incluir_qrcode=True
        )

        assert os.path.exists(arquivo_saida)
        assert os.path.getsize(arquivo_saida) > 0

    def test_gerar_gabarito_personalizado(self, temp_dir):
        """Testa geração de gabarito personalizado com seções mistas"""
        gerador = GeradorGabarito()
        arquivo_saida = os.path.join(temp_dir, "gabarito_personalizado.pdf")

        secoes = [
            {
                'tipo': 'multipla_escolha',
                'num_questoes': 15,
                'num_alternativas': 5,
                'titulo': 'Múltipla Escolha'
            },
            {
                'tipo': 'verdadeiro_falso',
                'num_questoes': 10,
                'titulo': 'Verdadeiro ou Falso'
            }
        ]

        gerador.gerar_gabarito_personalizado(
            secoes=secoes,
            arquivo_saida=arquivo_saida
        )

        assert os.path.exists(arquivo_saida)
        assert os.path.getsize(arquivo_saida) > 0

    def test_gerar_gabarito_uma_questao_minimo(self, temp_dir):
        """Testa geração de gabarito com apenas 1 questão (mínimo)"""
        gerador = GeradorGabarito()
        arquivo_saida = os.path.join(temp_dir, "gabarito_1q.pdf")

        gerador.gerar_gabarito_padrao(
            num_questoes=1,
            num_alternativas=5,
            arquivo_saida=arquivo_saida
        )

        assert os.path.exists(arquivo_saida)
        assert os.path.getsize(arquivo_saida) > 0

    def test_gerar_gabarito_100_questoes(self, temp_dir):
        """Testa geração de gabarito com 100 questões"""
        gerador = GeradorGabarito()
        arquivo_saida = os.path.join(temp_dir, "gabarito_100q.pdf")

        gerador.gerar_gabarito_padrao(
            num_questoes=100,
            num_alternativas=5,
            arquivo_saida=arquivo_saida
        )

        assert os.path.exists(arquivo_saida)
        assert os.path.getsize(arquivo_saida) > 0

    def test_gerar_gabarito_multiplas_colunas(self, temp_dir):
        """Testa geração de gabarito com múltiplas colunas"""
        gerador = GeradorGabarito()
        arquivo_saida = os.path.join(temp_dir, "gabarito_colunas.pdf")

        gerador.gerar_gabarito_padrao(
            num_questoes=40,
            num_alternativas=5,
            arquivo_saida=arquivo_saida,
            num_colunas=2
        )

        assert os.path.exists(arquivo_saida)
        assert os.path.getsize(arquivo_saida) > 0

    def test_arquivo_saida_path_invalido(self):
        """Testa comportamento com path de saída inválido"""
        gerador = GeradorGabarito()

        with pytest.raises(Exception):
            gerador.gerar_gabarito_padrao(
                num_questoes=10,
                num_alternativas=5,
                arquivo_saida="/diretorio/inexistente/gabarito.pdf"
            )

    def test_numero_questoes_invalido_zero(self):
        """Testa comportamento com número de questões zero"""
        gerador = GeradorGabarito()

        with pytest.raises((ValueError, Exception)):
            gerador.gerar_gabarito_padrao(
                num_questoes=0,
                num_alternativas=5,
                arquivo_saida="test.pdf"
            )

    def test_numero_questoes_invalido_negativo(self):
        """Testa comportamento com número de questões negativo"""
        gerador = GeradorGabarito()

        with pytest.raises((ValueError, Exception)):
            gerador.gerar_gabarito_padrao(
                num_questoes=-5,
                num_alternativas=5,
                arquivo_saida="test.pdf"
            )

    def test_numero_alternativas_invalido(self):
        """Testa comportamento com número de alternativas inválido"""
        gerador = GeradorGabarito()

        with pytest.raises((ValueError, Exception)):
            gerador.gerar_gabarito_padrao(
                num_questoes=10,
                num_alternativas=1,  # Mínimo deveria ser 2
                arquivo_saida="test.pdf"
            )
