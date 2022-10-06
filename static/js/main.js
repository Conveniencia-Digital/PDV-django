(function() {
  // Chama o método pra numerar os objetos ao carregar a página.
  reorderItems()
})();

document.querySelector('#addItem').addEventListener('click', function() {
  setTimeout(() => {
    reorderItems()
  }, 500)
})

function reorderItems() {
  Array.from(document.querySelectorAll("[id^='item-']"))
    .forEach((item, i) => {
      item.setAttribute('id', 'item-' + i)

      if (!item.querySelector('[data-field="vendas"]')) {
        return
      }

      item.querySelector('[data-field="vendas"]').setAttribute('name', 'items-' + i + '-vendas')
      item.querySelector('[data-field="vendas"]').setAttribute('id', 'id_items-' + i + '-vendas')

      item.querySelector('[data-field="produto"]').setAttribute('name', 'items-' + i + '-produto')
      item.querySelector('[data-field="produto"]').setAttribute('hx-target', '#id_items-'+ i +'-preco')


      item.querySelector('[data-field="quantidade"]').setAttribute('name', 'items-' + i + '-quantidade')

      item.querySelector('[data-field="preco"]').setAttribute('name', 'items-' + i + '-preco')
      item.querySelector('[data-field="preco"]').setAttribute('id', 'id_items-' + i + '-preco')
  })

  Array.from(document.querySelectorAll("#id_id"))
    .forEach((item, i) => item.setAttribute('name', 'items-' + (i + 1) + '-id'))

  let totalItems = $('#venda').children().length
  document.querySelector('#id_items-TOTAL_FORMS').value = totalItems

  // htmx.org/api/#process
  htmx.process(document.querySelector("#venda"))
}

function removeRow() {
  const span = event.target.parentNode
  const div = span.parentNode
  div.parentNode.removeChild(div)

  reorderItems()
}

Array.from(document.querySelectorAll('.remove-row'))
  .forEach((item, i) => {
    item.addEventListener('click', function() {
      document.querySelector('button[type="submit"]').style.display = 'none'
      document.querySelector('#btn-close').style.display = 'block' // seleciona o id #btn close e adiciona css
    })
  })