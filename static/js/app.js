// Elementos do DOM
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadStatus = document.getElementById('uploadStatus');
const reportsList = document.getElementById('reportsList');
const reportModal = document.getElementById('reportModal');
const modalClose = document.querySelector('.modal-close');
const reportContent = document.getElementById('reportContent');

// Event Listeners para Tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.getAttribute('data-tab');
        switchTab(tabName);
    });
});

// Event Listeners para Upload
uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

// Modal
modalClose.addEventListener('click', () => {
    reportModal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === reportModal) {
        reportModal.style.display = 'none';
    }
});

// Funções
async function handleFiles(files) {
    if (!files || files.length === 0) return;

    // Verificar se um gabarito está selecionado
    const gabaritoSelect = document.getElementById('gabaritoSelect');
    const gabaritoSelecionado = gabaritoSelect.value;

    if (!gabaritoSelecionado) {
        showStatus('✗ Selecione um gabarito antes de fazer o upload', 'error');
        return;
    }

    // Filtrar apenas PDFs
    const pdfFiles = Array.from(files).filter(file => file.type === 'application/pdf');

    if (pdfFiles.length === 0) {
        showStatus('✗ Nenhum arquivo PDF válido selecionado', 'error');
        return;
    }

    if (pdfFiles.length !== files.length) {
        showStatus(`⚠️ ${files.length - pdfFiles.length} arquivo(s) ignorado(s) (apenas PDFs são aceitos)`, 'error');
        await sleep(2000);
    }

    // Processar múltiplos arquivos
    await processarMultiplosArquivos(pdfFiles, gabaritoSelecionado);
}

async function processarMultiplosArquivos(files, gabarito) {
    const total = files.length;
    let sucessos = 0;
    let erros = 0;

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const atual = i + 1;

        showStatus(`⏳ Corrigindo ${atual}/${total}: ${file.name}...`, 'loading');
        addLog(`⏳ Corrigindo ${atual}/${total}: ${file.name}...`, 'loading');

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('gabarito', gabarito);

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            let data;
            try {
                data = await response.json();
            } catch (e) {
                // Se não conseguir fazer parse do JSON, capturar o texto
                const text = await response.text();
                data = { error: `Erro no servidor (${response.status})` };
                console.error('Resposta não-JSON:', text);
            }

            if (response.ok) {
                sucessos++;
                const msg = `✅ ${file.name} - Corrigido! (${data.report.acertos}/${data.report.total} - Nota: ${data.report.nota.toFixed(1)})`;
                showStatus(msg, 'success');
                addLog(msg, 'success');
            } else {
                erros++;
                const msg = `✗ ${file.name} - ${data.error}`;
                showStatus(msg, 'error');
                addLog(msg, 'error');
            }
        } catch (error) {
            erros++;
            const msg = `✗ ${file.name} - Erro: ${error.message}`;
            showStatus(msg, 'error');
            addLog(msg, 'error');
            console.error('Erro no upload:', error);
        }

        // Pequena pausa entre arquivos para mostrar o status
        await sleep(500);
    }

    // Mostrar resumo final
    if (erros === 0) {
        const msg = `✅ Todos os ${total} PDFs foram corrigidos com sucesso!`;
        showStatus(msg, 'success');
        addLog(msg, 'success');
    } else {
        const msg = `📊 Resumo: ${sucessos} corrigidos, ${erros} com erro (total: ${total})`;
        showStatus(msg, erros > sucessos ? 'error' : 'success');
        addLog(msg, erros > sucessos ? 'error' : 'success');
    }

    // Limpar input e recarregar dados
    fileInput.value = '';
    setTimeout(() => {
        uploadStatus.style.display = 'none';
        loadReports();
        loadStats();
    }, 3000);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = `upload-status ${type}`;
    uploadStatus.style.display = 'block';
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('totalReports').textContent = stats.total_relatorios;
        document.getElementById('avgGrade').textContent = stats.media_nota.toFixed(2);
        document.getElementById('maxGrade').textContent = stats.maior_nota.toFixed(1);
        document.getElementById('minGrade').textContent = stats.menor_nota.toFixed(1);
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

