(function () {
  var boundKey = 'profitMarginCalculatorBound';

  function parseDecimal(value) {
    var raw = String(value || '').trim();
    if (!raw) {
      return 0;
    }

    raw = raw.replace(/[^\d,.-]/g, '');
    if (raw.indexOf(',') !== -1 && raw.indexOf('.') !== -1) {
      raw = raw.replace(/\./g, '').replace(',', '.');
    } else {
      raw = raw.replace(',', '.');
    }

    var parsed = parseFloat(raw);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function isFilled(input) {
    return input && String(input.value || '').trim() !== '';
  }

  function formatDecimal(value) {
    return Number(value || 0).toFixed(2);
  }

  function getField(root, name) {
    return root.querySelector('[data-pricing-field="' + name + '"]');
  }

  function getBasis(root) {
    var hidden = root.querySelector('[data-pricing-last-edited]');
    return hidden ? hidden.value : root.dataset.pricingBasis;
  }

  function setBasis(root, basis) {
    var hidden = root.querySelector('[data-pricing-last-edited]');
    if (hidden) {
      hidden.value = basis;
    }
    root.dataset.pricingBasis = basis;
  }

  function inferBasis(root) {
    var margin = getField(root, 'margin');
    var price = getField(root, 'price');
    if (isFilled(margin)) {
      return 'margin';
    }
    if (isFilled(price)) {
      return 'price';
    }
    return '';
  }

  function calculate(root) {
    var costInput = getField(root, 'cost');
    var marginInput = getField(root, 'margin');
    var priceInput = getField(root, 'price');

    if (!costInput || !marginInput || !priceInput || !isFilled(costInput)) {
      return;
    }

    var basis = getBasis(root) || inferBasis(root);
    var cost = parseDecimal(costInput.value);
    var margin = parseDecimal(marginInput.value);
    var price = parseDecimal(priceInput.value);

    if (basis === 'margin' && isFilled(marginInput)) {
      priceInput.value = margin < 100 ? formatDecimal(cost / (1 - margin / 100)) : '0.00';
      setBasis(root, 'margin');
      return;
    }

    if (basis === 'price' && isFilled(priceInput)) {
      marginInput.value = price > cost ? formatDecimal((1 - (cost / price)) * 100) : '0.00';
      setBasis(root, 'price');
    }
  }

  function bind(root) {
    if (!root || root.dataset[boundKey] === 'true') {
      return;
    }

    var costInput = getField(root, 'cost');
    var marginInput = getField(root, 'margin');
    var priceInput = getField(root, 'price');
    if (!costInput || !marginInput || !priceInput) {
      return;
    }

    [costInput, marginInput, priceInput].forEach(function (input) {
      input.addEventListener('input', function () {
        var field = input.getAttribute('data-pricing-field');
        if (field === 'margin' || field === 'price') {
          setBasis(root, field);
        } else if (!getBasis(root)) {
          setBasis(root, inferBasis(root));
        }
        calculate(root);
      });
    });

    root.dataset[boundKey] = 'true';
  }

  function initAll(context) {
    var root = context || document;
    if (root.matches && root.matches('[data-profit-margin-calculator]')) {
      bind(root);
    }
    root.querySelectorAll('[data-profit-margin-calculator]').forEach(bind);
  }

  window.ProfitMarginCalculator = {
    init: bind,
    initAll: initAll,
  };

  document.addEventListener('DOMContentLoaded', function () {
    initAll(document);
  });

  document.body.addEventListener('htmx:afterSwap', function (event) {
    initAll(event.target);
  });
})();
