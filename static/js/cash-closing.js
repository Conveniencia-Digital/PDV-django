(function () {
    function parseDecimal(value) {
        var raw = String(value || '').trim();
        if (!raw) return 0;
        raw = raw.replace(/[^\d,.-]/g, '');
        if (raw.indexOf(',') !== -1 && raw.indexOf('.') !== -1) {
            raw = raw.replace(/\./g, '').replace(',', '.');
        } else {
            raw = raw.replace(',', '.');
        }
        var parsed = parseFloat(raw);
        return Number.isFinite(parsed) ? parsed : 0;
    }

    function formatCurrency(value) {
        return 'R$ ' + Number(value || 0).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function updateDifference(form) {
        var countedInput = form.querySelector('[name="valor_contado"]');
        var preview = form.querySelector('[data-cash-difference-preview]');
        var valueTarget = form.querySelector('[data-cash-difference-value]');
        var labelTarget = form.querySelector('[data-cash-difference-label]');
        if (!countedInput || !preview || !valueTarget || !labelTarget) return;

        var expected = parseDecimal(form.dataset.expectedBalance);
        var counted = parseDecimal(countedInput.value);
        var difference = counted - expected;

        valueTarget.textContent = formatCurrency(difference);
        preview.classList.remove('success', 'danger', 'neutral');

        if (!String(countedInput.value || '').trim()) {
            preview.classList.add('neutral');
            labelTarget.textContent = 'Informe o valor contado para calcular.';
            valueTarget.textContent = formatCurrency(0);
        } else if (difference > 0) {
            preview.classList.add('success');
            labelTarget.textContent = 'Sobra de Caixa: será registrada como receita.';
        } else if (difference < 0) {
            preview.classList.add('danger');
            labelTarget.textContent = 'Falta de Caixa: será registrada como despesa.';
        } else {
            preview.classList.add('success');
            labelTarget.textContent = 'Caixa balanceado.';
        }
    }

    function initCashClosingForm(form) {
        if (!form || form.dataset.cashClosingInit === '1') return;
        form.dataset.cashClosingInit = '1';
        var countedInput = form.querySelector('[name="valor_contado"]');
        if (countedInput) {
            countedInput.addEventListener('input', function () {
                updateDifference(form);
            });
        }
        updateDifference(form);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('[data-cash-closing-form]').forEach(initCashClosingForm);

        var toastElement = document.getElementById('cashClosingSuccessToast');
        if (toastElement && window.bootstrap && window.bootstrap.Toast) {
            new window.bootstrap.Toast(toastElement, { delay: 2800 }).show();
        }

        if (window.feather) {
            window.feather.replace();
        }
    });
})();