async function viewReport(jsonFile, htmlFile) {
    try {
        // Carregar JSON para mostrar dados detalhados
        const jsonResponse = await fetch(`/api/report/${jsonFile}`);
        const reportData = await jsonResponse.json();

        // Carregar gabarito oficial para comparar
        const gabaritoResponse = await fetch('/api/gabarito/atual');
        const gabaritoOficial = await gabaritoResponse.json();

        // Criar visualização detalhada
        let html = `
            <div style="padding: 20px;">
                <h2 style="margin: 0 0 10px 0; color: #2c3e50;">📋 Relatório Detalhado</h2>

                <!-- Informações do Aluno -->
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <p style="margin: 5px 0;"><strong>Nome:</strong> ${reportData.identificacao.nome}</p>
                    <p style="margin: 5px 0;"><strong>RA:</strong> ${reportData.identificacao.matricula}</p>
                    <p style="margin: 5px 0;"><strong>Turma:</strong> ${reportData.identificacao.turma}</p>
                    <p style="margin: 5px 0;"><strong>Data:</strong> ${reportData.data_correcao}</p>
                </div>

                <!-- Resumo da Prova -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div style="background: #d4edda; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 28px; font-weight: bold; color: #155724;">${reportData.acertos}</div>
                        <div style="color: #155724; font-size: 14px;">Acertos</div>
                    </div>
                    <div style="background: #f8d7da; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 28px; font-weight: bold; color: #721c24;">${reportData.erros}</div>
                        <div style="color: #721c24; font-size: 14px;">Erros</div>
                    </div>
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 28px; font-weight: bold; color: #856404;">${reportData.em_branco}</div>
                        <div style="color: #856404; font-size: 14px;">Em Branco</div>
                    </div>
                    <div style="background: #d1ecf1; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 28px; font-weight: bold; color: #0c5460;">${reportData.nota.toFixed(1)}/10</div>
                        <div style="color: #0c5460; font-size: 14px;">Nota Final</div>
                    </div>
                </div>

                <!-- Detalhamento das Questões -->
                <h3 style="margin: 20px 0 15px 0; color: #2c3e50;">📝 Questões Detalhadas</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(60px, 1fr)); gap: 8px;">
        `;

        // Criar uma visualização para cada questão
        for (let q = 1; q <= reportData.total_questoes; q++) {
            const respostaAluno = reportData.respostas_completas[q.toString()] || '-';
            const respostaGabarito = gabaritoOficial[q.toString()] || '?';

            let status = 'branco';
            let bgColor = '#fff3cd';
            let borderColor = '#ffc107';
            let icon = '⚪';
            let tooltipText = `Questão ${q}\nResposta do aluno: ${respostaAluno}\nGabarito: ${respostaGabarito}`;

            // Verificar se é múltipla marcação
            const isMultiplaMarcacao = reportData.questoes_multiplas_marcacoes &&
                                        reportData.questoes_multiplas_marcacoes.includes(q);

            if (reportData.questoes_certas.includes(q)) {
                status = 'certo';
                bgColor = '#d4edda';
                borderColor = '#28a745';
                icon = '✓';
            } else if (reportData.questoes_erradas.includes(q)) {
                status = 'errado';
                bgColor = '#f8d7da';
                borderColor = '#dc3545';
                icon = '✗';
            } else if (isMultiplaMarcacao) {
                // Múltiplas marcações ambíguas - claramente identificado!
                status = 'multipla';
                bgColor = '#ffe6e6';
                borderColor = '#ff6b6b';
                icon = '⚠️';
                tooltipText += '\n⚠️ MÚLTIPLAS MARCAÇÕES AMBÍGUAS detectadas';
            } else if (respostaAluno === '-') {
                // Realmente em branco (não marcou nada)
                tooltipText += '\n○ Questão não respondida (em branco)';
                icon = '○';
            }

            html += `
                <div style="
                    background: ${bgColor};
                    border: 2px solid ${borderColor};
                    border-radius: 8px;
                    padding: 8px;
                    text-align: center;
                    font-size: 12px;
                    cursor: help;
                " title="${tooltipText}">
                    <div style="font-weight: bold; font-size: 11px; color: #666; margin-bottom: 4px;">Q${q}</div>
                    <div style="font-size: 16px; margin-bottom: 2px;">${icon}</div>
                    <div style="font-size: 11px; color: #333;">
                        ${respostaAluno === '-' ? '—' : respostaAluno}
                        ${status !== 'branco' ? `<span style="color: #999;"> / ${respostaGabarito}</span>` : ''}
                    </div>
                </div>
            `;
        }

        html += `
                </div>

                <!-- Legenda -->
                <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <strong>Legenda:</strong>
                    <div style="display: flex; gap: 20px; margin-top: 10px; flex-wrap: wrap;">
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <div style="width: 20px; height: 20px; background: #d4edda; border: 2px solid #28a745; border-radius: 4px;"></div>
                            <span>✓ Acerto</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <div style="width: 20px; height: 20px; background: #f8d7da; border: 2px solid #dc3545; border-radius: 4px;"></div>
                            <span>✗ Erro</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <div style="width: 20px; height: 20px; background: #ffe6e6; border: 2px solid #ff6b6b; border-radius: 4px;"></div>
                            <span>⚠️ Múltiplas Marcações</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <div style="width: 20px; height: 20px; background: #fff3cd; border: 2px solid #ffc107; border-radius: 4px;"></div>
                            <span>○ Em Branco</span>
                        </div>
                    </div>
                    <div style="margin-top: 15px; padding: 10px; background: #fff3e6; border-left: 3px solid #ff6b6b; border-radius: 4px;">
                        <p style="margin: 0; font-size: 12px; color: #2c3e50;">
                            <strong>⚠️ Múltiplas Marcações:</strong> Indica que o aluno marcou 2 ou mais alternativas com intensidade similar,
                            impossibilitando o sistema de determinar qual era a resposta pretendida. Essa questão conta como erro.
                        </p>
                    </div>
                    <div style="margin-top: 10px; padding: 10px; background: #fff9e6; border-left: 3px solid #ffc107; border-radius: 4px;">
                        <p style="margin: 0; font-size: 12px; color: #2c3e50;">
                            <strong>○ Em Branco:</strong> Questão não foi respondida (nenhuma marcação detectada).
                        </p>
                    </div>
                    <p style="margin: 10px 0 0 0; font-size: 12px; color: #666;">
                        <strong>Formato:</strong> Resposta do Aluno / Gabarito Oficial
                    </p>
                </div>
            </div>
        `;

        reportContent.innerHTML = html;
        reportModal.style.display = 'block';
    } catch (error) {
        console.error('Erro ao carregar relatório:', error);
        alert('Erro ao carregar relatório');
    }
}

