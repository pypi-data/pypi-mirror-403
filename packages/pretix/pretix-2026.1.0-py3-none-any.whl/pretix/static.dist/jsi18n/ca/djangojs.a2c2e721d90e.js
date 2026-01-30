

'use strict';
{
  const globals = this;
  const django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    const v = n != 1;
    if (typeof v === 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  const newcatalog = {
    "(one more date)": [
      "(una data m\u00e9s)",
      "({num} dates m\u00e9s)"
    ],
    "=": "=",
    "Add condition": "Afegeix condici\u00f3",
    "Additional information required": "Cal informaci\u00f3 addicional",
    "All": "Tots",
    "All of the conditions below (AND)": "Complir totes les condicions seg\u00fcents",
    "An error has occurred.": "S'ha produ\u00eft un error.",
    "An error of type {code} occurred.": "S'ha produ\u00eft un error de tipus {code}.",
    "Apple Pay": "Apple Pay",
    "Approval pending": "Pendent d'aprovaci\u00f3",
    "At least one of the conditions below (OR)": "Complir almenys una de les condicions seg\u00fcents",
    "BLIK": "BLIK",
    "Bancontact": "Bancontact",
    "Barcode area": "\u00c0rea del codi de barres",
    "Boleto": "Boleto",
    "Calculating default price\u2026": "Calculant el preu per defecte\u2026",
    "Cancel": "Cancel\u00b7lar",
    "Canceled": "Cancel\u00b7lat",
    "Cart expired": "Cistella caducada",
    "Check-in QR": "Registre amb codi QR",
    "Checked-in Tickets": "Entrades registrades",
    "Click to close": "Prem per tancar",
    "Close message": "Tanca el missatge",
    "Comment:": "Comentari:",
    "Confirmed": "Confirmat",
    "Confirming your payment \u2026": "Confirmant el teu pagament\u2026",
    "Contacting Stripe \u2026": "S'est\u00e0 contactant amb Stripe\u2026",
    "Contacting your bank \u2026": "Contactant amb el teu banc\u2026",
    "Continue": "Continua",
    "Copied!": "Copiat!",
    "Count": "Quantitat",
    "Credit Card": "Targeta de cr\u00e8dit",
    "Current date and time": "Data i hora actuals",
    "Current day of the week (1 = Monday, 7 = Sunday)": "Dia actual de la setmana (1 = Dilluns, 7 = Diumenge)",
    "Current entry status": "Estat actual de l'entrada",
    "Currently inside": "Actualment dins",
    "Do you really want to leave the editor without saving your changes?": "Est\u00e0s segur que vols abandonar l'editor sense desar els canvis?",
    "Do you want to renew the reservation period?": "Vols ampliar el temps de reserva?",
    "Duplicate": "Duplicat",
    "Enter page number between 1 and %(max)s.": "Introdueix un n\u00famero de p\u00e0gina entre 1 i %(max)s.",
    "Entry": "Entrada",
    "Entry not allowed": "Entrada no permesa",
    "Error while uploading your PDF file, please try again.": "Error en pujar el fitxer PDF, torna-ho a provar.",
    "Error: Product not found!": "Error: Producte no trobat!",
    "Error: Variation not found!": "Error: Variaci\u00f3 no trobada!",
    "Event admission": "Admissi\u00f3 de l'esdeveniment",
    "Event end": "Finalitzaci\u00f3 de l'esdeveniment",
    "Event start": "Inici de l'esdeveniment",
    "Exit": "Sortida",
    "Exit recorded": "Sortida registrada",
    "Gate": "Porta",
    "Generating messages \u2026": "Generant missatges\u2026",
    "Group of objects": "Grup d'objectes",
    "If this takes longer than a few minutes, please contact us.": "Si triga m\u00e9s de pocs minuts, contacta'ns.",
    "Image area": "\u00c0rea de la imatge",
    "Information required": "Informaci\u00f3 requerida",
    "Invalid page number.": "N\u00famero de p\u00e0gina no v\u00e0lid.",
    "Ita\u00fa": "Ita\u00fa",
    "Load more": "Mostra'n m\u00e9s",
    "Marked as paid": "Marcat com a pagat",
    "Maxima": "Maxima",
    "Mercado Pago": "Mercado Pago",
    "Minutes since first entry (-1 on first entry)": "Minuts des de la primera entrada (-1 a la primera entrada)",
    "Minutes since last entry (-1 on first entry)": "Minuts des de l'\u00faltima entrada (-1 per la primera entrada)",
    "MyBank": "MyBank",
    "No": "No",
    "No active check-in lists found.": "No s'ha trobat cap lllista d'acreditaci\u00f3 activa.",
    "No results": "Cap resultat",
    "No tickets found": "No s'han trobat entrades",
    "None": "Cap",
    "Number of days with a previous entry": "Nombre de dies amb una entrada anterior",
    "Number of days with a previous entry before": "Nombre de dies amb una entrada anterior abans de",
    "Number of days with a previous entry since": "Nombre de dies amb una entrada anterior des de",
    "Number of previous entries": "Nombre d'entrades anteriors",
    "Number of previous entries before": "Nombre d\u2019entrades anteriors abans de",
    "Number of previous entries since": "Nombre d\u2019entrades anteriors des de",
    "Number of previous entries since midnight": "Nombre d\u2019entrades anteriors des de la mitjanit",
    "OXXO": "OXXO",
    "Object": "Objecte",
    "Order canceled": "S'ha cancel\u00b7lat la comanda",
    "Order not approved": "Comanda no aprovada",
    "Others": "Altres",
    "Paid orders": "Comandes pagades",
    "PayPal": "PayPal",
    "PayPal Credit": "PayPal Credit",
    "PayPal Pay Later": "PayPal Pay Later",
    "PayU": "PayU",
    "Payment method unavailable": "El m\u00e8tode de pagament no est\u00e0 disponible",
    "Placed orders": "Comanda realitzada",
    "Please enter the amount the organizer can keep.": "Introdueix l\u2019import que es queda l\u2019organitzador.",
    "Powered by pretix": "Impulsat per pretix",
    "Press Ctrl-C to copy!": "Prem Ctrl-C per copiar!",
    "Product": "Producte",
    "Product variation": "Variaci\u00f3 del producte",
    "Przelewy24": "Przelewy24",
    "Redeemed": "Reemborsat",
    "Renew reservation": "Renovar reserva",
    "Result": "Resultat",
    "SEPA Direct Debit": "SEPA Direct Debit",
    "SOFORT": "SOFORT",
    "Saving failed.": "Error en desar.",
    "Scan a ticket or search and press return\u2026": "Escaneja l'entrada o cerca i prem Retorn\u2026",
    "Search query": "Consulta de cerca",
    "Search results": "Resultats de la cerca",
    "Select a check-in list": "Selecciona una llista d'acreditaci\u00f3",
    "Selected only": "Nom\u00e9s seleccionats",
    "Switch check-in list": "Canvia la llista d'acreditaci\u00f3",
    "Switch direction": "Canvia la direcci\u00f3",
    "Text box": "Quadre de text",
    "Text object (deprecated)": "Objecte de text (obsolet)",
    "The PDF background file could not be loaded for the following reason:": "No s'ha pogut carregar el PDF de fons pel seg\u00fcent motiu:",
    "The items in your cart are no longer reserved for you. You can still complete your order as long as they're available.": "Ja no teniu reservat el contingut de la cistella. Encara podeu completar la comanda si els articles continuen disponibles.",
    "The items in your cart are no longer reserved for you. You can still complete your order as long as they\u2019re available.": "Ja no tens reservat el contingut de la cistella. Encara pots completar la comanda si els articles seleccionats continuen disponibles.",
    "The items in your cart are reserved for you for one\u00a0minute.": [
      "El contingut de la teva cistella est\u00e0 reservat durant un minut.",
      "El contingut de la teva cistella est\u00e0 reservat durant {num} minuts."
    ],
    "The organizer keeps %(currency)s %(amount)s": "L'entitat organitzadora es queda %(currency)s %(amount)s",
    "The request took too long. Please try again.": "Temps d\u2019espera esgotat. Torna-ho a provar.",
    "This ticket is not yet paid. Do you want to continue anyways?": "Aquesta entrada no est\u00e0 pagada. Vols continuar igualment?",
    "This ticket requires special attention": "Aquesta entrada requereix atenci\u00f3 especial",
    "Ticket already used": "Entrada ja utilitzada",
    "Ticket blocked": "Entrada bloquejada",
    "Ticket code is ambiguous on list": "Codi de l\u2019entrada ambigu a la llista",
    "Ticket code revoked/changed": "Codi d\u2019entrada anul\u00b7lat o modificat",
    "Ticket design": "Disseny del tiquet",
    "Ticket not paid": "Entrada no pagada",
    "Ticket not valid at this time": "Entrada no v\u00e0lida en aquest moment",
    "Ticket type not allowed here": "Tipus d'entrada no perm\u00e8s aqu\u00ed",
    "Tolerance (minutes)": "Toler\u00e0ncia (minuts)",
    "Total": "Total",
    "Total revenue": "Facturaci\u00f3 total",
    "Trustly": "Trustly",
    "Unknown error.": "Error desconegut.",
    "Unknown ticket": "Entrada desconeguda",
    "Unpaid": "No pagat",
    "Use a different name internally": "Utilitza un nom diferent internament",
    "Valid": "V\u00e0lid",
    "Valid Tickets": "Entrades v\u00e0lides",
    "Valid ticket": "Entrada v\u00e0lida",
    "Venmo": "Venmo",
    "Verkkopankki": "Verkkopankki",
    "We are currently sending your request to the server. If this takes longer than one minute, please check your internet connection and then reload this page and try again.": "Hem enviat la teva petici\u00f3 al servidor. Si triga m\u00e9s d'1 minut, comprova la connexi\u00f3, recarrega la p\u00e0gina i torna-ho a provar.",
    "We are processing your request \u2026": "Estem processant la vostra sol\u00b7licitud \u2026",
    "We currently cannot reach the server, but we keep trying. Last error code: {code}": "Actualment no podem connectar amb el servidor, per\u00f2 seguim intentant-ho. \u00daltim codi d\u2019error: {code}",
    "We currently cannot reach the server. Please try again. Error code: {code}": "No es pot connectar amb el servidor. Torna-ho a provar. Codi d\u2019error: {code}",
    "WeChat Pay": "WeChat Pay",
    "Yes": "S\u00ed",
    "You get %(currency)s %(amount)s back": "Rebr\u00e0s %(currency)s %(amount)s",
    "You have unsaved changes!": "Tens canvis sense desar!",
    "Your cart has expired.": "La teva cistella ha caducat.",
    "Your cart is about to expire.": "La teva cistella est\u00e0 a punt de caducar.",
    "Your color has decent contrast and is sufficient for minimum accessibility requirements.": "El teu color t\u00e9 un contrast acceptable i compleix els requisits m\u00ednims d\u2019accessibilitat.",
    "Your color has great contrast and will provide excellent accessibility.": "El teu color t\u00e9 molt contrast i garanteix bona accessibilitat.",
    "Your color has insufficient contrast to white. Accessibility of your site will be impacted.": "El color no t\u00e9 prou contrast amb el blanc i pot afectar a l'accessibilitat del lloc web.",
    "Your local time:": "La teva hora local:",
    "Your request arrived on the server but we still wait for it to be processed. If this takes longer than two minutes, please contact us or go back in your browser and try again.": "La teva sol\u00b7licitud ha arribat al servidor, estem esperant que es processi. Si aquesta acci\u00f3 triga m\u00e9s de 2 minuts, contacta'ns o torna enrere al navegador i prova-ho de nou.",
    "Your request has been queued on the server and will soon be processed.": "La teva sol\u00b7licitud s\u2019ha posat en cua al servidor i es processar\u00e0 aviat.",
    "Your request is currently being processed. Depending on the size of your event, this might take up to a few minutes.": "\u201cLa teva sol\u00b7licitud s\u2019est\u00e0 processant. Depenent de la mida del l'esdeveniment, aquesta acci\u00f3 pot trigar uns minuts.",
    "Zimpler": "Zimpler",
    "close": "Tanca",
    "custom date and time": "Data i hora personalitzades",
    "custom time": "Hora personalitzada",
    "entry_status\u0004absent": "absent",
    "entry_status\u0004present": "present",
    "eps": "eps",
    "giropay": "giropay",
    "iDEAL": "iDEAL",
    "is after": "despr\u00e9s de",
    "is before": "abans de",
    "is one of": "forma part de",
    "minutes": "en minuts",
    "required": "requerit",
    "widget\u0004Buy": "Compra",
    "widget\u0004Close ticket shop": "Tanca la botiga d'entrades",
    "widget\u0004Currently not available": "No disponible",
    "widget\u0004Decrease quantity": "Disminueix quantitat",
    "widget\u0004FREE": "GRATU\u00cfT",
    "widget\u0004Filter": "Filtra",
    "widget\u0004Filter events by": "Filtra els esdeveniments per",
    "widget\u0004Image of %s": "Imatge de %s",
    "widget\u0004Increase quantity": "Augmenta quantitat",
    "widget\u0004New price: %s": "Nou preu: %s",
    "widget\u0004Not available anymore": "Ja no est\u00e0 disponible",
    "widget\u0004Not yet available": "Encara no disponible",
    "widget\u0004Only available with a voucher": "Nom\u00e9s disponible amb un cup\u00f3",
    "widget\u0004Original price: %s": "Preu original: %s",
    "widget\u0004Price": "Preu",
    "widget\u0004Quantity": "Quantitat",
    "widget\u0004Register": "Registrar-vos",
    "widget\u0004Reserved": "Reservat",
    "widget\u0004Select": "Selecciona",
    "widget\u0004Select %s": "Selecciona %s",
    "widget\u0004Select variant %s": "Selecciona la variant %s",
    "widget\u0004Sold out": "Esgotat",
    "widget\u0004The ticket shop could not be loaded.": "No s'ha pogut carregar la botiga d'entrades.",
    "widget\u0004currently available: %s": "disponibles: %s",
    "widget\u0004from %(currency)s %(price)s": "des de %(price)s %(currency)s",
    "widget\u0004incl. %(rate)s% %(taxname)s": "Incl\u00f2s %(rate)s% %(taxname)s",
    "widget\u0004incl. taxes": "incl. impostos",
    "widget\u0004minimum amount to order: %s": "Comanda m\u00ednima: %s",
    "widget\u0004plus %(rate)s% %(taxname)s": "m\u00e9s %(rate)s% %(taxname)s",
    "widget\u0004plus taxes": "m\u00e9s impostos"
  };
  for (const key in newcatalog) {
    django.catalog[key] = newcatalog[key];
  }
  

  if (!django.jsi18n_initialized) {
    django.gettext = function(msgid) {
      const value = django.catalog[msgid];
      if (typeof value === 'undefined') {
        return msgid;
      } else {
        return (typeof value === 'string') ? value : value[0];
      }
    };

    django.ngettext = function(singular, plural, count) {
      const value = django.catalog[singular];
      if (typeof value === 'undefined') {
        return (count == 1) ? singular : plural;
      } else {
        return value.constructor === Array ? value[django.pluralidx(count)] : value;
      }
    };

    django.gettext_noop = function(msgid) { return msgid; };

    django.pgettext = function(context, msgid) {
      let value = django.gettext(context + '\x04' + msgid);
      if (value.includes('\x04')) {
        value = msgid;
      }
      return value;
    };

    django.npgettext = function(context, singular, plural, count) {
      let value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
      if (value.includes('\x04')) {
        value = django.ngettext(singular, plural, count);
      }
      return value;
    };

    django.interpolate = function(fmt, obj, named) {
      if (named) {
        return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
      } else {
        return fmt.replace(/%s/g, function(match){return String(obj.shift())});
      }
    };


    /* formatting library */

    django.formats = {
    "DATETIME_FORMAT": "j E \\d\\e Y \\a \\l\\e\\s G:i",
    "DATETIME_INPUT_FORMATS": [
      "%d/%m/%Y %H:%M:%S",
      "%d/%m/%Y %H:%M:%S.%f",
      "%d/%m/%Y %H:%M",
      "%d/%m/%y %H:%M:%S",
      "%d/%m/%y %H:%M:%S.%f",
      "%d/%m/%y %H:%M",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j E \\d\\e Y",
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y",
      "%d/%m/%y",
      "%Y-%m-%d"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": 1,
    "MONTH_DAY_FORMAT": "j E",
    "NUMBER_GROUPING": 3,
    "SHORT_DATETIME_FORMAT": "d/m/Y G:i",
    "SHORT_DATE_FORMAT": "d/m/Y",
    "THOUSAND_SEPARATOR": ".",
    "TIME_FORMAT": "G:i",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M:%S.%f",
      "%H:%M"
    ],
    "YEAR_MONTH_FORMAT": "F \\d\\e\\l Y"
  };

    django.get_format = function(format_type) {
      const value = django.formats[format_type];
      if (typeof value === 'undefined') {
        return format_type;
      } else {
        return value;
      }
    };

    /* add to global namespace */
    globals.pluralidx = django.pluralidx;
    globals.gettext = django.gettext;
    globals.ngettext = django.ngettext;
    globals.gettext_noop = django.gettext_noop;
    globals.pgettext = django.pgettext;
    globals.npgettext = django.npgettext;
    globals.interpolate = django.interpolate;
    globals.get_format = django.get_format;

    django.jsi18n_initialized = true;
  }
};

