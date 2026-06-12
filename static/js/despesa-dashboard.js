(function () {
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
                var canvas = root.querySelector('#expenseCategoryChart');

                if (canvas) {
                    context.setChart('category', context.charts.barChart(canvas, category.labels || [], [{
                        label: 'Despesas por categoria',
                        backgroundColor: '#f0ad4e',
                        borderColor: '#c47f10',
                        data: category.values || []
                    }]));
                }

                if (window.feather) {
                    window.feather.replace();
                }
            }
        });
    }

    function modalFormFromEvent(event) {
        var element = event.detail && event.detail.elt ? event.detail.elt : event.target;
        if (!element) return null;
        if (element.matches && element.matches('[data-despesa-modal-form]')) return element;
        return element.closest ? element.closest('[data-despesa-modal-form]') : null;
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

    function syncFiadoFields(form) {
        if (!form) return;

        var formaPagamento = form.querySelector('[name="forma_pagamento"]');
        var fiadoRow = form.querySelector('[data-despesa-fiado-row]');
        if (!formaPagamento || !fiadoRow) return;

        var isFiado = formaPagamento.value === 'Fiado a pagar';
        fiadoRow.hidden = !isFiado;
        fiadoRow.setAttribute('aria-hidden', isFiado ? 'false' : 'true');

        var fields = {
            valor_entrada: 'number',
            qtd_parcela: 'number',
            data_vencimento: 'date'
        };

        Object.keys(fields).forEach(function (name) {
            var field = form.querySelector('[name="' + name + '"]');
            if (!field) return;
            field.type = isFiado ? fields[name] : 'hidden';
        });

        var valorEntrada = form.querySelector('[name="valor_entrada"]');
        if (isFiado && valorEntrada && !valorEntrada.value) {
            valorEntrada.value = '0.00';
        }

        var qtdParcela = form.querySelector('[name="qtd_parcela"]');
        if (isFiado && qtdParcela && !qtdParcela.value) {
            qtdParcela.value = '1';
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
                return;
            }

            form.dataset.despesaFiadoInit = '1';
            var formaPagamento = form.querySelector('[name="forma_pagamento"]');
            if (formaPagamento) {
                formaPagamento.addEventListener('change', function () {
                    syncFiadoFields(form);
                });
            }
            syncFiadoFields(form);
        });
    }

    document.body.addEventListener('htmx:beforeRequest', function (event) {
        setSubmitState(modalFormFromEvent(event), true);
    });

    document.body.addEventListener('htmx:afterRequest', function (event) {
        setSubmitState(modalFormFromEvent(event), false);
    });

    document.body.addEventListener('htmx:responseError', function (event) {
        setSubmitState(modalFormFromEvent(event), false);
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

    document.body.addEventListener('despesaSalva', function () {
        handleSuccess('Despesa cadastrada com sucesso.');
    });

    document.body.addEventListener('despesaEditada', function () {
        handleSuccess('Despesa atualizada com sucesso.');
    });

    document.body.addEventListener('despesaExcluida', function () {
        showToast('Despesa excluida com sucesso.', 'danger');
        cleanupModalArtifacts();
    });

    document.addEventListener('hidden.bs.modal', function (event) {
        if (event.target && event.target.id === 'staticBackdrop') {
            cleanupModalArtifacts();
        }
    });
})();
