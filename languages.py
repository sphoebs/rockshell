#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Dec 26, 2014

@author: beatricevaleri
'''

en = {
    'date_format': 'mm/dd/yy',
    'date_time_format': 'mm/dd/yy hh:MM',
    'python_date': '%m/%d/%Y',
    'restaurants': 'restaurants',
    # MENU ITEMS
    'my_profile': 'My profile',
    'my_coupons': 'My coupons',
    'rate_more': 'Rate more places',
    'near_me' : 'Near me',
    'refresh' : 'Refresh recommendations',
    'discounts': 'Discounts',
    'inspire_me': 'Inspire me',
    'search_settings': 'Recommendation settings',
    'manage_rests': 'Manage restaurants',
    'log_out': 'Log out',
    # PROFILE SUMMARY
    'profile_edit': 'Edit profile',
    'profile_title': 'Your personal data',
    'you_gave': 'You gave',
    'ratings': 'ratings',
    'you_used': 'You used',
    'coupons': 'coupons',
    'have_role': 'You have role',
    'admin': 'administrator of PlanFree',
    'owner': 'owner of restaurants',
    
    # PROFILE 1
    'step' : 'step',
    'profile_intro': 'Hey there!! To offer you a personalized experience we need to know some information about you.',
    'first_name': 'First name',
    'last_name': 'Last name',
    'home_city': 'Home city',
    'gender': 'Gender',
    'age': 'Age',
    '<18_years': 'Less than 18 years old',
    'years_old' : 'years old',
    '>55_years': 'More than 55 years old',
    'save': 'Save',
      
    # PROFILE 2
    'profile2_text1': 'These are the places we found for',
    'profile2_text2': 'Tell us about your favourite hometown restaurants',
    'profile_feedback': 'This feedback would help people that visit your hometown!! No one knows better than a local :)',
    'no_places_city': 'Sorry, we do not know any restaurant in your city.',
    'prev': 'Prev',
    'next': 'Next',
    'continue': 'Continue', 
    'rating_purposes' : {
        'tourists': 'For a dinner with visitors',
        'partner': 'For a romantic dinner with the partner',
        'friends': 'For a dinner with friends',
        'price_quality': 'For a lunch break',
        'tips_like': 'I like it',
        'tips_neutral': 'I am neutral',
        'tips_notlike': 'I do not like it',
        'tips_notknow': 'I have never been here for this purpose'
    },
      
    # LETSGO
    'letsgo_title': 'Recommended restaurants around you',
    'letsgo_subtitle': 'Here you find some restaurants close to your position, recommended to you. We analyzed your tastes, expressed through your ratings, and we think that you should like these places. ',
    'welcome': 'Welcome',
    'loading': 'Loading',
    'loading_places': 'Loading the places around you',
    'loading_settings': 'Loading search settings',
    'getting_position': 'Getting your position',
    'in_this_picture' : 'In this picture',
    'restaurant_name' : 'Restaurant name',
    'address' : 'Address',
    'distance' : 'Distance',
    'no_geolocation' : 'Geolocation is not supported by this browser.',
    'no_places_position' : 'We are sorry, we found no places around your current position.',
    'coming_soon' : 'Coming soon.',
      
    'search_settings_popup' : {
        'title': 'Search settings',
        'purpose': 'Purpose',
        'tourists': 'Dinner with visitors',
        'partner': 'Romantic dinner with the partner',
        'friends': 'Dinner with friends',
        'price_quality': 'Lunch break',
        'max_distance': 'Maximum distance from current position in meters',
        'num_places': 'Number of places recommended',
        'save_reload': 'Save &amp; reload'
    },
      
    # RATINGS
    'new_rest_rating_popup' : {
        'title': 'Add new place and rate it',
        'name_placeholder': 'Restaurant name',
        'picture_placeholder': 'URL of restaurant picture',
        'save': 'Save'
    },
    'ratings_text1': 'Rate some restaurants and let us understand better your tastes.',
    'ratings_text2': 'Have you been in a restaurant that you already voted? Update your rating!',
    'city_select': 'Please, select a city you visited',
    'no_places_selected': 'We are sorry, we don\'t know places for the selected city.',
    'create_place_button': 'If you are not able to find the place you are searching, you can create it!',
    'add_place': 'Add place',
    'search_name': 'Search by name',
    'map_search': 'Search in the map',
    'done': 'I\'m done',
    'city_mandatory': 'The city must be set!!',
    
    # RESTAURANT PAGE + EDIT
    'rest_opening_hours': 'Opening hours',
    'rest_closed': 'Closed',
    'rest_name': 'Restaurant name',
    'rest_description': 'Description',
    'rest_address': 'Address',
    'rest_phone': 'Phone number',
    'rest_website': 'Website',
    'rest_email': 'E-mail',
    'rest_edit': 'Edit restaurant',
    'rest_new': 'New restaurant',
    'rest_picture': 'Picture (URL)',
    'opening_mon': 'Mon',
    'opening_tue': 'Tue',
    'opening_wed': 'Wed',
    'opening_thu': 'Thu',
    'opening_fri': 'Fri',
    'opening_sat': 'Sat',
    'opening_sun': 'Sun',
    'rest_closed_wday': 'closed',
    'open': 'from',
    'close': 'to',
    'add-day': 'Add new day',
    'picture_help': 'The picture should have 3:2 ratio (width/height), with minimum resolution of 600x400 px.',
    
    'back': 'Back',
    'back_to_rest' : 'Back to restaurant',
    'back_to_dlist' : 'Back to discounts',
    
    # OWNER RESTAURANT CHOICE
    'owner_choose_rest' : 'Choose the restaurant you want to manage.',
    'change_rest' : 'Change restaurant',
    
    # DISCOUNT
    'discount_edit': 'Edit discount',
    'discount_new': 'New discount',
    'discount_title': 'Title',
    'discount_description': 'Description',
    'discount_num_coupons': 'Number of coupons',
    'discount_end': 'The discount will be available till',
    'discount_list_all': 'Manage discounts',
    'published': 'Published',
    'not_published': 'Not published',
    'already_have_coupon': 'You alreaady have a coupon for this discount!',
    
    'discount_strings': {
                         'last': 'Last',
                         'coupons_available_till': 'coupons, available for',
                         'coupons_expired_at': 'coupons, expired at',
                         'coupons': 'Coupons',
                         'available_till': 'Available for',
                         'expired_at': 'Expired at',
                         'edit' : 'Edit',
                         'publish': 'Publish',
                         'delete': 'Delete',
                         'new_similar': 'Repropose it',
                         'buy': 'Get coupon',
                         'code': 'Code',
                         'status': 'Status',
                         'deleted': 'Deleted',
                         'used': 'Already used',
                         'not_used': 'Available',
                         'coupon': 'coupon',
                         'see_coupon': 'See my coupon',
                         'goto_restaurant': 'Go to restaurant',
    },
    'disc_publish_popup': {
                        'title': 'Confirm publication',
                        'message': 'Do you really want to publish this discount? <br/> After publication you will not be able to delete it.',
                        'cancel': 'Cancel',
                        'ok': 'Yes, publish'
    },
    'disc_delete_popup': {
                        'title': 'Confirm delete',
                        'message': 'Do you really want to delete this discount?',
                        'cancel': 'Cancel',
                        'ok': 'Yes, delete'
    },
    'disc_usecoupon_popup' :{
                        'title': 'Confirm use of coupon',
                        'message': 'Do you really want to mark this coupon as used?',
                        'message_2': 'We remind you that to get the discount to which the coupon refers to, you have to first show the coupon to the restaurant employee, then mark it as used while he/she is watching. If the restaurant employee does not see your coupon before the usage, he/she will not accept it as valid.',
                        'cancel': 'Cancel',
                        'ok': 'Yes, mark as used'
    },
    'coup_delete_popup' :{
                        'title': 'Confirm delete of coupon',
                        'message': 'Do you really want to delete this coupon?',
                        'cancel': 'Cancel',
                        'ok': 'Yes, delete it'
    },
    'no_discounts': 'Currently, there are no discounts available for this restaurant.',
    'no_discounts_list': 'No discounts',
    'discounts' : 'Discounts',
    'for' : 'for',
    'phone_short' : 'Tel.',
    'create_new_discount': 'Create new',
    
    'new_discounts': 'New discounts (not published yet)',
    'available_discounts': 'Currently available discounts',
    'old_discounts': 'Expired discounts',
    
    'no_coupons': 'No coupons',
    'your_coupons': 'Your coupons',
    'active_coupons': 'Active coupons',
    'used_coupons': 'Used coupons',
    'bought': 'bought on',
    'used': 'used on',
    'deleted': 'deleted on',
    'use': 'Use',
    'you_have_coupon_code': 'You have a coupon, with code',
    'coupon_used_date': 'The coupon has already been used in date',
    'coupon_deleted_date' : 'The coupon has been deleted in date',
    
    # ADMIN
    'select_city': 'Select a city for searching the places you want to edit',
    'rest_owner': 'Restaurant owner (email)',
    'manage_admins': 'Manage admins',
    
    
}


it = {
    'date_format': 'dd/mm/yy',
    'date_time_format': 'dd/mm/yy hh:MM',
    'python_date': '%d/%m/%Y',
    'restaurants': 'ristoranti',
    # MENU ITEMS
    'my_profile': 'Il mio profilo',
    'my_coupons': 'I miei coupons',
    'rate_more': u'Vota più posti',
    'near_me' : 'Vicino a me',
    'refresh' : 'Aggiorna raccomandazioni',
    'discounts': 'Offerte',
    'inspire_me': 'Ispirami',
    'search_settings': 'Impostazioni',
    'manage_rests': 'Gestisci ristoranti',
    'log_out': 'Esci',
    
    # PROFILE SUMMARY
    'profile_edit': 'Modifica profilo',
    'profile_title': 'I tuoi dati personali',
    'you_gave': 'Hai assegnato',
    'ratings': 'voti',
    'you_used': 'Hai usato',
    'coupons': 'coupons',
    'have_role': 'Hai il ruolo di',
    'admin': 'amministratore di PlanFree',
    'owner': 'proprietario di ristoranti',
    
    # PROFILE 1
    'step' : 'passo',
    'profile_intro': 'Ciao!! Per offrirti un\'esperienza personalizzata abbiamo bisogno di alcune indormazioni su di te.',
    'first_name': 'Nome',
    'last_name': 'Cognome',
    'home_city': u'Città di origine',
    'gender': 'Genere',
    'age': u'Età',
    '<18_years': 'Meno di 18 anni',
    'years_old' : 'anni',
    '>55_years': u'Più di 55 anni',
    'save': 'Salva',
      
    # PROFILE 2
    'profile2_text1': 'Questi sono i posti che abbiamo trovato per',
    'profile2_text2': u'Dicci cosa ne pensi dei ristoranti della tua città',
    'profile_feedback': u'Le tue opinioni aiuteranno le persone che visiteranno la tua città!! Nessuno li conosce meglio di uno del posto :) ',
    'no_places_city': u'Siamo spiacenti, non conosciamo nessun posto nella tua città.',
    'prev': 'Indietro',
    'next': 'Avanti',
    'continue': 'Continua', 
    'rating_purposes' : {
        'tourists': 'Per una cena con degli ospiti da fuori citt&agrave;',
        'partner': 'Per una cena romantica con il/la tuo/a compagno/a',
        'friends': 'Per una cena con gli amici',
        'price_quality': 'Per la pausa pranzo',
        'tips_like': 'Mi piace',
        'tips_neutral': 'Sono neutrale',
        'tips_notlike': 'Non mi piace',
        'tips_notknow': 'Non ci sono mai stato per questo motivo'
    },
      
    # LETSGO
    'letsgo_title': 'Ristoranti intorno a te che ti potrebbero piacere',
    'letsgo_subtitle': 'Qui trovi alcuni dei ristoranti attorno a te, che ti raccomandiamo. Abbiamo analizzato i tuoi gusti, espressi tramite i tuoi voti, e pensiamo che questi posti ti potrebbero piacere. ',
    'welcome': 'Benvenuto',
    'loading': 'Caricamento',
    'loading_places': 'Sto cercando i posti vicino a te',
    'loading_settings': 'Sto caricando le impostazioni',
    'getting_position': 'Sto ottenendo la tua posizione',
    'in_this_picture' : 'In questa immagine',
    'restaurant_name' : 'Nome del ristorante',
    'address' : 'Indirizzo',
    'distance' : 'Distanza',
    'no_geolocation' : u'La geolocalizzazione non è supportata da questo browser.',
    'no_places_position' : 'Siamo spiacenti, non abbiamo trovato alcun posto vicino alla tua posizione.',
    'coming_soon' : 'Presto disponibile.',
      
    'search_settings_popup' : {
        'title': 'Impostazioni di ricerca',
        'purpose': 'Motivo',
        'tourists': 'Cena con degli ospiti da fuori citt&agrave;',
        'partner': 'Cena romantica con il/la tuo/a compagno/a',
        'friends': 'Cena con gli amici',
        'price_quality': 'Pausa pranzo',
        'max_distance': 'Distanza massima dalla posizione attuale, in metri',
        'num_places': 'Numero di ristoranti raccomandati',
        'save_reload': 'Salva &amp; aggiorna'
    },
      
    # RATINGS
    'new_rest_rating_popup' : {
        'title': 'Aggiungi un nuovo posto e votalo',
        'name_placeholder': 'Nome del ristorante',
        'picture_placeholder': 'URL dell\'immagine del ristorante',
        'save': 'Salva'
    },
    'ratings_text1': 'Vota alcuni ristoranti e permettici di conoscere meglio i tuoi gusti.',
    'ratings_text2': 'Sei stato di nuovo in un ristorante che hai già votato? Aggiorna il tuo voto!',
    'city_select': u'Per favore, seleziona una città che hai visitato',
    'no_places_selected': u'Siamo spiacenti, non conosciamo ristoranti nella città selezionata.',
    'create_place_button': 'Se non trovi il ristorante che stai cercando, lo puoi aggiungere!',
    'add_place': 'Aggiungi posto',
    'search_name': 'Cerca per nome',
    'map_search': 'Cerca nella mappa',
    'done': 'Ho finito',
    'city_mandatory': u'La città deve essere selezionata!!',
    
    # RESTAURANT PAGE + EDIT
    'rest_opening_hours': 'Orario d\'apertura',
    'rest_closed': 'Chiuso',
    'rest_name': 'Nome del ristorante',
    'rest_description': 'Descrizione',
    'rest_address': 'Indirizzo',
    'rest_phone': 'Numero di telefono',
    'rest_website': 'Sito web',
    'rest_email': 'E-mail',
    'rest_edit': 'Modifica ristorante',
    'rest_new': 'Nuovo ristorante',
    'rest_picture': 'Immagine (URL)',
    'opening_mon': 'Lun',
    'opening_tue': 'Mar',
    'opening_wed': 'Mer',
    'opening_thu': 'Gio',
    'opening_fri': 'Ven',
    'opening_sat': 'Sab',
    'opening_sun': 'Dom',
    'rest_closed_wday': 'chiuso',
    'open': 'dalle',
    'close': 'alle',
    'add-day': 'Aggiungi giorno',
    'picture_help': 'L\'immagine deve avere un rapporto 3:2 (larghezza/altezza), con risoluzione minima di 600x400px.',
    
    'back': 'Indietro',
    'back_to_rest' : 'Torna al ristorante',
    'back_to_dlist' : 'Torna alle offerte',
    
    # OWNER RESTAURANT CHOICE
    'owner_choose_rest' : 'Scegli il ristorante che vuoi gestire.',
    'change_rest' : 'Cambia ristorante',
    
    # DISCOUNT
    'discount_edit': 'Modifica offerta',
    'discount_new': 'Crea nuova offerta',
    'discount_title': 'Titolo',
    'discount_description': 'Descrizione',
    'discount_num_coupons': 'Numero di coupon',
    'discount_end': u'L\'offerta sarà disponibile fino a',
    'discount_list_all': 'Gestisci offerte',
    'published': 'Pubblicata',
    'not_published': 'Non pubblicata',
    'already_have_coupon': u'Hai già un coupon per questa offerta!',
    
    'discount_strings': {
                         'last': 'Ultimi',
                         'coupons_available_till': 'coupons, disponibili per',
                         'coupons_expired_at': 'coupons, scaduti il',
                         'coupons': 'Coupons',
                         'available_till': 'Disponibile per',
                         'expired_at': 'Scaduto il',
                         'edit' : 'Modifica',
                         'publish': 'Pubblica',
                         'delete': 'Cancella',
                         'new_similar': 'Rinnova',
                         'buy': 'Prendi coupon',
                         'code': 'Codice',
                         'status': 'Stato',
                         'deleted': 'Cancellato',
                         'used': 'Usato',
                         'not_used': 'Disponibile',
                         'coupon': 'coupon',
                         'see_coupon': 'Accedi al mio coupon',
                         'goto_restaurant': 'Vai al ristorante',
    },
    'disc_publish_popup': {
                        'title': 'Conferma pubblicazione',
                        'message': 'Vuoi davvero pubblicare questa offerta? <br/> Dopo la pubblicazione non potrai pi&ugrave; cancellare questa offerta.',
                        'cancel': 'Annulla',
                        'ok': 'S&igrave;, pubblica'
    },
    'disc_delete_popup': {
                        'title': 'Conferma cancellazione',
                        'message': 'Vuoi davvero cancellare questa offerta?',
                        'cancel': 'Annulla',
                        'ok': 'S&igrave;, cancella'
    },
    'disc_usecoupon_popup' :{
                        'title': 'Conferma uso del coupon',
                        'message': 'Vuoi davvero marcare questo coupon come usato?',
                        'message_2': 'Ti ricordiamo che per ottenere l\'offerta a cui questo coupon si riferisce, devi per prima cosa mostrare il coupon all\'addetto del ristorante, quindi segnalare che lo stai usando sotto supervisione dell\'addetto. Se l\'addetto del ristorante non vede il coupon prima del suo utilizzo, il coupon non verr&agrave; accettato come valido.',
                        'cancel': 'Annulla',
                        'ok': 'S&igrave;, usa'     
    },
    'coup_delete_popup' :{
                        'title': 'Conferma cancellazione del coupon',
                        'message': 'Vuoi davvero cancellare questo coupon?',
                        'cancel': 'Annulla',
                        'ok': 'S&igrave;, cancella'
    },
    'no_discounts': 'Al momento, non ci sono offerte disponibili per questo ristorante.',
    'no_discounts_list': 'Nessuna offerta',
    'discounts' : 'Offerte',
    'for' : 'per',
    'phone_short' : 'Tel.',
    'create_new_discount': 'Crea nuova offerta',
    
    'new_discounts': 'Nuove offerte (ancora non pubblicate)',
    'available_discounts': 'Offerte attualmente disponibili',
    'old_discounts': 'Offerte scadute',
    
    'no_coupons': 'Nessun coupon',
    'your_coupons': 'I tuoi coupon',
    'active_coupons': 'Coupon attivi',
    'used_coupons': 'Coupon usati',
    'bought': 'acquistato il',
    'used': 'usato il',
    'use': 'Usa',
    'you_have_coupon_code': 'Hai un coupon, con codice',
    'coupon_used_date': u'Il coupon è già stato usato il ',
    
    
    # ADMIN
    'select_city': u'Seleziona una città per cercare i posti che vuoi modificare',
    'rest_owner': 'Proprietario del ristorante (email)',
    'manage_admins': 'Gestisci admins',
    
}

