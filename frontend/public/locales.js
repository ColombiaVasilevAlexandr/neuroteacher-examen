(() => {
  const ids = ['es','ru','en','de','fr','zh-Hans'];
  const labels = ['Español','Русский','English','Deutsch','Français','简体中文'];
  let current = ids.includes(localStorage.getItem('neuroteacher-language')) ? localStorage.getItem('neuroteacher-language') : 'es';
  const rows = [
    ['Hoy','Сегодня','Today','Heute',"Aujourd’hui",'今天'],
    ['Aprender','Изучение','Learn','Lernen','Apprendre','学习'],
    ['Entrenamiento','Тренировка','Practice','Üben','Entraînement','练习'],
    ['Examen','Экзамен','Exam','Prüfung','Examen','考试'],
    ['Progreso','Прогресс','Progress','Fortschritt','Progrès','进度'],
    ['Errores','Ошибки','Mistakes','Fehler','Erreurs','错题'],
    ['Repaso','Повторение','Review','Wiederholung','Révision','复习'],
    ['Conversación','Разговор','Conversation','Gespräch','Conversation','对话'],
    ['Ajustes','Настройки','Settings','Einstellungen','Réglages','设置'],
    ['Inicio','Главная','Home','Startseite','Accueil','首页'],
    ['Geografía','География','Geography','Geografie','Géographie','地理'],
    ['Historia','История','History','Geschichte','Histoire','历史'],
    ['Constitución','Конституция','Constitution','Verfassung','Constitution','宪法'],
    ['Castellano','Испанский','Spanish','Spanisch','Espagnol','西班牙语'],
    ['Cultura','Культура','Culture','Kultur','Culture','文化'],
    ['Naturalización','Натурализация','Naturalization','Einbürgerung','Naturalisation','入籍'],
    ['Microtemas','Микротемы','Other topics','Weitere Themen','Autres thèmes','其他主题'],
    ['Sesión de hoy','Занятие на сегодня',"Today’s practice",'Heutige Übung','Séance du jour','今日练习'],
    ['Cargando sesión…','Загружаем занятие…','Loading practice…','Übung wird geladen…','Chargement de la séance…','正在加载练习…'],
    ['Cargando…','Загрузка…','Loading…','Laden…','Chargement…','正在加载…'],
    ['Comprobar respuesta','Проверить ответ','Check answer','Antwort prüfen','Vérifier la réponse','检查答案'],
    ['Siguiente pregunta →','Следующий вопрос →','Next question →','Nächste Frage →','Question suivante →','下一题 →'],
    ['Finalizar','Завершить','Finish','Beenden','Terminer','完成'],
    ['Siguiente →','Далее →','Next →','Weiter →','Suivant →','下一步 →'],
    ['← Atrás','← Назад','← Back','← Zurück','← Retour','← 返回'],
    ['✓ ¡Correcto!','✓ Правильно','✓ Correct','✓ Richtig','✓ Correct','✓ 正确'],
    ['✕ Incorrecto','✕ Неверно','✕ Incorrect','✕ Falsch','✕ Incorrect','✕ 错误'],
    ['Formato del examen','Выбор формата экзамена','Exam format','Prüfungsformat',"Format de l’examen",'考试形式'],
    ['Elige un modo','Выберите режим','Choose a mode','Modus wählen','Choisir un mode','选择模式'],
    ['Iniciar examen','Начать полный экзамен','Start exam','Prüfung starten',"Commencer l’examen",'开始考试'],
    ['Aprobado','Зачёт','Passed','Bestanden','Réussi','通过'],
    ['Necesita repaso','Нужно повторить','More practice needed','Weitere Übung nötig','Révision nécessaire','需要继续复习'],
    ['SIMULACIÓN','УЧЕБНАЯ СИМУЛЯЦИЯ','PRACTICE EXAM','ÜBUNGSPRÜFUNG','EXAMEN BLANC','模拟考试'],
    ['FORMATO COMPLETO','ПОЛНЫЙ ФОРМАТ','FULL FORMAT','VOLLSTÄNDIGES FORMAT','FORMAT COMPLET','完整形式'],
    ['simulación','учебная симуляция','practice exam','Übungsprüfung','examen blanc','模拟考试'],
    ['examen','экзамен','exam','Prüfung','examen','考试'],
    ['incluye castellano','с испанским языком','includes Spanish','mit Spanisch','avec espagnol','含西班牙语'],
    ['sin castellano','без испанского языка','without Spanish','ohne Spanisch','sans espagnol','不含西班牙语'],
    ['preguntas','вопросов','questions','Fragen','questions','题'],
    ['minutos','минут','minutes','Minuten','minutes','分钟'],
    ['h','ч.','h','Std.','h','小时'],
    ['No se pudo iniciar el examen. Inténtalo de nuevo.','Не удалось начать экзамен. Повторите попытку.','Could not start the exam. Try again.','Die Prüfung konnte nicht gestartet werden. Versuchen Sie es erneut.',"Impossible de commencer l’examen. Réessayez.",'无法开始考试，请重试。'],
    ['El resultado no se guardó. Reintenta; si cambió el contenido del examen, inicia uno nuevo.','Результат не сохранён. Повторите отправку; если состав экзамена изменился, начните новый.','The result was not saved. Retry; if the exam content changed, start a new exam.','Das Ergebnis wurde nicht gespeichert. Senden Sie es erneut; bei geänderten Fragen starten Sie eine neue Prüfung.',"Le résultat n’a pas été enregistré. Réessayez ; si le contenu a changé, commencez un nouvel examen.",'结果未保存，请重新提交；如考试内容已改变，请开始新的考试。'],
    ['Traducción no disponible; se muestra el original en español.','Перевод недоступен; показан испанский оригинал.','Translation unavailable; the Spanish original is shown.','Übersetzung nicht verfügbar; das spanische Original wird angezeigt.',"Traduction indisponible ; l’original espagnol est affiché.",'暂无译文，显示西班牙语原文。'],
    ['Pregunta en español','Вопрос на испанском','Question in Spanish','Frage auf Spanisch','Question en espagnol','西班牙语题目'],
    ['Traducción · original en español debajo','Перевод · испанский оригинал ниже','Translation · Spanish original below','Übersetzung · spanisches Original unten','Traduction · original espagnol ci-dessous','译文 · 下方为西班牙语原文'],
    ['Respuesta correcta','Верный вариант','Correct answer','Richtige Antwort','Bonne réponse','正确答案'],
    ['Preguntas con errores','Вопросы с ошибками','Incorrectly answered questions','Falsch beantwortete Fragen','Questions avec erreurs','答错的题目'],
    ['Repásalas primero','Повторите их в первую очередь','Review these first','Diese zuerst wiederholen','Les réviser en priorité','优先复习这些题目'],
    ['Tu lista de repaso','Ваш список повторения','Your review list','Ihre Wiederholungsliste','Votre liste de révision','复习列表'],
    ['Aún no hay errores','Ошибок пока нет','No mistakes yet','Noch keine Fehler','Pas encore d’erreurs','暂无错题'],
    ['Empezar repaso','Начать повторение','Start review','Wiederholung starten','Commencer la révision','开始复习'],
    ['PLAN DE HOY','ПЛАН НА СЕГОДНЯ',"TODAY’S PLAN",'HEUTIGER PLAN','PLAN DU JOUR','今日计划'],
    ['▷  COMENZAR SESIÓN','▷  НАЧАТЬ ЗАНЯТИЕ','▷  START PRACTICE','▷  ÜBUNG STARTEN','▷  COMMENCER LA SÉANCE','▷  开始练习'],
    ['TU NIVEL DE PREPARACIÓN','ТВОЙ УРОВЕНЬ ПОДГОТОВКИ','YOUR PREPARATION LEVEL','IHR VORBEREITUNGSSTAND','VOTRE NIVEAU DE PRÉPARATION','备考水平'],
    ['Sin datos','Нет данных','No data','Keine Daten','Aucune donnée','暂无数据'],
    ['Buen progreso','Хороший прогресс','Good progress','Guter Fortschritt','Bonne progression','进展良好'],
    ['Sigue practicando','Продолжайте практику','Keep practicing','Weiter üben','Continuez à pratiquer','继续练习'],
    ['Simulacros','Симуляции','Practice exams','Übungsprüfungen','Examens blancs','模拟考试'],
    ['Promedio','Средний балл','Average','Durchschnitt','Moyenne','平均分'],
    ['Respuestas correctas','Правильные ответы','Correct answers','Richtige Antworten','Bonnes réponses','正确答案'],
    ['Tiempo promedio','Среднее время','Average time','Durchschnittszeit','Temps moyen','平均用时'],
    ['TUS TEMAS DÉBILES','ТВОИ СЛАБЫЕ ТЕМЫ','TOPICS TO PRACTICE','THEMEN ZUM ÜBEN','THÈMES À TRAVAILLER','需要加强的主题'],
    ['Ver todos','Все темы','View all','Alle anzeigen','Tout voir','查看全部'],
    ['ACTIVIDAD RECIENTE','ПОСЛЕДНИЕ ДЕЙСТВИЯ','RECENT ACTIVITY','LETZTE AKTIVITÄTEN','ACTIVITÉ RÉCENTE','最近活动'],
    ['Aún no hay actividad.','История пока пуста.','No activity yet.','Noch keine Aktivitäten.',"Pas encore d’activité.",'暂无活动记录。'],
    ['RACHA DE ESTUDIO','СЕРИЯ ЗАНЯТИЙ','STUDY STREAK','LERNSERIE','SÉRIE D’ÉTUDE','连续学习'],
    ['HERRAMIENTAS RÁPIDAS','БЫСТРЫЕ ИНСТРУМЕНТЫ','QUICK TOOLS','SCHNELLZUGRIFF','OUTILS RAPIDES','快捷工具'],
    ['Escuchar pregunta','Прослушать вопрос','Listen to the question','Frage anhören','Écouter la question','听题'],
    ['Responder por voz','Ответить голосом','Answer by voice','Per Sprache antworten','Répondre à voix haute','语音作答'],
    ['Conversación con asesor','Разговор с консультантом','Talk to the adviser','Mit dem Berater sprechen','Parler au conseiller','与顾问交流'],
    ['Repasar marcados','Повторить отмеченные','Review bookmarks','Markierte Fragen wiederholen','Réviser les favoris','复习收藏题目'],
    ['Ver explicaciones','Посмотреть объяснения','View explanations','Erklärungen anzeigen','Voir les explications','查看解释'],
    ['Guardar','Сохранить','Save','Speichern','Enregistrer','保存'],
    ['Cerrar','Закрыть','Close','Schließen','Fermer','关闭'],
    ['Continuar','Продолжить','Continue','Weiter','Continuer','继续'],
    ['Respuesta','Ответ','Answer','Antwort','Réponse','答案'],
    ['Sin fecha','Не задано','Not set','Nicht festgelegt','Non définie','尚未设置'],
    ['Simulación de práctica','Учебная симуляция','Practice simulation','Übungssimulation','Simulation d’entraînement','练习模拟'],
  ];
  const catalog = new Map();
  rows.forEach(row => row.forEach(value => { if (!catalog.has(value)) catalog.set(value,row); }));
  function text(value, locale=current) {
    if (typeof value !== 'string') return value;
    const row=catalog.get(value.trim());
    if (!row) return value;
    const index=ids.indexOf(locale);
    return value.replace(value.trim(),row[index < 0 ? 0 : index]);
  }
  function set(locale) {
    current=ids.includes(locale)?locale:'es';
    localStorage.setItem('neuroteacher-language',current);
    document.documentElement.lang=current;
  }
  function children(value) {
    return Array.isArray(value)?value.map(children):text(value);
  }
  function wrap(jsx) {
    const props = p => p && !p['data-content'] && p.lang !== 'es' && p.translate !== 'no'
      ? {...p,children:children(p.children),title:text(p.title),'aria-label':text(p['aria-label'])}:p;
    return {...jsx,jsx:(type,p,key)=>jsx.jsx(type,props(p),key),jsxs:(type,p,key)=>jsx.jsxs(type,props(p),key)};
  }
  window.ColombiaLocales={ids,labels,text,set,wrap,escape:value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),get current(){return current;},fallback:()=>text('Traducción no disponible; se muestra el original en español.')};
  set(current);
  const fetchOriginal=window.fetch.bind(window);
  window.fetch=(input,init)=>{
    const request=input instanceof Request;
    const raw=request?input.url:String(input);
    const resolved=raw.replace(/^https?:\/\/(?:127\.0\.0\.1|localhost):8000\/api/,window.COLOMBIA_API_BASE);
    const url=new URL(resolved,window.location.href);
    const base=new URL(window.COLOMBIA_API_BASE);
    if(url.origin===base.origin && /\/(questions(?:\/\d+\/answer)?|study-plan\/questions|review\/due|errors|attempts|explanations|bookmarks|exams\/start)$/.test(url.pathname)) {
      if(!url.searchParams.has('locale'))url.searchParams.set('locale',current);
      return fetchOriginal(request?new Request(url,input):url.toString(),init);
    }
    return fetchOriginal(input,init);
  };
})();
