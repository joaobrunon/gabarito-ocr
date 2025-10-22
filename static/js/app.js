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
    const file = files[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
        showStatus('Apenas arquivos PDF são permitidos', 'error');
        return;
    }

    // Enviar arquivo
    const formData = new FormData();
    formData.append('file', file);

    showStatus('⏳ Corrigindo PDF...', 'loading');

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showStatus('✅ PDF corrigido com sucesso!', 'success');
            fileInput.value = '';
            setTimeout(() => {
                uploadStatus.style.display = 'none';
                loadReports();
                loadStats();
            }, 1500);
        } else {
            showStatus(`✗ ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`✗ Erro: ${error.message}`, 'error');
    }
}

function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = `upload-status ${type}`;
    uploadStatus.style.display = 'block';
}

async function loadReports() {
    try {
        const response = await fetch('/api/reports');
        const reports = await response.json();

        if (reports.length === 0) {
            reportsList.innerHTML = '<div class="empty-state">Nenhum relatório ainda. Envie um PDF para começar!</div>';
            return;
        }

        reportsList.innerHTML = reports.map(report => {
            const gradeClass = report.nota >= 7 ? 'excellent' : report.nota >= 5 ? 'good' : 'poor';
            return `
                <div class="report-item" onclick="viewReport('${report.json_file}', '${report.html_file}')">
                    <div class="report-info">
                        <div class="report-name">📋 ${report.nome}</div>
                        <div class="report-meta">
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
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Erro ao carregar relatórios:', error);
        reportsList.innerHTML = '<div class="empty-state">Erro ao carregar relatórios</div>';
    }
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
        // Carregar JSON para mostrar dados
        const jsonResponse = await fetch(`/api/report/${jsonFile}`);
        const reportData = await jsonResponse.json();

        // Carregar HTML
        const htmlResponse = await fetch(`/relatorio/${htmlFile}`);
        const htmlContent = await htmlResponse.text();

        reportContent.innerHTML = htmlContent;
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

// Carregar dados ao iniciar
loadReports();
loadStats();

// Recarregar a cada 30 segundos
setInterval(() => {
    loadReports();
    loadStats();
}, 30000);