// Funções de Abas
function switchTab(tabName) {
    // Remover ativo das abas
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Adicionar ativo à aba selecionada
    document.getElementById(`tab-${tabName}`).classList.add('active');
    event.target.classList.add('active');

    // Se for gabaritos, carregar dados
    if (tabName === 'gabaritos') {
        loadGabaritos();
        loadGabaroAtual();
        loadPDFsGerados();
        setupQuestoesInputs();
    }
}

// Funções de Gabaritos
function setupQuestoesInputs() {
    const numQuestoes = parseInt(document.getElementById('numQuestoes').value);
    const container = document.getElementById('questoesContainer');
    container.innerHTML = '';

    for (let i = 1; i <= numQuestoes; i++) {
        const div = document.createElement('div');
        div.className = 'questao-linha';

        const numeroDiv = document.createElement('div');
        numeroDiv.className = 'questao-numero';
        numeroDiv.textContent = `Q${i}:`;

        const circulosDiv = document.createElement('div');
        circulosDiv.className = 'questao-circulos';

        ['A', 'B', 'C', 'D', 'E'].forEach(letra => {
            const circulo = document.createElement('div');
            circulo.className = 'circulo-resposta';
            circulo.textContent = letra;
            circulo.id = `q${i}_${letra}`;
            circulo.onclick = () => selecionarResposta(i, letra, circulo);
            circulosDiv.appendChild(circulo);
        });

        div.appendChild(numeroDiv);
        div.appendChild(circulosDiv);
        container.appendChild(div);
    }
}

function selecionarResposta(questao, letra, elemento) {
    // Remover seleção anterior da questão
    document.querySelectorAll(`#q${questao}_A, #q${questao}_B, #q${questao}_C, #q${questao}_D, #q${questao}_E`).forEach(el => {
        el.classList.remove('ativo');
    });

    // Adicionar seleção ao novo elemento
    elemento.classList.add('ativo');
}

async function criarGabarito() {
    const nome = document.getElementById('nomeGabarito').value.trim();
    const mensagem = document.getElementById('mensagemGabarito');

    if (!nome) {
        mensagem.textContent = '✗ Digite um nome para o gabarito';
        mensagem.style.color = '#e74c3c';
        return;
    }

    const numQuestoes = parseInt(document.getElementById('numQuestoes').value);
    const questoes = [];

    for (let i = 1; i <= numQuestoes; i++) {
        // Procurar qual círculo está ativo
        let resposta = '';
        ['A', 'B', 'C', 'D', 'E'].forEach(letra => {
            const elemento = document.getElementById(`q${i}_${letra}`);
            if (elemento && elemento.classList.contains('ativo')) {
                resposta = letra;
            }
        });

        if (!resposta) {
            mensagem.textContent = `✗ Selecione a resposta da questão ${i}`;
            mensagem.style.color = '#e74c3c';
            return;
        }
        questoes.push(resposta);
    }

    try {
        console.log('Enviando:', { nome, questoes });
        const response = await fetch('/api/gabarito/criar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, questoes })
        });

        const data = await response.json();

        if (response.ok) {
            const msg = '✓ ' + data.message;
            mensagem.textContent = msg;
            mensagem.style.color = '#27ae60';
            mensagem.style.display = 'block';
            console.log(msg);
            document.getElementById('nomeGabarito').value = '';
            setupQuestoesInputs();
            setTimeout(() => {
                loadGabaritos();
            }, 1500);
        } else {
            mensagem.textContent = '✗ ' + (data.error || 'Erro desconhecido');
            mensagem.style.color = '#e74c3c';
        }
    } catch (error) {
        console.error('Erro:', error);
        mensagem.textContent = '✗ Erro: ' + error.message;
        mensagem.style.color = '#e74c3c';
    }
}

