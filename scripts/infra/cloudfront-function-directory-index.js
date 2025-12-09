function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // If URI ends with '/', append 'index.html'
    if (uri.endsWith('/')) {
        request.uri = uri + 'index.html';
    }
    // If URI has no extension and doesn't end with '/', try directory with index.html
    else if (!uri.includes('.')) {
        request.uri = uri + '/index.html';
    }

    return request;
}
