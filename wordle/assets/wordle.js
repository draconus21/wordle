document.addEventListener("keydown", function onPress(event) {
    url = `/keypress/${event.key}`;
    if (event.key == "Backspace") {
        url = `/keypress/Delete`;
    }
    fetch(`${url}`, {
        method: 'GET'
    })
        .then(location.reload())
        //.then(response => response.json())
        //.then(data => console.log(data))
        .catch(error => console.error('Error:', error));
    //location.reload();
    console.log(event.key);
});