async function loadGabaritos() {
    try {
        const response = await fetch('/api/gabaritos');
        const gabaritos = await response.json();

        const container = document.getElementById('gabaritosLista');

        if (gabaritos.length === 0) {
            container.innerHTML = '<div class="empty-state">Nenhum gabarito criado ainda</div>';
            return;
        }

        container.innerHTML = gabaritos.map(gab => `
            <div class="gabarito-card">
                ${gab.oficial ? '<div class="oficial-badge">✓ Oficial</div>' : ''}
                <h4>${gab.nome}</h4>
                <p>📊 ${gab.questoes} questões</p>
                <div class="gabarito-actions">
                    ${!gab.oficial ? `<button class="btn btn-success btn-small" onclick="selecionarGabarito('${gab.nome}')">Usar</button>` : ''}
                    <button class="btn btn-danger btn-small" onclick="deletarGabarito('${gab.nome}')">Deletar</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Erro ao carregar gabaritos:', error);
    }
}

async function loadGabaroAtual() {
    try {
        const response = await fetch('/api/gabarito/atual');
        const gabarito = await response.json();

        if (response.ok) {
            const numQuestoes = Object.keys(gabarito).length;
            document.getElementById('gabaroOfiialInfo').innerHTML = `
                <p><strong>Questões:</strong> ${numQuestoes}</p>
                <p><strong>Respostas:</strong> ${Object.values(gabarito).join(', ')}</p>
            `;
        } else {
            document.getElementById('gabaroOfiialInfo').innerHTML = '<p>Nenhum gabarito selecionado</p>';
        }
    } catch (error) {
        document.getElementById('gabaroOfiialInfo').innerHTML = '<p>Nenhum gabarito selecionado</p>';
    }
}

async function selecionarGabarito(nome) {
    try {
        const response = await fetch(`/api/gabarito/selecionar/${nome}`, { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            alert('✓ ' + data.message);
            loadGabaritos();
            loadGabaroAtual();
        } else {
            alert('✗ ' + data.error);
        }
    } catch (error) {
        alert('Erro: ' + error.message);
    }
}

async function deletarGabarito(nome) {
    if (!confirm(`Tem certeza que deseja deletar o gabarito "${nome}"?`)) return;

    try {
        const response = await fetch(`/api/gabarito/deletar/${nome}`, { method: 'DELETE' });
        const data = await response.json();

        if (response.ok) {
            alert('✓ ' + data.message);
            loadGabaritos();
        } else {
            alert('✗ ' + data.error);
        }
    } catch (error) {
        alert('Erro: ' + error.message);
    }
}

async function limparGabaritos() {
    if (!confirm('⚠️ Tem certeza que deseja deletar TODOS os gabaritos JSON? Esta ação não pode ser desfeita!')) return;

    try {
        const response = await fetch('/api/gabaritos/limpar', { method: 'DELETE' });
        const data = await response.json();

        if (response.ok) {
            alert('✓ ' + data.message);
            loadGabaritos();
            loadGabaroAtual();
        } else {
            alert('✗ ' + data.error);
        }
    } catch (error) {
        alert('Erro: ' + error.message);
    }
}

// Funções de Geração de PDF
async function gerarGabaritoPDF() {
    const mensagem = document.getElementById('mensagemPDF');

    const dados = {
        nome_arquivo: document.getElementById('pdfNomeArquivo').value.trim(),
        titulo: document.getElementById('pdfTitulo').value.trim() || 'GABARITO DE PROVA',
        disciplina: document.getElementById('pdfDisciplina').value.trim(),
        professor: document.getElementById('pdfProfessor').value.trim(),
        codigo_prova: document.getElementById('pdfCodigo').value.trim(),
        num_questoes: parseInt(document.getElementById('pdfNumQuestoes').value),
        alternativas: document.getElementById('pdfAlternativas').value.trim() || 'A,B,C,D,E'
    };

    if (!dados.nome_arquivo) {
        mensagem.textContent = '✗ Digite um nome para o arquivo';
        mensagem.style.color = '#e74c3c';
        mensagem.style.display = 'block';
        return;
    }

    mensagem.textContent = '⏳ Gerando PDF...';
    mensagem.style.color = '#3498db';
    mensagem.style.display = 'block';

    try {
        const response = await fetch('/api/gabarito/gerar-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        const data = await response.json();

        if (response.ok) {
            mensagem.textContent = '✓ ' + data.message;
            mensagem.style.color = '#27ae60';

            // Limpar formulário
            document.getElementById('pdfNomeArquivo').value = '';
            document.getElementById('pdfDisciplina').value = '';
            document.getElementById('pdfProfessor').value = '';
            document.getElementById('pdfCodigo').value = '';

            // Recarregar lista
            setTimeout(() => {
                loadPDFsGerados();
                mensagem.style.display = 'none';
            }, 2000);

            // Oferecer download
            if (confirm('PDF gerado! Deseja fazer download agora?')) {
                window.location.href = `/api/gabarito/download-pdf/${data.arquivo}`;
            }
        } else {
            mensagem.textContent = '✗ ' + (data.error || 'Erro ao gerar PDF');
            mensagem.style.color = '#e74c3c';
        }
    } catch (error) {
        console.error('Erro:', error);
        mensagem.textContent = '✗ Erro: ' + error.message;
        mensagem.style.color = '#e74c3c';
    }
}

async function loadPDFsGerados() {
    try {
        const response = await fetch('/api/gabaritos-pdf');
        const pdfs = await response.json();

        const container = document.getElementById('pdfsList');

        if (pdfs.length === 0) {
            container.innerHTML = '<div class="empty-state">Nenhum PDF gerado ainda</div>';
            return;
        }

        container.innerHTML = pdfs.map(pdf => `
            <div class="pdf-card">
                <div class="pdf-icon">📄</div>
                <h4>${pdf.nome}</h4>
                <p class="pdf-info">
                    <span>📊 ${pdf.tamanho} KB</span><br>
                    <span>📅 ${pdf.data_criacao}</span>
                </p>
                <button class="btn btn-primary btn-small" onclick="downloadPDF('${pdf.caminho_relativo || pdf.nome}')">
                    ⬇️ Baixar
                </button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Erro ao carregar PDFs:', error);
        document.getElementById('pdfsList').innerHTML = '<div class="empty-state">Erro ao carregar PDFs</div>';
    }
}

function downloadPDF(filename) {
    window.location.href = `/api/gabarito/download-pdf/${filename}`;
}

async function baixarTodosPDFs() {
    try {
        // Verificar se há PDFs
        const response = await fetch('/api/gabaritos-pdf');
        const pdfs = await response.json();

        if (pdfs.length === 0) {
            alert('Nenhum PDF para baixar');
            return;
        }

        // Confirmar download
        const confirmar = confirm(`Baixar ${pdfs.length} PDF(s) em um arquivo ZIP?`);
        if (!confirmar) return;

        // Fazer download
        window.location.href = '/api/gabaritos-pdf/download-todos';
    } catch (error) {
        console.error('Erro ao baixar PDFs:', error);
        alert('Erro ao baixar PDFs: ' + error.message);
    }
}

async function limparPDFs() {
    if (!confirm('⚠️ Tem certeza que deseja deletar TODOS os PDFs gerados? Esta ação não pode ser desfeita!')) return;

    try {
        const response = await fetch('/api/gabaritos-pdf/limpar', { method: 'DELETE' });
        const data = await response.json();

        if (response.ok) {
            alert('✓ ' + data.message);
            loadPDFsGerados();
        } else {
            alert('✗ ' + data.error);
        }
    } catch (error) {
        alert('Erro: ' + error.message);
    }
}

// Funções de Upload e Geração de CSV
let csvFilenameGlobal = '';
let turmasDisponiveisGlobal = [];

// Event listeners para CSV
const csvUploadArea = document.getElementById('csvUploadArea');
const csvFileInput = document.getElementById('csvFileInput');

csvUploadArea.addEventListener('click', () => csvFileInput.click());

csvUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    csvUploadArea.classList.add('dragover');
});

