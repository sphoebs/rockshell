//load underscore template
var xmlhttp = new XMLHttpRequest();
xmlhttp.open("GET","/static/js_templates/error_popup.ejs",false);
xmlhttp.send(null);
var template = xmlhttp.responseText;
var compiled = _.template(template);

function show_error(strings){
	var html = compiled({strings: strings });
	$('.popup-area').html(html);
	
	$('.popup-area').show();
	
//	$('.popup-scrollable').enscroll({
//	    showOnHover: false,
//	    verticalScrolling: true,
//		horizontalScrolling: false,
//		zIndex: 320,
//	    verticalTrackClass: 'track-red',
//	    verticalHandleClass: 'handle-red'
//	});
	
	$('#close-popup, #cancel').click(function(){
		$('.popup-area').html('');
	});
}