function zmiToggleClick(toggle, callback) {
	$ZMI.writeDebug('zmiToggleClick: '+toggle+'['+($(toggle).length)+'];callback='+(typeof callback));
	var $container = $(toggle).parents("ol:first");
	$container.children(".zmi-page").remove();
	if ($(toggle).hasClass($ZMI.icon_clazz("icon-caret-right"))) {
		$(toggle).removeClass($ZMI.icon_clazz("icon-caret-right")).addClass($ZMI.icon_clazz("icon-caret-down")).attr({title:'-'});
		var href = '';
		var homeId = null;
		$(toggle).parents(".zmi-page").each(function(){
				var dataId = $(this).attr("data-id");
				var dataHomeId = $(this).attr("data-home-id");
				if (homeId == null) {
					homeId = dataHomeId;
				}
				if (homeId != dataHomeId) {
					href = '/'+dataHomeId+'/'+homeId+href;
					homeId = dataHomeId;
				}
				else {
					href = '/'+dataId+href;
				}
			});
		if (!href.indexOf('/'+homeId)==0) {
			href = '/'+homeId+href;
		}
		var base = $ZMI.getPhysicalPath();
		base = base.substr(0,base.indexOf('/'+homeId));
		// Set wait-cursor.
		$container.append( '<div id="loading" class="zmi-page"><i class="icon-spinner icon-spin"></i>&nbsp;&nbsp;'+getZMILangStr('MSG_LOADING')+'<'+'/div>');
		// JQuery.AJAX.get
		$ZMI.writeDebug('zmiToggleClick:'+base+href+'/manage_ajaxGetChildNodes?lang='+getZMILang());
		$.get(base+href+'/manage_ajaxGetChildNodes',{lang:getZMILang(),meta_types:$ZMI.getConfProperty('zms.plugins.www.object.manage_menu.meta_types','0,ZMSTrashcan')},function(data){
				// Reset wait-cursor.
				$("#loading").remove();
				// Get and iterate pages.
				var pages = $("pages",data).children("page");
				if ( pages.length == 0) {
					$(toggle).removeClass($ZMI.icon_clazz("icon-caret-down")).attr({title:''});
				}
				else {
					for (var i = 0; i < pages.length; i++) {
						var page = pages[i];
						var page_home_id = $(page).attr("home_id");
						var page_id = $(page).attr("id").substr(page_home_id.length+1);
						var page_absolute_url = $(page).attr("absolute_url");
						var page_meta_type = $(page).attr("meta_id");
						var page_titlealt = $(page).attr("titlealt");
						var page_type = $(page).attr("attr_dc_type");
						var page_display_icon = $(page).attr("display_icon");
						var html = '';
						html += '<'+'ol data-id="'+page_id+'" data-home-id="'+page_home_id+'" class="zmi-page '+page_meta_type+'">';
						html += '<'+'div class="';
						if ($(page).attr("active")== "0") {
							html += 'inactive ';
						} else {
							html += 'active ';
						}
						if (typeof(page_type) != 'undefined') {
							if ( page_type.length > 0 ) {
								html += 'type-'+page_type+' ';
							}
						}
						if ($(page).attr("restricted")=="True") {
							html += 'restricted" title= "Login Required';
						}
						html += '">';
						html += $ZMI.icon("icon-caret-right toggle",'title="+" onclick="zmiToggleClick(this)"')+' ';
						html += '<'+'a href="'+page_absolute_url+'/manage_main?lang='+getZMILang()+'" onclick="return zmiFollowHref(this)">';
						html += page_display_icon+' ';
						html += page_titlealt;
						html += '<'+'/a> ';
						html += '<'+'/div>';
						html += '<'+'/ol>';
						$container.append(html);
					}
				}
				if (typeof callback == 'function') {
					$ZMI.writeDebug('zmiToggleClick: callback()');
					callback();
				}
			});
	}
	else if ($(toggle).hasClass($ZMI.icon_clazz("icon-caret-down"))) {
		$(toggle).removeClass($ZMI.icon_clazz("icon-caret-down")).addClass($ZMI.icon_clazz("icon-caret-right")).attr({title:'+'});
		if (typeof callback == 'function') {
			$ZMI.writeDebug('zmiToggleClick: callback()');
			callback();
		}
	}
}
function zmiFollowHref(anchor) {
	self.window.parent.manage_main.location.href=$(anchor).attr("href");
	return false;
}
function zmiRefresh() {
	$("ol:not(:first)").remove();
	$('.toggle').removeClass($ZMI.icon_clazz("icon-caret-down")).addClass($ZMI.icon_clazz("icon-caret-right"))
	var $ol = $("ol:first");
	var id = $ol.attr("data-id");
	var homeId = $ol.attr("data-home-id");
	$ZMI.writeDebug('zmiRefresh: id='+id+'; homeId='+homeId);
	var href = $ZMI.getPhysicalPath();
	try {
		href = self.window.parent.manage_main.$ZMI.getPhysicalPath();
	}
	catch(e) {
		$ZMI.writeDebug('zmiRefresh: cannot get physical-path from parent - ' + e);
	}
	href = href.substr(href.indexOf(homeId));
	$ZMI.writeDebug('zmiRefresh: href='+href);
	var ids = href.split('/');
	var fn = function() {
			$ZMI.writeDebug("zmiRefresh.ids= "+ids.join(', '));
			var oldHomeId = homeId;
			if (ids.length > 0) {
				var id = ids[0];
				ids = ids.slice(1,ids.length);
				if (id == homeId) {
					id = 'content'
				}
				if ($('*[data-id="'+id+'"][data-home-id="'+homeId+'"]').length==0) {
					homeId = id;
					id = 'content';
				}
				if (homeId!=oldHomeId) {
					$('*[data-id!="content"][data-home-id="'+oldHomeId+'"]').hide();
				}
				if (ids.length > 0 && ids[0] == id) {
					ids = ids.slice(1,ids.length);
				}
				$ZMI.writeDebug("zmiRefesh.id= "+id+",home-id="+homeId+"->"+$('*[data-id="'+id+'"][data-home-id="'+homeId+'"]').length);
				zmiToggleClick($('*[data-id="'+id+'"][data-home-id="'+homeId+'"] .toggle'),arguments.callee);
			}
		};
	fn();
}

function frmresize(r) {
	var frmwidth = 224;
	var frmset = parent.document.getElementsByTagName('frameset');
	if (typeof r != "undefined") {
		var frmwidth = parseInt(frmset[0].cols);
		frmwidth = frmwidth + r
	}
	var colval = frmwidth + ",*";
	frmset[0].cols=colval;
	$.cookies.set('zmi_menu_frmsize',colval, { expires: 365 });
	// loc = location.origin; 
	try {
		localStorage.setItem( 'zmi_menu_frmsize' , colval );
	} catch(err) {
		// do nothing
	}
}

$ZMI.registerReady(function(){
	// loc = location.origin; 
	zmiRefresh();
	runPluginCookies(function() {
			if ( $.cookies.get('zmi_menu_frmsize') ) {
				parent.document.getElementsByTagName('frameset')[0].cols = $.cookies.get('zmi_menu_frmsize');
			} else {
				try {
					if ( localStorage.getItem( 'zmi_menu_frmsize' ) ) {
						parent.document.getElementsByTagName('frameset')[0].cols = localStorage.getItem( 'zmi_menu_frmsize' )
					}
				} catch(err) {
					// do nothing
				}
			};
		});
});

