document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
});


// Preenche o seletor de cor quando uma cor sugerida é clicada.
document.querySelectorAll(".color-preset").forEach((botao) => {
  botao.addEventListener("click", () => {
    const seletor = document.querySelector("#cor_destaque");
    if (seletor) seletor.value = botao.dataset.color;
  });
});