csvUploadArea.addEventListener('dragleave', () => {
    csvUploadArea.classList.remove('dragover');
});

csvUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    csvUploadArea.classList.remove('dragover');
    handleCSVFiles(e.dataTransfer.files);
});

csvFileInput.addEventListener('change', (e) => {
    handleCSVFiles(e.target.files);
});

async function handleCSVFiles(files) {
    const file = files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
        showCSVStatus('Apenas arquivos CSV são permitidos', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    showCSVStatus('⏳ Analisando CSV...', 'loading');

    try {
        const response = await fetch('/api/csv/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            csvFilenameGlobal = data.arquivo;
            turmasDisponiveisGlobal = data.turmas;

            showCSVStatus(`✅ CSV carregado! ${data.total_alunos} alunos em ${data.total_turmas} turmas`, 'success');

            // Mostrar turmas e configuração
            mostrarTurmas(data.turmas);
            document.getElementById('csvConfigSection').style.display = 'block';

            csvFileInput.value = '';
        } else {
            showCSVStatus(`✗ ${data.error}`, 'error');
        }
    } catch (error) {
        showCSVStatus(`✗ Erro: ${error.message}`, 'error');
    }
}

function showCSVStatus(message, type) {
    const status = document.getElementById('csvStatus');
    status.textContent = message;
    status.className = type;
    status.style.display = 'block';
}

function mostrarTurmas(turmas) {
    const container = document.getElementById('turmasCheckboxes');
    container.innerHTML = '';

    turmas.forEach((turma, idx) => {
        const div = document.createElement('div');
        div.className = 'turma-checkbox';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `turma_${idx}`;
        checkbox.value = turma.nome;
        checkbox.checked = true;

        const label = document.createElement('label');
        label.htmlFor = `turma_${idx}`;
        label.textContent = `${turma.nome} (${turma.num_alunos} alunos)`;

        div.appendChild(checkbox);
        div.appendChild(label);
        container.appendChild(div);
    });

    // Botão selecionar todas
    const btnDiv = document.createElement('div');
    btnDiv.style.marginTop = '10px';

    const btnAll = document.createElement('button');
    btnAll.className = 'btn btn-small';
    btnAll.textContent = 'Selecionar Todas';
    btnAll.onclick = () => {
        document.querySelectorAll('.turma-checkbox input').forEach(cb => cb.checked = true);
    };

    const btnNone = document.createElement('button');
    btnNone.className = 'btn btn-small';
    btnNone.textContent = 'Desmarcar Todas';
    btnNone.style.marginLeft = '10px';
    btnNone.onclick = () => {
        document.querySelectorAll('.turma-checkbox input').forEach(cb => cb.checked = false);
    };

    btnDiv.appendChild(btnAll);
    btnDiv.appendChild(btnNone);
    container.appendChild(btnDiv);
}

async function gerarGabaritosDeCSV() {
    const mensagem = document.getElementById('mensagemCSV');

    if (!csvFilenameGlobal) {
        mensagem.textContent = '✗ Faça o upload de um CSV primeiro';
        mensagem.style.color = '#e74c3c';
        mensagem.style.display = 'block';
        return;
    }

    // Obter turmas selecionadas
    const turmasSelecionadas = [];
    document.querySelectorAll('.turma-checkbox input:checked').forEach(cb => {
        turmasSelecionadas.push(cb.value);
    });

    if (turmasSelecionadas.length === 0) {
        mensagem.textContent = '✗ Selecione pelo menos uma turma';
        mensagem.style.color = '#e74c3c';
        mensagem.style.display = 'block';
        return;
    }

    const dados = {
        csv_filename: csvFilenameGlobal,
        turmas: turmasSelecionadas,
        titulo: document.getElementById('csvTitulo').value.trim() || 'GABARITO DE PROVA',
        disciplina: document.getElementById('csvDisciplina').value.trim(),
        professor: document.getElementById('csvProfessor').value.trim(),
        codigo_prova: document.getElementById('csvCodigo').value.trim(),
        num_questoes: parseInt(document.getElementById('csvNumQuestoes').value),
        alternativas: document.getElementById('csvAlternativas').value.trim() || 'A,B,C,D,E'
    };

    mensagem.textContent = `⏳ Gerando gabaritos para ${turmasSelecionadas.length} turma(s)... Isso pode levar alguns minutos.`;
    mensagem.style.color = '#3498db';
    mensagem.style.display = 'block';

    try {
        const response = await fetch('/api/csv/gerar-gabaritos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        const data = await response.json();

        if (response.ok) {
            mensagem.textContent = `✓ ${data.message}\n${data.total_alunos} alunos processados em ${data.total_turmas} turma(s)`;
            mensagem.style.color = '#27ae60';

            // Limpar formulário
            document.getElementById('csvConfigSection').style.display = 'none';
            csvFilenameGlobal = '';

            // Recarregar lista de PDFs
            setTimeout(() => {
                loadPDFsGerados();
                mensagem.style.display = 'none';
            }, 3000);
        } else {
            mensagem.textContent = '✗ ' + (data.error || 'Erro ao gerar gabaritos');
            mensagem.style.color = '#e74c3c';
        }
    } catch (error) {
        console.error('Erro:', error);
        mensagem.textContent = '✗ Erro: ' + error.message;
        mensagem.style.color = '#e74c3c';
    }
}

// Função para carregar gabaritos no select
async function loadGabaritosSelect() {
    try {
        const response = await fetch('/api/gabaritos');
        const gabaritos = await response.json();

        const select = document.getElementById('gabaritoSelect');

        if (gabaritos.length === 0) {
            select.innerHTML = '<option value="">Nenhum gabarito disponível - Crie um na aba Gabaritos</option>';
            return;
        }

        // Encontrar o gabarito oficial
        const gabaritoOficial = gabaritos.find(g => g.oficial);

        select.innerHTML = gabaritos.map(gab => {
            const selected = gab.oficial ? 'selected' : '';
            const label = gab.oficial ? `${gab.nome} (Oficial) - ${gab.questoes} questões` : `${gab.nome} - ${gab.questoes} questões`;
            return `<option value="${gab.nome}" ${selected}>${label}</option>`;
        }).join('');

    } catch (error) {
        console.error('Erro ao carregar gabaritos:', error);
        const select = document.getElementById('gabaritoSelect');
        select.innerHTML = '<option value="">Erro ao carregar gabaritos</option>';
    }
}

// Funções de Logs
function addLog(message, type = 'loading') {
    const logsContainer = document.getElementById('logsContainer');

    // Remover mensagem de "nenhuma correção"
    const emptyMsg = logsContainer.querySelector('p');
    if (emptyMsg && emptyMsg.textContent.includes('Nenhuma correção')) {
        emptyMsg.remove();
    }

    // Criar entrada de log
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;

    const time = new Date().toLocaleTimeString('pt-BR');

    logEntry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-message">${message}</span>
    `;

    // Adicionar no topo da lista
    logsContainer.insertBefore(logEntry, logsContainer.firstChild);

    // Scroll para o topo
    logsContainer.scrollTop = 0;

    // Limitar a 100 logs
    while (logsContainer.children.length > 100) {
        logsContainer.removeChild(logsContainer.lastChild);
    }
}

function limparLogs() {
    const logsContainer = document.getElementById('logsContainer');
    logsContainer.innerHTML = '<p style="color: #999; text-align: center; margin: 10px 0;">Nenhuma correção realizada ainda...</p>';
}

// Funções de Download
function downloadJSON(filename) {
    window.location.href = `/api/report/${filename}?download=1`;
}

async function downloadHTML(filename) {
    try {
        const response = await fetch(`/relatorio/${filename}`);
        const htmlContent = await response.text();

        const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';

        document.body.appendChild(link);
        link.click();

        // Cleanup
        setTimeout(() => {
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }, 100);

        addLog(`📥 Baixado relatório HTML: ${filename}`, 'success');
    } catch (error) {
        console.error('Erro ao baixar HTML:', error);
        alert('Erro ao baixar HTML: ' + error.message);
    }
}

async function exportarTodosCSV() {
    try {
        const response = await fetch('/api/reports');
        const reports = await response.json();

        if (reports.length === 0) {
            alert('Nenhum relatório para exportar');
            return;
        }

        // Criar CSV
        let csv = 'Nome,Turma,Data,Acertos,Erros,Total,Percentual,Nota\n';

        for (const report of reports) {
            const erros = report.total - report.acertos;
            const percentual = ((report.acertos / report.total) * 100).toFixed(1);

            csv += `"${report.nome}","${report.turma || 'N/A'}","${report.data}",${report.acertos},${erros},${report.total},${percentual}%,${report.nota.toFixed(1)}\n`;
        }

        // Download
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        const now = new Date();
        const timestamp = now.toISOString().slice(0, 10).replace(/-/g, '');

        link.setAttribute('href', url);
        link.setAttribute('download', `relatorios_${timestamp}.csv`);
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        addLog(`📊 Exportados ${reports.length} relatórios para CSV`, 'success');
    } catch (error) {
        console.error('Erro ao exportar CSV:', error);
        alert('Erro ao exportar CSV: ' + error.message);
    }
}

// Funções de CSV de Referência
const csvRefInput = document.getElementById('csvRefInput');
csvRefInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/csv-alunos/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            atualizarStatusCSVRef();
            addLog(`✅ CSV carregado: ${data.total_alunos} alunos em ${data.total_turmas} turmas`, 'success');
        } else {
            alert('Erro: ' + data.error);
        }
    } catch (error) {
        alert('Erro ao carregar CSV: ' + error.message);
    }

    csvRefInput.value = '';
});

async function atualizarStatusCSVRef() {
    try {
        const response = await fetch('/api/csv-alunos/status');
        const data = await response.json();

        const statusDiv = document.getElementById('csvRefStatus');
        const btnLimpar = document.getElementById('btnLimparCSVRef');

        if (data.carregado) {
            statusDiv.innerHTML = `✅ <strong>${data.total_alunos} alunos</strong> em <strong>${data.total_turmas} turmas</strong>`;
            statusDiv.style.color = '#27ae60';
            btnLimpar.style.display = 'inline-block';

            // Atualizar filtro de turmas
            atualizarFiltroTurmas(data.turmas);
        } else {
            statusDiv.textContent = 'Nenhum CSV carregado';
            statusDiv.style.color = '#999';
            btnLimpar.style.display = 'none';
        }
    } catch (error) {
        console.error('Erro ao verificar status do CSV:', error);
    }
}

async function limparCSVReferencia() {
    if (!confirm('Tem certeza que deseja remover o CSV de referência?')) return;

    try {
        const response = await fetch('/api/csv-alunos/limpar', { method: 'DELETE' });
        const data = await response.json();

        if (response.ok) {
            atualizarStatusCSVRef();
            addLog('🗑️ CSV de referência removido', 'success');
        } else {
            alert('Erro: ' + data.error);
        }
    } catch (error) {
        alert('Erro ao remover CSV: ' + error.message);
    }
}

function atualizarFiltroTurmas(turmas) {
    const select = document.getElementById('filtroTurma');

    // Preservar valor selecionado
    const valorAtual = select.value;

    // Reconstruir opções
    select.innerHTML = '<option value="">Todas as turmas</option>';

    if (turmas && turmas.length > 0) {
        turmas.forEach(turma => {
            const option = document.createElement('option');
            option.value = turma;
            option.textContent = turma;
            if (turma === valorAtual) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }
}

async function filtrarPorTurma() {
    const turma = document.getElementById('filtroTurma').value;
    await loadReports(turma);
}

// Modificar loadReports para aceitar filtro
async function loadReports(filtroTurma = '') {
    try {
        const url = filtroTurma ? `/api/reports?turma=${encodeURIComponent(filtroTurma)}` : '/api/reports';
        const response = await fetch(url);
        const reports = await response.json();

        if (reports.length === 0) {
            const mensagem = filtroTurma ? `Nenhum relatório encontrado para a turma "${filtroTurma}"` : 'Nenhum relatório ainda. Envie um PDF para começar!';
            reportsList.innerHTML = `<div class="empty-state">${mensagem}</div>`;
            return;
        }

        reportsList.innerHTML = reports.map(report => {
            const gradeClass = report.nota >= 7 ? 'excellent' : report.nota >= 5 ? 'good' : 'poor';
            return `
                <div class="report-item">
                    <div class="report-info" onclick="viewReport('${report.json_file}', '${report.html_file}')" style="cursor: pointer; flex: 1;">
                        <div class="report-name">📋 ${report.nome}</div>
                        <div class="report-meta">
                            <span>🏫 ${report.turma}</span>
                            <span>📅 ${report.data}</span>
                            <span>✓ ${report.acertos}/${report.total} acertos</span>
                        </div>
                    </div>
                    <div class="report-stats">
                        <div class="report-stat">
                            <div class="report-stat-number">${report.acertos}/${report.total}</div>
                            <div class="report-stat-label">Acertos</div>
                        </div>
                        <div class="grade-badge ${gradeClass}">
                            ${report.nota.toFixed(1)}
                        </div>
                    </div>
                    <div class="report-actions">
                        <button class="btn btn-small btn-primary" onclick="event.stopPropagation(); downloadJSON('${report.json_file}')" title="Baixar JSON">
                            📄 JSON
                        </button>
                        <button class="btn btn-small btn-success" onclick="event.stopPropagation(); downloadHTML('${report.html_file}')" title="Baixar HTML">
                            🌐 HTML
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Adicionar botão para exportar tudo
        if (reports.length > 0) {
            const exportBtn = document.createElement('div');
            exportBtn.style.marginTop = '20px';
            exportBtn.style.textAlign = 'center';
            exportBtn.innerHTML = `
                <button class="btn btn-primary" onclick="exportarTodosCSV()">
                    📊 Exportar Todos para CSV
                </button>
            `;
            reportsList.appendChild(exportBtn);
        }

        // Atualizar lista de turmas no filtro (caso haja novas turmas)
        const turmasUnicas = [...new Set(reports.map(r => r.turma))].sort();
        atualizarFiltroTurmas(turmasUnicas);
    } catch (error) {
        console.error('Erro ao carregar relatórios:', error);
        reportsList.innerHTML = '<div class="empty-state">Erro ao carregar relatórios</div>';
    }
}

// Carregar e renderizar envios por turma
async function loadEnvios() {
    const container = document.getElementById('enviosContainer');

    try {
        const response = await fetch('/api/envios');
        const turmas = await response.json();

        if (turmas.length === 0) {
            container.innerHTML = '<div class="empty-state">Nenhum envio encontrado</div>';
            return;
        }

        let html = '';

        turmas.forEach(turma => {
            html += `
                <div class="turma-card">
                    <div class="turma-header">
                        <div class="turma-info" onclick="toggleTurma(this.parentElement)">
                            <h3 class="turma-nome">📚 ${turma.turma || 'Sem turma'}</h3>
                            <span class="turma-stats">
                                ${turma.total_alunos} aluno${turma.total_alunos !== 1 ? 's' : ''}
                                • Média: ${turma.media_nota.toFixed(1)}/10
                            </span>
                        </div>
                        <div class="turma-actions">
                            <button class="btn-export" onclick="exportarTurmaExcel('${encodeURIComponent(turma.turma)}', event)" title="Exportar para Excel">
                                📊 Excel
                            </button>
                            <div class="turma-expand" onclick="toggleTurma(this.parentElement)">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="6 9 12 15 18 9"></polyline>
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div class="turma-content" style="display: none;">
                        <div class="turma-estatisticas">
                            <div class="stat-item">
                                <span class="stat-label">Maior nota:</span>
                                <span class="stat-value">${turma.maior_nota.toFixed(1)}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Menor nota:</span>
                                <span class="stat-value">${turma.menor_nota.toFixed(1)}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Média:</span>
                                <span class="stat-value">${turma.media_nota.toFixed(1)}</span>
                            </div>
                        </div>

                        <div class="alunos-tabela-wrapper">
                            <table class="alunos-tabela">
                                <thead>
                                    <tr>
                                        <th>Nome</th>
                                        <th>RA</th>
                                        <th>Acertos</th>
                                        <th>%</th>
                                        <th>Nota</th>
                                        <th>Data</th>
                                        <th>Ações</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${turma.alunos.map(aluno => `
                                        <tr>
                                            <td class="aluno-nome">${aluno.nome}</td>
                                            <td class="aluno-ra">${aluno.matricula || '-'}</td>
                                            <td class="aluno-acertos">${aluno.acertos}/${aluno.total}</td>
                                            <td class="aluno-percentual">
                                                <span class="badge ${getNotaClass(aluno.percentual)}">${aluno.percentual.toFixed(1)}%</span>
                                            </td>
                                            <td class="aluno-nota">
                                                <strong>${aluno.nota.toFixed(1)}</strong>
                                            </td>
                                            <td class="aluno-data">${formatDataEnvio(aluno.data_envio)}</td>
                                            <td class="aluno-acoes">
                                                <button class="btn-icon" onclick="viewReport('${aluno.relatorio_json}', '${aluno.relatorio_html}')" title="Ver relatório detalhado">
                                                    👁️
                                                </button>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

    } catch (error) {
        console.error('Erro ao carregar envios:', error);
        container.innerHTML = '<div class="empty-state">Erro ao carregar envios</div>';
    }
}

// Toggle accordion de turma
function toggleTurma(header) {
    const card = header.closest('.turma-card');
    const content = card.querySelector('.turma-content');
    const icon = card.querySelector('.turma-expand svg');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        icon.style.transform = 'rotate(0deg)';
    }
}

// Exportar turma para Excel
function exportarTurmaExcel(turmaNome, event) {
    event.stopPropagation(); // Evitar que clique no botão expanda/recolha a turma

    // Fazer download do Excel
    window.location.href = `/api/envios/export/${turmaNome}`;
}

// Limpar todos os envios
async function limparTodosEnvios() {
    // Confirmação
    const confirmacao = confirm(
        '⚠️ ATENÇÃO!\n\n' +
        'Você está prestes a deletar TODOS os relatórios de correção.\n\n' +
        'Esta ação NÃO pode ser desfeita!\n\n' +
        'Deseja continuar?'
    );

    if (!confirmacao) {
        return;
    }

    try {
        const response = await fetch('/api/envios/limpar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            alert(`✅ Sucesso!\n\n${data.message}\n\n` +
                  `• ${data.json_deletados} relatórios JSON\n` +
                  `• ${data.html_deletados} relatórios HTML`);

            // Recarregar dados
            loadEnvios();
            loadReports();
            loadStats();
        } else {
            alert(`❌ Erro ao limpar envios:\n\n${data.error}`);
        }
    } catch (error) {
        console.error('Erro ao limpar envios:', error);
        alert('❌ Erro ao limpar envios. Verifique o console para mais detalhes.');
    }
}

// Classificar nota por cor
function getNotaClass(percentual) {
    if (percentual >= 70) return 'badge-success';
    if (percentual >= 50) return 'badge-warning';
    return 'badge-danger';
}

// Formatar data de envio
function formatDataEnvio(dataStr) {
    const data = new Date(dataStr);
    const hoje = new Date();
    const ontem = new Date(hoje);
    ontem.setDate(ontem.getDate() - 1);

    const dataFormatada = data.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    const horaFormatada = data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

    if (data.toDateString() === hoje.toDateString()) {
        return `Hoje ${horaFormatada}`;
    } else if (data.toDateString() === ontem.toDateString()) {
        return `Ontem ${horaFormatada}`;
    } else {
        return `${dataFormatada} ${horaFormatada}`;
    }
}

// Carregar dados ao iniciar
loadReports();
loadStats();
loadEnvios();
loadGabaritosSelect();
atualizarStatusCSVRef();

// Recarregar a cada 30 segundos
setInterval(() => {
    loadReports();
    loadStats();
    loadEnvios();
    loadGabaritosSelect();
    atualizarStatusCSVRef();
}, 30000);
