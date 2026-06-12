(function () {
  if (window.CardFeePreview) return;

  function parseDecimal(value) {
    var parsed = parseFloat(String(value || '0').replace(',', '.'));
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function formatMoney(value) {
    return parseDecimal(value).toFixed(2);
  }

  function isCardPayment(value) {
    return value === 'Cartāo de credito' || value === 'Cartāo de debito';
  }

  function isCreditPayment(value) {
    return value === 'Cartāo de credito';
  }

  function getBaseAmount(form) {
    var selector = form.dataset.cardTotalTarget || '#totalValue';
    var totalInput = form.querySelector(selector);
    return formatMoney(totalInput ? totalInput.value : 0);
  }

  function setHidden(form, name, value) {
    var field = form.querySelector('[data-card-hidden="' + name + '"]');
    if (field) field.value = value === null || value === undefined ? '' : value;
  }

  function setDisplay(form, name, value) {
    var field = form.querySelector('[data-card-display="' + name + '"]');
    if (!field) return;
    field.value = name === 'fee_percentage' ? formatMoney(value) + '%' : formatMoney(value);
  }

  function setMessage(form, message, isError) {
    var messageBox = form.querySelector('[data-card-fee-message]');
    if (!messageBox) return;
    messageBox.textContent = message || '';
    messageBox.classList.toggle('text-danger', Boolean(isError && message));
    messageBox.classList.toggle('text-muted', Boolean(!isError && message));
  }

  function applyPreview(form, data) {
    data = data || {};
    var baseAmount = data.base_amount || getBaseAmount(form);
    var finalAmount = data.final_amount || baseAmount;

    setHidden(form, 'payment_type', data.payment_type || '');
    setHidden(form, 'fee_percentage', data.fee_percentage || '0.00');
    setHidden(form, 'fee_amount', data.fee_amount || '0.00');
    setHidden(form, 'base_amount', baseAmount);
    setHidden(form, 'final_amount', finalAmount);
    setDisplay(form, 'fee_percentage', data.fee_percentage || 0);
    setDisplay(form, 'base_amount', baseAmount);
    setDisplay(form, 'fee_amount', data.fee_amount || 0);
    setDisplay(form, 'final_amount', finalAmount);
    setMessage(form, data.message || '', false);
  }

  function reset(form) {
    var baseAmount = getBaseAmount(form);
    applyPreview(form, {
      payment_type: '',
      fee_percentage: '0.00',
      fee_amount: '0.00',
      base_amount: baseAmount,
      final_amount: baseAmount,
      message: '',
    });
  }

  function recalculate(form) {
    var formaPagamento = form.querySelector('[name$="forma_pagamento"]');
    var cardSection = form.querySelector('[data-card-payment-section]');
    if (!formaPagamento || !cardSection || cardSection.hidden) {
      reset(form);
      return;
    }

    var machine = form.querySelector('[name$="card_machine"]');
    var installments = form.querySelector('[name$="card_installments"]');
    var passFee = form.querySelector('[name$="pass_card_fee_to_customer"]');
    var baseAmount = getBaseAmount(form);

    if (!machine || !machine.value) {
      applyPreview(form, {
        payment_type: '',
        fee_percentage: '0.00',
        fee_amount: '0.00',
        base_amount: baseAmount,
        final_amount: baseAmount,
        message: 'Selecione a máquina de cartão.',
      });
      setMessage(form, 'Selecione a máquina de cartão.', true);
      return;
    }

    var url = form.dataset.cardFeeUrl;
    if (!url) return;

    if (form._cardFeeController) {
      form._cardFeeController.abort();
    }
    form._cardFeeController = new AbortController();

    var params = new URLSearchParams({
      forma_pagamento: formaPagamento.value,
      card_machine: machine.value,
      installments: installments ? installments.value : '',
      base_amount: baseAmount,
      pass_fee: passFee && passFee.checked ? '1' : '0',
    });

    fetch(url + '?' + params.toString(), {
      credentials: 'same-origin',
      signal: form._cardFeeController.signal,
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then(function (response) {
        return response.json().then(function (data) {
          data._error = !response.ok;
          return data;
        });
      })
      .then(function (data) {
        applyPreview(form, data);
        setMessage(form, data.message || '', data._error);
      })
      .catch(function (error) {
        if (error.name === 'AbortError') return;
        setMessage(form, 'Não foi possível carregar a taxa da maquininha.', true);
      });
  }

  function updateVisibility(form) {
    var formaPagamento = form.querySelector('[name$="forma_pagamento"]');
    var cardSection = form.querySelector('[data-card-payment-section]');
    var installmentsWrap = form.querySelector('[data-card-installments-wrap]');
    var installments = form.querySelector('[name$="card_installments"]');
    if (!formaPagamento || !cardSection) return;

    var isCard = isCardPayment(formaPagamento.value);
    var isCredit = isCreditPayment(formaPagamento.value);
    cardSection.hidden = !isCard;
    cardSection.setAttribute('aria-hidden', isCard ? 'false' : 'true');

    if (installmentsWrap) {
      installmentsWrap.hidden = !isCredit;
      installmentsWrap.setAttribute('aria-hidden', isCredit ? 'false' : 'true');
    }
    if (installments && isCredit && !installments.value) {
      installments.value = '1';
    }

    if (!isCard) {
      reset(form);
      return;
    }
    recalculate(form);
  }

  window.CardFeePreview = {
    recalculate: recalculate,
    reset: reset,
    updateVisibility: updateVisibility,
  };
})();
