$(document).ready(function() {
	// webmail provider -> email address domains
	var webmail = [
		['Gmail', ['gmail.com', 'googlemail.com']],
		['Outlook.com', ['hotmail.com', 'msn.com', 'live.com', 'outlook.com', 'outlook.com.br', 'hotmail.co.uk', 'hotmail.fr', 'hotmail.de', 'hotmail.be', 'hotmail.com.ar', 'hotmail.es', 'hotmail.com.mx', 'hotmail.com.br', 'live.de', 'live.be', 'live.com.ar', 'live.com.mx']],
		['Office 365', []],
		['Yahoo! Mail', ['yahoo.com', 'rocketmail.com', 'ymail.com', 'yahoo.co.uk', 'yahoo.fr', 'yahoo.de', 'yahoo.com.ar', 'yahoo.com.mx', 'yahoo.com.br', 'yahoo.co.jp', 'yahoo.co.kr', 'yahoo.co.id', 'yahoo.co.in', 'yahoo.com.sg', 'yahoo.com.ph']],
		['Yandex Mail', ['yandex.com', 'yandex.ru']],
		['Mail.Ru', ['mail.ru']],
		['Rambler Mail', ['rambler.ru']],
		['AOL Mail', ['aol.com', 'love.com', 'ygm.com', 'games.com', 'wow.com']],
		['Comcast', ['comcast.net']],
		['WEB.DE', ['web.de']],
		['Terra Mail', ['terra.com.br']],
		['Freenet.de', ['freenet.de']],
		['t-online.de', ['t-online.de']],
		['Orange.fr', ['orange.fr']],
		['Sina', ['sina.com', 'sina.cn']],
		['163.com', ['163.com']],
		['126.com', ['126.com']],
		['Yeah.net', ['yeah.net']],
		['QQ Mail', ['qq.com']],
		['Naver Mail', ['naver.com']],
		['GMX Mail', ['gmx.com', 'gmx.de', 'gmx.net', 'gmx.fr']],
		['Zoho', ['zoho.com']],
		['AT&T Email', ['att.net', 'sbcglobal.net']],
		['Verizon Email', ['verizon.net']],
		['Lycos Mail', ['lycos.com']],
		['Inbox.com', ['inbox.com']],
		['Hushmail', ['hush.com', 'hushmail.com']],
		['iCloud Mail', ['icloud.com', 'me.com', 'mac.com']],
		['ProtonMail', ['protonmail.com', 'protonmail.ch']],
		['atmail', []],
		['Tutanota', ['tutanota.com', 'tutanota.de', 'tutamail.com', 'tuta.io', 'keemail.me']],
		['Runbox', ['runbox.com']],
		['FastMail', ['fastmail.com', 'fastmail.fm']],
		['Zimbra', []]
	];
	var providers = {};
	webmail.forEach(function(x) {
		var name = x[0], domains = x[1];
		domains.forEach(function(domain) { providers[domain] = name; });
	});

	// categorized list of all mail clients
	var mailClients = {
		'web': webmail.slice(0).map(function(x) { return x[0] }),
		'desktop': [
			// Apple Mail
			'Apple Mail 10',
			'Apple Mail 9',

			// Outlook
			'Outlook 2016',
			'Outlook 2013',
			'Outlook 2011',
			'Outlook 2010',
			'Outlook 2007',
			'Outlook 2003',
			'Outlook 2002',
			'Outlook 2000',
			'Windows 10 Mail',
			'Windows 8 Mail',

			// Thunderbird
			'Thunderbird',

			// Lotus Notes
			'IBM Notes 9',
			'Lotus Notes 8.5',
			'Lotus Notes 8',
			'Lotus Notes 7'
		],
		'mobile': [
			// default mail apps
			'Apple Mail',
			'Android Mail',

			// email provider apps
			'Microsoft Outlook',
			'Gmail',
			'Inbox by Gmail',
			'Yahoo Mail',
			'Mail.Ru',
			'Yandex.Mail',
			'AOL',
			'GMX Mail',
			'WEB.DE Mail',
			'Zoho Mail',
			'AT&T Mail',
			'NetEase Mail',
			'NAVER Mail',
			'Rambler Mail',

			// third-party apps
			'Alto Mail',
			'TypeApp Mail',
			'VMware Boxer',
			'CloudMagic Newton Mail',
			'K-9 Mail',
			'Blue Mail',
			'ASUS Email',
			'HTC Mail',
			'Samsung Email',
			'Spark',
			'AirMail',
			'Dispatch'
		]
	};

	// initialize suggestion engine
	var bloodhound = new Bloodhound({
		datumTokenizer: Bloodhound.tokenizers.whitespace,
		queryTokenizer: Bloodhound.tokenizers.whitespace,
		local: []
	});
	bloodhound.initialize();

	// enable default suggestions
	function bloodhoundWithDefaults(q, sync) {
		if (q === '') {
			switch ($('#platform').val()) {
			case 'web':
				var email = $('#email').val();
				if (email) {
					// suggest based on provider
					var index = email.lastIndexOf('@');
					if (index > -1 && index < email.length - 1) {
						var domain = email.substring(index + 1);
						var provider = providers[domain];
						if (provider)
							sync(bloodhound.get(provider));
					}
				} else {
					// suggest popular clients
					sync(bloodhound.get('Gmail', 'Outlook.com', 'Yahoo! Mail'));
				}
				break;
			case 'desktop':
				// suggest popular clients
				sync(bloodhound.get('Outlook 2016', 'Apple Mail 10', 'Windows 10 Mail', 'Thunderbird'));
				break;
			case 'mobile':
				// suggest popular clients
				sync(bloodhound.get('Apple Mail', 'Gmail', 'Microsoft Outlook'));
				break;
			}
		} else {
			bloodhound.search(q, sync);
		}
	}

	// add typeahead
	var createTypeahead = function() {
		$('#client').typeahead(
			{ hint: true, highlight: true, minLength: 0 },
			{ name: 'clients', source: bloodhoundWithDefaults }
		);
	};
	createTypeahead();

	// trigger dataset change events
	$('#platform').on('change', function() {
		var source = mailClients[this.value];
		if (source) {
			// change data source
			bloodhound.clear();
			bloodhound.local = source;
			bloodhound.initialize(true);

			// reinitialize typeahead
			$('#client').typeahead('val', '');
			$('#client').typeahead('destroy');
			createTypeahead();
		}
	});

	// enable tooltips
	$('[data-toggle="tooltip"]').tooltip();
});
