"""
Gerador de Gabaritos em PDF
Cria gabaritos de provas para impressão com diversos layouts
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm, cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import qrcode
from io import BytesIO
from PIL import Image
import barcode
from barcode.writer import ImageWriter


class GeradorGabarito:
    """Classe para gerar gabaritos de prova em PDF"""

    def __init__(self, nome_arquivo='gabarito.pdf', tamanho_pagina=A4):
        """
        Inicializa o gerador de gabarito

        Args:
            nome_arquivo: Nome do arquivo PDF a ser gerado
            tamanho_pagina: Tamanho da página (A4 ou letter)
        """
        self.nome_arquivo = nome_arquivo
        self.tamanho_pagina = tamanho_pagina
        self.largura, self.altura = tamanho_pagina
        self.c = canvas.Canvas(nome_arquivo, pagesize=tamanho_pagina)

    def _desenhar_marcadores_ocr(self):
        """Desenha marcadores OCR (perspectiva, calibração, marcas de corte)"""
        # Marcadores nos 4 cantos (perspectiva)
        tamanho = 0.4*cm
        self.c.setLineWidth(2)
        # Top-left
        self.c.rect(0.2*cm, self.altura - 0.6*cm, tamanho, tamanho, fill=0)
        # Top-right
        self.c.rect(self.largura - 0.6*cm, self.altura - 0.6*cm, tamanho, tamanho, fill=0)
        # Bottom-left
        self.c.rect(0.2*cm, 0.2*cm, tamanho, tamanho, fill=0)
        # Bottom-right
        self.c.rect(self.largura - 0.6*cm, 0.2*cm, tamanho, tamanho, fill=0)

        # Marca de calibração (preto, cinza, branco)
        self.c.setLineWidth(1)
        x_cal = 0.5*cm
        y_cal = self.altura - 1.2*cm
        cal_w = 0.8*cm
        cal_h = 0.3*cm

        # Preto
        self.c.setFillColorRGB(0, 0, 0)
        self.c.rect(x_cal, y_cal, cal_w, cal_h, fill=1, stroke=1)

        # Cinza
        self.c.setFillColorRGB(0.5, 0.5, 0.5)
        self.c.rect(x_cal + 1*cm, y_cal, cal_w, cal_h, fill=1, stroke=1)

        # Branco
        self.c.setFillColorRGB(1, 1, 1)
        self.c.rect(x_cal + 2*cm, y_cal, cal_w, cal_h, fill=1, stroke=1)

        # Marcas de corte
        self.c.setLineWidth(1)
        self.c.setStrokeColorRGB(0, 0, 0)

        # Topo
        self.c.line(self.largura/2 - 0.4*cm, self.altura - 0.05*cm, self.largura/2 + 0.4*cm, self.altura - 0.05*cm)
        # Base
        self.c.line(self.largura/2 - 0.4*cm, 0.05*cm, self.largura/2 + 0.4*cm, 0.05*cm)
        # Esquerda
        self.c.line(0.05*cm, self.altura/2 - 0.4*cm, 0.05*cm, self.altura/2 + 0.4*cm)
        # Direita
        self.c.line(self.largura - 0.05*cm, self.altura/2 - 0.4*cm, self.largura - 0.05*cm, self.altura/2 + 0.4*cm)

        self.c.setFillColorRGB(0, 0, 0)  # Reset

    def _desenhar_cabecalho(self, titulo='GABARITO DE PROVA', info_adicional=None, codigo_prova=None, ra_aluno=None):
        """Desenha o cabeçalho do gabarito"""
        # Desenhar marcadores OCR primeiro (background)
        self._desenhar_marcadores_ocr()

        # Código de barras no canto superior direito (com RA do aluno para identificação)
        if ra_aluno:
            # Barcode contém: apenas o RA do Aluno (ex: "000114154807")
            self._adicionar_barcode(ra_aluno, self.largura - 4.5*cm, self.altura - 2.5*cm, 1.5*cm)

        # Título
        self.c.setFont("Helvetica-Bold", 16)
        self.c.drawCentredString(self.largura / 2, self.altura - 2*cm, titulo)

        # Informações adicionais
        if info_adicional:
            self.c.setFont("Helvetica", 10)
            y = self.altura - 2.8*cm
            for info in info_adicional:
                self.c.drawCentredString(self.largura / 2, y, info)
                y -= 0.5*cm

        # Linha separadora
        self.c.line(2*cm, self.altura - 4*cm, self.largura - 2*cm, self.altura - 4*cm)

    def _desenhar_campo_identificacao(self, y_inicial):
        """Desenha os campos para identificação do aluno"""
        self.c.setFont("Helvetica-Bold", 10)
        y = y_inicial

        # Nome
        self.c.drawString(2*cm, y, "Nome:")
        self.c.rect(4*cm, y - 0.3*cm, self.largura - 6*cm, 0.7*cm)

        # Matrícula
        y -= 1.2*cm
        self.c.drawString(2*cm, y, "Matrícula:")
        self.c.rect(4*cm, y - 0.3*cm, 5*cm, 0.7*cm)

        # Turma
        self.c.drawString(10*cm, y, "Turma:")
        self.c.rect(11.5*cm, y - 0.3*cm, 3.2*cm, 0.7*cm)

        # Data
        self.c.drawString(15*cm, y, "Data:")
        self.c.rect(16.2*cm, y - 0.3*cm, self.largura - 18.2*cm, 0.7*cm)

        return y - 1.5*cm

    def _desenhar_marcadores_alinhamento(self, x_inicial, y_inicial, largura_total):
        """
        Desenha marcadores de alinhamento nos cantos para facilitar detecção automática
        e correção de perspectiva
        """
        tamanho = 0.5*cm

        # Marcador superior esquerdo
        self.c.setFillColorRGB(0, 0, 0)
        self.c.rect(x_inicial - 0.3*cm, y_inicial + 0.3*cm, tamanho, tamanho, fill=1, stroke=0)

        # Marcador superior direito
        self.c.rect(x_inicial + largura_total - 0.2*cm, y_inicial + 0.3*cm, tamanho, tamanho, fill=1, stroke=0)

        # Marcador inferior esquerdo (aproximado)
        self.c.rect(x_inicial - 0.3*cm, y_inicial - 14*cm, tamanho, tamanho, fill=1, stroke=0)

        # Marcador inferior direito (aproximado)
        self.c.rect(x_inicial + largura_total - 0.2*cm, y_inicial - 14*cm, tamanho, tamanho, fill=1, stroke=0)

        self.c.setFillColorRGB(0, 0, 0)  # Reset

    def _desenhar_orientacoes(self, y_inicial):
        """Desenha um quadro com orientações para preenchimento em 2 colunas"""
        x_esq = 1.5*cm
        x_dir = self.largura - 1.5*cm
        altura_quadro = 1.8*cm
        y_topo = y_inicial
        y_base = y_inicial - altura_quadro

        # Desenhar quadro
        self.c.setLineWidth(1.5)
        self.c.rect(x_esq, y_base, x_dir - x_esq, altura_quadro, fill=0)

        # Título
        self.c.setFont("Helvetica-Bold", 10)
        self.c.drawString(x_esq + 0.3*cm, y_topo - 0.35*cm, "ORIENTAÇÕES PARA PREENCHIMENTO:")

        # Orientações em 2 colunas
        self.c.setFont("Helvetica", 7.5)

        # Coluna esquerda
        col1_x = x_esq + 0.3*cm
        y_col = y_topo - 0.7*cm
        self.c.drawString(col1_x, y_col, "• Use somente caneta preta")
        self.c.drawString(col1_x, y_col - 0.35*cm, "• Preencha completamente o círculo")
        self.c.drawString(col1_x, y_col - 0.7*cm, "• Não deixe rasuras ou borrões")

        # Coluna direita
        col2_x = x_esq + 10*cm
        self.c.drawString(col2_x, y_col, "• Marque uma única resposta")
        self.c.drawString(col2_x, y_col - 0.35*cm, "• Não dobre ou amasse o documento")
        self.c.drawString(col2_x, y_col - 0.7*cm, "• Verifique suas respostas antes de entregar")

        return y_base - 0.5*cm  # Retorna a posição Y para as próximas questões

    def _desenhar_questoes_multipla_escolha(self, num_questoes, alternativas, y_inicial,
                                           colunas=2, tamanho_circulo=0.3*cm):
        """
        Desenha as questões de múltipla escolha com instruções

        Args:
            num_questoes: Número total de questões
            alternativas: Lista de alternativas (ex: ['A', 'B', 'C', 'D', 'E'])
        """
        # Instruções
        self.c.setFont("Helvetica-Bold", 10)
        self.c.drawCentredString(self.largura / 2, y_inicial, "RESPOSTAS - Preencha completamente o círculo")

        # Linha separadora
        self.c.setLineWidth(0.5)
        self.c.line(2*cm, y_inicial - 0.3*cm, self.largura - 2*cm, y_inicial - 0.3*cm)

        y_inicial -= 1*cm
        y = y_inicial
        questoes_por_coluna = (num_questoes + colunas - 1) // colunas

        # Calcular largura de cada questão (número + alternativas)
        num_alternativas = len(alternativas)
        largura_questao = 1.3*cm + (num_alternativas * 1.3*cm) + 0.5*cm  # número + círculos + margem

        # Calcular largura total necessária
        largura_total_questoes = colunas * largura_questao + (colunas - 1) * 2.5*cm  # espaço entre colunas

        # Centralizar horizontalmente
        margem_lateral = (self.largura - largura_total_questoes) / 2

        # Desenhar marcadores de alinhamento nos cantos (para detecção automática)
        self._desenhar_marcadores_alinhamento(margem_lateral, y, largura_total_questoes)

        for col in range(colunas):
            x_base = margem_lateral + col * (largura_questao + 2.5*cm)
            questao_inicial = col * questoes_por_coluna + 1
            questao_final = min((col + 1) * questoes_por_coluna, num_questoes)

            y_temp = y

            for q in range(questao_inicial, questao_final + 1):
                # Número da questão
                self.c.setFont("Helvetica-Bold", 9)
                self.c.drawString(x_base, y_temp, f"{q:02d}.")

                # Alternativas
                x_alt = x_base + 1.3*cm
                for alt in alternativas:
                    # Círculo com borda mais grossa para melhor detecção
                    self.c.setLineWidth(1.5)  # Borda mais grossa
                    self.c.circle(x_alt, y_temp + 0.2*cm, tamanho_circulo,
                                stroke=1, fill=0)
                    self.c.setLineWidth(1)  # Resetar para normal

                    # Letra
                    self.c.setFont("Helvetica", 7)
                    self.c.drawCentredString(x_alt, y_temp + 0.1*cm, alt)
                    x_alt += 1.3*cm  # Espaçamento entre círculos

                y_temp -= 0.7*cm  # Espaçamento entre linhas

                # Verificar se precisa de nova página
                if y_temp < 3*cm and q < questao_final:
                    self.c.showPage()
                    self._desenhar_cabecalho(titulo='GABARITO DE PROVA (continuação)')
                    y_temp = self.altura - 5*cm

        return y_temp

    def _desenhar_questoes_verdadeiro_falso(self, num_questoes, y_inicial, colunas=2):
        """Desenha questões de verdadeiro ou falso"""
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(2*cm, y_inicial, "VERDADEIRO (V) ou FALSO (F)")

        y = y_inicial - 1*cm
        questoes_por_coluna = (num_questoes + colunas - 1) // colunas
        largura_coluna = (self.largura - 4*cm) / colunas

        for col in range(colunas):
            x_base = 2*cm + col * largura_coluna
            questao_inicial = col * questoes_por_coluna + 1
            questao_final = min((col + 1) * questoes_por_coluna, num_questoes)

            y_temp = y

            for q in range(questao_inicial, questao_final + 1):
                self.c.setFont("Helvetica-Bold", 9)
                self.c.drawString(x_base, y_temp, f"{q:02d}.")

                # V
                x_v = x_base + 1*cm
                self.c.circle(x_v, y_temp + 0.15*cm, 0.4*cm, stroke=1, fill=0)
                self.c.setFont("Helvetica", 8)
                self.c.drawCentredString(x_v, y_temp, "V")

                # F
                x_f = x_base + 2.2*cm
                self.c.circle(x_f, y_temp + 0.15*cm, 0.4*cm, stroke=1, fill=0)
                self.c.drawCentredString(x_f, y_temp, "F")

                y_temp -= 0.7*cm

        return y_temp

    def _adicionar_qrcode(self, dados, x, y, tamanho=2*cm):
        """Adiciona um QR Code ao gabarito"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(dados)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Converter para formato que o ReportLab aceita
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            # Criar objeto ImageReader do ReportLab
            from reportlab.lib.utils import ImageReader
            img_reader = ImageReader(buffer)

            self.c.drawImage(img_reader, x, y, width=tamanho, height=tamanho)
        except Exception as e:
            # Se falhar, apenas não adiciona o QR code
            print(f"Aviso: Não foi possível adicionar QR code: {e}")

    def _adicionar_barcode(self, dados, x, y, altura=1.2*cm):
        """Adiciona um código de barras (Code128) ao gabarito como backup"""
        try:
            import tempfile
            import os as os_module

            # Gerar código de barras (usar apenas números e caracteres válidos)
            dados_barcode = str(dados).replace("|", "").replace(" ", "")[:20]  # Limitar a 20 caracteres

            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # Gerar barcode com alta resolução (300 DPI)
                writer = ImageWriter()
                writer.dpi = 300  # Alta resolução
                barcode_instance = barcode.get_barcode('code128', dados_barcode, writer=writer)
                save_path = tmp_path.replace('.png', '')
                barcode_instance.save(save_path)

                # O arquivo real tem a extensão .png adicionada
                png_path = save_path + '.png'

                if os_module.path.exists(png_path):
                    # Carregar a imagem
                    from reportlab.lib.utils import ImageReader
                    img_reader = ImageReader(png_path)

                    # Desenhar o código de barras
                    self.c.drawImage(img_reader, x, y, width=4*cm, height=altura)

                    # Limpar arquivo PNG
                    os_module.remove(png_path)
            except Exception as e:
                pass
        except Exception as e:
            # Se falhar, apenas não adiciona o código de barras
            pass

    def _desenhar_rodape(self, nome_aluno=None, codigo_prova=None, ra_aluno=None):
        """Desenha o rodapé do gabarito com QR Code, assinatura e nome do aluno"""
        # QR Code (lado esquerdo) - contém apenas o RA do aluno
        if ra_aluno:
            self._adicionar_qrcode(ra_aluno, 0.8*cm, 0.8*cm, 1.5*cm)

        # Campo de assinatura (centro/direita)
        x_assinatura = self.largura - 8*cm
        y_assinatura = 2.0*cm

        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(x_assinatura, y_assinatura + 1.2*cm, "Assinatura do Aluno:")

        # Linha para assinatura (abaixo do texto)
        self.c.line(x_assinatura, y_assinatura, x_assinatura + 6*cm, y_assinatura)

        # Nome do aluno abaixo da linha de assinatura (com espaço maior)
        if nome_aluno:
            self.c.setFont("Helvetica", 7)
            self.c.drawCentredString(x_assinatura + 3*cm, y_assinatura - 0.8*cm, nome_aluno.upper())

        # Data de geração (centro inferior)
        self.c.setFont("Helvetica", 7)
        self.c.drawCentredString(self.largura / 2, 0.5*cm,
                         f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    def gerar_gabarito_padrao(self, num_questoes=30, alternativas=['A', 'B', 'C', 'D', 'E'],
                             titulo='GABARITO DE PROVA', disciplina=None, professor=None,
                             codigo_prova=None):
        """
        Gera um gabarito padrão com múltipla escolha

        Args:
            num_questoes: Número de questões
            alternativas: Lista de alternativas
            titulo: Título do gabarito
            disciplina: Nome da disciplina
            professor: Nome do professor
            codigo_prova: Código identificador da prova
        """
        # Informações adicionais
        info_adicional = []
        if disciplina:
            info_adicional.append(f"Disciplina: {disciplina}")
        if professor:
            info_adicional.append(f"Professor(a): {professor}")
        if codigo_prova:
            info_adicional.append(f"Código: {codigo_prova}")

        # Cabeçalho
        self._desenhar_cabecalho(titulo, info_adicional if info_adicional else None, codigo_prova)

        # Campos de identificação
        y = self._desenhar_campo_identificacao(self.altura - 5*cm)

        # QR Code (se houver código da prova)
        if codigo_prova:
            self._adicionar_qrcode(codigo_prova, self.largura - 4*cm, self.altura - 9*cm, 2*cm)

        # Questões
        self._desenhar_questoes_multipla_escolha(num_questoes, alternativas, y - 1*cm)

        # Rodapé
        self._desenhar_rodape()

        # Salvar
        self.c.save()
        print(f"Gabarito gerado com sucesso: {self.nome_arquivo}")

    def gerar_gabarito_personalizado(self, configuracao):
        """
        Gera um gabarito com configuração personalizada

        Args:
            configuracao: Dicionário com as configurações
                {
                    'titulo': str,
                    'info_adicional': list,
                    'secoes': [
                        {
                            'tipo': 'multipla_escolha' ou 'verdadeiro_falso',
                            'num_questoes': int,
                            'alternativas': list (opcional),
                            'colunas': int (opcional)
                        }
                    ],
                    'codigo_prova': str (opcional)
                }
        """
        # Cabeçalho
        self._desenhar_cabecalho(
            configuracao.get('titulo', 'GABARITO DE PROVA'),
            configuracao.get('info_adicional'),
            configuracao.get('codigo_prova')
        )

        # Campos de identificação
        y = self._desenhar_campo_identificacao(self.altura - 5*cm)

        # QR Code
        if configuracao.get('codigo_prova'):
            self._adicionar_qrcode(
                configuracao['codigo_prova'],
                self.largura - 4*cm,
                self.altura - 9*cm,
                2*cm
            )

        # Processar seções
        y -= 1.5*cm
        for secao in configuracao.get('secoes', []):
            tipo = secao.get('tipo', 'multipla_escolha')
            num_questoes = secao.get('num_questoes', 10)

            if tipo == 'multipla_escolha':
                alternativas = secao.get('alternativas', ['A', 'B', 'C', 'D', 'E'])
                colunas = secao.get('colunas', 2)
                y = self._desenhar_questoes_multipla_escolha(
                    num_questoes, alternativas, y, colunas
                )
            elif tipo == 'verdadeiro_falso':
                colunas = secao.get('colunas', 2)
                y = self._desenhar_questoes_verdadeiro_falso(num_questoes, y, colunas)

            y -= 1*cm

        # Rodapé
        self._desenhar_rodape()

        # Salvar
        self.c.save()
        print(f"Gabarito personalizado gerado: {self.nome_arquivo}")


if __name__ == '__main__':
    # Exemplo de uso
    gerador = GeradorGabarito('exemplo_gabarito.pdf')
    gerador.gerar_gabarito_padrao(
        num_questoes=40,
        alternativas=['A', 'B', 'C', 'D', 'E'],
        titulo='PROVA DE MATEMÁTICA',
        disciplina='Matemática Avançada',
        professor='Prof. João Silva',
        codigo_prova='MAT2024-P1'
    )
