(function () {
    if (!window.FinanceCharts || !window.FinanceCharts.registerHtmxDashboard) return;

    window.OrcamentoDashboardCharts = FinanceCharts.registerHtmxDashboard({
        name: 'orcamento',
        rootId: 'bloco-dados',
        swapTargetId: 'bloco-dados',
        dataScriptId: 'orcamentoChartsData',
        render: function (context) {
            var root = context.root;
            var data = context.data;
            var charts = context.charts;
            var revenue = data.revenue || {};
            var items = data.items || {};
            var revenueLabels = revenue.labels && revenue.labels.length ? revenue.labels : ['Sem dados'];
            var revenueValues = revenue.values && revenue.values.length ? revenue.values : [0];
            var itemLabels = items.labels && items.labels.length ? items.labels : ['Sem itens'];
            var itemValues = items.revenues && items.revenues.length ? items.revenues : [0];

            var revenueCanvas = root.querySelector('#orcamentoRevenueChart');
            if (revenueCanvas) {
                context.setChart('revenue', charts.lineChart(revenueCanvas, revenueLabels, {
                    label: 'Receita finalizada',
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.12)',
                    pointBackgroundColor: '#198754',
                    fill: true,
                    data: revenueValues
                }));
            }

            var itemsCanvas = root.querySelector('#orcamentoItemsChart');
            if (itemsCanvas) {
                context.setChart('items', charts.barChart(itemsCanvas, itemLabels, [{
                    label: 'Valor solicitado',
                    backgroundColor: '#2470dc',
                    borderColor: '#1849a9',
                    data: itemValues
                }]));
            }
        }
    });
})();
