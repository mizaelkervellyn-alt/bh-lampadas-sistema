// Pesquisa dinâmica progressiva: a busca normal por GET continua funcionando sem JavaScript.
(() => {
  const input = document.querySelector('[data-live]');
  const tbody = document.getElementById('resultados');
  const feedback = document.getElementById('estado-busca');
  if (!input || !tbody || !feedback) return;
  const kind = input.dataset.live;
  let timer;
  let request;
  function cell(text, label) {
    const td = document.createElement('td');
    if (label) {
      const strong = document.createElement('strong'); strong.textContent = String(text ?? '—'); td.appendChild(strong);
    } else td.textContent = String(text ?? '—');
    return td;
  }
  function draw(items) {
    tbody.replaceChildren();
    feedback.textContent = `${items.length} ${kind === 'produtos' ? 'produtos encontrados' : 'clientes encontrados'}.`;
    if (!items.length) {
      const tr = document.createElement('tr'), td = cell('Nenhum resultado encontrado.');
      td.colSpan = kind === 'produtos' ? 5 : 4;
      tr.appendChild(td); tbody.appendChild(tr); return;
    }
    for (const item of items) {
      const tr = document.createElement('tr');
      if (kind === 'produtos') {
        const first = cell(item.descricao, true);
        const small = document.createElement('small'); small.className='secondary-line'; small.textContent=item.codigo_space || 'Sem código'; first.appendChild(small); tr.appendChild(first);
        tr.appendChild(cell(item.grupo || '—')); tr.appendChild(cell(item.unidade || '—'));
        tr.appendChild(cell(item.preco_venda_centavos == null ? 'Revisar preço' : `R$ ${(item.preco_venda_centavos / 100).toFixed(2).replace('.', ',')}`));
      } else {
        tr.appendChild(cell(item.nome,true)); tr.appendChild(cell(item.tipo_pessoa));
        tr.appendChild(cell(`${item.cidade || '—'}/${item.uf || '—'}`));
      }
      const actions = document.createElement('td'), link = document.createElement('a');
      link.href=`/${kind}/${encodeURIComponent(item.id)}/editar`;
      link.textContent='Editar'; actions.appendChild(link); tr.appendChild(actions); tbody.appendChild(tr);
    }
  }
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer=setTimeout(async () => {
      if (request) request.abort();
      request=new AbortController();
      feedback.textContent='Pesquisando…';
      try {
        const res=await fetch(`/api/${kind}?q=${encodeURIComponent(input.value)}`, {signal:request.signal,headers:{'Accept':'application/json'}});
        if (!res.ok) throw Error('Não foi possível atualizar a busca');
        draw(await res.json());
      } catch(e) {
        if (e.name !== 'AbortError') feedback.textContent='Busca dinâmica indisponível. Use o botão Pesquisar.';
      }
    },260);
  });
})();
