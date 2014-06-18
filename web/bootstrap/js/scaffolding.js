Index = {
	settings: {
		transparent: true,
	},

	init: function() {
		s = this.settings;
	},

	scrollEvent: function(e) {
	    if( e.scrollTop() > 550 ) {
	        if(s.transparent) {
	            s.transparent = false;
	            $('nav[role="navigation"]').removeClass('navbar-transparent');
	        }
	    } else {
	        if( !s.transparent ) {
	            s.transparent = true;
	            $('nav[role="navigation"]').addClass('navbar-transparent');
	        }
	    }		
	},

};

Login = {
	settings: {

	},

	init: function(e) {
		s = this.settings;
		this.login();
		this.bindUIActions();
	},

	login: function() {
		$("#login-form").submit(function(e) {

			$('#login-btn').attr('disabled', 'disabled');
			var uname = $("#uname").val();
			var password = $("#password").val();

			if (uname.length < 1) {
				e.preventDefault();						
				$("#uname-label").text("Must enter a username");
				$("#uname-group").addClass('shake');
				return;
			}

			if (password.length < 1) {
				e.preventDefault();			
				$("#password-label").text("Must enter a password");
				$("#password-group").addClass("shake");
				return;
			}
		})
	},

	bindUIActions: function() {
		$('#uname-group').on('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function() {
			$("#uname-group").removeClass('shake');
			$('#login-btn').removeAttr('disabled');
		});

		$('#password-group').on('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function() {
			$("#password-group").removeClass('shake');
			$('#login-btn').removeAttr('disabled');
		});	
	},
}

SignUp = {
	settings: {
		price: '',
	},

	init: function(price) {
		s = this.settings;
		s.price = price;
		this.priceChanger();		
		this.bindUIActions();
	},

	priceChanger: function() {
		$('input[name=currency]').on('click', function() {

			var curr = $('input[name=currency]:checked').val();

			$(".currency").text(curr);

			$("#permonth").text(s.price[curr]['bitusenet']['onemonth']);
			$("#month").text(s.price[curr]['bitusenet']['onemonth']);

			$("#3permonth").text(s.price[curr]['bitusenet']['threepermonth']);
			$("#3month").text(s.price[curr]['bitusenet']['threemonth']);

			$("#6permonth").text(s.price[curr]['bitusenet']['sixpermonth']);
			$("#6month").text(s.price[curr]['bitusenet']['sixmonth']);

			$("#12permonth").text(s.price[curr]['bitusenet']['twelvepermonth']);
			$("#12month").text(s.price[curr]['bitusenet']['twelvemonth']);
		});
	},

	bindUIActions: function() {
		$("#signup-form").submit(function(e) {
			$('#submit-btn').attr('disabled', 'disabled');		
			var uname = $("#uname").val();
			var password = $("#password").val();

			if (uname.length < 1) {
				e.preventDefault();			
				$("#uname-label").text("Username must be entered");
				$("#uname-group").addClass('shake').addClass('has-error');
				return;
			}

			if (password.length < 1) {
				e.preventDefault();
				$("#password-label").text("Password must be entered");
				$("#password-group").addClass("shake").addClass('has-error');
				return;
			}
		})

		$('#uname-group').on('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function() {
			$("#uname-group").removeClass('shake');
			$('#submit-btn').removeAttr('disabled');
		});	

		$('#password-group').on('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function() {
			$("#password-group").removeClass('shake');
			$('#submit-btn').removeAttr('disabled');
		});	
	},
};