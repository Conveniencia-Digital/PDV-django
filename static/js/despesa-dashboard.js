(function () {
    function currencyLabel(value) {
        return 'R$ ' + Number(value || 0).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function diagonalCategoryChart(element, labels, datasets) {
        if (!element || !window.Chart) return null;
        return new Chart(element, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
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
                    xAxes: [{
                        ticks: {
                            minRotation: 45,
                            maxRotation: 45,
                            autoSkip: false
                        }
                    }],
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            callback: function (value) { return currencyLabel(value); }
                        }
                    }]
                }
            }
        });
    }

    function chartLabels(source, emptyLabel) {
        return source && source.labels && source.labels.length ? source.labels : [emptyLabel || 'Sem dados'];
    }

    function chartValues(source) {
        return source && source.values && source.values.length ? source.values : [0];
    }

    function renderCategoryChart(context, key, element, source, datasetOptions, emptyLabel) {
        if (!element) return;

        var dataset = Object.assign({}, datasetOptions, {
            data: chartValues(source)
        });

        try {
            context.setChart(key, diagonalCategoryChart(element, chartLabels(source, emptyLabel), [dataset]));
        } catch (error) {
            context.setChart(key, null);
            element.dataset.chartError = 'true';
        }
    }

    if (window.FinanceCharts && window.FinanceCharts.registerHtmxDashboard) {
        window.DespesaDashboardCharts = FinanceCharts.registerHtmxDashboard({
            name: 'despesa',
            rootId: 'bloco-dados',
            swapTargetId: 'bloco-dados',
            dataScriptId: 'despesaChartsData',
            render: function (context) {
                var root = context.root;
                var data = context.data || {};
                var category = data.category_ranking || {};
                var prolaboreCategory = data.prolabore_category_ranking || {};
                var canvas = root.querySelector('#expenseCategoryChart');
                var prolaboreCanvas = root.querySelector('#prolaboreCategoryChart');

                renderCategoryChart(context, 'category', canvas, category, {
                    label: 'Despesas por categoria',
                    backgroundColor: '#f0ad4e',
                    borderColor: '#c47f10'
                }, 'Sem despesas');

                renderCategoryChart(context, 'prolaboreCategory', prolaboreCanvas, prolaboreCategory, {
                    label: 'Pró-labore por categoria',
                    backgroundColor: '#f59e0b',
                    borderColor: '#b45309'
                }, 'Sem Pró-labore');

                if (window.feather) {
                    window.feather.replace();
                }
            }
        });
    }

    document.body.addEventListener('shown.bs.collapse', function (event) {
        if (
            event.target &&
            event.target.closest &&
            event.target.closest('#bloco-dados') &&
            window.DespesaDashboardCharts &&
            typeof window.DespesaDashboardCharts.resize === 'function'
        ) {
            window.setTimeout(function () {
                window.DespesaDashboardCharts.resize();
            }, 80);
        }
    });

    function modalFormFromEvent(event) {
        var element = event.detail && event.detail.elt ? event.detail.elt : event.target;
        if (!element) return null;
        if (element.matches && element.matches('[data-despesa-modal-form]')) return element;
        if (element.matches && element.matches('[data-despesa-category-form]')) return element;
        if (!element.closest) return null;
        return element.closest('[data-despesa-modal-form], [data-despesa-category-form]');
    }

    function setSubmitState(form, isLoading) {
        if (!form) return;
        var buttons = form.querySelectorAll('button[type="submit"], button:not([type]), input[type="submit"]');
        buttons.forEach(function (button) {
            if (isLoading) {
                if (!button.dataset.originalHtml) {
                    button.dataset.originalHtml = button.innerHTML || button.value || '';
                }
                button.disabled = true;
                if (button.tagName === 'INPUT') {
                    button.value = form.dataset.loadingText || 'Salvando...';
                } else {
                    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>' + (form.dataset.loadingText || 'Salvando...');
                }
            } else {
                button.disabled = false;
                if (button.dataset.originalHtml) {
                    if (button.tagName === 'INPUT') {
                        button.value = button.dataset.originalHtml;
                    } else {
                        button.innerHTML = button.dataset.originalHtml;
                    }
                    delete button.dataset.originalHtml;
                }
            }
        });
    }

    function cleanupModalArtifacts() {
        if (!document.querySelector('.modal.show')) {
            document.body.classList.remove('modal-open');
            document.body.style.removeProperty('overflow');
            document.body.style.removeProperty('padding-right');
            document.querySelectorAll('.modal-backdrop').forEach(function (backdrop) {
                backdrop.remove();
            });
        }
    }

    function closeMainModal() {
        var modalElement = document.getElementById('staticBackdrop');
        closeModalElement(modalElement);
    }

    function closeCategoryModal() {
        var modalElement = document.getElementById('staticBackdrop2');
        closeModalElement(modalElement);
    }

    function closeModalElement(modalElement) {
        if (!modalElement) {
            cleanupModalArtifacts();
            return;
        }

        if (window.bootstrap && window.bootstrap.Modal) {
            var modal = window.bootstrap.Modal.getInstance(modalElement) || new window.bootstrap.Modal(modalElement);
            modal.hide();
        } else {
            modalElement.classList.remove('show');
            modalElement.style.display = 'none';
            modalElement.setAttribute('aria-hidden', 'true');
        }

        window.setTimeout(cleanupModalArtifacts, 250);
    }

    function ensureToastContainer() {
        var container = document.getElementById('despesaToastContainer');
        if (container) return container;

        container = document.createElement('div');
        container.id = 'despesaToastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1085';
        document.body.appendChild(container);
        return container;
    }

    function showToast(message, variant) {
        var toast = document.createElement('div');
        toast.className = 'toast align-items-center text-bg-' + (variant || 'success') + ' border-0';
        toast.setAttribute('role', 'status');
        toast.setAttribute('aria-live', 'polite');
        toast.setAttribute('aria-atomic', 'true');
        toast.innerHTML = [
            '<div class="d-flex">',
            '<div class="toast-body">', message, '</div>',
            '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Fechar"></button>',
            '</div>'
        ].join('');

        ensureToastContainer().appendChild(toast);

        if (window.bootstrap && window.bootstrap.Toast) {
            var instance = new window.bootstrap.Toast(toast, { delay: 2600 });
            toast.addEventListener('hidden.bs.toast', function () {
                toast.remove();
            });
            instance.show();
        } else {
            window.setTimeout(function () {
                toast.remove();
            }, 2600);
        }
    }

    function handleSuccess(message, variant) {
        closeMainModal();
        showToast(message, variant || 'success');
    }

    var recentTriggerRuns = {};
    var triggerActions = {
        despesaSalva: function () {
            handleSuccess('Despesa cadastrada com sucesso.');
        },
        prolaboreSalvo: function () {
            handleSuccess('Pró-labore cadastrado com sucesso.');
        },
        dividaSalva: function () {
            handleSuccess('Dívida cadastrada com sucesso.');
        },
        despesaEditada: function () {
            handleSuccess('Despesa atualizada com sucesso.');
        },
        prolaboreEditado: function () {
            handleSuccess('Pró-labore atualizado com sucesso.');
        },
        dividaEditada: function () {
            handleSuccess('Dívida atualizada com sucesso.');
        },
        despesaExcluida: function () {
            showToast('Despesa excluida com sucesso.', 'danger');
            cleanupModalArtifacts();
        },
        prolaboreExcluido: function () {
            showToast('Pró-labore excluido com sucesso.', 'danger');
            cleanupModalArtifacts();
        },
        dividaExcluida: function () {
            showToast('Dívida excluida com sucesso.', 'danger');
            cleanupModalArtifacts();
        },
        despesaCategoriaSalva: function () {
            showToast('Categoria cadastrada com sucesso.');
        },
        despesaCategoriaEditada: function () {
            closeCategoryModal();
            showToast('Categoria atualizada com sucesso.');
        },
        despesaCategoriaExcluida: function () {
            showToast('Categoria excluida com sucesso.', 'danger');
            cleanupModalArtifacts();
        }
    };

    function runTriggerAction(triggerName) {
        var action = triggerActions[triggerName];
        if (!action) return;

        var now = Date.now();
        if (recentTriggerRuns[triggerName] && now - recentTriggerRuns[triggerName] < 500) {
            return;
        }

        recentTriggerRuns[triggerName] = now;
        action();
    }

    function triggerNamesFromHeader(header) {
        if (!header) return [];

        var value = String(header).trim();
        if (!value) return [];

        if (value.charAt(0) === '{') {
            try {
                return Object.keys(JSON.parse(value));
            } catch (error) {
                return [];
            }
        }

        return value.split(/[\s,]+/).filter(Boolean);
    }

    function runHeaderTriggerActions(event) {
        var xhr = event.detail && event.detail.xhr;
        if (!xhr || !xhr.getResponseHeader) return;

        triggerNamesFromHeader(xhr.getResponseHeader('HX-Trigger')).forEach(runTriggerAction);
    }

    function syncFiadoFields(form) {
        if (!form) return;

        var formaPagamento = form.querySelector('[name="forma_pagamento"]');
        var fiadoRow = form.querySelector('[data-despesa-fiado-row]');
        if (!formaPagamento || !fiadoRow) return;

        var isFiado = formaPagamento.value === 'Fiado a pagar';
        var qtdParcela = form.querySelector('[name="qtd_parcela"]');
        var quantidadeParcelas = qtdParcela && qtdParcela.value ? parseInt(qtdParcela.value, 10) : 1;
        var isParceladoMensal = isFiado && quantidadeParcelas > 1;
        fiadoRow.hidden = !isFiado;
        fiadoRow.setAttribute('aria-hidden', isFiado ? 'false' : 'true');

        var fields = {
            valor_entrada: 'number',
            qtd_parcela: 'number'
        };

        Object.keys(fields).forEach(function (name) {
            var field = form.querySelector('[name="' + name + '"]');
            if (!field) return;
            field.type = isFiado ? fields[name] : 'hidden';
        });

        var dataVencimento = form.querySelector('[name="data_vencimento"]');
        var diaVencimentoParcela = form.querySelector('[name="dia_vencimento_parcela"]');
        var dataVencimentoGroup = form.querySelector('[data-fiado-vencimento-data]');
        var diaVencimentoGroup = form.querySelector('[data-fiado-vencimento-dia]');

        if (dataVencimentoGroup) {
            dataVencimentoGroup.hidden = !isFiado || isParceladoMensal;
            dataVencimentoGroup.setAttribute('aria-hidden', isFiado && !isParceladoMensal ? 'false' : 'true');
        }
        if (diaVencimentoGroup) {
            diaVencimentoGroup.hidden = !isParceladoMensal;
            diaVencimentoGroup.setAttribute('aria-hidden', isParceladoMensal ? 'false' : 'true');
        }
        if (dataVencimento) {
            dataVencimento.type = isFiado && !isParceladoMensal ? 'date' : 'hidden';
            dataVencimento.required = false;
            if (isParceladoMensal || !isFiado) {
                dataVencimento.value = '';
            }
        }
        if (diaVencimentoParcela) {
            diaVencimentoParcela.type = isParceladoMensal ? 'number' : 'hidden';
            diaVencimentoParcela.required = isParceladoMensal;
            if (!isParceladoMensal) {
                diaVencimentoParcela.value = '';
            }
        }

        var valorEntrada = form.querySelector('[name="valor_entrada"]');
        if (isFiado && valorEntrada && !valorEntrada.value) {
            valorEntrada.value = '0.00';
        }

        if (isFiado && qtdParcela && !qtdParcela.value) {
            qtdParcela.value = '1';
        }
    }

    function syncDespesaFixaFields(form) {
        if (!form) return;

        var despesaFixa = form.querySelector('[name="despesa_fixa"]');
        var vencimentoRow = form.querySelector('[data-despesa-fixa-row]');
        if (!despesaFixa || !vencimentoRow) return;

        var isFixed = despesaFixa.checked;
        vencimentoRow.hidden = !isFixed;
        vencimentoRow.setAttribute('aria-hidden', isFixed ? 'false' : 'true');

        var diaVencimento = form.querySelector('[name="dia_vencimento_fixo"]');
        if (!diaVencimento) return;

        diaVencimento.type = isFixed ? 'number' : 'hidden';
        diaVencimento.required = isFixed;
        if (!isFixed) {
            diaVencimento.value = '';
        }
    }

    function initFiadoFields(context) {
        context = context || document;
        var forms = [];

        if (context.matches && context.matches('[data-despesa-modal-form]')) {
            forms.push(context);
        }
        context.querySelectorAll('[data-despesa-modal-form]').forEach(function (form) {
            forms.push(form);
        });

        forms.forEach(function (form) {
            if (form.dataset.despesaFiadoInit === '1') {
                syncFiadoFields(form);
                syncDespesaFixaFields(form);
                return;
            }

            form.dataset.despesaFiadoInit = '1';
            var formaPagamento = form.querySelector('[name="forma_pagamento"]');
            if (formaPagamento) {
                formaPagamento.addEventListener('change', function () {
                    syncFiadoFields(form);
                });
            }
            var qtdParcela = form.querySelector('[name="qtd_parcela"]');
            if (qtdParcela) {
                qtdParcela.addEventListener('input', function () {
                    syncFiadoFields(form);
                });
                qtdParcela.addEventListener('change', function () {
                    syncFiadoFields(form);
                });
            }
            var despesaFixa = form.querySelector('[name="despesa_fixa"]');
            if (despesaFixa) {
                despesaFixa.addEventListener('change', function () {
                    syncDespesaFixaFields(form);
                });
            }
            syncFiadoFields(form);
            syncDespesaFixaFields(form);
        });
    }

    document.body.addEventListener('htmx:beforeRequest', function (event) {
        setSubmitState(modalFormFromEvent(event), true);
    });

    document.body.addEventListener('htmx:afterRequest', function (event) {
        setSubmitState(modalFormFromEvent(event), false);
        runHeaderTriggerActions(event);
    });

    document.body.addEventListener('htmx:responseError', function (event) {
        setSubmitState(modalFormFromEvent(event), false);
    });

    document.body.addEventListener('change', function (event) {
        var target = event.target;
        if (!target || !target.matches || !target.matches('[name="despesa_fixa"]')) return;

        syncDespesaFixaFields(target.closest('[data-despesa-modal-form]'));
    });

    document.body.addEventListener('htmx:afterSwap', function (event) {
        var target = event.detail && event.detail.target ? event.detail.target : event.target;
        if (target) {
            initFiadoFields(target);
        }
        if (target && target.id === 'bloco-dados' && window.feather) {
            window.feather.replace();
        }
    });

    document.addEventListener('DOMContentLoaded', function () {
        initFiadoFields(document);
    });

    Object.keys(triggerActions).forEach(function (triggerName) {
        document.body.addEventListener(triggerName, function () {
            runTriggerAction(triggerName);
        });
    });

    document.addEventListener('hidden.bs.modal', function (event) {
        if (event.target && (event.target.id === 'staticBackdrop' || event.target.id === 'staticBackdrop2')) {
            cleanupModalArtifacts();
        }
    });
})();
