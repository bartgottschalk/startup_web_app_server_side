function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // If URI ends with '/', append 'index.html'
    if (uri.endsWith('/')) {
        request.uri = uri + 'index.html';
    }
    // Special case: /account is a directory with index.html
    // All other extensionless files exist at root level and should not be rewritten
    else if (uri === '/account') {
        request.uri = '/account/index.html';
    }

    return request;
}
