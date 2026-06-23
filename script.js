let historicalData = []; // Se llenará para el simulador

document.addEventListener('DOMContentLoaded', async () => {
    try {
        // 1. Cargar datos procesados
        const response = await fetch('data/dashboard_data.json');
        if (!response.ok) throw new Error('No se encontró el archivo de datos');
        const data = await response.json();

        // Cargar historial crudo para el simulador (Módulo F)
        const histResponse = await fetch('data/historial.json');
        historicalData = await histResponse.json();

        // 2. Renderizar Módulos
        renderModuleA(data.meta);
        renderModuleB(data.modulo_b);
        renderModuleC(data.modulo_c);
        renderModuleE(data.modulo_e);
        
        document.getElementById('last-update').textContent = `Actualizado: ${data.meta.actualizacion}`;

    } catch (error) {
        console.error("Error cargando el dashboard:", error);
        document.body.innerHTML = `<div class="p-8 text-center text-red-600">Error al cargar los datos. Asegúrate de ejecutar los scripts de Python primero.</div>`;
    }
});

function renderModuleA(meta) {
    const container = document.getElementById('kpi-container');
    const numerosHTML = meta.ultimo_sorteo.numeros.map(n => 
        `<span class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 font-bold text-sm">${n.toString().padStart(2, '0')}</span>`
    ).join(' ');

    container.innerHTML = `
        <div class="bg-slate-50 p-4 rounded-lg border border-slate-200">
            <p class="text-sm text-slate-500">Sorteo N°</p>
            <p class="text-2xl font-bold text-slate-800">#${meta.ultimo_sorteo.sorteo}</p>
        </div>
        <div class="bg-slate-50 p-4 rounded-lg border border-slate-200">
            <p class="text-sm text-slate-500">Fecha</p>
            <p class="text-xl font-bold text-slate-800">${meta.ultimo_sorteo.fecha}</p>
        </div>
        <div class="bg-slate-50 p-4 rounded-lg border border-slate-200 md:col-span-2">
            <p class="text-sm text-slate-500 mb-2">Números Extraídos</p>
            <div class="flex flex-wrap gap-2">${numerosHTML}</div>
        </div>
    `;
}

function renderModuleB(moduloB) {
    document.getElementById('hot-numbers').textContent = moduloB.calientes.map(n => n.toString().padStart(2, '0')).join(', ');
    document.getElementById('cold-numbers').textContent = moduloB.frios.map(n => n.toString().padStart(2, '0')).join(', ');

    const ctx = document.getElementById('freqChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: moduloB.frecuencias.map(d => d.numero.toString().padStart(2, '0')),
            datasets: [{
                label: 'Frecuencia Histórica',
                data: moduloB.frecuencias.map(d => d.frecuencia),
                backgroundColor: moduloB.frecuencias.map(d => 
                    moduloB.calientes.includes(d.numero) ? 'rgba(239, 68, 68, 0.7)' : 
                    moduloB.frios.includes(d.numero) ? 'rgba(59, 130, 246, 0.7)' : 'rgba(148, 163, 184, 0.5)'
                ),
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function renderModuleC(grupos) {
    const tbody = document.getElementById('grupos-table-body');
    tbody.innerHTML = Object.entries(grupos).map(([nombre, stats]) => `
        <tr class="hover:bg-slate-50 transition">
            <td class="px-4 py-3 font-bold text-blue-700">${nombre}</td>
            <td class="px-4 py-3 font-mono text-xs text-slate-600">${stats.numeros.map(n => n.toString().padStart(2, '0')).join(', ')}</td>
            <td class="px-4 py-3 text-center font-semibold text-green-600">${stats.aciertos_100}</td>
            <td class="px-4 py-3 text-center font-bold text-purple-600">${stats.max_500}</td>
            <td class="px-4 py-3 text-center text-slate-500">${stats.freq_max_500} veces</td>
        </tr>
    `).join('');
}

function renderModuleE(probs) {
    const container = document.getElementById('probabilities-container');
    container.innerHTML = `
        <div class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p class="text-sm text-yellow-800 font-bold">14 Aciertos</p>
            <p class="text-xl font-mono text-yellow-900">${probs.probabilidad_14}</p>
        </div>
        <div class="p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <p class="text-sm text-orange-800 font-bold">13 Aciertos</p>
            <p class="text-xl font-mono text-orange-900">${probs.probabilidad_13}</p>
        </div>
        <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p class="text-sm text-red-800 font-bold">12 Aciertos</p>
            <p class="text-xl font-mono text-red-900">${probs.probabilidad_12}</p>
        </div>
    `;
}

// MÓDULO F: Simulador
function runSimulation() {
    const input = document.getElementById('simulator-input').value;
    const resultDiv = document.getElementById('simulator-result');
    
    try {
        const userNumbers = new Set(input.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n) && n >= 1 && n <= 25));
        
        if (userNumbers.size === 0) throw new Error("Ingresa al menos un número válido (1-25).");
        if (userNumbers.size > 14) throw new Error("El Kino permite un máximo de 14 números por combinación.");

        let maxAciertos = 0;
        let freqMax = 0;
        let totalAciertos100 = 0;
        
        const ultimos100 = historicalData.slice(-100);
        
        ultimos100.forEach(sorteo => {
            const aciertos = [...userNumbers].filter(n => sorteo.numeros.includes(n)).length;
            totalAciertos100 += aciertos;
            if (aciertos > maxAciertos) {
                maxAciertos = aciertos;
                freqMax = 1;
            } else if (aciertos === maxAciertos) {
                freqMax++;
            }
        });

        resultDiv.classList.remove('hidden');
        resultDiv.innerHTML = `
            <h3 class="font-bold text-lg mb-2">Resultados del Análisis (Últimos 100 sorteos)</h3>
            <div class="grid grid-cols-3 gap-4 text-center">
                <div>
                    <p class="text-sm text-slate-500">Números analizados</p>
                    <p class="font-mono font-bold text-blue-700">${[...userNumbers].map(n => n.toString().padStart(2, '0')).join(', ')}</p>
                </div>
                <div>
                    <p class="text-sm text-slate-500">Total de aciertos</p>
                    <p class="text-2xl font-bold text-green-600">${totalAciertos100}</p>
                </div>
                <div>
                    <p class="text-sm text-slate-500">Máximo aciertos en un sorteo</p>
                    <p class="text-2xl font-bold text-purple-600">${maxAciertos} <span class="text-sm font-normal text-slate-500">(${freqMax} veces)</span></p>
                </div>
            </div>
        `;
    } catch (error) {
        resultDiv.classList.remove('hidden');
        resultDiv.innerHTML = `<p class="text-red-600 font-bold">⚠️ ${error.message}</p>`;
    }
}