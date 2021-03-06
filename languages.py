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
#     'profile_intro': 'Hey there!! To offer you a personalized experience we need to know some information about you.',
    'profile_intro': 'Hey there!! To offer you a personalized experience with the best restaurant recommendations *for you*, we need to know where you come from.',
    'profile_edit_intro' : 'Edit your personal data.',
    'first_name': 'First name',
    'last_name': 'Last name',
    'home_city': 'In which city do you live?',
    'gender': 'Gender',
    'age': 'Age',
    '<18_years': 'Less than 18 years old',
    'years_old' : 'years old',
    '>55_years': 'More than 55 years old',
    'save': 'Save',
      
    # PROFILE 2
    'profile2_text1': 'These are the places we found for',
    'profile2_text2': 'Tell us about your favourite hometown restaurants',
#     'profile_feedback': 'This feedback would help people that visit your hometown!! No one knows better than a local :)',
    'profile_feedback': 'The more you rate, the better we will know your tastes and we will make better recommendations for you! :)',
    'no_places_city': 'Sorry, we do not know any restaurant in your city.',
    'prev': 'Prev',
    'next': 'Next',
    'continue': 'Continue',
    'done_next_step': 'Done, go to next step', 
    'done_letsgo': 'Done, go to recommendations', 
    'rating_purposes' : {
        'how_experience': 'How was your experience?',
        'tourists': 'For a dinner with visitors',
        'partner': 'For a romantic dinner with the partner',
        'friends': 'For a dinner with friends',
        'price_quality': 'For a lunch break',
        'tourists_short': 'with visitors',
        'partner_short': 'romantic',
        'friends_short': 'with friends',
        'price_quality_short': 'lunch break',
        'tips_like': 'I like it',
        'tips_neutral': 'I am neutral',
        'tips_notlike': 'I do not like it',
        'tips_notknow': 'I have never been here for this purpose'
    },
      
    # LETSGO
    'letsgo_title': 'Recommended restaurants around you',
    'letsgo_title_city': 'Recommended restaurants in',
    'geoposition_error': 'We are not able to find your current position now, we set Trento as your city. Use the refresh button to retry your geolocalization.',
    'letsgo_subtitle': 'Here you find some restaurants close to your position, recommended to you. We analyzed your tastes, expressed through your ratings, and we think that you should like these places. ',
    'welcome': 'Welcome',
    'loading': 'Loading',
    'loading_places': 'We are analyzing your tastes, expressed through your ratings, and we are searching for the restaurants that you should like the most.',
    'loading_settings': 'Loading search settings',
    'getting_position': 'Getting your position',
    'in_this_picture' : 'In this picture',
    'restaurant_name' : 'Restaurant name',
    'with_visitors': 'with visitors',
    'romantic_dinner': 'romantic',
    'with_friends': 'with friends',
    'lunch': 'lunch break',
    'select_purpose': 'Select your purpose',
    'address' : 'Address',
    'distance' : 'Distance',
    'no_geolocation' : 'Geolocation is not supported by this browser.',
    'no_places_position' : 'We are sorry, we found no places around your current position.',
    'coming_soon' : 'Coming soon.',
      
    'search_settings_popup' : {
        'title': 'Search settings',
        'purpose': 'Select your purpose',
        'purpose_help': 'Select the default purpose that will be shown as first at your next access.',
        'tourists': 'Dinner with visitors',
        'partner': 'Romantic dinner',
        'friends': 'Dinner with friends',
        'price_quality': 'Lunch break',
        'max_distance': 'Maximum distance in meters',
        'num_places': 'Number of places recommended',
        'select_different_city': 'Select a different city',
        'save_reload': 'Save and reload',
        'city_error': 'Please, select the city from the autocomplete list or remove the city you indicated.',
    },
      
    'today_closed': 'Closed today',
    'today_closed_tomorrow': 'Closed today, ',
    'opens_at': 'It opens at ',
    'open_till': 'It is open till ',
    'tomorrow_closed': 'Closed tomorrow',
    'tomorrow_open_at': 'It opens tomorrow at',
    'today_tomorrow_closed': 'Closed today and tomorrow',
    'prediction': 'Our guess of your interest',
    'next_text': 'No, thanks. Next',
    
    'reclist_end': 'You reached the end of your recommendations.',
