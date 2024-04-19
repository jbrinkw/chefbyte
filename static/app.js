// Event listener for DOMContentLoaded to ensure the DOM is fully loaded before scripts run
document.addEventListener('DOMContentLoaded', function() {
    fetchStock(); // Call function to load and display existing stock when page loads

    // Event listener for form submission to add new stock
    document.getElementById('addStockForm').addEventListener('submit', function(e) {
        e.preventDefault(); // Prevent the default form submission action
        addStock(); // Call function to add new stock item
    });

    // Event listener to start barcode scanning
    document.getElementById('scanBarcode').addEventListener('click', function() {
        startBarcodeScanner(); // Call function to handle barcode scanning
    });
});

// Global variables to store the last barcode and the last scan timestamp
let lastBarcode = null;
let lastScanTime = 0;

// Debounce function to prevent processing the same barcode multiple times rapidly
function debounceBarcodeScan(barcode, processFunction, interval) {
    const now = Date.now();

    if (barcode !== lastBarcode || now - lastScanTime > interval) {
        lastBarcode = barcode;
        lastScanTime = now;
        processFunction(barcode); // Process the barcode using the provided function
    } else {
        console.log('Duplicate scan ignored'); // Log or handle duplicates quietly
    }
}


var stream; // Global variable to store the stream

// Add an event listener to the "Cancel Scan" button to stop the stream
document.getElementById('cancelScan').addEventListener('click', function() {
    if (stream) {
        stream.getTracks().forEach(function(track) {
            track.stop();
        });
    }
});

// Function to start barcode scanning with Quagga
function startBarcodeScanner() {
    var barcodeScannerDiv = document.getElementById('barcodeScanner');
    barcodeScannerDiv.style.display = 'block'; // Show the barcode scanner div

    var constraints = {
        video: { facingMode: "environment" }
    };

    navigator.mediaDevices.getUserMedia(constraints).then(function(mediaStream) {
        var videoElement = document.getElementById('barcodeVideo');
        videoElement.srcObject = mediaStream;
        stream = mediaStream; // Store the stream globally

        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: videoElement
            },
            decoder: {
                readers: ["ean_reader"]
            }
        }, function(err) {
            if (err) {
                console.error("Error initializing Quagga:", err);
                return;
            }
            Quagga.start();
        });

        Quagga.onDetected(function(result) {
            console.log("Detection:", result);
            Quagga.stop(); // Stop barcode scanning immediately
            stopStream(); // Stop the camera stream immediately
            barcodeScannerDiv.style.display = 'none'; // Hide the scanner div

            // Use debounce function to process the barcode
            debounceBarcodeScan(result.codeResult.code, processDetectedBarcode, 1000); // 1000 ms debounce interval
        });
    }).catch(function(err) {
        console.error("Error accessing the camera:", err);
    });
}

function stopStream() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null; // Clear the global stream reference
    }
}

function processDetectedBarcode(barcode) {
    console.log("Barcode detected:", barcode);
    fetchItemFromOpenFoodFacts(barcode);
}


function fetchItemFromOpenFoodFacts(barcode) {
    fetch(`https://world.openfoodfacts.org/api/v0/product/${barcode}.json`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 1) {
                const product = data.product;
                const itemName = product.product_name;
                const quantity = 1;
                const expirationDate = ''; // Handle as needed
                addStockFromBarcode(itemName, quantity, expirationDate);
            } else {
                alert("No product found for barcode: " + barcode);
            }
        })
        .catch(error => {
            console.error('Error fetching from OpenFoodFacts:', error);
        });
}



