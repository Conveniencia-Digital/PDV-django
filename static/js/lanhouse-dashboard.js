(function () {
    if (!window.FinanceCharts || !window.FinanceCharts.registerHtmxDashboard) return;

    window.LanhouseDashboardCharts = FinanceCharts.registerHtmxDashboard({
        name: 'lanhouse',
        rootId: 'bloco-dados',
        swapTargetId: 'bloco-dados',
        dataScriptId: 'lanhouseChartsData',
        render: function (context) {
            var root = context.root;
            var data = context.data || {};
            var charts = context.charts;
            var revenue = data.revenue || {};
            var services = data.services || {};
            var revenueLabels = revenue.labels && revenue.labels.length ? revenue.labels : ['Sem dados'];
            var revenueValues = revenue.values && revenue.values.length ? revenue.values : [0];
            var serviceLabels = services.labels && services.labels.length ? services.labels : ['Sem serviços'];
            var serviceValues = services.revenues && services.revenues.length ? services.revenues : [0];

            var revenueCanvas = root.querySelector('#lanhouseRevenueChart');
            if (revenueCanvas) {
                context.setChart('revenue', charts.lineChart(revenueCanvas, revenueLabels, {
                    label: 'Receita',
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.12)',
                    pointBackgroundColor: '#198754',
                    fill: true,
                    data: revenueValues
                }));
            }

            var serviceCanvas = root.querySelector('#lanhouseServiceChart');
            if (serviceCanvas) {
                context.setChart('services', charts.barChart(serviceCanvas, serviceLabels, [{
                    label: 'Receita gerada',
                    backgroundColor: '#2470dc',
                    borderColor: '#1849a9',
                    data: serviceValues
                }]));
            }
        }
    });
})();
