(function () {
    if (window.FinanceCharts) return;

    function currencyLabel(value) {
        return 'R$ ' + Number(value || 0).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function defaultOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            legend: { labels: { boxWidth: 14 } },
            tooltips: {
                callbacks: {
                    label: function (tooltipItem, data) {
                        var dataset = data.datasets[tooltipItem.datasetIndex];
                        return dataset.label + ': ' + currencyLabel(tooltipItem.yLabel || tooltipItem.value);
                    }
                }
            },
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true,
                        callback: function (value) { return currencyLabel(value); }
                    }
                }]
            }
        };
    }

    function barChart(element, labels, datasets) {
        if (!element || !window.Chart) return null;
        return new Chart(element, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: defaultOptions()
        });
    }

    function lineChart(element, labels, dataset) {
        if (!element || !window.Chart) return null;
        return new Chart(element, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [dataset]
            },
            options: defaultOptions()
        });
    }

    function doughnutChart(element, labels, values, colors) {
        if (!element || !window.Chart) return null;
        return new Chart(element, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors || ['#198754', '#2470dc', '#f0ad4e', '#6f42c1', '#0dcaf0']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: { position: 'bottom' },
                tooltips: {
                    callbacks: {
                        label: function (tooltipItem, data) {
                            var label = data.labels[tooltipItem.index] || '';
                            var value = data.datasets[0].data[tooltipItem.index] || 0;
                            return label + ': ' + currencyLabel(value);
                        }
                    }
                }
            }
        });
    }

    function registerHtmxDashboard(config) {
        var charts = {};
        var pendingInit = null;
        var chartReadyAttempts = 0;
        var rootId = config.rootId || 'bloco-dados';
        var targetId = config.swapTargetId || rootId;

        function destroyChart(key) {
            if (charts[key] && typeof charts[key].destroy === 'function') {
                charts[key].destroy();
            }
            charts[key] = null;
        }

        function destroyAll() {
            Object.keys(charts).forEach(destroyChart);
        }

        function resizeAll() {
            Object.keys(charts).forEach(function (key) {
                if (charts[key] && typeof charts[key].resize === 'function') {
                    charts[key].resize();
                }
            });
        }

        function liveRoot() {
            return document.getElementById(rootId);
        }

        function findRoot(context, allowDocument) {
            var currentRoot = liveRoot();
            if (!context) return currentRoot || (allowDocument ? document : null);
            if (context === document) return currentRoot || document;
            if (context.id === rootId) return context.isConnected ? context : currentRoot;
            if (context.querySelector && context.querySelector('#' + rootId)) {
                return context.querySelector('#' + rootId);
            }
            return currentRoot || (allowDocument ? document : null);
        }

        function readData(root) {
            var dataElement = root.querySelector('#' + config.dataScriptId) || document.getElementById(config.dataScriptId);
            if (!dataElement) return null;
            try {
                return JSON.parse(dataElement.textContent);
            } catch (error) {
                return null;
            }
        }

        function setChart(key, chart) {
            destroyChart(key);
            charts[key] = chart;
        }

        function initNow(context, allowDocument) {
            if (!window.Chart && chartReadyAttempts < 20) {
                chartReadyAttempts += 1;
                window.setTimeout(function () {
                    scheduleInit(context, allowDocument);
                }, 100);
                return;
            }

            var root = findRoot(context, allowDocument);
            if (!root) return;

            var data = readData(root);
            if (!data) return;

            chartReadyAttempts = 0;
            destroyAll();
            config.render({
                root: root,
                data: data,
                setChart: setChart,
                charts: window.FinanceCharts
            });
            window.setTimeout(resizeAll, 80);
        }

        function scheduleInit(context, allowDocument) {
            if (pendingInit) {
                window.cancelAnimationFrame(pendingInit);
            }
            pendingInit = window.requestAnimationFrame(function () {
                pendingInit = window.requestAnimationFrame(function () {
                    pendingInit = null;
                    initNow(context, allowDocument);
                });
            });
        }

        function scheduleStableInit(context, allowDocument) {
            scheduleInit(context, allowDocument);
            window.setTimeout(function () {
                scheduleInit(context, allowDocument);
            }, 250);
            window.setTimeout(function () {
                scheduleInit(context, allowDocument);
            }, 700);
        }

        function swapTouchesDashboard(target) {
            return Boolean(
                target &&
                (
                    target.id === targetId ||
                    target.id === rootId ||
                    (target.querySelector && (target.querySelector('#' + targetId) || target.querySelector('#' + rootId)))
                )
            );
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function () {
                scheduleStableInit(document, true);
            });
        } else {
            scheduleStableInit(document, true);
        }

        window.addEventListener('load', function () {
            scheduleStableInit(document, true);
        });

        document.body.addEventListener('htmx:beforeSwap', function (event) {
            if (swapTouchesDashboard(event.detail.target)) {
                destroyAll();
            }
        });

        document.body.addEventListener('htmx:afterSwap', function (event) {
            var target = event.detail && event.detail.target ? event.detail.target : event.target;
            if (swapTouchesDashboard(target)) {
                scheduleStableInit(document, true);
            }
        });

        window.addEventListener('resize', function () {
            window.clearTimeout(window['_' + (config.name || rootId) + 'DashboardResizeTimer']);
            window['_' + (config.name || rootId) + 'DashboardResizeTimer'] = window.setTimeout(resizeAll, 120);
        });

        return {
            init: function (context) {
                scheduleInit(context || document, context === document);
            },
            destroy: destroyAll,
            resize: resizeAll
        };
    }

    window.FinanceCharts = {
        currencyLabel: currencyLabel,
        defaultOptions: defaultOptions,
        barChart: barChart,
        lineChart: lineChart,
        doughnutChart: doughnutChart,
        registerHtmxDashboard: registerHtmxDashboard
    };
})();
