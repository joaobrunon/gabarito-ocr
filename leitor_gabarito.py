"""
Leitor Final v2 - Adaptativo e Resiliente
Funciona com PDFs impressos de qualidade variável
"""

import cv2
import numpy as np
from typing import Dict, Optional, Tuple
import json


class LeitorFinalV2:
    """Leitor adaptativo com detecção resiliente"""

    def __init__(self, num_questoes: int = 40, alternativas: list = None):
        self.num_questoes = num_questoes
        self.alternativas = alternativas or ['A', 'B', 'C', 'D', 'E']
        self.debug = False

    def ler_gabarito(self, caminho_imagem: str, debug: bool = False) -> Dict:
        """Lê gabarito com adaptação automática"""

        self.debug = debug

        # Carregar
        imagem = cv2.imread(caminho_imagem)
        if imagem is None:
            raise ValueError(f"Erro: {caminho_imagem}")

        cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

        # Preprocessar
        processada = self._preprocessar_adaptativo(cinza)

        # Detectar círculos
        circulos = self._detectar_circulos_robusto(processada)
        if circulos is None:
            return {}

        # Organizar
        grade = self._organizar_grade(circulos)

        # Detectar respostas com múltiplos métodos
        respostas = self._detectar_com_ensemble(cinza, circulos, grade)

        return respostas

    def _preprocessar_adaptativo(self, cinza: np.ndarray) -> np.ndarray:
        """Preprocessamento adaptativo baseado na imagem"""

        # 1. CLAHE adaptativo
        media = np.mean(cinza)
        if media < 100:
            # Imagem muito escura
            clip_limit = 3.0
        elif media > 200:
            # Imagem muito clara
            clip_limit = 1.0
        else:
            clip_limit = 2.0

        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        cinza = clahe.apply(cinza)

        # 2. Bilateral filter
        cinza = cv2.bilateralFilter(cinza, 9, 75, 75)

        # 3. Normalizar
        cinza = cv2.normalize(cinza, None, 0, 255, cv2.NORM_MINMAX)

        return cinza

    def _detectar_circulos_robusto(self, imagem: np.ndarray) -> Optional[np.ndarray]:
        """Detecção robusta com múltiplas tentativas"""

        # Blur
        blur = cv2.GaussianBlur(imagem, (5, 5), 1.5)

        # Parâmetros múltiplos
        configs = [
            {'minDist': 19, 'param1': 45, 'param2': 28, 'minRadius': 8, 'maxRadius': 21},
            {'minDist': 20, 'param1': 40, 'param2': 25, 'minRadius': 8, 'maxRadius': 22},
            {'minDist': 21, 'param1': 35, 'param2': 20, 'minRadius': 7, 'maxRadius': 23},
            {'minDist': 18, 'param1': 50, 'param2': 30, 'minRadius': 9, 'maxRadius': 20},
        ]

        melhores_circulos = None
        max_count = 0

        for config in configs:
            circ = cv2.HoughCircles(
                blur,
                cv2.HOUGH_GRADIENT,
                dp=1,
                **config
            )

            if circ is not None and len(circ[0]) > max_count:
                melhores_circulos = circ
                max_count = len(circ[0])

        return melhores_circulos

    def _organizar_grade(self, circulos: np.ndarray) -> Dict:
        """Organiza em grade com robustez"""

        circ_lista = [(int(x), int(y), int(r)) for x, y, r in circulos[0]]

        # Agrupar por Y com melhor agrupamento
        linhas = {}
        circ_lista_sorted = sorted(circ_lista, key=lambda c: c[1])

        for x, y, r in circ_lista_sorted:
            encontrado = False
            # Procurar linha mais próxima
            min_dist = float('inf')
            melhor_y = None

            for y_g in linhas:
                dist = abs(y - y_g)
                if dist < 22 and dist < min_dist:
                    min_dist = dist
                    melhor_y = y_g
                    encontrado = True

            if encontrado:
                linhas[melhor_y].append((x, y, r))
            else:
                linhas[y] = [(x, y, r)]

        # Ordenar por X e limpar duplicatas
        for y_g in linhas:
            # Remover duplicatas (círculos muito próximos)
            linhas[y_g] = sorted(set((c[0], c[1], c[2]) for c in linhas[y_g]), key=lambda c: c[0])

        return linhas

    def _detectar_com_ensemble(self, cinza: np.ndarray, circulos: np.ndarray,
                               linhas: Dict) -> Dict:
        """Detecta usando votação de múltiplos métodos"""

        # Preparar versões diferentes
        _, binaria = cv2.threshold(cinza, 127, 255, cv2.THRESH_BINARY)
        cinza_inv = 255 - cinza

        respostas = {}
        linhas_ord = sorted(linhas.items())

        # Filtrar linhas válidas (devem ter ~10 círculos para questões)
        linhas_validas = [(y_g, cl) for y_g, cl in linhas_ord if len(cl) >= 10]

        for idx_l, (y_g, circ_linha) in enumerate(linhas_validas):
            if idx_l >= 20:
                break

            # Esquerda
            if len(circ_linha) >= 5:
                q_esq = idx_l + 1
                grupo_esq = circ_linha[:5]

                resposta = self._ensemble_deteccao(cinza, binaria, cinza_inv, grupo_esq)
                if resposta:
                    respostas[str(q_esq)] = resposta

            # Direita - detectar gap
            if len(circ_linha) >= 10:
                x_coords = [c[0] for c in circ_linha]
                diffs = [x_coords[i+1] - x_coords[i] for i in range(len(x_coords)-1)]

                if diffs:
                    gap_idx = diffs.index(max(diffs))
                    grupo_dir = circ_linha[gap_idx+1:gap_idx+6]
                else:
                    grupo_dir = circ_linha[5:10]

                q_dir = idx_l + 21
                if len(grupo_dir) >= 5:
                    resposta = self._ensemble_deteccao(cinza, binaria, cinza_inv, grupo_dir[:5])
                    if resposta:
                        respostas[str(q_dir)] = resposta

        return respostas

    def _ensemble_deteccao(self, cinza: np.ndarray, binaria: np.ndarray,
                          cinza_inv: np.ndarray, circulos_alt: list) -> Optional[str]:
        """Votação de múltiplos métodos para detectar resposta"""

        votos = {alt: [] for alt in self.alternativas}

        for idx, (x, y, r) in enumerate(circulos_alt):
            # ROI
            y1, y2 = max(0, y - r - 2), min(cinza.shape[0], y + r + 2)
            x1, x2 = max(0, x - r - 2), min(cinza.shape[1], x + r + 2)

            roi_c = cinza[y1:y2, x1:x2]
            roi_b = binaria[y1:y2, x1:x2]
            roi_ci = cinza_inv[y1:y2, x1:x2]

            if roi_c.size == 0:
                continue

            alt = self.alternativas[idx]

            # Método 1: Pixels escuros em cinza (ajustado)
            m1 = np.sum(roi_c < 115) / roi_c.size

            # Método 2: Pixels pretos em binária
            m2 = np.sum(roi_b == 0) / roi_b.size

            # Método 3: Pixels claros em invertida
            m3 = np.sum(roi_ci > 140) / roi_ci.size

            # Método 4: Desvio padrão (marcações têm mais variação)
            m4 = min(np.std(roi_c) / 35, 1.0)

            # Método 5: Média de intensidade
            m5 = 1.0 - (np.mean(roi_c) / 255.0)

            # Score final - pesos ajustados
            score = (m1 * 0.30 + m2 * 0.30 + m3 * 0.20 + m4 * 0.10 + m5 * 0.10)

            votos[alt].append(score)

        # Calcular score médio
        scores_finais = {}
        for alt, scores in votos.items():
            if scores:
                scores_finais[alt] = np.mean(scores)
            else:
                scores_finais[alt] = 0.0

        if not scores_finais or max(scores_finais.values()) < 0.10:
            return None

        # Melhor alternativa
        melhor = max(scores_finais, key=scores_finais.get)
        melhor_score = scores_finais[melhor]

        # Validar ambiguidade
        scores_ord = sorted(scores_finais.values(), reverse=True)
        if len(scores_ord) > 1:
            diferenca = scores_ord[0] - scores_ord[1]
            if diferenca < 0.06:  # Threshold mais relaxado
                return None

        return melhor


if __name__ == '__main__':
    leitor = LeitorFinalV2()
    respostas = leitor.ler_gabarito('/home/proatec/gabarito/temp_images/pagina_001.png')

    print("\n" + "="*60)
    print("RESPOSTAS - LEITOR FINAL V2:")
    print("="*60)

    for q in sorted([int(k) for k in respostas.keys()]):
        print(f"Q{q:02d}: {respostas[str(q)]}")

    print(f"\nTotal: {len(respostas)}/40")

    with open('/home/proatec/gabarito/respostas_v2.json', 'w') as f:
        json.dump(respostas, f)