#     'your_settings': 'You are searching {num} restaurants within {dist} meters from{loc}',
#     'current_position': ' your current position.',
#     'city_center': ' city center.',
#     'change_settings': 'You can get more recommendations by changing your settings. You can open the menu on the left and use the "Recommendation settings" menu item to access and change your settings. In alternative, use the following button.',
    'change_settings': 'If you want to have more recommendations, please configure your recommendation settings accordingly.',
    'goto_settings': 'Access recommendation settings',
    
      
    # RATINGS
    'new_rest_rating_popup' : {
        'title': 'Add new place and rate it',
        'name_placeholder': 'Restaurant name',
        'address_placeholder': 'Address',
        'picture_placeholder': 'URL of picture',
        'save': 'Save',
        'how_experience': 'How was your experience?',
        'tourists_short': 'with visitors',
        'partner_short': 'romantic',
        'friends_short': 'with friends',
        'price_quality_short': 'lunch break',
    },
    'suggest_rest_popup' : {
        'title': 'Suggest a restaurant',
        'email': 'Email address',
        'email_helper': 'Your email address is used to contact you and to thank you for your contribution.',
        'rest_name': 'Restaurant name',
        'missing_name': 'Please, insert at least the name of the restaurant you are suggesting.',
        'details': 'Other details',
        'send_suggestion': 'Send suggestion',
        'suggestion_sent': 'Suggestion sent successfully, thank you.',                    
    },
    'ratings_text1': 'The more you rate the better we can recommend to you!',
    'ratings_text2': 'Have you been in a restaurant that you already voted? Update your rating! ',
    'city_select': 'Please, select a city',
    'no_places_selected': 'We are sorry, we don\'t know places for the selected city.',
    'create_place_button': 'If you are not able to find the place you are looking for, you can create it!',
    'add_place': 'Add place',
    'suggest_place_button': 'If you are not able to find the place you are looking for, you can suggest it!',
    'suggest_place': 'Suggest restaurant',
    'search_name': 'Search by name',
    'map_search': 'Search in the map',
    'done': 'I\'m done',
    'city_mandatory': 'The city must be set!!',
    'new_place_saved': 'The new restaurant has been correctly saved and added to the list.',
    'missing_name': 'Please, fill in the name of the restaurant!',
    'missing_address': 'Please, fill in the address of the restaurant!',
    'rating_hints': ['very bad', 'bad', 'neutral', 'good', 'very good'],
    
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
    'rest_main_picture': 'Main picture (URL)',
    'rest_other_pictures': 'Other pictures (URLs)',
    'add_picture': 'Add new picture',
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
    'picture_help': 'The picture should have size 700*429 (width/height). If the size of the picture is different, the picture will be resized and cutted to fit in these dimensions. Check the following preview before saving.',
    
    'read_more': 'Read more',
    'read_less': 'Read less',
    
    'back': 'Back',
    'back_to_rest' : 'Back to restaurant',
    'back_to_dlist' : 'Back to discounts',
    
    # OWNER RESTAURANT CHOICE
    'owner_choose_rest' : 'Choose the restaurant you want to manage.',
    'change_rest' : 'Change restaurant',
    
    # DISCOUNT
    'your_coupon': 'Your coupon',
    'discount': 'Discount',
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
                         'no_coupons': 'Coupons already sold out',
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
                         'see_used_coupon': 'You used your coupon',
                         'goto_restaurant': 'Go to restaurant',
                         'use': 'Use',
                         'you_have_coupon_code': 'You have a coupon with code',
                         'delete': 'Delete', 
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
    'you_have_coupon_with': 'You have a coupon with',
    'code': 'code',
    'coupon_used_date': 'The coupon has already been used in date',
    'coupon_deleted_date' : 'The coupon has been deleted in date',
    
    # ADMIN
    'restaurant_list_edit': 'Search restaurant',
    'admin_select_city': 'Select a city for searching the places you want to edit',
    'rest_owner': 'Restaurant owner (email)',
    'manage_admins': 'Manage admins',
    'add_admin': 'Add new admin',
    'current_admins': 'Current admins',
    
    # ERROR
    'close_button': 'Close',
    'error': 'Error',
    'error_sorry': 'We are sorry for the incovenience, we will try to solve the problem as soon as possible.',
    'logout_error': {
                     'title': 'Error',
                     'message': 'An error happened during logout. Retry again later, in any case the session will expire in 30 minutes.',
                     'close': 'Close',
    },
    'error_city_missing': {
                     'title': 'City not selected',
                     'message': 'Please, select your city from the autocomplete list before saving it.',
                     'close': 'Close',
    },
    'unauthorized_error': {
                           'title': 'Error',
                           'message': 'You are not authorized to perform this operation. Check that you are logged in and that you have the right permissions.',
                           'close': 'Close',
    },
    'permission_error': {
                         'title': 'Permission error',
                         'message': 'This service needs you to accept the permissions to work. Please, go back and accept the permissions to read your public information and your email address.',
    },
    'admin_delete_error': {
                     'title': 'Error',
                     'message': 'An error happened during the delete of an administrator.',
                     'close': 'Close',
    },
    'admin_save_error': {
                     'title': 'Error',
                     'message': 'An error happened saving the new administrator. Verify that the email is correct and try again.',
                     'close': 'Close',
    },
    'discount_save_error': {
                     'title': 'Error',
                     'message': 'An error happened saving the discount. Verify that the data are correct and try again.',
                     'close': 'Close',
    },
    'discount_publish_error': {
                     'title': 'Error',
                     'message': 'An error happened during the publication of the discount.',
                     'close': 'Close',
    },
    'discount_delete_error': {
                     'title': 'Error',
                     'message': 'An error happened during the delete of the discount.',
                     'close': 'Close',
    },
    'discount_list_load_error' : {
                     'title': 'Error',
                     'message': 'An error happened during the loading of the discount list.',
                     'close': 'Close',
    },
    'already_have_coupon_error': {
                     'title': 'Error',
                     'message': 'You already have a coupon for this discount! You cannot get another one.',
                     'close': 'Close',
    },
    'coupon_get_error': {
                     'title': 'Error',
                     'message': 'An error happened during the creation of the new coupon.',
                     'close': 'Close',
    },
    'coupon_use_error': {
                     'title': 'Error',
                     'message': 'An error happened during the usage of the coupon. The coupon has already been used or is not valid.',
                     'close': 'Close',
    },
    'coupon_delete_error': {
                     'title': 'Error',
                     'message': 'An error happened during the delete of the coupon.',
                     'close': 'Close',
    },
    'coupon_list_load_error' : {
                     'title': 'Error',
                     'message': 'An error happened during the loading of the coupon list.',
                     'close': 'Close',
    },
    'recommendations_get_error': {
                     'title': 'Error',
                     'message': 'An error happened during the loading of the places recommended for you.',
                     'close': 'Close',
    },
    'rating_save_error': {
                     'title': 'Error',
                     'message': 'An error happened while saving your rating.',
                     'close': 'Close',
    },
    'place_list_load_error': {
                     'title': 'Error',
                     'message': 'An error happened during the loading of the list of restaurants.',
                     'close': 'Close',
    },
    'place_save_error': {
                     'title': 'Error',
                     'message': 'An error happened while saving the restaurant.',
                     'close': 'Close',
    },
    'place_suggest_error': {
                     'title': 'Error',
                     'message': 'An error happened while sending the suggestion.',
                     'close': 'Close',
    },
    'owner_save_error': {
                     'title': 'Error',
                     'message': 'An error happened while saving the owner of the restaurant.',
                     'close': 'Close',
    },
    'settings_save_error': {
                     'title': 'Error',
                     'message': 'An error happened while saving your settings.',
                     'close': 'Close',
    },
    'user_home_save_error': {
                     'title': 'Error',
                     'message': 'An error happened while saving your home city.',
                     'close': 'Close',
    },
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
#     'profile_intro': 'Ciao!! Per offrirti un\'esperienza personalizzata abbiamo bisogno di alcune indormazioni su di te.',
    'profile_intro': 'Ciao!! Per offrirti un\'esperienza personalizzata con le migliori raccomandazioni di ristoranti *per te*, abbiamo bisogno di sapere da dove vieni.',
    'profile_edit_intro' : 'Modifica le tue informazioni personali.',
    'first_name': 'Nome',
    'last_name': 'Cognome',
    'home_city': u'In quale città vivi?',
    'gender': 'Genere',
    'age': u'Età',
    '<18_years': 'Meno di 18 anni',
    'years_old' : 'anni',
    '>55_years': u'Più di 55 anni',
    'save': 'Salva',
      
    # PROFILE 2
    'profile2_text1': 'Questi sono i posti che abbiamo trovato per',
    'profile2_text2': u'Dicci cosa ne pensi dei ristoranti della tua città',
