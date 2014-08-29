/**
 * Unicorn Admin Template
 * Version 2.2.0
 * Diablo9983 -> diablo9983@gmail.com
**/
$(function(){
	
	var ul = $('#sidebar > ul');	
	var ul2 = $('#sidebar > ul > li.open ul');

	// === Resize window related === //
	$(window).on('resize',function()
	{
		wwidth = $(window).width();
		if(wwidth >= 768 && wwidth <= 991)
		{	
			$('#sidebar > ul > li.open ul').attr('style','').parent().removeClass('open');
			ul.css({'display':'block'});
		}
		
		if(wwidth <= 767)
		{
			$('#sidebar').niceScroll();
			$('#sidebar').getNiceScroll().resize();

			if($(window).scrollTop() > 35) {
				$('body').addClass('fixed');
			} 
			$(window).scroll(function(){
				if($(window).scrollTop() > 35) {
					$('body').addClass('fixed');
				} else {
					$('body').removeClass('fixed');
				}
			});
		}

		if(wwidth > 767)
		{
			ul.css({'display':'block'});
			
			$('body').removeClass('menu-open');
			$('#sidebar').attr('style','');
			$('#user-nav > ul').css({width:'auto',margin:'0'});
		}

	});
	
	if($(window).width() <= 767)
	{
		if($(window).scrollTop() > 35) {
			$('body').addClass('fixed');
		} 
		$(window).scroll(function(){
			if($(window).scrollTop() > 35) {
				$('body').addClass('fixed');
			} else {
				$('body').removeClass('fixed');
			}
		});
		//jPM.on();
		$('#sidebar').niceScroll({
			zindex: '9999'
		});
		$('#sidebar').getNiceScroll().resize();
	}

	if($(window).width() > 767)
	{
		ul.css({'display':'block'});
	}
	if($(window).width() > 767 && $(window).width() < 992) {
		ul2.css({'display':'none'});
	}

	$('#menu-trigger').on('click',function(){
		if($(window).width() <= 767) {
			if($('body').hasClass('menu-open')) {
				$('body').removeClass('menu-open');
			} else {
				$('body').addClass('menu-open');
			}
		}
		return false;
	});

	

	// === Tooltips === //
	$('.tip').tooltip();	
	$('.tip-left').tooltip({ placement: 'left' });	
	$('.tip-right').tooltip({ placement: 'right' });	
	$('.tip-top').tooltip({ placement: 'top' });	
	$('.tip-bottom').tooltip({ placement: 'bottom' });	
		
	// === Style switcher === //
	$('#style-switcher i').click(function()
	{
		if($(this).hasClass('open'))
		{
			$(this).parent().animate({right:'-=220'});
			$(this).removeClass('open');
		} else 
		{
			$(this).parent().animate({right:'+=220'});
			$(this).addClass('open');
		}
		$(this).toggleClass('icon-arrow-left');
		$(this).toggleClass('icon-arrow-right');
	});
	
	$('#style-switcher a').click(function()
	{
		var style = $(this).attr('href').replace('#','');
		$('.skin-color').attr('href','css/unicorn.'+style+'.css');
		$(this).siblings('a').css({'border-color':'transparent'});
		$(this).css({'border-color':'#aaaaaa'});
	});

	$(document).on('click', '.submenu > a',function(e){
		e.preventDefault();
		var submenu = $(this).siblings('ul');
		var li = $(this).parents('li');

		var submenus = $('#sidebar li.submenu ul');
		var submenus_parents = $('#sidebar li.submenu');

		
		if(li.hasClass('open'))
		{
			if(($(window).width() > 976) || ($(window).width() < 768)) {
				submenu.slideUp();
			} else {
				submenu.fadeOut(150);
			}
			li.removeClass('open');
		} else 
		{
			if(($(window).width() > 976) || ($(window).width() < 768)) {
				submenus.slideUp();			
				submenu.slideDown();
			} else {
				submenus.fadeOut(150);			
				submenu.fadeIn(150);
			}
			submenus_parents.removeClass('open');		
			li.addClass('open');	
		}
		$('#sidebar').getNiceScroll().resize();
	});

	$('#sidebar li.submenu ul').on('mouseleave',function(){
		if($(window).width() >= 768 && $(window).width() < 977) {
			$(this).fadeOut(150).parent().removeClass('open');
		}
	});

	$('.go-full-screen').click(function(){
		backdrop = $('.white-backdrop');
		wbox = $(this).parents('.widget-box');
		/*if($('body > .white-backdrop').length <= 0) {
			$('<div class="white-backdrop">').appendTo('body');
		}*/
		if(wbox.hasClass('widget-full-screen')) {
			backdrop.fadeIn(200,function(){
				wbox.removeClass('widget-full-screen',function(){
					backdrop.fadeOut(200);
				});
			});
		} else {
			backdrop.fadeIn(200,function(){
				wbox.addClass('widget-full-screen',function(){
					backdrop.fadeOut(200);
				});
			});
		}
	});

	// IE7 
	$(function($) {
	    $("input[type=text], input[type=password], textarea").bind('focus blur',function(){$(this).toggleClass('focus')});
	});

	//Theme Switcher
	switcherBtn = $('#switcher-button');
	switcherPanel = $('#switcher-inner');

	switcherBtn.click(function(){
		if(switcherPanel.hasClass('open')) {
			switcherPanel.hide(300);
			switcherPanel.removeClass('open');
		} else {
			switcherPanel.show(300);
			switcherPanel.addClass('open');
		}
	});

	color = $('body').data('color');
	$('#color-style a[data-color='+color+']').addClass('active');

	$('#color-style a').click(function(){
		var color = $(this).attr('data-color');
		$(this).parent().find('a').removeClass('active');
		$(this).addClass('active');
		$('body').attr('data-color',color);
		return false;
	});

	if($('body').hasClass('flat')) {
		$('#layout-type a[data-option="flat"]').addClass('active');
	} else {
		$('#layout-type a[data-option="old"]').addClass('active');
	}
	$('#layout-type a').click(function(){
		var type = $(this).attr('data-option');
		if(type == 'flat') {
			$('body').addClass('flat');
		} else {
			$('body').removeClass('flat');
		}
		$(this).parent().find('a').removeClass('active');
		$(this).addClass('active');
	});
});

