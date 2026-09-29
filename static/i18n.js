/* Display translations only. Form values, field IDs and REDCap payloads stay in English. */
(() => {
  'use strict';
  const keys = ['Language','Data Collection','Inventory','Profiling','Gap Analysis','Analysis','Users','My Entries','Refresh Countries','Import Standard Excel','General Guide','User Manual','Admin Guide','Log out','Save Inventory','Save Profiling','Country','Reporting period','Required','Optional','Response','Comments','Yes','No','Unknown','Planned','No response','Previous','Next','Close','Search countries','Add Group','Save changes','Test Country','Assessment data','Working as'];
  const packs = {
    fr: ['Langue','Collecte des données','Inventaire','Profilage','Analyse des lacunes','Analyse','Utilisateurs','Mes entrées','Actualiser les pays','Importer le fichier Excel standard','Guide général','Manuel utilisateur','Guide administrateur','Se déconnecter','Enregistrer l’inventaire','Enregistrer le profilage','Pays','Période de rapport','Obligatoire','Facultatif','Réponse','Commentaires','Oui','Non','Inconnu','Prévu','Aucune réponse','Précédent','Suivant','Fermer','Rechercher un pays','Ajouter un groupe','Enregistrer les modifications','Pays test','Données de l’évaluation','Rôle'],
    ar: ['اللغة','جمع البيانات','الجرد','التوصيف','تحليل الفجوات','التحليل','المستخدمون','مدخلاتي','تحديث البلدان','استيراد ملف Excel القياسي','الدليل العام','دليل المستخدم','دليل المسؤول','تسجيل الخروج','حفظ الجرد','حفظ التوصيف','البلد','فترة الإبلاغ','مطلوب','اختياري','الإجابة','تعليقات','نعم','لا','غير معروف','مخطط','لا توجد إجابة','السابق','التالي','إغلاق','البحث عن البلدان','إضافة مجموعة','حفظ التغييرات','بلد الاختبار','بيانات التقييم','الدور'],
    pt: ['Idioma','Recolha de dados','Inventário','Caracterização','Análise de lacunas','Análise','Utilizadores','As minhas entradas','Atualizar países','Importar Excel padrão','Guia geral','Manual do utilizador','Guia do administrador','Terminar sessão','Guardar inventário','Guardar caracterização','País','Período de referência','Obrigatório','Opcional','Resposta','Comentários','Sim','Não','Desconhecido','Planeado','Sem resposta','Anterior','Seguinte','Fechar','Pesquisar países','Adicionar grupo','Guardar alterações','País de teste','Dados da avaliação','Função'],
    es: ['Idioma','Recopilación de datos','Inventario','Caracterización','Análisis de brechas','Análisis','Usuarios','Mis entradas','Actualizar países','Importar Excel estándar','Guía general','Manual de usuario','Guía de administración','Cerrar sesión','Guardar inventario','Guardar caracterización','País','Período de informe','Obligatorio','Opcional','Respuesta','Comentarios','Sí','No','Desconocido','Planificado','Sin respuesta','Anterior','Siguiente','Cerrar','Buscar países','Añadir grupo','Guardar cambios','País de prueba','Datos de la evaluación','Función'],
    sw: ['Lugha','Ukusanyaji wa data','Orodha ya mifumo','Uchambuzi wa mfumo','Uchambuzi wa mapengo','Uchambuzi','Watumiaji','Maingizo yangu','Onyesha nchi upya','Ingiza Excel ya kawaida','Mwongozo wa jumla','Mwongozo wa mtumiaji','Mwongozo wa msimamizi','Toka','Hifadhi orodha','Hifadhi uchambuzi wa mfumo','Nchi','Kipindi cha taarifa','Lazima','Hiari','Jibu','Maoni','Ndiyo','Hapana','Haijulikani','Imepangwa','Hakuna jibu','Iliyotangulia','Inayofuata','Funga','Tafuta nchi','Ongeza kikundi','Hifadhi mabadiliko','Nchi ya majaribio','Data ya tathmini','Jukumu']
  };
  const dictionaries = Object.fromEntries(Object.entries(packs).map(([code, values]) => [code, Object.fromEntries(keys.map((key, i) => [key, values[i]]))]));
  let questionPacks = {};
  const supported = ['en', ...Object.keys(packs)];
  const originals = new WeakMap();
  const attributeOriginals = new WeakMap();
  const translatable = 'button, a, summary, h1, h2, h3, h4, p, span, label, option, legend, th, td, .domain-name, .question-label';
  let language = supported.includes(localStorage.getItem('africaCdcLanguage')) ? localStorage.getItem('africaCdcLanguage') : 'en';
  let scheduled = false;
  function translateText(text) {
    const match = /^(\s*)(.*?)(\s*)$/s.exec(text);
    if (!match) return text;
    if (match[2] === 'Test Country') return text;
    return match[1] + (questionPacks[language]?.[match[2]] || dictionaries[language]?.[match[2]] || match[2]) + match[3];
  }
  function render() {
    scheduled = false;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const parent = node.parentElement;
      if (!parent || !parent.closest(translatable) || parent.closest('script, style, textarea, input, select#app-language, #toast, #connection-status, .assistant-message, .domain-meta, .assignment-owner')) continue;
      if (!originals.has(node)) originals.set(node, node.nodeValue);
      const original = originals.get(node);
      if (parent.tagName === 'OPTION' && !parent.hasAttribute('value')) parent.value = original.trim();
      const translated = language === 'en' ? original : translateText(original);
      if (node.nodeValue !== translated) node.nodeValue = translated;
    }
    document.querySelectorAll('[placeholder],[aria-label],[title]').forEach(element => {
      const saved = attributeOriginals.get(element) || {};
      for (const attribute of ['placeholder', 'aria-label', 'title']) {
        if (!element.hasAttribute(attribute)) continue;
        const current = element.getAttribute(attribute);
        if (!saved[attribute] || current !== saved[attribute].rendered) saved[attribute] = {original: current};
        const translated = language === 'en' ? saved[attribute].original : translateText(saved[attribute].original);
        if (current !== translated) element.setAttribute(attribute, translated);
        saved[attribute].rendered = translated;
      }
      attributeOriginals.set(element, saved);
    });
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
    const selector = document.getElementById('app-language');
    if (selector) selector.value = language;
  }
  function queue() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(render);
  }
  document.addEventListener('DOMContentLoaded', () => {
    const selector = document.getElementById('app-language');
    if (!selector) return;
    selector.value = language;
    selector.addEventListener('change', () => {
      language = selector.value;
      localStorage.setItem('africaCdcLanguage', language);
      render();
    });
    new MutationObserver(queue).observe(document.body, {subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['placeholder', 'aria-label', 'title']});
    render();
    Promise.all(['/question-translations.json?v=3', '/choice-translations.json?v=2', '/interface-translations.json?v=2'].map(path =>
      fetch(path).then(response => response.ok ? response.json() : {}).catch(() => ({}))
    )).then(([questions, choices, ui]) => {
      questionPacks = Object.fromEntries(supported.map(code => [code, {...(ui[code] || {}), ...(choices[code] || {}), ...(questions[code] || {})}]));
      render();
    });
  });
})();
