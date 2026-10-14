(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var input = document.getElementById('tags');
    var list = document.getElementById('tags-suggestions');
    if (!input || !list) return;

    // [[nom, nombre d'utilisations], ...] déjà trié par fréquence
    var allTags = JSON.parse(input.dataset.tags || '[]');
    var shown = [];
    var active = -1;

    // Minuscules + sans accents : "ecole" retrouve "école"
    function norm(text) {
      return text.toLowerCase().normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '').trim();
    }

    // Tag en cours de saisie : entre les virgules autour du curseur
    function currentSegment() {
      var value = input.value;
      var pos = input.selectionStart;
      var start = value.slice(0, pos).lastIndexOf(',') + 1;
      var end = value.indexOf(',', pos);
      if (end === -1) end = value.length;
      var index = value.slice(0, pos).split(',').length - 1;
      return { start: start, end: end, index: index,
               text: value.slice(start, end).trim() };
    }

    function hide() {
      list.hidden = true;
      active = -1;
    }

    function setActive(i) {
      var items = list.children;
      if (!items.length) return;
      if (active >= 0) items[active].classList.remove('active');
      active = (i + items.length) % items.length;
      items[active].classList.add('active');
      items[active].scrollIntoView({ block: 'nearest' });
    }

    function pick(name) {
      var seg = currentSegment();
      var left = input.value.slice(0, seg.start).replace(/\s+$/, '');
      var tail = input.value.slice(seg.end);   // vide ou commence par ","
      var prefix = left ? left + ' ' : '';
      input.value = prefix + name + (tail || ', ');
      var caret = (prefix + name).length + (tail ? 0 : 2);
      input.setSelectionRange(caret, caret);
      hide();
      input.focus();
    }

    function render() {
      var seg = currentSegment();
      var query = norm(seg.text);
      if (!query) return hide();

      // Tags déjà saisis dans le champ (hors segment en cours)
      var used = input.value.split(',')
        .filter(function (_, i) { return i !== seg.index; })
        .map(norm);

      shown = allTags
        .filter(function (t) {
          var n = norm(t[0]);
          return n.indexOf(query) !== -1 && n !== query && used.indexOf(n) === -1;
        })
        .sort(function (a, b) {
          var sa = norm(a[0]).indexOf(query) === 0 ? 0 : 1;
          var sb = norm(b[0]).indexOf(query) === 0 ? 0 : 1;
          return sa - sb || b[1] - a[1];
        })
        .slice(0, 8);

      if (!shown.length) return hide();

      list.innerHTML = '';
      shown.forEach(function (t) {
        var li = document.createElement('li');
        li.setAttribute('role', 'option');
        var name = document.createElement('span');
        name.textContent = t[0];
        var count = document.createElement('small');
        count.textContent = t[1];
        li.appendChild(name);
        li.appendChild(count);
        // mousedown (et non click) : s'exécute avant la perte de focus
        li.addEventListener('mousedown', function (e) {
          e.preventDefault();
          pick(t[0]);
        });
        list.appendChild(li);
      });
      active = -1;
      list.hidden = false;
    }

    input.addEventListener('input', render);
    input.addEventListener('click', render);
    input.addEventListener('blur', hide);

    input.addEventListener('keydown', function (e) {
      if (list.hidden) return;
      if (e.key === 'ArrowDown') { e.preventDefault(); setActive(active + 1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(active - 1); }
      else if (e.key === 'Enter' && active >= 0) {
        e.preventDefault();               // ne pas soumettre le formulaire
        pick(shown[active][0]);
      }
      else if (e.key === 'Escape') { hide(); }
    });
  });
})();