function addStockFromBarcode(itemName, quantity, expirationDate) {
    const data = {
        item_name: itemName,
        quantity: quantity,
        expiration_date: expirationDate
    };

    // Existing function to add stock
    fetch('/inventory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        fetchStock(); // Reload stock items to include the new item
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}


// Function to fetch and display existing stock items
function fetchStock() {
    fetch('/inventory') // API call to retrieve inventory data
        .then(response => response.json()) // Parse the JSON response
        .then(data => {
            const table = document.getElementById('stockTable'); // Access the table element
            // Loop to remove all rows except the header
            while (table.rows.length > 1) {
                table.deleteRow(1);
            }
            // Add each item as a row in the table
            data.forEach(item => {
                addRow(table, item);
            });
        })
        .catch(error => {
            console.error('Error fetching stock:', error); // Log errors if the fetch fails
        });
}

// Function to add a row to the stock table for each item
function addRow(table, item) {
    const row = table.insertRow(-1); // Insert a new row at the end of the table
    row.setAttribute('data-item-id', item.id); // Set a data attribute for the row

    // Create cells for item details and add to the row
    const itemNameCell = row.insertCell(0);
    const quantityCell = row.insertCell(1);
    const expirationDateCell = row.insertCell(2);
    const actionsCell = row.insertCell(3); // Cell for action buttons

    // Set text content for cells
    itemNameCell.textContent = item.item_name;
    quantityCell.textContent = item.quantity;
    expirationDateCell.textContent = item.expiration_date || 'N/A';

    // Create and append buttons for editing and deleting items
    const editButton = createEditButton(row, item);
    const deleteButton = createDeleteButton(item.id);
    actionsCell.appendChild(editButton);
    actionsCell.appendChild(deleteButton);
}

// Function to create an edit button for each item
function createEditButton(row, item) {
    const button = document.createElement('button');
    button.textContent = 'Edit';
    button.onclick = function() {
        makeRowEditable(row, item); // Call function to make row editable
    };
    return button;
}

// Function to create a delete button for each item
function createDeleteButton(itemId) {
    const button = document.createElement('button');
    button.textContent = 'Delete';
    button.onclick = function() {
        deleteStock(itemId); // Call function to delete the item
    };
    return button;
}

// Function to make a table row editable
function makeRowEditable(row, item) {
    // Replace cell contents with input fields pre-populated with existing values
    row.cells[0].innerHTML = `<input type='text' value='${item.item_name}'>`;
    row.cells[1].innerHTML = `<input type='number' value='${item.quantity}'>`;
    row.cells[2].innerHTML = `<input type='date' value='${item.expiration_date || ''}'>`;

    // Clear the actions cell and add confirm and cancel buttons
    const actionsCell = row.cells[3];
    actionsCell.innerHTML = '';
    actionsCell.appendChild(createConfirmButton(row, item.id));
    actionsCell.appendChild(createCancelButton(row, item));
}

// Function to create a confirm button for saving changes
function createConfirmButton(row, itemId) {
    const button = document.createElement('button');
    button.textContent = 'Confirm';
    button.onclick = function() {
        updateStock(row, itemId); // Call function to save changes
    };
    return button;
}

// Function to create a cancel button to revert changes
function createCancelButton(row, item) {
    const button = document.createElement('button');
    button.textContent = 'Cancel';
    button.onclick = function() {
        cancelEdit(row, item); // Call function to cancel editing
    };
    return button;
}

// Function to revert a row to non-editable state and restore original data
function cancelEdit(row, item) {
    // Restore original cell contents from item data
    row.cells[0].textContent = item.item_name;
    row.cells[1].textContent = item.quantity;
    row.cells[2].textContent = item.expiration_date || 'N/A';
    // Restore action buttons
    const actionsCell = row.cells[3];
    actionsCell.innerHTML = '';
    actionsCell.appendChild(createEditButton(row, item));
    actionsCell.appendChild(createDeleteButton(item.id));
}

// Function to update an item
function updateStock(row, itemId) {
    // Get updated values from input fields
    const newName = row.cells[0].querySelector('input').value;
    const newQuantity = row.cells[1].querySelector('input').value;
    const newExpirationDate = row.cells[2].querySelector('input').value;

    // Prepare data for API request
    const data = {
        item_name: newName,
        quantity: parseInt(newQuantity, 10),
        expiration_date: newExpirationDate
    };

    // API call to update the item
    fetch(`/inventory/${itemId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        fetchStock(); // Reload stock items to reflect changes
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

// Function to add a new stock item
function addStock() {
    // Get values from form inputs
    const itemName = document.getElementById('itemName').value;
    const itemQuantity = document.getElementById('itemQuantity').value;
    const itemExpirationDate = document.getElementById('itemExpirationDate').value;

    // Prepare data for API request
    const data = { 
        item_name: itemName, 
        quantity: itemQuantity, 
        expiration_date: itemExpirationDate 
    };

    // API call to add a new item
    fetch('/inventory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        fetchStock(); // Reload stock items to include the new item
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

// Function to delete an item
function deleteStock(itemId) {
    // API call to delete the item
    fetch(`/inventory/${itemId}`, {
        method: 'DELETE',
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        fetchStock(); // Reload stock items to reflect the deletion
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}
