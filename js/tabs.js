$(function(){
	$("div.admin_tools")
		.find("span")
			.toggle(function (e) {
					$('div.admin').hide();
					var $this = $(this),
						$div = $this.find(">div");
					$div
						.show('fast')
						.css("top", 100 - $this.offset().top + "px")
					$('body').click(function (e) {
						$div.hide();
					});
				},function (e) {
					if ($(e.srcElement).hasClass("admin_tab")) {
						$(this)
							.find("div:not(.tab_strip, .default)")
							.hide('fast')
							.find(".default")
							.show();
					}
				});
	$("div.admin_tools span div").click(function (e) {
		e.stopPropagation(); 
		return true;
	});
	$("div.admin_tools span div.admin>div.tab_strip>span")
		.show_panel();
	$(".content-edit-list .content a")
		.ajax_edit({
			result:"div.content_edit>div.look",
			callback: function(){
				$("div.content_edit>div.tab_strip>span.look_tab")
					.trigger("click");
			}
		});
	$(".user_edit .user-edit-list .user a")
		.ajax_edit({
			result:"div.user_edit>div.data",
			callback: function(){
				$("div.user_edit>div.tab_strip>span.data_tab").trigger("click");
			}
		});
	
	$("textarea.tinymce").tinymce({
		width : 600,
		height : 600,
		script_url:"/addons/tiny_mce/tiny_mce.js",
		theme:"advanced", 
		plugins:"fullscreen, template", 
		external_image_list_url : "/admin/lists/images"
	});
	$("textarea.tinymce").each(function(){
		var $ta = $(this);
		$ta.parent("form").bind("submit", function () { 
			$ta.val($ta.tinymce().getContent()); 
			return true;
		});
	});
});
(function(){
	$.plugin = {
		addFunction : function(name, object){
			$.fn[name] = function(options){
				var args = Array.prototype.slice.call(arguments, 1);
				if(this.length){
					return this.each(function(){
						var instance = $.data(this, name);
						if(instance){
							instance[options].apply(instance, args);
						}else{
							instance = $.data(this, name, Object.create(object).init(options, this));
						}
					});
				}else{
					return this;
				}
			}
		},
		removeFunction : function(name){
			delete $.fn[name];
		},
		listFunctions : function(){
			for(k in $.fn){
				if(typeof $.fn[k] === "function"){
					console.log(k);
				}
			}
		}
	}
	var webspinner = nsjs.ns('webspinner');
	webspinner.ns('admin');
	// webspinner.admin jquery plugins
	webspinner.admin = {
		show_panel: {
			init: function(options, elem){
				this.options = $.extend({}, this.options, options);
				this.elem = elem;
				this.$elem = $(elem);
				this._build()
			},
			_build: function(){
				this.$elem.click(function(e){
					var $this = $(this);
					$("div.admin_tab>div.admin").hide();
					var tab = $this.attr("class").split(' ').filter(function(className){
						return className.indexOf('_tab') > -1;
					})[0].replace("_tab", "");
					$this
						.parents("div.admin")
						.show()
						.children(":not(.tab_strip)")
						.hide();
					$this
						.parents(".admin")
						.find("." + tab)
						.show();
				});
			}
		},
		ajax_edit: {
			init: function(options, elem){
				this.options = $.extend({}, this.options, options);
				this.elem = elem;
				this.$elem = $(elem);
				this._build();
			},
			_build: function(){
				var obj = this;
				this.$elem.click(function(){
					$.get($(this).attr("href"), function(data){
						$(obj.options.result)
							.html(data);
						$(obj.options.result)
							.show();
					});
					if(typeof object.options.callback === "function"){
						obj.options.callback.apply(this);
					}
					return false;
				})
			},
			options : {
				result : null,
				callback : function(){
					console.log("callback fired!")
				}
			}
		}
	}
	$.plugin.addFunction('ajax_edit',webspinner.admin.ajax_edit);
	$.plugin.addFunction('show_panel', webspinner.admin.show_panel);	
}());
