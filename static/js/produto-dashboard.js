(function () {
    function percentageLabel(value) {
        return Number(value || 0).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }) + '%';
    }

    if (window.FinanceCharts && window.FinanceCharts.registerHtmxDashboard) {
        window.ProdutoDashboardCharts = FinanceCharts.registerHtmxDashboard({
            name: 'produto',
            rootId: 'bloco-dados',
            swapTargetId: 'bloco-dados',
            dataScriptId: 'produtoChartsData',
            render: function (context) {
                var root = context.root;
                var data = context.data || {};
                var charts = context.charts;
                var categorias = data.categorias || {};
                var margens = data.margens || {};
                var categoryLabels = categorias.labels && categorias.labels.length ? categorias.labels : ['Sem categorias'];
                var categoryValues = categorias.values && categorias.values.length ? categorias.values : [0];
                var marginLabels = margens.labels && margens.labels.length ? margens.labels : ['Sem produtos'];
                var marginValues = margens.values && margens.values.length ? margens.values : [0];

                var categoryCanvas = root.querySelector('#produtoCategoryChart');
                if (categoryCanvas) {
                    context.setChart('categorias', charts.barChart(categoryCanvas, categoryLabels, [{
                        label: 'Valor em estoque',
                        backgroundColor: '#2470dc',
                        borderColor: '#1849a9',
                        data: categoryValues
                    }]));
                }

                var marginCanvas = root.querySelector('#produtoMarginChart');
                if (marginCanvas && window.Chart) {
                    context.setChart('margens', new Chart(marginCanvas, {
                        type: 'bar',
                        data: {
                            labels: marginLabels,
                            datasets: [{
                                label: 'Margem de lucro',
                                backgroundColor: '#198754',
                                borderColor: '#027a48',
                                data: marginValues
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            legend: { labels: { boxWidth: 14 } },
                            tooltips: {
                                callbacks: {
                                    label: function (tooltipItem, chartData) {
                                        var dataset = chartData.datasets[tooltipItem.datasetIndex];
                                        return dataset.label + ': ' + percentageLabel(tooltipItem.yLabel || tooltipItem.value);
                                    }
                                }
                            },
                            scales: {
                                yAxes: [{
                                    ticks: {
                                        beginAtZero: true,
                                        callback: function (value) { return percentageLabel(value); }
                                    }
                                }]
                            }
                        }
                    }));
                }

                if (window.feather) {
                    window.feather.replace();
                }
            }
        });
    }

    function bindProdutoForm(form) {
        if (!form || form.dataset.produtoFormBound === 'true') return;
        form.dataset.produtoFormBound = 'true';

        var payment = form.querySelector('[data-produto-payment]');
        var fiadoFields = form.querySelector('[data-produto-fiado-fields]');
        if (!payment || !fiadoFields) return;

        function toggleFiadoFields() {
            var visible = payment.value === 'Fiado a pagar';
            fiadoFields.hidden = !visible;
            fiadoFields.querySelectorAll('input, select, textarea').forEach(function (field) {
                field.disabled = !visible;
            });
        }

        payment.addEventListener('change', toggleFiadoFields);
        toggleFiadoFields();
    }

    function initProdutoForms(context) {
        var root = context || document;
        if (root.matches && root.matches('[data-produto-form]')) {
            bindProdutoForm(root);
        }
        root.querySelectorAll('[data-produto-form]').forEach(bindProdutoForm);
    }

    function cleanupBootstrapArtifacts() {
        window.setTimeout(function () {
            if (!document.querySelector('.modal.show')) {
                document.querySelectorAll('.modal-backdrop').forEach(function (backdrop) {
                    backdrop.remove();
                });
                document.body.classList.remove('modal-open');
                document.body.style.removeProperty('padding-right');
                document.body.style.removeProperty('overflow');
            }
        }, 120);
    }

    function closeProdutoModal() {
        var modal = document.getElementById('staticBackdrop');
        if (!modal || !window.bootstrap) return;

        var instance = window.bootstrap.Modal.getInstance(modal);
        if (!instance) {
            instance = new window.bootstrap.Modal(modal);
        }
        instance.hide();
        cleanupBootstrapArtifacts();
    }

    function showProdutoToast(message, type) {
        var stack = document.querySelector('[data-produto-toast-stack]');
        if (!stack) {
            stack = document.createElement('div');
            stack.className = 'produto-toast-stack';
            stack.setAttribute('data-produto-toast-stack', 'true');
            document.body.appendChild(stack);
        }

        var toast = document.createElement('div');
        toast.className = 'produto-toast ' + (type || 'success');
        toast.setAttribute('role', 'status');
        toast.innerHTML = '<i class="fa-solid ' + (type === 'warning' ? 'fa-triangle-exclamation' : 'fa-circle-check') + '" aria-hidden="true"></i><span></span>';
        toast.querySelector('span').textContent = message;
        stack.appendChild(toast);

        window.setTimeout(function () {
            toast.classList.add('is-hiding');
            window.setTimeout(function () {
                toast.remove();
                if (!stack.children.length) {
                    stack.remove();
                }
            }, 180);
        }, 3600);
    }

    function refreshProdutoDashboard() {
        var root = document.getElementById('bloco-dados');
        if (!root || !window.htmx) return;

        window.setTimeout(function () {
            window.htmx.ajax('GET', window.location.pathname + window.location.search, {
                target: '#bloco-dados',
                swap: 'outerHTML'
            });
        }, 140);
    }

    function handleProdutoMutationSuccess() {
        closeProdutoModal();
        refreshProdutoDashboard();
    }

    function handleProdutoDeleted(event) {
        var message = event.detail && event.detail.message
            ? event.detail.message
            : 'Produto excluido com sucesso.';
        cleanupBootstrapArtifacts();
        showProdutoToast(message, 'success');
        refreshProdutoDashboard();
    }

    function handleProdutoDeleteBlocked(event) {
        var message = event.detail && event.detail.message
            ? event.detail.message
            : 'Produto possui vendas vinculadas e nao pode ser excluido.';
        cleanupBootstrapArtifacts();
        showProdutoToast(message, 'warning');
    }

    document.addEventListener('DOMContentLoaded', function () {
        initProdutoForms(document);
    });

    document.body.addEventListener('htmx:afterSwap', function (event) {
        initProdutoForms(event.target);
    });

    document.body.addEventListener('hidden.bs.modal', cleanupBootstrapArtifacts);
    document.body.addEventListener('produtoSalvo', handleProdutoMutationSuccess);
    document.body.addEventListener('produtoEditado', handleProdutoMutationSuccess);
    document.body.addEventListener('produtoExcluido', handleProdutoDeleted);
    document.body.addEventListener('produtoExclusaoBloqueada', handleProdutoDeleteBlocked);
})();