#     'profile_feedback': u'Le tue opinioni aiuteranno le persone che visiteranno la tua città!! Nessuno li conosce meglio di uno del posto :) ',
    'profile_feedback': u'Più ristoranti voti, meglio potremo capire i tuoi gusti e migliori saranno le raccomandazioni calcolte per te! :) ',
    'no_places_city': u'Siamo spiacenti, non conosciamo nessun posto nella tua città.',
    'prev': 'Indietro',
    'next': 'Avanti',
    'continue': 'Continua', 
    'done_next_step': 'Fatto, vai al prossimo passo',
    'done_letsgo': 'Fatto, vai alle raccomandazioni',
    'rating_purposes' : {
        'how_experience': 'Come &egrave; stata la tua esperienza?',
        'tourists': 'Per una cena con degli ospiti da fuori citt&agrave;',
        'partner': 'Per una cena romantica con il/la tuo/a compagno/a',
        'friends': 'Per una cena con gli amici',
        'price_quality': 'Per la pausa pranzo',
        'tourists_short': 'con ospiti',
        'partner_short': 'romantico',
        'friends_short': 'con amici',
        'price_quality_short': 'pausa pranzo',
        'tips_like': 'Mi piace',
        'tips_neutral': 'Sono neutrale',
        'tips_notlike': 'Non mi piace',
        'tips_notknow': 'Non ci sono mai stato per questo motivo'
    },
      
    # LETSGO
    'letsgo_title': 'Ristoranti raccomandati vicino a te',
    'letsgo_title_city': 'Ristoranti raccomandati a',
    'geoposition_error': 'Non siamo in grado di stabilire la tua posizione al momento, abbiamo impostato Trento come tua citta`. Usa il bottone di refresh per riprovare la geolocalizzazione.',
    'letsgo_subtitle': 'Qui trovi alcuni dei ristoranti attorno a te, che ti raccomandiamo. Abbiamo analizzato i tuoi gusti, espressi tramite i tuoi voti, e pensiamo che questi posti ti potrebbero piacere. ',
    'welcome': 'Benvenuto',
    'loading': 'Caricamento',
    'loading_places': u'Stiamo analizzando i tuoi gusti, espressi tramite i voti, e stiamo cercando i ristoranti che ti piaceranno di più.',
    'loading_settings': 'Sto caricando le impostazioni',
    'getting_position': 'Sto ottenendo la tua posizione',
    'in_this_picture' : 'In questa immagine',
    'with_visitors': 'con ospiti',
    'romantic_dinner': 'romantico',
    'with_friends': 'con amici',
    'lunch': 'pausa pranzo',
    'select_purpose': 'Seleziona il tuo motivo',
    'restaurant_name' : 'Nome del ristorante',
    'address' : 'Indirizzo',
    'distance' : 'Distanza',
    'no_geolocation' : u'La geolocalizzazione non è supportata da questo browser.',
    'no_places_position' : 'Siamo spiacenti, non abbiamo trovato alcun posto vicino alla tua posizione.',
    'coming_soon' : 'Presto disponibile.',
      
    'search_settings_popup' : {
        'title': 'Impostazioni di ricerca',
        'purpose': 'Seleziona il tuo motivo',
        'purpose_help': 'Seleziona il motivo di base che verr&agrave; visualizzato per primo al tuo prossimo accesso.',
        'tourists': 'Cena con degli ospiti',
        'partner': 'Cena romantica',
        'friends': 'Cena con gli amici',
        'price_quality': 'Pausa pranzo',
        'max_distance': 'Distanza massima in metri',
        'num_places': 'Numero di ristoranti raccomandati',
        'select_different_city': 'Seleziona una citt&agrave; diversa',
        'save_reload': 'Salva e aggiorna',
        'city_error': 'Per favore, seleziona la citt&agrave; dalla lista di autocompletamento oppure rimuovi la citt&agrave; che hai indicato.',
    },
      
    'today_closed': 'Oggi chiuso',
    'today_closed_tomorrow': 'Oggi chiuso, ',
    'opens_at': 'Apre alle ',
    'open_till': 'E\' aperto fino alle ',
    'tomorrow_closed': 'Domani chiuso',
    'tomorrow_open_at': 'Apre domani alle ',
    'today_tomorrow_closed': 'Chuso oggi e domani',
    'prediction': 'La nosta previsione del tuo gradimento',
    'next_text': 'No, grazie. Il prossimo',
    
    'reclist_end': 'Hai raggiunto la fine delle tue raccomandazioni.',
