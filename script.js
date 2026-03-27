const REGRAS = {
    megasena: { dezenas: 6, total: 60, cor: "#209869" },
    lotofacil: { dezenas: 15, total: 25, cor: "#930089" },
    quina: { dezenas: 5, total: 80, cor: "#260085" }
};

let dadosUltimoConcurso = null;
let meuGrafico = null;

// Busca o último resultado na API
async function buscarResultado(loteria) {
    const info = document.getElementById('info-concurso');
    info.innerText = "Buscando dados atualizados...";
    
    try {
        const response = await fetch(`https://loteriascaixa-api.herokuapp.com/api/${loteria}/latest`);
        dadosUltimoConcurso = await response.json();
        renderizarUltimoResultado(loteria);
    } catch (error) {
        info.innerText = "Erro ao conectar com a API. Verifique sua internet.";
    }
}

function renderizarUltimoResultado(loteria) {
    const info = document.getElementById('info-concurso');
    const containerBalls = document.getElementById('dezenas-sorteadas');
    const config = REGRAS[loteria];
    
    document.documentElement.style.setProperty('--primary', config.cor);
    
    info.innerHTML = `Concurso <strong>#${dadosUltimoConcurso.concurso}</strong> (${dadosUltimoConcurso.data})`;
    containerBalls.innerHTML = '';
    
    dadosUltimoConcurso.dezenas.forEach(num => {
        const ball = document.createElement('div');
        ball.className = 'ball';
        ball.style.backgroundColor = config.cor;
        ball.innerText = num;
        containerBalls.appendChild(ball);
    });

    atualizarGrafico(dadosUltimoConcurso.dezenas, config);
}

function gerarNumeros(estrategia, config) {
    let numeros = [];
    let pool = Array.from({length: config.total}, (_, i) => i + 1);

    // Estratégia Baseada em Concursos Passados
    if (estrategia === "quentes" && dadosUltimoConcurso) {
        const ultimas = dadosUltimoConcurso.dezenas.map(Number);
        const quantidadeParaRepetir = Math.floor(config.dezenas / 3); // Tenta repetir 1/3 dos números
        
        for(let i=0; i < quantidadeParaRepetir; i++) {
            let index = Math.floor(Math.random() * ultimas.length);
            let num = ultimas.splice(index, 1)[0];
            numeros.push(num);
            // Remove do pool geral para não duplicar
            pool = pool.filter(n => n !== num);
        }
    }

    // Completa o resto do jogo aleatoriamente
    while (numeros.length < config.dezenas) {
        let index = Math.floor(Math.random() * pool.length);
        let num = pool.splice(index, 1)[0];
        numeros.push(num);
    }
    return numeros.sort((a, b) => a - b);
}

document.getElementById('btn-gerar').addEventListener('click', () => {
    const loteria = document.getElementById('loteria-select').value;
    const qtd = parseInt(document.getElementById('qtd-jogos').value);
    const est = document.getElementById('estrategia').value;
    const lista = document.getElementById('lista-jogos');
    const config = REGRAS[loteria];
    
    lista.innerHTML = '';
    
    for (let i = 0; i < qtd; i++) {
        const jogo = gerarNumeros(est, config);
        const sorteadas = dadosUltimoConcurso.dezenas.map(Number);
        const acertos = jogo.filter(n => sorteadas.includes(n));
        
        const div = document.createElement('div');
        div.className = 'jogo-item';
        div.innerHTML = `
            <strong>Palpite ${i+1}:</strong> ${jogo.map(n => n.toString().padStart(2, '0')).join(' - ')}
            <br><small style="color: #555;">Simulação: ${acertos.length} acertos no último concurso.</small>
        `;
        lista.appendChild(div);
    }
});

function atualizarGrafico(dezenas, config) {
    const ctx = document.getElementById('grafico-distribuicao').getContext('2d');
    if (meuGrafico) meuGrafico.destroy();
    
    meuGrafico = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dezenas.map((_, i) => `Bola ${i+1}`),
            datasets: [{
                label: 'Dezenas Sorteadas (Distribuição)',
                data: dezenas.map(Number),
                borderColor: config.cor,
                backgroundColor: config.cor + '22',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { min: 1, max: config.total } }
        }
    });
}

// Troca de loteria no seletor
document.getElementById('loteria-select').addEventListener('change', (e) => buscarResultado(e.target.value));

// Inicia com a Mega-Sena
buscarResultado('megasena');