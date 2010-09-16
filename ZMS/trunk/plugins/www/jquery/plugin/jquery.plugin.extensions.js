/*
 * @see http://nicolas.rudas.info/jQuery/getPlugin/
 */

/*
 * Defaults
 */
$(function(){
	$.plugin('zms',{
		files: ['/++resource++zms_/jquery/jquery.cookies.2.1.0.min.js',
				'/++resource++zms_/jquery/jquery.dimensions.1.2.0.min.js']
		});
	$.plugin('zms').get('body',function(){
	  if (self.location.href.indexOf('preview=preview')>0) {
	    $('.ZMSObject')
          .mouseover( function(evt) {
            $(this).addClass('preview').addClass('highlight'); 
          })
          .mouseout( function(evt) {
            $(this).removeClass('preview').removeClass('highlight'); 
          })
          .dblclick( function(evt) {
            var id = $(this).attr('id');
            var href = self.location.href;
            if (href.indexOf('?')>0) {
              href = href.substr(0,href.indexOf('?'));
            }
            if (href.lastIndexOf('/')>0) {
              href = href.substr(0,href.lastIndexOf('/'));
            }
            self.location.href = href+'/'+id+'/manage_main'; 
          })
          .attr( "title", "Double-click to edit!");
	  }
	});
});


/* Fancybox
 * @see http://fancybox.net/
 */
$(function(){
	pluginFancybox('a.fancybox',function() {
			$('a.fancybox').fancybox({
				'autoScale'		: false,
				'titleShow'		: false,
				'hideOnContentClick': true,
				'transitionIn'	: 'elastic',
				'transitionOut'	: 'elastic'
			});
		}
	);
});

function pluginFancybox(s, c) {
	$.plugin('fancybox',{
		files: ['/++resource++zms_/jquery/fancybox/jquery.easing-1.3.pack.js',
				'/++resource++zms_/jquery/fancybox/jquery.fancybox-1.3.1.pack.js',
				'/++resource++zms_/jquery/fancybox/jquery.fancybox-1.3.1.css']
		});
	$.plugin('fancybox').get(s,c);
}


/* Autocomplete
 * @see http://bassistance.de/jquery-plugins/jquery-plugin-autocomplete/
 */
function pluginAutocomplete(s, c) {
	$.plugin('autocomplete',{
		files: ['/++resource++zms_/jquery/autocomplete/jquery.bgiframe.min.js',
				'/++resource++zms_/jquery/jquery.dimensions.1.2.0.min.js',
				'/++resource++zms_/jquery/autocomplete/jquery.autocomplete.min.js',
				'/++resource++zms_/jquery/autocomplete/jquery.autocomplete.css']
	});
	$.plugin('autocomplete').get(s,c);
}


/* jQuery Editable Combobox (jEC)
 * @see http://code.google.com/p/jquery-jec/
 */
function pluginJEC(s, c) {
	$.plugin('jec',{
		files: ['/++resource++zms_/jquery/jec/jquery.jec.min-0.5.2.js']
	});
	$.plugin('jec').get(s,c);
}