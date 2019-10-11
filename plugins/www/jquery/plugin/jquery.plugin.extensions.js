/*
 * @see http://nicolas.rudas.info/jQuery/getPlugin/
 */
 
function pluginLanguage() {
	return getZMILangStr('LOCALE',{'nocache':""+new Date()});
}

/**
 * jQuery UI
 */
function pluginUI(s, c) {
	//$ZMI.setCursorWait("pluginUI");
	$.plugin('ui',{
		files: [
				$ZMI.getConfProperty('jquery.ui'),
				$ZMI.getConfProperty('zmi.ui')
		]});
	$.plugin('ui').get(s,function(){
			//$ZMI.setCursorAuto("pluginUI");
			c();
		});
}

/**
 * jQuery UI Datepicker
 */
function pluginUIDatepicker(s, c) {
	//$ZMI.setCursorWait("pluginUIDatepicker");
	var lang = pluginLanguage();
	$.plugin('ui_datepicker',{
		files: [
				'/++resource++zms_/jquery/ui/i18n/jquery.ui.datepicker-'+lang+'.js'
		]});
	pluginUI(s,function() {
			//$ZMI.setCursorAuto("pluginUIDatepicker");
			$.plugin('ui_datepicker').get(s,c);
		});
}

/**
 * jQuery Autocomplete
 */
function zmiAutocomplete(s, o) { 
	pluginAutocomplete(s,function() { 
 		$(s).autocomplete(o).after('<i class="icon-search fas fa-search"></i>').parent().addClass("inner-addon right-addon"); 
	}); 
}

/**
 * ZMSLightbox
 */
$(function(){
	$('a.zmslightbox,a.fancybox')
		.each(function() {
				var $img = $("img",$(this));
				$img.attr("data-hiresimg",$(this).attr("href"));
				$(this).click(function() {
						return showFancybox($img);
					});
			});
});

function pluginFancybox(s, c) {
	$.plugin('zmslightbox',{
		files: ['/++resource++zms_/jquery/zmslightbox/zmslightbox.js',
				'/++resource++zms_/jquery/zmslightbox/zmslightbox.css']
		});
	$.plugin('zmslightbox').get(s,c);
}

function showFancybox($sender) {
	pluginFancybox('body',function() {
			show_zmslightbox($sender);
		});
	return false;
}


/**
 * Autocomplete
 * @see http://bassistance.de/jquery-plugins/jquery-plugin-autocomplete/
 * @deprecated
 */
function pluginAutocomplete(s, c) {
	$.plugin('autocomplete',{
		files: ['/++resource++zms_/jquery/autocomplete/jquery.autocomplete.min.js',
				'/++resource++zms_/jquery/autocomplete/jquery.autocomplete.css']
	});
	$.plugin('autocomplete').get(s,c);
}


/**
 * Jcrop - the jQuery Image Cropping Plugin
 * @see http://deepliquid.com/content/Jcrop.html
 */
function runPluginJcrop(c) {
	$.plugin('jcrop',{
		files: ['/++resource++zms_/jquery/jcrop/jquery.Jcrop.min.js',
				'/++resource++zms_/jquery/jcrop/jquery.Jcrop.css']
		});
	$.plugin('jcrop').get('body',c);
}