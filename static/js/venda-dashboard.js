(function () {
    if (!window.FinanceCharts || !window.FinanceCharts.registerHtmxDashboard) return;

    window.VendaDashboardCharts = FinanceCharts.registerHtmxDashboard({
        name: 'venda',
        rootId: 'bloco-dados',
        swapTargetId: 'bloco-dados',
        dataScriptId: 'vendasChartsData',
        render: function (context) {
            var root = context.root;
            var data = context.data || {};
            var charts = context.charts;
            var revenue = data.revenue || {};
            var products = data.products || {};
            var revenueLabels = revenue.labels && revenue.labels.length ? revenue.labels : ['Sem dados'];
            var revenueValues = revenue.values && revenue.values.length ? revenue.values : [0];
            var productLabels = products.labels && products.labels.length ? products.labels : ['Sem produtos'];
            var productValues = products.revenues && products.revenues.length ? products.revenues : [0];

            var revenueCanvas = root.querySelector('#vendasRevenueChart');
            if (revenueCanvas) {
                context.setChart('revenue', charts.lineChart(revenueCanvas, revenueLabels, {
                    label: 'Receita entregue',
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.12)',
                    pointBackgroundColor: '#198754',
                    fill: true,
                    data: revenueValues
                }));
            }

            var productCanvas = root.querySelector('#vendasProductChart');
            if (productCanvas) {
                context.setChart('products', charts.barChart(productCanvas, productLabels, [{
                    label: 'Receita gerada',
                    backgroundColor: '#2470dc',
                    borderColor: '#1849a9',
                    data: productValues
                }]));
            }

            if (window.feather) {
                window.feather.replace();
            }
        }
    });
})();
