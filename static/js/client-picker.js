(function () {
  if (window.ClientPicker) return;

  var activePicker = null;
  var pendingCreatePicker = null;

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function normalizeClient(client) {
    client = client || {};
    return {
      id: String(client.id || ''),
      text: client.text || client.name || '',
      name: client.name || client.text || '',
      phone: client.phone || '',
      phone_secondary: client.phone_secondary || '',
      cpf: client.cpf || '',
      price: client.price || '',
      cost: client.cost || '',
      meta: client.meta || ''
    };
  }

  function getNativeSelect(root) {
    return root.querySelector('[data-client-picker-native]');
  }

  function getSelectedFromNative(root) {
    var select = getNativeSelect(root);
    if (!select || !select.value) return null;
    var option = select.options[select.selectedIndex];
    if (!option) return null;
    var price = option.dataset.price || '';
    if (!price && root.dataset.priceTarget) {
      var scope = root.closest('[data-linha-item]') || root.closest('form') || document;
      var priceField = scope.querySelector(root.dataset.priceTarget);
      price = priceField ? priceField.value : '';
    }
    return normalizeClient({
      id: option.value,
      text: option.textContent,
      name: option.textContent,
      phone: option.dataset.phone || '',
      price: price,
      cost: option.dataset.cost || '',
      meta: option.dataset.meta || (price ? 'R$ ' + price : '')
    });
  }

  function updateSelectedDisplay(root, client) {
    var selectedName = root.querySelector('[data-client-picker-selected-name]');
    var selectedMeta = root.querySelector('[data-client-picker-selected-meta]');
    var placeholder = root.dataset.placeholder || 'Selecione um cliente';
    client = client ? normalizeClient(client) : null;

    if (!selectedName || !selectedMeta) return;

    if (client && client.id) {
      selectedName.textContent = client.name || client.text;
      selectedMeta.textContent = client.meta || client.phone || client.cpf || client.price || 'Item selecionado';
      root.classList.add('has-value');
    } else {
      selectedName.textContent = placeholder;
      selectedMeta.textContent = root.dataset.metaPlaceholder || 'Busque pelo texto desejado';
      root.classList.remove('has-value');
    }
  }

  function ensureOption(select, client) {
    var id = String(client.id);
    var option = Array.from(select.options).find(function (item) {
      return item.value === id;
    });

    if (!option) {
      option = new Option(client.text || client.name, id, true, true);
      select.add(option);
    }

    option.textContent = client.text || client.name;
    option.dataset.phone = client.phone || '';
    option.dataset.price = client.price || '';
    option.dataset.cost = client.cost || '';
    option.dataset.meta = client.meta || '';
    option.selected = true;
    select.value = id;
  }

  function applySelectionEffects(root, client) {
    if (!client.price) return;

    var targetSelector = root.dataset.priceTarget;
    if (!targetSelector) return;

    var scope = root.closest('[data-linha-item]') || root.closest('form') || document;
    var priceField = scope.querySelector(targetSelector);
    if (!priceField) return;

    priceField.value = client.price;
    priceField.dispatchEvent(new Event('input', { bubbles: true }));
    priceField.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function triggerNativeChange(select, client) {
    select.dispatchEvent(new Event('input', { bubbles: true }));
    select.dispatchEvent(new Event('change', { bubbles: true }));

    if (window.jQuery) {
      var $select = window.jQuery(select);
      $select.trigger('change');
      if ($select.data('select2')) {
        $select.trigger({
          type: 'select2:select',
          params: { data: client }
        });
      }
    }
  }

  function selectClient(root, client, shouldClose) {
    var select = getNativeSelect(root);
    if (!select || !client || !client.id) return;
    client = normalizeClient(client);

    ensureOption(select, client);
    updateSelectedDisplay(root, client);
    applySelectionEffects(root, client);
    triggerNativeChange(select, client);
    root.dispatchEvent(new CustomEvent('client-picker:selected', {
      bubbles: true,
      detail: client
    }));

    if (shouldClose !== false) {
      closePicker(root);
    }
  }

  function setActiveIndex(root, index) {
    var options = Array.from(root.querySelectorAll('[data-client-picker-option]'));
    if (!options.length) return;

    if (index < 0) index = options.length - 1;
    if (index >= options.length) index = 0;

    options.forEach(function (option, optionIndex) {
      option.classList.toggle('is-active', optionIndex === index);
      option.setAttribute('aria-selected', optionIndex === index ? 'true' : 'false');
    });

    root.dataset.activeIndex = String(index);
    options[index].scrollIntoView({ block: 'nearest' });
  }

  function renderMessage(root, message, className) {
    var results = root.querySelector('[data-client-picker-results]');
    if (!results) return;
    results.innerHTML = '<div class="' + className + '">' + escapeHtml(message) + '</div>';
    root.dataset.activeIndex = '-1';
  }

  function renderResults(root, clients) {
    var results = root.querySelector('[data-client-picker-results]');
    var select = getNativeSelect(root);
    var selectedId = select ? String(select.value || '') : '';
    if (!results) return;

    if (!clients.length) {
      renderMessage(root, root.dataset.emptyText || 'Nenhum resultado encontrado.', 'client-picker-empty');
      return;
    }

    results.innerHTML = clients.map(function (rawClient) {
      var client = normalizeClient(rawClient);
      var meta = client.meta || client.phone || client.cpf || client.price || 'Sem informação adicional';
      var selectedClass = client.id === selectedId ? ' is-selected' : '';
      return [
        '<button type="button"',
        ' class="client-picker-option' + selectedClass + '"',
        ' role="option"',
        ' data-client-picker-option',
        ' data-client-id="' + escapeHtml(client.id) + '"',
        ' data-client-text="' + escapeHtml(client.text) + '"',
        ' data-client-name="' + escapeHtml(client.name) + '"',
        ' data-client-phone="' + escapeHtml(client.phone) + '"',
        ' data-client-cpf="' + escapeHtml(client.cpf) + '"',
        ' data-client-price="' + escapeHtml(client.price) + '"',
        ' data-client-cost="' + escapeHtml(client.cost) + '"',
        ' data-client-meta="' + escapeHtml(client.meta) + '"',
        ' aria-selected="false">',
        '<span class="client-picker-option-name">' + escapeHtml(client.name || client.text) + '</span>',
        '<span class="client-picker-option-meta">' + escapeHtml(meta) + '</span>',
        '</button>'
      ].join('');
    }).join('');

    setActiveIndex(root, 0);
  }

  function loadClients(root, query) {
    var url = root.dataset.searchUrl;
    if (!url) return;

    if (root._clientPickerController) {
      root._clientPickerController.abort();
    }

    root._clientPickerController = new AbortController();
    renderMessage(root, 'Buscando...', 'client-picker-loading');

    var separator = url.indexOf('?') === -1 ? '?' : '&';
    fetch(url + separator + 'q=' + encodeURIComponent(query || ''), {
      credentials: 'same-origin',
      signal: root._clientPickerController.signal,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (response) {
        if (!response.ok) throw new Error('Erro ao buscar.');
        return response.json();
      })
      .then(function (data) {
        renderResults(root, (data && data.results) || []);
      })
      .catch(function (error) {
        if (error.name === 'AbortError') return;
        renderMessage(root, 'Nao foi possivel carregar os resultados.', 'client-picker-empty');
      });
  }

  function openPicker(root) {
    var dropdown = root.querySelector('[data-client-picker-dropdown]');
    var trigger = root.querySelector('[data-client-picker-trigger]');
    var search = root.querySelector('[data-client-picker-search]');
    if (!dropdown || !trigger || !search) return;

    if (activePicker && activePicker !== root) {
      closePicker(activePicker);
    }

    dropdown.hidden = false;
    root.classList.add('is-open');
    trigger.setAttribute('aria-expanded', 'true');
    activePicker = root;

    loadClients(root, search.value);
    window.setTimeout(function () {
      search.focus();
      search.select();
    }, 0);
  }

  function closePicker(root) {
    if (!root) return;
    var dropdown = root.querySelector('[data-client-picker-dropdown]');
    var trigger = root.querySelector('[data-client-picker-trigger]');
    if (dropdown) dropdown.hidden = true;
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
    root.classList.remove('is-open');
    root.dataset.activeIndex = '-1';
    if (activePicker === root) activePicker = null;
  }

  function optionClient(option) {
    return normalizeClient({
      id: option.dataset.clientId,
      text: option.dataset.clientText,
      name: option.dataset.clientName,
      phone: option.dataset.clientPhone,
      cpf: option.dataset.clientCpf,
      price: option.dataset.clientPrice,
      cost: option.dataset.clientCost,
      meta: option.dataset.clientMeta
    });
  }

  function selectActiveOption(root) {
    var options = Array.from(root.querySelectorAll('[data-client-picker-option]'));
    var index = parseInt(root.dataset.activeIndex || '0', 10);
    if (options[index]) {
      selectClient(root, optionClient(options[index]), true);
    }
  }

  function debounce(fn, delay) {
    var timeoutId = null;
    return function () {
      var args = arguments;
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(function () {
        fn.apply(null, args);
      }, delay);
    };
  }

  function initPicker(root) {
    if (!root || root.dataset.clientPickerInit === '1') return;
    root.dataset.clientPickerInit = '1';
    root.dataset.activeIndex = '-1';

    var trigger = root.querySelector('[data-client-picker-trigger]');
    var search = root.querySelector('[data-client-picker-search]');
    var results = root.querySelector('[data-client-picker-results]');
    var create = root.querySelector('[data-client-picker-create]');
    var select = getNativeSelect(root);
    var searchDebounced = debounce(function () {
      loadClients(root, search.value);
    }, 180);

    updateSelectedDisplay(root, getSelectedFromNative(root));

    if (trigger) {
      trigger.addEventListener('click', function () {
        if (root.classList.contains('is-open')) {
          closePicker(root);
        } else {
          openPicker(root);
        }
      });

      trigger.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' || event.key === ' ' || event.key === 'ArrowDown') {
          event.preventDefault();
          openPicker(root);
        }
      });
    }

    if (search) {
      search.addEventListener('input', searchDebounced);
      search.addEventListener('keydown', function (event) {
        var options = Array.from(root.querySelectorAll('[data-client-picker-option]'));
        var index = parseInt(root.dataset.activeIndex || '0', 10);

        if (event.key === 'ArrowDown') {
          event.preventDefault();
          setActiveIndex(root, index + 1);
        } else if (event.key === 'ArrowUp') {
          event.preventDefault();
          setActiveIndex(root, index - 1);
        } else if (event.key === 'Enter') {
          if (options.length) {
            event.preventDefault();
            selectActiveOption(root);
          }
        } else if (event.key === 'Escape') {
          event.preventDefault();
          closePicker(root);
          if (trigger) trigger.focus();
        }
      });
    }

    if (results) {
      results.addEventListener('mousemove', function (event) {
        var option = event.target.closest('[data-client-picker-option]');
        if (!option) return;
        var options = Array.from(root.querySelectorAll('[data-client-picker-option]'));
        setActiveIndex(root, options.indexOf(option));
      });

      results.addEventListener('click', function (event) {
        var option = event.target.closest('[data-client-picker-option]');
        if (!option) return;
        selectClient(root, optionClient(option), true);
      });
    }

    if (create) {
      create.addEventListener('click', function () {
        pendingCreatePicker = root;
        closePicker(root);
      });
    }

    if (select) {
      select.addEventListener('change', function () {
        updateSelectedDisplay(root, getSelectedFromNative(root));
      });
    }
  }

  function initPickers(context) {
    context = context || document;
    if (context.matches && context.matches('[data-client-picker]')) {
      initPicker(context);
    }
    context.querySelectorAll('[data-client-picker]').forEach(initPicker);
  }

  function closeClientModal(picker) {
    var modalId = picker?.dataset.childModalId || 'clientePickerModal';
    var modal = document.getElementById(modalId);
    if (!modal || !window.bootstrap) return;
    var instance = window.bootstrap.Modal.getInstance(modal);
    if (!instance) instance = new window.bootstrap.Modal(modal);
    instance.hide();
  }

  function handleCreatedClient(event) {
    var detail = event.detail || {};
    var client = normalizeClient(detail.id ? detail : detail.value);
    var picker = pendingCreatePicker || activePicker || document.querySelector('[data-client-picker]');

    if (picker && client.id) {
      selectClient(picker, client, true);
    }

    closeClientModal(picker);
    pendingCreatePicker = null;
  }

  document.addEventListener('click', function (event) {
    if (activePicker && !activePicker.contains(event.target)) {
      closePicker(activePicker);
    }
  });

  document.body.addEventListener('clienteCriado', handleCreatedClient);
  document.body.addEventListener('lanhouseServicoCriado', handleCreatedClient);
  document.body.addEventListener('orcamentoServicoCriado', handleCreatedClient);
  document.body.addEventListener('orcamentoPecaCriada', handleCreatedClient);
  document.body.addEventListener('produtoCategoriaCriada', handleCreatedClient);
  document.body.addEventListener('despesaCategoriaCriada', handleCreatedClient);
  document.body.addEventListener('fornecedorCriado', handleCreatedClient);
  document.body.addEventListener('htmx:afterSwap', function (event) {
    initPickers(event.target);
  });

  document.addEventListener('show.bs.modal', function (event) {
    if (!event.target.classList.contains('client-picker-client-modal')) return;
    event.target.style.zIndex = 1080;
    window.setTimeout(function () {
      var backdrops = document.querySelectorAll('.modal-backdrop:not(.client-picker-modal-backdrop)');
      var backdrop = backdrops[backdrops.length - 1];
      if (backdrop) {
        backdrop.classList.add('client-picker-modal-backdrop');
      }
    }, 0);
  });

  document.addEventListener('hidden.bs.modal', function (event) {
    if (!event.target.classList.contains('client-picker-client-modal')) return;
    if (document.querySelector('.modal.show')) {
      document.body.classList.add('modal-open');
    }
  });

  document.addEventListener('DOMContentLoaded', function () {
    initPickers(document);
  });

  window.ClientPicker = {
    init: initPickers,
    select: selectClient
  };
})();
