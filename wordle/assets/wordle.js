document.addEventListener("keydown", function onPress(event) {
    url = `/keypress/${event.key.toUpperCase()}?key-${event.key.toUpperCase()}=`;
    fetch(`${url}`, {
        method: 'GET'
    })
        //.then(location.reload())
        //.then(response => response.json())
        //.then(data => console.log(data))
        .catch(error => console.error('Error:', error));
    location.reload();
});