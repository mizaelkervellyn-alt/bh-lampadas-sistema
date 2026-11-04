// A janela pywebview utiliza "Salvar como" nativo; no navegador normal
// o link continua baixando o TXT pelo metodo HTTP existente.
(function () {
  'use strict';
  async function interceptarClique(evento) {
    var api = window.pywebview && window.pywebview.api;
    if (!api || typeof api.salvar_txt_pedido !== 'function') {
      // Navegador convencional / ponte ainda nao carregada: seguir o link normal.
      return;
    }
    evento.preventDefault();
    var link = evento.currentTarget;
    var aviso = document.getElementById('status-download-txt');
    var rotulo = link.textContent;
    link.style.pointerEvents = 'none';
    link.setAttribute('aria-disabled', 'true');
    if (aviso) aviso.textContent = 'Preparando TXT...';
    try {
      var resposta = await fetch(link.href, {credentials: 'same-origin'});
      if (!resposta.ok) throw new Error('Nao foi possivel obter o pedido (HTTP ' + resposta.status + ').');
      // Content-Type da rota e Windows-1252, como esperado pela impressora.
      var buffer = await resposta.arrayBuffer();
      var texto = new TextDecoder('windows-1252').decode(buffer);
      var resultado = await api.salvar_txt_pedido(parseInt(link.dataset.pedidoId, 10), texto);
      if (resultado && resultado.status === 'salvo') {
        if (aviso) aviso.textContent = 'TXT salvo: ' + resultado.arquivo;
        else window.alert('TXT salvo: ' + resultado.arquivo);
      } else if (resultado && resultado.status === 'cancelado') {
        if (aviso) aviso.textContent = 'Salvamento cancelado.';
      } else {
        throw new Error((resultado && resultado.mensagem) || 'Falha ao salvar o arquivo TXT.');
      }
    } catch (erro) {
      if (aviso) aviso.textContent = 'Erro ao salvar TXT: ' + erro.message;
      else window.alert('Erro ao salvar TXT: ' + erro.message);
    } finally {
      link.style.pointerEvents = '';
      link.removeAttribute('aria-disabled');
      link.textContent = rotulo;
    }
  }
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('a[data-pedido-id]').forEach(function (link) {
      link.addEventListener('click', interceptarClique);
    });
  });
}());
