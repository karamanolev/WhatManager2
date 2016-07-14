chrome.runtime.onMessageExternal.addListener(function(request, sender, sendResponse) {
	if (request != "stealBibliotikId") {
		return;
	}
	chrome.cookies.getAll({}, function(cookies) {
		for (var i in cookies) {
			var cookie = cookies[i];
			if (cookie.domain == ".bibliotik.me" && cookie.name == "id") {
				sendResponse(cookie.value);
				return;
			}
		}
		sendResponse(null);
	});
	return true;
});
