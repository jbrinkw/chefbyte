document.addEventListener('DOMContentLoaded', function() {
    fetchStock();

    document.getElementById('addStockForm').addEventListener('submit', function(e) {
        e.preventDefault();
        addStock();
    });
});

function fetchStock() {
    fetch('/inventory')
        .then(response => response.json())
        .then(data => {
            const table = document.getElementById('stockTable');
            while (table.rows.length > 1) {
                table.deleteRow(1);
            }
            data.forEach(item => {
                addRow(table, item);
            });
        })
        .catch(error => {
            console.error('Error fetching stock:', error);
        });
}

function addRow(table, item) {
    const row = table.insertRow(-1);
    row.setAttribute('data-item-id', item.id);

    const itemNameCell = row.insertCell(0);
    const quantityCell = row.insertCell(1);
    const expirationDateCell = row.insertCell(2);
    const actionsCell = row.insertCell(3);

    itemNameCell.textContent = item.item_name;
    quantityCell.textContent = item.quantity;
    expirationDateCell.textContent = item.expiration_date || 'N/A';

    const editButton = createEditButton(row, item);
    const deleteButton = createDeleteButton(item.id);
    
    actionsCell.appendChild(editButton);
    actionsCell.appendChild(deleteButton);
}

function createEditButton(row, item) {
    const button = document.createElement('button');
    button.textContent = 'Edit';
    button.onclick = function() {
        makeRowEditable(row, item);
    };
    return button;
}

function createDeleteButton(itemId) {
    const button = document.createElement('button');
    button.textContent = 'Delete';
    button.onclick = function() {
        deleteStock(itemId);
    };
    return button;
}

function makeRowEditable(row, item) {
    row.cells[0].innerHTML = `<input type='text' value='${item.item_name}'>`;
    row.cells[1].innerHTML = `<input type='number' value='${item.quantity}'>`;
    row.cells[2].innerHTML = `<input type='date' value='${item.expiration_date || ''}'>`;

    const actionsCell = row.cells[3];
    actionsCell.innerHTML = ''; // Clear the actions cell
    actionsCell.appendChild(createConfirmButton(row, item.id));
    actionsCell.appendChild(createCancelButton(row, item));
}

function createConfirmButton(row, itemId) {
    const button = document.createElement('button');
    button.textContent = 'Confirm';
    button.onclick = function() {
        updateStock(row, itemId);
    };
    return button;
}

function createCancelButton(row, item) {
    const button = document.createElement('button');
    button.textContent = 'Cancel';
    button.onclick = function() {
        cancelEdit(row, item);
    };
    return button;
}

function cancelEdit(row, item) {
    // Revert the row to non-editable state with the original item data
    row.cells[0].textContent = item.item_name;
    row.cells[1].textContent = item.quantity;
    row.cells[2].textContent = item.expiration_date || 'N/A';
    const actionsCell = row.cells[3];
    actionsCell.innerHTML = '';
    actionsCell.appendChild(createEditButton(row, item));
    actionsCell.appendChild(createDeleteButton(item.id));
}

function updateStock(row, itemId) {
    const newName = row.cells[0].querySelector('input').value;
    const newQuantity = row.cells[1].querySelector('input').value;
    const newExpirationDate = row.cells[2].querySelector('input').value;

    const data = {
        item_name: newName,
        quantity: parseInt(newQuantity, 10),
        expiration_date: newExpirationDate
    };

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
        fetchStock(); // Reload the stock items
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function addStock() {
    const itemName = document.getElementById('itemName').value;
    const itemQuantity = document.getElementById('itemQuantity').value;
    const itemExpirationDate = document.getElementById('itemExpirationDate').value;

    const data = { 
        item_name: itemName, 
        quantity: itemQuantity, 
        expiration_date: itemExpirationDate 
    };

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
        fetchStock(); // Reload the stock items
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function deleteStock(itemId) {
    fetch(`/inventory/${itemId}`, {
        method: 'DELETE',
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        fetchStock(); // Reload the stock items
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}