#     'your_settings': 'Stai cercando {num} ristoranti a meno di {dist} metri da{loc}',
#     'current_position': 'lla tua posizione attuale.',
#     'city_center': u', centro città.',
#     'change_settings': u'Puoi ottenere più raccomandazioni cambiando le tue impostazioni. Apri il menu a sinistra e usa la voce "Impostazioni" per accedere e modificare le tue impostazioni. In alternativa, usa il bottone qui sotto.',
    'change_settings': u'Se vuoi ricevere più raccomandazioni, per favore configura le tue impostazioni in modo appropriato.',
    'goto_settings': 'Accedi alle impostazioni',
      
    # RATINGS
    'new_rest_rating_popup' : {
        'title': 'Aggiungi un nuovo posto e votalo',
        'name_placeholder': 'Nome del ristorante',
        'address_placeholder': 'Indirizzo',
        'picture_placeholder': 'URL dell\'immagine',
        'save': 'Salva',
        'how_experience': 'Come &egrave; stata la tua esperienza?',
        'tourists_short': 'con ospite',
        'partner_short': 'romantico',
        'friends_short': 'con amici',
        'price_quality_short': 'pausa pranzo',
    },
      
    'suggest_rest_popup' : {
        'title': 'Suggerisci un ristorante',
        'email': 'Indirizzo email',
        'email_helper': 'Il tuo indirizzo email serve per poterti contattare e ringraziare per il tuo contributo.',
        'rest_name': 'Nome del ristorante',
        'missing_name': 'Per favore, inserisci almeno il nome del ristorante che stai suggerendo.',
        'details': 'Altri dettagli',
        'send_suggestion': 'Manda suggerimento',
        'suggestion_sent': 'Suggerimento mandato con successo, grazie.',                    
    },
    'ratings_text1': u'Più voti assegnerai, migliori saranno le raccomandazioni calcolate apposta per te!',
    'ratings_text2': u'Sei stato di nuovo in un ristorante che hai già votato? Aggiorna il tuo voto!',
    'city_select': u'Per favore, seleziona una città',
    'no_places_selected': u'Siamo spiacenti, non conosciamo ristoranti nella città selezionata.',
    'create_place_button': 'Se non trovi il ristorante che stai cercando, lo puoi aggiungere!',
    'add_place': 'Aggiungi posto',
    'suggest_place_button': 'Se non trovi il ristorante che stai cercando, lo puoi suggerire!',
    'suggest_place': 'Suggerisci ristorante',
    'search_name': 'Cerca per nome',
    'map_search': 'Cerca nella mappa',
    'done': 'Ho finito',
    'city_mandatory': u'La città deve essere selezionata!!',
    'new_place_saved': 'Il nuovo ristorante e` stato salvato correttamente ed e` stato aggiunto alla lista.',
    'missing_name': 'Per favore, inserisci il nome del ristorante!',
    'missing_address': 'Per favore, inserisci l\'indirizzo del ristorante!',
    'rating_hints': ['molto cattivo', 'cattivo', 'neutrale', 'buono', 'molto buono'],
    
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
    'rest_main_picture': 'Immagine principale (URL)',
    'rest_other_pictures': 'Altre immagini (URL)',
    'add_picture': 'Aggiungi nuova immagine',
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
    'picture_help': 'L\'immagine deve avere dimensioni 700*429 (larghezza/altezza). Se le dimensioni sono diverse, l\'immagine viene ridimensionata e tagliata per corrispondere a queste dimensioni. Controlla l\'anteprima qui sotto prima di salvare.',
    
    'read_more': u'Leggi di più',
    'read_less': 'Leggi di meno',
    
    'back': 'Indietro',
    'back_to_rest' : 'Torna al ristorante',
    'back_to_dlist' : 'Torna alle offerte',
    
    # OWNER RESTAURANT CHOICE
    'owner_choose_rest' : 'Scegli il ristorante che vuoi gestire.',
    'change_rest' : 'Cambia ristorante',
    
    # DISCOUNT
    'your_coupon': 'Il tuo coupon',
    'discount': 'Offerta',
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
                         'no_coupons': 'Coupon esauriti',
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
                         'see_used_coupon': 'Hai usato il tuo coupon',
                         'goto_restaurant': 'Vai al ristorante',
                         'use': 'Usa',
                         'you_have_coupon_code': 'Hai un coupon con codice',
                         'delete': 'Cancella',
                         
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
    'you_have_coupon_with': 'Hai un coupon con',
    'code': 'codice',
    'coupon_used_date': u'Il coupon è già stato usato il ',
    'coupon_deleted_date': u'Il coupon è già stato cancellato il ',
    
    # ADMIN
    'restaurant_list_edit': 'Cerca ristorante',
    'select_city': u'Seleziona una città per cercare i posti che vuoi modificare',
    'rest_owner': 'Proprietario del ristorante (email)',
    'manage_admins': 'Gestisci amministratori',
    'add_admin': 'Aggiungi nuovo amministratore',
    'current_admins': 'Attuali amministratori',
    
    # ERROR
    'close_button': 'Chiudi',
    'error': 'Errore',
    'error_sorry': 'Ci scusiamo per l\'inconveniente, cercheremo di risolvere il problema il prima possibile.',
    'logout_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il logout. Riprovare pi&ugrave; tardi. In ogni caso, la sessione scadr&agrave; in 30 minuti.',
                     'close': 'Chiudi',
    },
    'error_city_missing': {
                     'title': 'Citt&agrave; non selezionata',
                     'message': 'Per favore, seleziona la tua citt&agrave; dalla lista di autocompletamento prima di salvare.',
                     'close': 'Chiudi',
    },
    'unauthorized_error': {
                           'title': 'Errore',
                           'message': 'Non sei autorizzato ad eseguire questa operazione.Controlla di esserti autenticato e di avere i permessi necessari.',
                           'close': 'Chiudi',
    },
    'permission_error': {
                         'title': 'Errore di autorizzazione',
                         'message': 'Questo servizio ha bisogno che tu accetti i permessi richiesti per funzionare. Per favore, torna indietro e accetta i permessi per accedre ai tuoi dati pubblici e al tuo indirizzo email.',
    },
    'admin_delete_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante la cancellazione di un amministratore.',
                     'close': 'Chiudi',
    },
    'admin_save_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il salvataggio di un nuovo amministratore. Controlla che l\'email sia corretta e prova nuovamente.',
                     'close': 'Chiudi',
    },
    'discount_save_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il salvataggio dell\'offerta. Controlla che i dati siano corretti e prova nuovamente.',
                     'close': 'Chiudi',
    },
    'discount_publish_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante la pubblicazione dell\'offerta.',
                     'close': 'Chiudi',
    },
    'discount_delete_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante la cancellazione dell\'offerta.',
                     'close': 'Chiudi',
    },
    'discount_list_load_error' : {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il caricamento delle offerte.',
                     'close': 'Chiudi',
    },
    'already_have_coupon_error': {
                     'title': 'Errore',
                     'message': 'Hai gi&agrave; un coupon per questa offerta! Non puoi ottenerne un altro.',
                     'close': 'Chiudi',
    },
    'coupon_get_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante la creazione del nuovo coupon.',
                     'close': 'Chiudi',
    },
    'coupon_use_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante l\'utilizzo del coupon. Il coupon &egrave; gi&agrave; stato usato o non &egrave; valido.',
                     'close': 'Chiudi',
    },
    'coupon_delete_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante la cancellazione del coupon.',
                     'close': 'Chiudi',
    },
    'coupon_list_load_error' : {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il caricamento dei coupons.',
                     'close': 'Chiudi',
    },
    'recommendations_get_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il caricamento dei ristoranti che ti raccomandiamo.',
                     'close': 'Chiudi',
    },
    'rating_save_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il salvataggio del tuo voto.',
                     'close': 'Chiudi',
    },
    'place_list_load_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il caricamento della lista di ristoranti.',
                     'close': 'Chiudi',
    },
    'place_save_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il salvataggio del ristorante.',
                     'close': 'Chiudi',
    },
    'place_suggest_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante l\'invio del suggerimento.',
                     'close': 'Chiudi',
    },
    'owner_save_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il salvataggio del proprietario del ristorante.',
                     'close': 'Chiudi',
    },
    'settings_save_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il salvataggio delle tue impostazioni.',
                     'close': 'Chiudi',
    },
    'user_home_save_error': {
                     'title': 'Errore',
                     'message': 'Si &egrave; verificato un errore durante il salvataggio della tua citt&agrave;.',
                     'close': 'Chiudi',
    },
    
}

